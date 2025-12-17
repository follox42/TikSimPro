# backend/api/routes/accounts.py
"""
Connected accounts management.
Only videos from connected accounts can be scraped.
"""

import os
import sys
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from backend.api.database import (
    get_db, ConnectedAccount, ConnectedAccountCreate, ConnectedAccountResponse,
    normalize_account_url
)

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("/", response_model=List[ConnectedAccountResponse])
async def list_accounts(db: AsyncSession = Depends(get_db)):
    """List all connected accounts."""
    result = await db.execute(
        select(ConnectedAccount).where(ConnectedAccount.is_active == True)
    )
    accounts = result.scalars().all()
    return accounts


@router.post("/", response_model=ConnectedAccountResponse)
async def add_account(request: ConnectedAccountCreate, db: AsyncSession = Depends(get_db)):
    """
    Add a connected account (your own YouTube channel or TikTok profile).
    Only connected accounts can be scraped for metrics.
    """
    if request.platform not in ['youtube', 'tiktok']:
        raise HTTPException(status_code=400, detail="Platform must be 'youtube' or 'tiktok'")

    # Normalize the URL for matching
    normalized = normalize_account_url(request.platform, request.account_url)

    # Check if already exists
    result = await db.execute(
        select(ConnectedAccount).where(
            ConnectedAccount.platform == request.platform,
            ConnectedAccount.normalized_url == normalized
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Reactivate if inactive
        if not existing.is_active:
            existing.is_active = True
            await db.commit()
            await db.refresh(existing)
        return existing

    # Create new account
    account = ConnectedAccount(
        platform=request.platform,
        account_url=request.account_url,
        account_name=request.account_name,
        account_id=normalized,
        normalized_url=normalized,
        is_active=True
    )

    db.add(account)
    await db.commit()
    await db.refresh(account)

    return account


@router.delete("/{account_id}")
async def remove_account(account_id: int, db: AsyncSession = Depends(get_db)):
    """Remove a connected account (soft delete)."""
    result = await db.execute(
        select(ConnectedAccount).where(ConnectedAccount.id == account_id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    account.is_active = False
    await db.commit()

    return {"status": "removed", "account_id": account_id}


@router.get("/verify/{platform}")
async def verify_url(platform: str, url: str, db: AsyncSession = Depends(get_db)):
    """
    Check if a URL belongs to a connected account.
    Returns whether scraping is allowed.
    """
    if platform not in ['youtube', 'tiktok']:
        raise HTTPException(status_code=400, detail="Platform must be 'youtube' or 'tiktok'")

    normalized = normalize_account_url(platform, url)

    result = await db.execute(
        select(ConnectedAccount).where(
            ConnectedAccount.platform == platform,
            ConnectedAccount.normalized_url == normalized,
            ConnectedAccount.is_active == True
        )
    )
    account = result.scalar_one_or_none()

    return {
        "url": url,
        "normalized": normalized,
        "platform": platform,
        "is_connected": account is not None,
        "scraping_allowed": account is not None,
        "account": ConnectedAccountResponse.model_validate(account) if account else None
    }


# Helper function for other modules
async def is_account_authorized(platform: str, url: str, db: AsyncSession) -> bool:
    """Check if an account URL is authorized for scraping."""
    normalized = normalize_account_url(platform, url)

    result = await db.execute(
        select(ConnectedAccount).where(
            ConnectedAccount.platform == platform,
            ConnectedAccount.normalized_url == normalized,
            ConnectedAccount.is_active == True
        )
    )
    return result.scalar_one_or_none() is not None
