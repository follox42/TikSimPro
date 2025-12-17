# backend/worker.py
"""
Celery worker for background tasks.
Handles video generation and metrics scraping.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Redis URL
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "tiksimpro",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    worker_prefetch_multiplier=1,  # One task at a time
)


@celery_app.task(bind=True, name="generate_video")
def generate_video_task(self):
    """
    Generate a video using the learning pipeline.
    """
    try:
        from src.pipelines import create_learning_pipeline

        pipeline = create_learning_pipeline(
            output_dir="videos",
            auto_publish=False,
            use_ai_decisions=True
        )

        # Set up components
        _setup_pipeline_components(pipeline)

        # Update task state
        self.update_state(state="GENERATING", meta={"status": "starting generation"})

        # Generate
        result = pipeline.run_once()

        if result:
            # Update database with new video
            _update_video_in_db(result, pipeline)

            return {
                "status": "success",
                "video_path": result,
                "video_id": pipeline.get_current_video_id()
            }
        else:
            return {"status": "failed", "error": "Generation returned None"}

    except Exception as e:
        return {"status": "error", "error": str(e)}


@celery_app.task(bind=True, name="scrape_metrics")
def scrape_metrics_task(self, platform: str = None):
    """
    Scrape metrics for published videos.

    Args:
        platform: Optional - 'youtube' or 'tiktok' to scrape only one platform.
                  If None, scrapes all platforms.
    """
    try:
        from src.analytics.performance_scraper import PerformanceScraper
        from src.core.video_database import VideoDatabase, MetricsRecord

        db = VideoDatabase()
        scraper = PerformanceScraper(headless=True)

        videos = db.get_all_videos(limit=50)
        published = [v for v in videos if v.platform_video_id]

        # Filter by platform if specified
        if platform:
            published = [v for v in published if v.platform == platform]
            print(f"Scraping {platform} only: {len(published)} videos")

        scraped_count = 0
        platform_stats = {"youtube": 0, "tiktok": 0}

        for video in published:
            try:
                self.update_state(
                    state="SCRAPING",
                    meta={
                        "current": scraped_count,
                        "total": len(published),
                        "platform": video.platform
                    }
                )

                metrics = None

                if video.platform == "youtube":
                    yt_metrics = scraper.scrape_youtube_video(video.platform_video_id)
                    if yt_metrics:
                        metrics = MetricsRecord(
                            video_id=video.id,
                            platform="youtube",
                            views=yt_metrics.views,
                            likes=yt_metrics.likes,
                            comments=yt_metrics.comments
                        )
                        platform_stats["youtube"] += 1

                elif video.platform == "tiktok":
                    tt_metrics = scraper.scrape_tiktok_video(video.platform_video_id)
                    if tt_metrics:
                        metrics = MetricsRecord(
                            video_id=video.id,
                            platform="tiktok",
                            views=tt_metrics.views,
                            likes=tt_metrics.likes,
                            comments=tt_metrics.comments,
                            shares=tt_metrics.shares
                        )
                        platform_stats["tiktok"] += 1

                if metrics:
                    db.add_metrics(metrics)
                    scraped_count += 1

                # Rate limiting
                import time
                time.sleep(2)

            except Exception as e:
                print(f"Error scraping video {video.id}: {e}")

        scraper.close()

        return {
            "status": "success",
            "platform_filter": platform or "all",
            "scraped_count": scraped_count,
            "total_videos": len(published),
            "by_platform": platform_stats
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}


@celery_app.task(bind=True, name="scrape_account")
def scrape_account_task(self, platform: str, account_url: str, limit: int = 20):
    """
    Scrape all videos from a YouTube channel or TikTok profile.

    Args:
        platform: 'youtube' or 'tiktok'
        account_url: Channel/profile URL
        limit: Max videos to scrape
    """
    import asyncio
    from datetime import datetime

    try:
        from src.analytics.performance_scraper import PerformanceScraper

        print(f"Starting account scrape: {platform} - {account_url}")
        self.update_state(state="SCRAPING", meta={"platform": platform, "url": account_url})

        scraper = PerformanceScraper(headless=True)
        results = []

        if platform == "youtube":
            metrics_list = scraper.scrape_youtube_channel_videos(account_url, limit=limit)
            for m in metrics_list:
                results.append({
                    "platform": "youtube",
                    "video_id": m.video_id,
                    "video_url": m.video_url,
                    "title": m.title,
                    "views": m.views,
                    "likes": m.likes,
                    "comments": m.comments,
                    "scraped_at": datetime.now().isoformat()
                })

        elif platform == "tiktok":
            metrics_list = scraper.scrape_tiktok_profile(account_url, limit=limit)
            for m in metrics_list:
                results.append({
                    "platform": "tiktok",
                    "video_id": m.video_id,
                    "video_url": m.video_url,
                    "description": m.description,
                    "views": m.views,
                    "likes": m.likes,
                    "comments": m.comments,
                    "shares": m.shares,
                    "scraped_at": datetime.now().isoformat()
                })

        scraper.close()

        # Save to PostgreSQL
        if results:
            asyncio.run(_save_scraped_videos(results))

        print(f"Scraped {len(results)} videos from {platform}")
        return {
            "status": "success",
            "platform": platform,
            "videos_found": len(results),
            "videos": results[:5]  # Return first 5 as sample
        }

    except Exception as e:
        import traceback
        print(f"Error scraping account: {e}")
        traceback.print_exc()
        return {"status": "error", "error": str(e)}


async def _save_scraped_videos(videos: list):
    """Save scraped videos to PostgreSQL."""
    from backend.api.database import AsyncSessionLocal, Video, Metric
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        for v in videos:
            # Check if video already exists
            result = await session.execute(
                select(Video).where(Video.platform_video_id == v["video_id"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update metrics
                metric = Metric(
                    video_id=existing.id,
                    platform=v["platform"],
                    views=v.get("views", 0),
                    likes=v.get("likes", 0),
                    comments=v.get("comments", 0),
                    shares=v.get("shares", 0),
                    engagement_rate=_calc_engagement(v)
                )
                session.add(metric)
            else:
                # Create new video record
                video = Video(
                    generator_name=f"scraped_{v['platform']}",
                    generator_params={"source": "scrape", "url": v.get("video_url")},
                    platform=v["platform"],
                    platform_video_id=v["video_id"],
                    validation_score=None
                )
                session.add(video)
                await session.flush()

                # Add initial metrics
                metric = Metric(
                    video_id=video.id,
                    platform=v["platform"],
                    views=v.get("views", 0),
                    likes=v.get("likes", 0),
                    comments=v.get("comments", 0),
                    shares=v.get("shares", 0),
                    engagement_rate=_calc_engagement(v)
                )
                session.add(metric)

        await session.commit()


def _calc_engagement(video: dict) -> float:
    """Calculate engagement rate."""
    views = video.get("views", 0)
    if views == 0:
        return 0.0
    interactions = video.get("likes", 0) + video.get("comments", 0) + video.get("shares", 0)
    return round(interactions / views, 4)


def _setup_pipeline_components(pipeline):
    """Setup pipeline components."""
    try:
        from src.trend_analyzers.gemini_trend_analyzer import GeminiTrendAnalyzer
        pipeline.set_trend_analyzer(GeminiTrendAnalyzer())
    except Exception as e:
        print(f"Could not setup trend analyzer: {e}")

    try:
        from src.video_generators.random_generator import RandomVideoGenerator
        import json

        config = {}
        if os.path.exists("config.json"):
            with open("config.json") as f:
                config = json.load(f)

        duration = config.get("video_generator", {}).get("params", {}).get("duration", 60)

        pipeline.set_video_generator(RandomVideoGenerator(
            width=1080,
            height=1920,
            fps=60,
            duration=duration
        ))
    except Exception as e:
        print(f"Could not setup video generator: {e}")

    try:
        from src.audio_generators.viral_sound_engine import ViralSoundEngine
        pipeline.set_audio_generator(ViralSoundEngine())
    except Exception as e:
        print(f"Could not setup audio generator: {e}")

    try:
        from src.media_combiners.ffmpeg_combiner import FFmpegCombiner
        pipeline.set_media_combiner(FFmpegCombiner())
    except Exception as e:
        print(f"Could not setup media combiner: {e}")


def _update_video_in_db(video_path: str, pipeline):
    """Update PostgreSQL database with new video."""
    import asyncio
    from backend.api.database import AsyncSessionLocal, Video

    async def update():
        async with AsyncSessionLocal() as session:
            # Get video record from learning pipeline's sqlite DB
            db = pipeline.get_database()
            video_id = pipeline.get_current_video_id()

            if video_id:
                sqlite_video = db.get_video(video_id)
                if sqlite_video:
                    # Create new video in PostgreSQL
                    pg_video = Video(
                        generator_name=sqlite_video.generator_name,
                        generator_params=sqlite_video.generator_params,
                        audio_mode=sqlite_video.audio_mode,
                        audio_params=sqlite_video.audio_params,
                        video_path=video_path,
                        duration=sqlite_video.duration,
                        fps=sqlite_video.fps,
                        width=sqlite_video.width,
                        height=sqlite_video.height,
                        validation_score=sqlite_video.validation_score,
                        git_commit=sqlite_video.git_commit
                    )
                    session.add(pg_video)
                    await session.commit()

    asyncio.run(update())


if __name__ == "__main__":
    celery_app.start()
