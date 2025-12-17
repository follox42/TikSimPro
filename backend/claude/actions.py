# backend/claude/actions.py
"""
Action executor for Claude Brain.
Handles execution of actions Claude decides to take.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc


class ActionExecutor:
    """
    Executes actions requested by Claude.

    Available actions:
    - start_loop: Start the generation loop
    - stop_loop: Stop the generation loop
    - generate_one: Generate a single video
    - change_config: Update configuration
    - scrape_metrics: Trigger metrics scraping
    - scrape_account: Scrape videos from YouTube channel or TikTok profile
    - analyze_video: Analyze a specific video
    """

    def __init__(self):
        self.available_actions = {
            "start_loop": self._start_loop,
            "stop_loop": self._stop_loop,
            "generate_one": self._generate_one,
            "change_config": self._change_config,
            # Legacy action (still works but deprecated)
            "scrape_metrics": self._scrape_all_metrics,
            "scrape_account": self._scrape_account,
            # YouTube specific actions
            "scrape_youtube": self._scrape_youtube,
            "scrape_youtube_metrics": self._scrape_youtube_metrics,
            # TikTok specific actions
            "scrape_tiktok": self._scrape_tiktok,
            "scrape_tiktok_metrics": self._scrape_tiktok_metrics,
            # Combined
            "scrape_all_metrics": self._scrape_all_metrics,
            # Analysis
            "analyze_video": self._analyze_video,
            "get_video_details": self._get_video_details,
            "compare_videos": self._compare_videos,
        }

    async def execute(self, action: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """
        Execute an action.

        Args:
            action: Action dict with 'action' key and optional params
            db: Database session

        Returns:
            Result dict
        """
        action_type = action.get("action")

        if not action_type:
            return {"error": "No action specified"}

        if action_type not in self.available_actions:
            return {"error": f"Unknown action: {action_type}"}

        try:
            handler = self.available_actions[action_type]
            result = await handler(action, db)
            return {
                "success": True,
                "action": action_type,
                "result": result,
                "executed_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "action": action_type,
                "error": str(e),
                "executed_at": datetime.utcnow().isoformat()
            }

    async def _start_loop(self, action: Dict, db: AsyncSession) -> Dict:
        """Start the generation loop."""
        from backend.api.database import SystemState

        result = await db.execute(
            select(SystemState).order_by(desc(SystemState.id)).limit(1)
        )
        state = result.scalar_one_or_none()

        if not state:
            state = SystemState(loop_running=True)
            db.add(state)
        else:
            if state.loop_running:
                return {"status": "already_running"}
            state.loop_running = True
            state.updated_at = datetime.utcnow()

        await db.commit()

        # Broadcast via WebSocket
        from backend.api.websocket.handler import manager
        await manager.broadcast_pipeline_status(True, "Loop started by Claude")

        return {"status": "started"}

    async def _stop_loop(self, action: Dict, db: AsyncSession) -> Dict:
        """Stop the generation loop."""
        from backend.api.database import SystemState

        result = await db.execute(
            select(SystemState).order_by(desc(SystemState.id)).limit(1)
        )
        state = result.scalar_one_or_none()

        if state:
            state.loop_running = False
            state.updated_at = datetime.utcnow()
            await db.commit()

        # Broadcast via WebSocket
        from backend.api.websocket.handler import manager
        await manager.broadcast_pipeline_status(False, "Loop stopped by Claude")

        return {"status": "stopped"}

    async def _generate_one(self, action: Dict, db: AsyncSession) -> Dict:
        """Generate a single video."""
        try:
            # Try using Celery task
            from backend.worker import generate_video_task
            task = generate_video_task.delay()
            return {"status": "queued", "task_id": task.id}
        except Exception as e:
            # Fallback: direct generation
            try:
                import sys
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

                if result:
                    return {"status": "generated", "video_path": result}
                else:
                    return {"status": "failed", "error": "Generation returned None"}

            except Exception as inner_e:
                return {"status": "error", "error": str(inner_e)}

    async def _change_config(self, action: Dict, db: AsyncSession) -> Dict:
        """Update configuration."""
        params = action.get("params", {})

        if not params:
            return {"error": "No params provided"}

        # Update system state config
        from backend.api.database import SystemState

        result = await db.execute(
            select(SystemState).order_by(desc(SystemState.id)).limit(1)
        )
        state = result.scalar_one_or_none()

        if not state:
            state = SystemState(config=params)
            db.add(state)
        else:
            current = state.config or {}
            current.update(params)
            state.config = current
            state.updated_at = datetime.utcnow()

        await db.commit()

        # Also update config.json if requested
        if action.get("update_file", False):
            config_path = "config.json"
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                config.update(params)
                with open(config_path, "w") as f:
                    json.dump(config, f, indent=2)

        return {"status": "updated", "config": state.config}

    async def _scrape_all_metrics(self, action: Dict, db: AsyncSession) -> Dict:
        """Trigger metrics scraping for all platforms."""
        try:
            from backend.worker import scrape_metrics_task
            task = scrape_metrics_task.delay()
            return {"status": "queued", "task_id": task.id, "platforms": ["youtube", "tiktok"]}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _scrape_youtube(self, action: Dict, db: AsyncSession) -> Dict:
        """Scrape videos from the connected YouTube channel."""
        from backend.api.database import ConnectedAccount

        # Find connected YouTube account
        result = await db.execute(
            select(ConnectedAccount).where(
                ConnectedAccount.platform == "youtube",
                ConnectedAccount.is_active == True
            )
        )
        account = result.scalar_one_or_none()

        if not account:
            return {
                "error": "No YouTube account connected. Add your YouTube channel first via POST /api/accounts"
            }

        params = action.get("params", {})
        limit = params.get("limit", 20)

        try:
            from backend.worker import scrape_account_task
            task = scrape_account_task.delay("youtube", account.account_url, limit)
            return {
                "status": "queued",
                "task_id": task.id,
                "platform": "youtube",
                "account_url": account.account_url,
                "account_name": account.account_name,
                "limit": limit
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _scrape_youtube_metrics(self, action: Dict, db: AsyncSession) -> Dict:
        """Scrape metrics for published YouTube videos only."""
        try:
            from backend.worker import scrape_metrics_task
            task = scrape_metrics_task.delay(platform="youtube")
            return {"status": "queued", "task_id": task.id, "platform": "youtube"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _scrape_tiktok(self, action: Dict, db: AsyncSession) -> Dict:
        """Scrape videos from the connected TikTok profile."""
        from backend.api.database import ConnectedAccount

        # Find connected TikTok account
        result = await db.execute(
            select(ConnectedAccount).where(
                ConnectedAccount.platform == "tiktok",
                ConnectedAccount.is_active == True
            )
        )
        account = result.scalar_one_or_none()

        if not account:
            return {
                "error": "No TikTok account connected. Add your TikTok profile first via POST /api/accounts"
            }

        params = action.get("params", {})
        limit = params.get("limit", 20)

        try:
            from backend.worker import scrape_account_task
            task = scrape_account_task.delay("tiktok", account.account_url, limit)
            return {
                "status": "queued",
                "task_id": task.id,
                "platform": "tiktok",
                "account_url": account.account_url,
                "account_name": account.account_name,
                "limit": limit
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _scrape_tiktok_metrics(self, action: Dict, db: AsyncSession) -> Dict:
        """Scrape metrics for published TikTok videos only."""
        try:
            from backend.worker import scrape_metrics_task
            task = scrape_metrics_task.delay(platform="tiktok")
            return {"status": "queued", "task_id": task.id, "platform": "tiktok"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _scrape_account(self, action: Dict, db: AsyncSession) -> Dict:
        """
        Scrape all videos from a YouTube channel or TikTok profile.

        SECURITY: Only connected (user's own) accounts can be scraped.

        Params:
            platform: 'youtube' or 'tiktok'
            account_url: The channel/profile URL
            limit: Max videos to scrape (default 20)
        """
        params = action.get("params", {})
        platform = params.get("platform")
        account_url = params.get("account_url") or params.get("url")
        limit = params.get("limit", 20)

        if not platform:
            return {"error": "No platform specified (youtube or tiktok)"}
        if not account_url:
            return {"error": "No account_url specified"}
        if platform not in ["youtube", "tiktok"]:
            return {"error": f"Invalid platform: {platform}. Use 'youtube' or 'tiktok'"}

        # SECURITY: Check if account is connected (user's own account)
        from backend.api.database import ConnectedAccount, normalize_account_url

        normalized = normalize_account_url(platform, account_url)

        result = await db.execute(
            select(ConnectedAccount).where(
                ConnectedAccount.platform == platform,
                ConnectedAccount.normalized_url == normalized,
                ConnectedAccount.is_active == True
            )
        )
        account = result.scalar_one_or_none()

        if not account:
            return {
                "error": f"Account not connected. You can only scrape user's own accounts. "
                        f"The user must first add this account via the dashboard or API: "
                        f"POST /api/accounts with platform='{platform}' and account_url='{account_url}'"
            }

        try:
            from backend.worker import scrape_account_task
            task = scrape_account_task.delay(platform, account_url, limit)
            return {
                "status": "queued",
                "task_id": task.id,
                "platform": platform,
                "account_url": account_url,
                "account_name": account.account_name,
                "limit": limit
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _analyze_video(self, action: Dict, db: AsyncSession) -> Dict:
        """Analyze a specific video."""
        video_id = action.get("video_id")

        if not video_id:
            return {"error": "No video_id provided"}

        from backend.api.database import Video, Metric

        # Get video
        result = await db.execute(select(Video).where(Video.id == video_id))
        video = result.scalar_one_or_none()

        if not video:
            return {"error": f"Video {video_id} not found"}

        # Get metrics
        metrics_result = await db.execute(
            select(Metric)
            .where(Metric.video_id == video_id)
            .order_by(desc(Metric.scraped_at))
            .limit(1)
        )
        latest_metrics = metrics_result.scalar_one_or_none()

        return {
            "video_id": video_id,
            "generator": video.generator_name,
            "params": video.generator_params,
            "audio_mode": video.audio_mode,
            "validation_score": video.validation_score,
            "platform": video.platform,
            "metrics": {
                "views": latest_metrics.views if latest_metrics else 0,
                "likes": latest_metrics.likes if latest_metrics else 0,
                "engagement": latest_metrics.engagement_rate if latest_metrics else 0
            } if latest_metrics else None,
            "created_at": video.created_at.isoformat() if video.created_at else None
        }

    async def _get_video_details(self, action: Dict, db: AsyncSession) -> Dict:
        """Get detailed information about a video."""
        return await self._analyze_video(action, db)

    async def _compare_videos(self, action: Dict, db: AsyncSession) -> Dict:
        """Compare multiple videos."""
        video_ids = action.get("video_ids", [])

        if not video_ids or len(video_ids) < 2:
            return {"error": "Need at least 2 video_ids to compare"}

        from backend.api.database import Video, Metric
        from sqlalchemy import func

        results = []
        for vid in video_ids[:5]:  # Max 5 videos
            video_result = await db.execute(select(Video).where(Video.id == vid))
            video = video_result.scalar_one_or_none()

            if not video:
                continue

            metrics_result = await db.execute(
                select(Metric)
                .where(Metric.video_id == vid)
                .order_by(desc(Metric.scraped_at))
                .limit(1)
            )
            metrics = metrics_result.scalar_one_or_none()

            results.append({
                "id": vid,
                "generator": video.generator_name,
                "params": video.generator_params,
                "views": metrics.views if metrics else 0,
                "likes": metrics.likes if metrics else 0,
                "engagement": metrics.engagement_rate if metrics else 0
            })

        # Sort by views
        results.sort(key=lambda x: x["views"], reverse=True)

        return {
            "comparison": results,
            "best_performer": results[0]["id"] if results else None
        }
