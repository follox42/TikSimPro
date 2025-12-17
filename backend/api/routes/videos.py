# backend/api/routes/videos.py
"""
Video CRUD endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import List, Optional
import os

from backend.api.database import (
    get_db, Video, Metric,
    VideoResponse, MetricResponse
)

router = APIRouter()


@router.get("/", response_model=List[VideoResponse])
async def list_videos(
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    generator: Optional[str] = None,
    platform: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all videos with optional filters."""
    query = select(Video).order_by(desc(Video.created_at))

    if generator:
        query = query.where(Video.generator_name == generator)
    if platform:
        query = query.where(Video.platform == platform)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    videos = result.scalars().all()

    return videos


@router.get("/stats")
async def video_stats(db: AsyncSession = Depends(get_db)):
    """Get video statistics."""
    # Total videos
    total_result = await db.execute(select(func.count(Video.id)))
    total = total_result.scalar()

    # By generator
    by_generator_result = await db.execute(
        select(Video.generator_name, func.count(Video.id))
        .group_by(Video.generator_name)
    )
    by_generator = {row[0]: row[1] for row in by_generator_result.all()}

    # By platform
    by_platform_result = await db.execute(
        select(Video.platform, func.count(Video.id))
        .where(Video.platform.isnot(None))
        .group_by(Video.platform)
    )
    by_platform = {row[0]: row[1] for row in by_platform_result.all()}

    # Average validation score
    avg_score_result = await db.execute(
        select(func.avg(Video.validation_score))
        .where(Video.validation_score.isnot(None))
    )
    avg_score = avg_score_result.scalar() or 0

    return {
        "total_videos": total,
        "by_generator": by_generator,
        "by_platform": by_platform,
        "average_validation_score": round(avg_score, 2)
    }


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(video_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific video."""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    return video


@router.get("/{video_id}/metrics", response_model=List[MetricResponse])
async def get_video_metrics(video_id: int, db: AsyncSession = Depends(get_db)):
    """Get metrics for a video."""
    result = await db.execute(
        select(Metric)
        .where(Metric.video_id == video_id)
        .order_by(desc(Metric.scraped_at))
    )
    metrics = result.scalars().all()
    return metrics


@router.get("/{video_id}/file")
async def get_video_file(video_id: int, db: AsyncSession = Depends(get_db)):
    """Get the video file."""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if not video.video_path or not os.path.exists(video.video_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    return FileResponse(
        video.video_path,
        media_type="video/mp4",
        filename=f"video_{video_id}.mp4"
    )


@router.get("/{video_id}/thumbnail")
async def get_video_thumbnail(video_id: int, db: AsyncSession = Depends(get_db)):
    """Get video thumbnail (generated from first frame)."""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Check for existing thumbnail
    if video.video_path:
        thumb_path = video.video_path.replace(".mp4", "_thumb.jpg")
        if os.path.exists(thumb_path):
            return FileResponse(thumb_path, media_type="image/jpeg")

    # Generate thumbnail on the fly
    if video.video_path and os.path.exists(video.video_path):
        import subprocess
        thumb_path = f"/tmp/thumb_{video_id}.jpg"

        subprocess.run([
            "ffmpeg", "-y", "-i", video.video_path,
            "-vframes", "1", "-q:v", "2",
            thumb_path
        ], capture_output=True)

        if os.path.exists(thumb_path):
            return FileResponse(thumb_path, media_type="image/jpeg")

    raise HTTPException(status_code=404, detail="Thumbnail not available")


@router.delete("/{video_id}")
async def delete_video(video_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a video."""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Delete file
    if video.video_path and os.path.exists(video.video_path):
        os.remove(video.video_path)

    await db.delete(video)
    await db.commit()

    return {"status": "deleted", "id": video_id}
