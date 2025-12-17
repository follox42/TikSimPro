# backend/api/routes/claude.py
"""
Claude consciousness chat endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from datetime import datetime

from backend.api.database import (
    get_db, Conversation, ConversationSummary,
    ConversationCreate, ConversationResponse
)
from backend.api.websocket.handler import manager

router = APIRouter()

# Claude Brain instance (lazy loaded)
_claude_brain = None


def get_claude_brain():
    """Get or create Claude Brain instance."""
    global _claude_brain
    if _claude_brain is None:
        from backend.claude.brain import ClaudeBrain
        _claude_brain = ClaudeBrain()
    return _claude_brain


@router.post("/chat", response_model=ConversationResponse)
async def chat_with_claude(
    message: ConversationCreate,
    db: AsyncSession = Depends(get_db)
):
    """Send a message to Claude and get a response."""
    brain = get_claude_brain()

    try:
        # Get response from Claude
        response, actions = await brain.chat(message.message, db)

        # Save conversation
        conversation = Conversation(
            user_message=message.message,
            assistant_message=response,
            actions_taken=actions,
            context_snapshot=await brain.get_context_snapshot(db)
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

        # Broadcast to WebSocket clients
        await manager.broadcast({
            "type": "claude_response",
            "conversation_id": conversation.id,
            "message": response,
            "actions": actions
        })

        return conversation

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Claude error: {str(e)}")


@router.get("/history", response_model=List[ConversationResponse])
async def get_chat_history(
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Get conversation history."""
    result = await db.execute(
        select(Conversation)
        .order_by(desc(Conversation.created_at))
        .offset(offset)
        .limit(limit)
    )
    conversations = result.scalars().all()
    return conversations


@router.get("/analysis")
async def get_analysis(db: AsyncSession = Depends(get_db)):
    """Get Claude's analysis of current performance."""
    brain = get_claude_brain()

    try:
        analysis = await brain.analyze_performance(db)
        return {
            "analysis": analysis,
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@router.get("/suggestions")
async def get_suggestions(db: AsyncSession = Depends(get_db)):
    """Get Claude's suggestions for improvement."""
    brain = get_claude_brain()

    try:
        suggestions = await brain.get_suggestions(db)
        return {
            "suggestions": suggestions,
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suggestions error: {str(e)}")


@router.get("/context")
async def get_context(db: AsyncSession = Depends(get_db)):
    """Get the current context Claude has access to."""
    brain = get_claude_brain()
    context = await brain.get_context_snapshot(db)
    return context


@router.delete("/history")
async def clear_history(db: AsyncSession = Depends(get_db)):
    """Clear conversation history (creates a summary first)."""
    # Get all conversations
    result = await db.execute(select(Conversation).order_by(Conversation.created_at))
    conversations = result.scalars().all()

    if not conversations:
        return {"status": "empty", "message": "No history to clear"}

    # Create summary
    brain = get_claude_brain()
    summary_text = await brain.summarize_conversations(conversations)

    summary = ConversationSummary(
        period_start=conversations[0].created_at,
        period_end=conversations[-1].created_at,
        summary=summary_text,
        key_decisions=[c.actions_taken for c in conversations if c.actions_taken]
    )
    db.add(summary)

    # Delete conversations
    for conv in conversations:
        await db.delete(conv)

    await db.commit()

    return {
        "status": "cleared",
        "conversations_archived": len(conversations),
        "summary_id": summary.id
    }


@router.get("/summaries")
async def get_summaries(db: AsyncSession = Depends(get_db)):
    """Get conversation summaries (long-term memory)."""
    result = await db.execute(
        select(ConversationSummary)
        .order_by(desc(ConversationSummary.created_at))
    )
    summaries = result.scalars().all()

    return {
        "summaries": [
            {
                "id": s.id,
                "period_start": s.period_start.isoformat(),
                "period_end": s.period_end.isoformat(),
                "summary": s.summary,
                "key_decisions_count": len(s.key_decisions) if s.key_decisions else 0
            }
            for s in summaries
        ]
    }


@router.post("/action")
async def execute_action(
    action: dict,
    db: AsyncSession = Depends(get_db)
):
    """Execute an action that Claude suggested."""
    brain = get_claude_brain()

    action_type = action.get("action")
    if not action_type:
        raise HTTPException(status_code=400, detail="Missing 'action' field")

    try:
        result = await brain.execute_action(action, db)

        # Broadcast action result
        await manager.broadcast({
            "type": "action_executed",
            "action": action_type,
            "result": result
        })

        return {"status": "executed", "action": action_type, "result": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Action failed: {str(e)}")
