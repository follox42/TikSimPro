# backend/api/routes/scraper.py
"""
Scraper API routes.
Direct endpoints to trigger and monitor scraping tasks.

SECURITY: Only connected (user's own) accounts can be scraped.
"""

import os
import sys
from typing import Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from backend.api.database import get_db, ConnectedAccount, normalize_account_url

router = APIRouter(prefix="/api/scraper", tags=["scraper"])


class ScrapeAccountRequest(BaseModel):
    platform: str  # "youtube" or "tiktok"
    account_url: str
    limit: Optional[int] = 20


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[dict] = None


@router.post("/account")
async def scrape_account(request: ScrapeAccountRequest, db: AsyncSession = Depends(get_db)):
    """
    Scrape videos from a YouTube channel or TikTok profile.

    SECURITY: Only connected accounts (your own) can be scraped.
    Add your accounts via POST /api/accounts first.

    Returns a task_id that can be used to check status.
    """
    if request.platform not in ["youtube", "tiktok"]:
        raise HTTPException(status_code=400, detail="Platform must be 'youtube' or 'tiktok'")

    # SECURITY: Check if account is connected (user's own account)
    normalized = normalize_account_url(request.platform, request.account_url)

    result = await db.execute(
        select(ConnectedAccount).where(
            ConnectedAccount.platform == request.platform,
            ConnectedAccount.normalized_url == normalized,
            ConnectedAccount.is_active == True
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=403,
            detail=f"Account not connected. You can only scrape your own accounts. "
                   f"Add this account first via POST /api/accounts with platform='{request.platform}' "
                   f"and account_url='{request.account_url}'"
        )

    try:
        from backend.worker import scrape_account_task

        task = scrape_account_task.delay(
            request.platform,
            request.account_url,
            request.limit
        )

        return {
            "status": "queued",
            "task_id": task.id,
            "platform": request.platform,
            "account_url": request.account_url,
            "account_name": account.account_name,
            "limit": request.limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a scraping task."""
    try:
        from backend.worker import celery_app

        result = celery_app.AsyncResult(task_id)

        response = {
            "task_id": task_id,
            "status": result.status,
            "ready": result.ready()
        }

        if result.ready():
            response["result"] = result.result
        elif result.status == "SCRAPING":
            response["meta"] = result.info

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metrics")
async def scrape_metrics():
    """Trigger metrics scraping for all published videos."""
    try:
        from backend.worker import scrape_metrics_task

        task = scrape_metrics_task.delay()

        return {
            "status": "queued",
            "task_id": task.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== COOKIE MANAGEMENT ====================

class CookieImportRequest(BaseModel):
    platform: str
    cookies: List[dict]


@router.get("/cookies")
async def list_cookies():
    """List all saved cookie sessions."""
    try:
        from src.analytics.cookie_manager import get_cookie_info

        result = {}
        for platform in ['youtube', 'tiktok']:
            info = get_cookie_info(platform)
            if info:
                result[platform] = info
            else:
                result[platform] = {"status": "no_cookies"}

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cookies/{platform}")
async def get_cookies(platform: str):
    """Get cookie info for a specific platform."""
    if platform not in ['youtube', 'tiktok']:
        raise HTTPException(status_code=400, detail="Platform must be 'youtube' or 'tiktok'")

    try:
        from src.analytics.cookie_manager import get_cookie_info

        info = get_cookie_info(platform)
        if info:
            return info
        else:
            return {"platform": platform, "status": "no_cookies"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cookies/{platform}")
async def import_cookies(platform: str, request: CookieImportRequest):
    """
    Import cookies for a platform.

    Send cookies as JSON array:
    [{"name": "cookie_name", "value": "cookie_value", "domain": ".youtube.com", ...}, ...]
    """
    if platform not in ['youtube', 'tiktok']:
        raise HTTPException(status_code=400, detail="Platform must be 'youtube' or 'tiktok'")

    try:
        from src.analytics.cookie_manager import get_cookie_path
        import json
        from datetime import datetime

        cookie_path = get_cookie_path(platform)

        with open(cookie_path, 'w') as f:
            json.dump({
                'cookies': request.cookies,
                'saved_at': datetime.now().isoformat(),
                'platform': platform
            }, f, indent=2)

        return {
            "status": "success",
            "platform": platform,
            "cookie_count": len(request.cookies),
            "path": str(cookie_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cookies/{platform}/upload")
async def upload_cookies(platform: str, file: UploadFile = File(...)):
    """
    Upload a cookies JSON file for a platform.

    The file should be a JSON array of cookies exported from browser.
    """
    if platform not in ['youtube', 'tiktok']:
        raise HTTPException(status_code=400, detail="Platform must be 'youtube' or 'tiktok'")

    try:
        import json
        from datetime import datetime
        from src.analytics.cookie_manager import get_cookie_path

        content = await file.read()
        data = json.loads(content)

        # Handle both formats
        if isinstance(data, list):
            cookies = data
        else:
            cookies = data.get('cookies', data)

        cookie_path = get_cookie_path(platform)

        with open(cookie_path, 'w') as f:
            json.dump({
                'cookies': cookies,
                'saved_at': datetime.now().isoformat(),
                'platform': platform,
                'imported_from': file.filename
            }, f, indent=2)

        return {
            "status": "success",
            "platform": platform,
            "cookie_count": len(cookies),
            "filename": file.filename
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cookies/{platform}")
async def delete_cookies(platform: str):
    """Delete saved cookies for a platform."""
    if platform not in ['youtube', 'tiktok']:
        raise HTTPException(status_code=400, detail="Platform must be 'youtube' or 'tiktok'")

    try:
        from src.analytics.cookie_manager import delete_cookies as del_cookies

        success = del_cookies(platform)
        return {
            "status": "deleted" if success else "not_found",
            "platform": platform
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
