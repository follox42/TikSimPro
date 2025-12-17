# backend/claude/memory.py
"""
Conversation memory management for Claude.
Handles persistent storage, retrieval, and summarization.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, delete


class ConversationMemory:
    """
    Manages Claude's conversation memory.

    Features:
    - Store all conversations
    - Retrieve recent conversations
    - Search conversation history
    - Automatic summarization for old conversations
    """

    def __init__(self, max_recent: int = 50, summarize_after_days: int = 7):
        self.max_recent = max_recent
        self.summarize_after_days = summarize_after_days

    async def get_recent(
        self,
        db: AsyncSession,
        limit: int = 20
    ) -> List[Any]:
        """Get recent conversations."""
        from backend.api.database import Conversation

        result = await db.execute(
            select(Conversation)
            .order_by(Conversation.created_at)  # Oldest first for context
            .limit(limit)
        )
        return result.scalars().all()

    async def save(
        self,
        db: AsyncSession,
        user_message: str,
        assistant_message: str,
        actions: List[dict] = None,
        context: Dict[str, Any] = None
    ) -> int:
        """Save a conversation."""
        from backend.api.database import Conversation

        conversation = Conversation(
            user_message=user_message,
            assistant_message=assistant_message,
            actions_taken=actions or [],
            context_snapshot=context or {}
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

        # Check if we need to summarize old conversations
        await self._maybe_summarize_old(db)

        return conversation.id

    async def search(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 10
    ) -> List[Any]:
        """Search conversation history."""
        from backend.api.database import Conversation

        # Simple text search (could be improved with full-text search)
        result = await db.execute(
            select(Conversation)
            .where(
                Conversation.user_message.ilike(f"%{query}%") |
                Conversation.assistant_message.ilike(f"%{query}%")
            )
            .order_by(desc(Conversation.created_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_context_for_prompt(
        self,
        db: AsyncSession,
        include_summaries: bool = True
    ) -> str:
        """Get formatted context for system prompt."""
        parts = []

        # Add summaries first (long-term memory)
        if include_summaries:
            from backend.api.database import ConversationSummary

            summaries_result = await db.execute(
                select(ConversationSummary)
                .order_by(desc(ConversationSummary.created_at))
                .limit(3)
            )
            summaries = summaries_result.scalars().all()

            if summaries:
                parts.append("## MÉMOIRE LONG TERME (résumés)")
                for s in summaries:
                    parts.append(f"- [{s.period_start.strftime('%Y-%m-%d')} à {s.period_end.strftime('%Y-%m-%d')}]: {s.summary[:500]}...")

        # Recent conversations
        recent = await self.get_recent(db, limit=10)
        if recent:
            parts.append("\n## CONVERSATIONS RÉCENTES")
            for conv in recent[-5:]:  # Last 5
                parts.append(f"User: {conv.user_message[:200]}...")
                parts.append(f"Assistant: {conv.assistant_message[:200]}...")
                if conv.actions_taken:
                    parts.append(f"Actions: {conv.actions_taken}")
                parts.append("")

        return "\n".join(parts)

    async def _maybe_summarize_old(self, db: AsyncSession):
        """Summarize old conversations if needed."""
        from backend.api.database import Conversation, ConversationSummary

        # Check total count
        from sqlalchemy import func
        count_result = await db.execute(select(func.count(Conversation.id)))
        total = count_result.scalar() or 0

        if total <= self.max_recent:
            return

        # Get old conversations
        cutoff = datetime.utcnow() - timedelta(days=self.summarize_after_days)
        old_result = await db.execute(
            select(Conversation)
            .where(Conversation.created_at < cutoff)
            .order_by(Conversation.created_at)
        )
        old_convs = old_result.scalars().all()

        if len(old_convs) < 10:  # Don't summarize too few
            return

        # Create summary (simplified - in production, use Claude to summarize)
        summary_text = self._simple_summarize(old_convs)

        summary = ConversationSummary(
            period_start=old_convs[0].created_at,
            period_end=old_convs[-1].created_at,
            summary=summary_text,
            key_decisions=[c.actions_taken for c in old_convs if c.actions_taken]
        )
        db.add(summary)

        # Delete old conversations
        for conv in old_convs:
            await db.delete(conv)

        await db.commit()

    def _simple_summarize(self, conversations: List[Any]) -> str:
        """Simple summarization without Claude API call."""
        topics = set()
        actions = []

        for conv in conversations:
            # Extract key topics from user messages
            words = conv.user_message.lower().split()
            for word in words:
                if len(word) > 5 and word.isalpha():
                    topics.add(word)

            # Collect actions
            if conv.actions_taken:
                actions.extend(conv.actions_taken)

        return f"Période de {len(conversations)} conversations. " \
               f"Sujets abordés: {', '.join(list(topics)[:10])}. " \
               f"Actions exécutées: {len(actions)}."

    async def clear_all(self, db: AsyncSession):
        """Clear all conversation history."""
        from backend.api.database import Conversation, ConversationSummary

        await db.execute(delete(Conversation))
        await db.execute(delete(ConversationSummary))
        await db.commit()

    async def get_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """Get memory statistics."""
        from backend.api.database import Conversation, ConversationSummary
        from sqlalchemy import func

        conv_count = await db.execute(select(func.count(Conversation.id)))
        summary_count = await db.execute(select(func.count(ConversationSummary.id)))

        oldest_result = await db.execute(
            select(Conversation.created_at)
            .order_by(Conversation.created_at)
            .limit(1)
        )
        oldest = oldest_result.scalar_one_or_none()

        return {
            "total_conversations": conv_count.scalar() or 0,
            "total_summaries": summary_count.scalar() or 0,
            "oldest_conversation": oldest.isoformat() if oldest else None,
            "max_recent": self.max_recent
        }
