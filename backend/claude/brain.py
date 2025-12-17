# backend/claude/brain.py
"""
Claude Brain - The consciousness system for TikSimPro.
Claude has full awareness of the system and can analyze, suggest, and control.
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from anthropic import AsyncAnthropic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from backend.claude.memory import ConversationMemory
from backend.claude.system_prompt import SystemPromptBuilder
from backend.claude.actions import ActionExecutor


class ClaudeBrain:
    """
    Claude with full consciousness of the TikSimPro system.

    Capabilities:
    - See all code (read-only)
    - Access database (videos, metrics, decisions)
    - Remember all conversations
    - Analyze performance and suggest improvements
    - Control the pipeline (start/stop/generate)
    - Execute actions
    """

    def __init__(self):
        self.client = AsyncAnthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
        self.model = "claude-sonnet-4-20250514"
        self.memory = ConversationMemory()
        self.prompt_builder = SystemPromptBuilder()
        self.action_executor = ActionExecutor()

    async def chat(self, user_message: str, db: AsyncSession) -> Tuple[str, List[dict]]:
        """
        Chat with Claude.

        Args:
            user_message: User's message
            db: Database session

        Returns:
            Tuple of (response_text, actions_taken)
        """
        # Build system prompt with current context
        system_prompt = await self.prompt_builder.build(db)

        # Get conversation history
        history = await self.memory.get_recent(db, limit=20)

        # Prepare messages
        messages = []
        for conv in history:
            messages.append({"role": "user", "content": conv.user_message})
            messages.append({"role": "assistant", "content": conv.assistant_message})

        messages.append({"role": "user", "content": user_message})

        # Call Claude
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            system=system_prompt,
            messages=messages
        )

        response_text = response.content[0].text

        # Extract and execute any actions from response
        actions = await self._extract_and_execute_actions(response_text, db)

        return response_text, actions

    async def _extract_and_execute_actions(
        self,
        response: str,
        db: AsyncSession
    ) -> List[dict]:
        """Extract JSON actions from response and execute them."""
        actions_taken = []

        # Find JSON blocks in response (supports nested objects)
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*"action"[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, response)

        # Also try to find complete JSON objects containing "action"
        if not matches:
            # Alternative: find balanced braces containing "action"
            for i, char in enumerate(response):
                if char == '{':
                    depth = 1
                    j = i + 1
                    while j < len(response) and depth > 0:
                        if response[j] == '{':
                            depth += 1
                        elif response[j] == '}':
                            depth -= 1
                        j += 1
                    if depth == 0:
                        candidate = response[i:j]
                        if '"action"' in candidate:
                            matches.append(candidate)

        for match in matches:
            try:
                action = json.loads(match)
                if "action" in action:
                    result = await self.action_executor.execute(action, db)
                    actions_taken.append({
                        "action": action,
                        "result": result,
                        "executed_at": datetime.utcnow().isoformat()
                    })
            except json.JSONDecodeError:
                continue
            except Exception as e:
                actions_taken.append({
                    "action": match,
                    "error": str(e),
                    "executed_at": datetime.utcnow().isoformat()
                })

        return actions_taken

    async def analyze_performance(self, db: AsyncSession) -> str:
        """Get Claude's analysis of current performance."""
        context = await self.get_context_snapshot(db)

        prompt = f"""Analyse les performances actuelles de TikSimPro.

CONTEXTE ACTUEL:
{json.dumps(context, indent=2, ensure_ascii=False, default=str)}

Fournis:
1. Un résumé des tendances observées
2. Ce qui semble marcher le mieux (générateurs, paramètres, audio)
3. Ce qui pourrait être amélioré
4. Des recommandations concrètes pour les prochaines vidéos
5. Une estimation du potentiel d'amélioration

Sois concis mais actionnable. Utilise des chiffres quand possible."""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    async def get_suggestions(self, db: AsyncSession) -> List[dict]:
        """Get specific suggestions for improvement."""
        context = await self.get_context_snapshot(db)

        prompt = f"""Basé sur l'état actuel du système TikSimPro:

{json.dumps(context, indent=2, ensure_ascii=False, default=str)}

Génère 3-5 suggestions d'amélioration concrètes.

Pour chaque suggestion, retourne un JSON avec:
- "title": titre court
- "description": explication détaillée
- "priority": "high", "medium", ou "low"
- "action": action JSON à exécuter (optionnel)
- "expected_impact": impact attendu

Réponds UNIQUEMENT avec un array JSON valide."""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse JSON response
        try:
            text = response.content[0].text
            # Find JSON array
            start = text.find('[')
            end = text.rfind(']') + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
        except:
            pass

        return []

    async def get_context_snapshot(self, db: AsyncSession) -> Dict[str, Any]:
        """Get current system context for Claude."""
        from backend.api.database import Video, Metric, SystemState, AIDecision

        context = {
            "timestamp": datetime.utcnow().isoformat(),
            "system": {},
            "videos": {},
            "metrics": {},
            "ai_decisions": []
        }

        # System state
        result = await db.execute(
            select(SystemState).order_by(desc(SystemState.id)).limit(1)
        )
        state = result.scalar_one_or_none()
        if state:
            context["system"] = {
                "loop_running": state.loop_running,
                "last_error": state.last_error,
                "last_video_id": state.last_video_id,
                "config": state.config
            }

        # Video stats
        total_result = await db.execute(select(func.count(Video.id)))
        context["videos"]["total"] = total_result.scalar() or 0

        # Recent videos
        recent_result = await db.execute(
            select(Video)
            .order_by(desc(Video.created_at))
            .limit(5)
        )
        recent = recent_result.scalars().all()
        context["videos"]["recent"] = [
            {
                "id": v.id,
                "generator": v.generator_name,
                "params": v.generator_params,
                "audio_mode": v.audio_mode,
                "validation_score": v.validation_score,
                "platform": v.platform,
                "created_at": v.created_at.isoformat() if v.created_at else None
            }
            for v in recent
        ]

        # Performance by generator
        perf_result = await db.execute(
            select(
                Video.generator_name,
                func.count(Video.id).label("count"),
                func.avg(Metric.views).label("avg_views"),
                func.avg(Metric.engagement_rate).label("avg_engagement")
            )
            .join(Metric, Video.id == Metric.video_id, isouter=True)
            .group_by(Video.generator_name)
        )
        context["videos"]["by_generator"] = {
            row.generator_name: {
                "count": row.count,
                "avg_views": round(row.avg_views or 0, 0),
                "avg_engagement": round(row.avg_engagement or 0, 4)
            }
            for row in perf_result.all()
        }

        # Metrics summary
        metrics_result = await db.execute(
            select(
                func.sum(Metric.views).label("total_views"),
                func.sum(Metric.likes).label("total_likes"),
                func.avg(Metric.engagement_rate).label("avg_engagement")
            )
        )
        row = metrics_result.one()
        context["metrics"] = {
            "total_views": row.total_views or 0,
            "total_likes": row.total_likes or 0,
            "avg_engagement": round(row.avg_engagement or 0, 4)
        }

        # Recent AI decisions
        decisions_result = await db.execute(
            select(AIDecision)
            .order_by(desc(AIDecision.created_at))
            .limit(3)
        )
        context["ai_decisions"] = [
            {
                "id": d.id,
                "decision": d.decision,
                "reasoning": d.reasoning[:200] if d.reasoning else None,
                "created_at": d.created_at.isoformat() if d.created_at else None
            }
            for d in decisions_result.scalars().all()
        ]

        return context

    async def summarize_conversations(
        self,
        conversations: List[Any]
    ) -> str:
        """Summarize a list of conversations for archival."""
        if not conversations:
            return "No conversations to summarize."

        conv_text = "\n\n".join([
            f"User: {c.user_message}\nAssistant: {c.assistant_message}"
            for c in conversations[:50]  # Limit for token management
        ])

        prompt = f"""Résume les conversations suivantes en gardant les informations importantes:
- Décisions prises
- Problèmes identifiés
- Améliorations suggérées
- Actions exécutées

CONVERSATIONS:
{conv_text}

Fournis un résumé structuré et concis."""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    async def execute_action(self, action: dict, db: AsyncSession) -> dict:
        """Execute a specific action."""
        return await self.action_executor.execute(action, db)
