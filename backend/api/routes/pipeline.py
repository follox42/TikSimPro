# backend/api/routes/pipeline.py
"""
Pipeline control endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timedelta
from typing import Optional

from backend.api.database import get_db, Video, SystemState, PipelineStatus
from backend.api.websocket.handler import manager

router = APIRouter()

# Global pipeline state (in production, use Redis)
_pipeline_task = None


@router.get("/status", response_model=PipelineStatus)
async def pipeline_status(db: AsyncSession = Depends(get_db)):
    """Get current pipeline status."""
    # Get system state
    result = await db.execute(select(SystemState).order_by(desc(SystemState.id)).limit(1))
    state = result.scalar_one_or_none()

    # Count videos today
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_result = await db.execute(
        select(func.count(Video.id)).where(Video.created_at >= today)
    )
    videos_today = today_result.scalar() or 0

    # Total videos
    total_result = await db.execute(select(func.count(Video.id)))
    total = total_result.scalar() or 0

    return PipelineStatus(
        running=state.loop_running if state else False,
        last_video_id=state.last_video_id if state else None,
        last_error=state.last_error if state else None,
        videos_today=videos_today,
        total_videos=total
    )


@router.post("/start")
async def start_pipeline(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Start the generation pipeline."""
    global _pipeline_task

    # Check if already running
    result = await db.execute(select(SystemState).order_by(desc(SystemState.id)).limit(1))
    state = result.scalar_one_or_none()

    if state and state.loop_running:
        raise HTTPException(status_code=400, detail="Pipeline already running")

    # Update state
    if not state:
        state = SystemState(loop_running=True)
        db.add(state)
    else:
        state.loop_running = True
        state.updated_at = datetime.utcnow()

    await db.commit()

    # Start background task
    background_tasks.add_task(run_pipeline_loop, db)

    # Notify via WebSocket
    await manager.broadcast({
        "type": "pipeline_status",
        "running": True,
        "message": "Pipeline started"
    })

    return {"status": "started", "message": "Pipeline started"}


@router.post("/stop")
async def stop_pipeline(db: AsyncSession = Depends(get_db)):
    """Stop the generation pipeline."""
    global _pipeline_task

    # Update state
    result = await db.execute(select(SystemState).order_by(desc(SystemState.id)).limit(1))
    state = result.scalar_one_or_none()

    if state:
        state.loop_running = False
        state.updated_at = datetime.utcnow()
        await db.commit()

    # Notify via WebSocket
    await manager.broadcast({
        "type": "pipeline_status",
        "running": False,
        "message": "Pipeline stopped"
    })

    return {"status": "stopped", "message": "Pipeline stopped"}


@router.post("/generate")
async def generate_one(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Generate a single video."""
    # Start generation in background
    background_tasks.add_task(generate_single_video)

    # Notify via WebSocket
    await manager.broadcast({
        "type": "generation_started",
        "message": "Starting video generation"
    })

    return {"status": "generating", "message": "Video generation started"}


@router.get("/config")
async def get_config(db: AsyncSession = Depends(get_db)):
    """Get current pipeline configuration."""
    result = await db.execute(select(SystemState).order_by(desc(SystemState.id)).limit(1))
    state = result.scalar_one_or_none()

    # Load config.json
    import json
    import os

    config = {}
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            config = json.load(f)

    return {
        "config": config,
        "system_state": state.config if state else {}
    }


@router.put("/config")
async def update_config(
    config_update: dict,
    db: AsyncSession = Depends(get_db)
):
    """Update pipeline configuration."""
    result = await db.execute(select(SystemState).order_by(desc(SystemState.id)).limit(1))
    state = result.scalar_one_or_none()

    if not state:
        state = SystemState(config=config_update)
        db.add(state)
    else:
        current_config = state.config or {}
        current_config.update(config_update)
        state.config = current_config
        state.updated_at = datetime.utcnow()

    await db.commit()

    return {"status": "updated", "config": state.config}


# ===== BACKGROUND TASKS =====

async def run_pipeline_loop(db: AsyncSession):
    """Run the pipeline loop (background task)."""
    import asyncio

    while True:
        # Check if still running
        result = await db.execute(select(SystemState).order_by(desc(SystemState.id)).limit(1))
        state = result.scalar_one_or_none()

        if not state or not state.loop_running:
            break

        try:
            # Generate video
            await generate_single_video()

            # Notify
            await manager.broadcast({
                "type": "video_generated",
                "message": "New video generated"
            })

        except Exception as e:
            # Update error state
            state.last_error = str(e)
            await db.commit()

            await manager.broadcast({
                "type": "error",
                "message": f"Generation error: {e}"
            })

        # Wait before next iteration (30 minutes)
        await asyncio.sleep(30 * 60)


async def generate_single_video():
    """Generate a single video using Celery task."""
    try:
        # Import here to avoid circular imports
        from backend.worker import generate_video_task

        # Queue task
        task = generate_video_task.delay()

        return task.id

    except Exception as e:
        print(f"Error queuing video generation: {e}")

        # Fallback: run directly (for development)
        try:
            import sys
            import os
            sys.path.insert(0, os.getcwd())

            from src.pipelines import create_learning_pipeline
            from dotenv import load_dotenv
            load_dotenv()

            pipeline = create_learning_pipeline(
                output_dir="videos",
                auto_publish=False,
                use_ai_decisions=True
            )

            result = pipeline.run_once()
            return result

        except Exception as inner_e:
            print(f"Direct generation also failed: {inner_e}")
            raise
