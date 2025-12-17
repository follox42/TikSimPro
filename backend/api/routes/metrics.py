# backend/api/routes/metrics.py
"""
Metrics and analytics endpoints.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import List, Optional
from datetime import datetime, timedelta

from backend.api.database import get_db, Video, Metric, MetricResponse

router = APIRouter()


@router.get("/summary")
async def metrics_summary(db: AsyncSession = Depends(get_db)):
    """Get overall metrics summary."""
    # Total views, likes, etc.
    result = await db.execute(
        select(
            func.sum(Metric.views).label("total_views"),
            func.sum(Metric.likes).label("total_likes"),
            func.sum(Metric.comments).label("total_comments"),
            func.sum(Metric.shares).label("total_shares"),
            func.avg(Metric.engagement_rate).label("avg_engagement")
        )
    )
    row = result.one()

    # Best performing video
    best_result = await db.execute(
        select(Metric)
        .order_by(desc(Metric.views))
        .limit(1)
    )
    best = best_result.scalar_one_or_none()

    return {
        "total_views": row.total_views or 0,
        "total_likes": row.total_likes or 0,
        "total_comments": row.total_comments or 0,
        "total_shares": row.total_shares or 0,
        "average_engagement_rate": round(row.avg_engagement or 0, 4),
        "best_video_id": best.video_id if best else None,
        "best_video_views": best.views if best else 0
    }


@router.get("/tiktok")
async def tiktok_metrics(
    days: int = Query(7, le=90),
    db: AsyncSession = Depends(get_db)
):
    """Get TikTok specific metrics."""
    since = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(Metric)
        .where(Metric.platform == "tiktok")
        .where(Metric.scraped_at >= since)
        .order_by(desc(Metric.scraped_at))
    )
    metrics = result.scalars().all()

    # Aggregate
    total_views = sum(m.views for m in metrics)
    total_likes = sum(m.likes for m in metrics)
    total_shares = sum(m.shares for m in metrics)

    # Group by video
    by_video = {}
    for m in metrics:
        if m.video_id not in by_video:
            by_video[m.video_id] = {
                "video_id": m.video_id,
                "views": m.views,
                "likes": m.likes,
                "shares": m.shares,
                "comments": m.comments
            }

    return {
        "platform": "tiktok",
        "period_days": days,
        "total_views": total_views,
        "total_likes": total_likes,
        "total_shares": total_shares,
        "video_count": len(by_video),
        "videos": list(by_video.values())
    }


@router.get("/youtube")
async def youtube_metrics(
    days: int = Query(7, le=90),
    db: AsyncSession = Depends(get_db)
):
    """Get YouTube specific metrics."""
    since = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(Metric)
        .where(Metric.platform == "youtube")
        .where(Metric.scraped_at >= since)
        .order_by(desc(Metric.scraped_at))
    )
    metrics = result.scalars().all()

    # Aggregate
    total_views = sum(m.views for m in metrics)
    total_likes = sum(m.likes for m in metrics)

    # Group by video
    by_video = {}
    for m in metrics:
        if m.video_id not in by_video:
            by_video[m.video_id] = {
                "video_id": m.video_id,
                "views": m.views,
                "likes": m.likes,
                "comments": m.comments,
                "watch_time_avg": m.watch_time_avg
            }

    return {
        "platform": "youtube",
        "period_days": days,
        "total_views": total_views,
        "total_likes": total_likes,
        "video_count": len(by_video),
        "videos": list(by_video.values())
    }


@router.get("/performance")
async def performance_by_generator(db: AsyncSession = Depends(get_db)):
    """Get performance breakdown by generator."""
    # Join videos and metrics
    result = await db.execute(
        select(
            Video.generator_name,
            func.count(Video.id).label("video_count"),
            func.avg(Metric.views).label("avg_views"),
            func.avg(Metric.likes).label("avg_likes"),
            func.avg(Metric.engagement_rate).label("avg_engagement")
        )
        .join(Metric, Video.id == Metric.video_id, isouter=True)
        .group_by(Video.generator_name)
    )

    rows = result.all()

    return {
        "by_generator": [
            {
                "generator": row.generator_name,
                "video_count": row.video_count,
                "avg_views": round(row.avg_views or 0, 0),
                "avg_likes": round(row.avg_likes or 0, 0),
                "avg_engagement": round(row.avg_engagement or 0, 4)
            }
            for row in rows
        ]
    }


@router.get("/timeline")
async def metrics_timeline(
    days: int = Query(7, le=30),
    db: AsyncSession = Depends(get_db)
):
    """Get metrics over time for charts."""
    since = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(Metric)
        .where(Metric.scraped_at >= since)
        .order_by(Metric.scraped_at)
    )
    metrics = result.scalars().all()

    # Group by day
    by_day = {}
    for m in metrics:
        day = m.scraped_at.strftime("%Y-%m-%d")
        if day not in by_day:
            by_day[day] = {"date": day, "views": 0, "likes": 0, "videos": 0}
        by_day[day]["views"] += m.views
        by_day[day]["likes"] += m.likes
        by_day[day]["videos"] += 1

    return {
        "period_days": days,
        "timeline": list(by_day.values())
    }


@router.get("/best-performers")
async def best_performers(
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get best performing videos."""
    # Get latest metrics per video
    result = await db.execute(
        select(Metric)
        .order_by(desc(Metric.views))
        .limit(limit)
    )
    metrics = result.scalars().all()

    # Get video details
    video_ids = [m.video_id for m in metrics]
    videos_result = await db.execute(
        select(Video).where(Video.id.in_(video_ids))
    )
    videos = {v.id: v for v in videos_result.scalars().all()}

    return {
        "best_performers": [
            {
                "video_id": m.video_id,
                "generator": videos[m.video_id].generator_name if m.video_id in videos else None,
                "platform": m.platform,
                "views": m.views,
                "likes": m.likes,
                "engagement_rate": m.engagement_rate,
                "created_at": videos[m.video_id].created_at.isoformat() if m.video_id in videos else None
            }
            for m in metrics
        ]
    }
