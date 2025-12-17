# src/analytics/cookie_manager.py
"""
Cookie manager for authenticated scraping.
Stores and loads browser cookies for YouTube and TikTok sessions.
"""

import os
import json
import pickle
from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path

# Cookie storage path
COOKIE_DIR = Path(__file__).parent.parent.parent / "data" / "cookies"


def get_cookie_path(platform: str) -> Path:
    """Get the cookie file path for a platform."""
    COOKIE_DIR.mkdir(parents=True, exist_ok=True)
    return COOKIE_DIR / f"{platform}_cookies.json"


def save_cookies(driver, platform: str) -> str:
    """
    Save cookies from a Selenium driver to a file.

    Args:
        driver: Selenium WebDriver instance
        platform: 'youtube' or 'tiktok'

    Returns:
        Path to saved cookie file
    """
    cookies = driver.get_cookies()
    cookie_path = get_cookie_path(platform)

    with open(cookie_path, 'w') as f:
        json.dump({
            'cookies': cookies,
            'saved_at': datetime.now().isoformat(),
            'platform': platform
        }, f, indent=2)

    return str(cookie_path)


def load_cookies(driver, platform: str) -> bool:
    """
    Load cookies into a Selenium driver.

    Args:
        driver: Selenium WebDriver instance
        platform: 'youtube' or 'tiktok'

    Returns:
        True if cookies were loaded successfully
    """
    cookie_path = get_cookie_path(platform)

    if not cookie_path.exists():
        return False

    try:
        with open(cookie_path, 'r') as f:
            data = json.load(f)

        # First navigate to the domain to set cookies
        if platform == 'youtube':
            driver.get('https://www.youtube.com')
        elif platform == 'tiktok':
            driver.get('https://www.tiktok.com')

        # Add each cookie
        for cookie in data.get('cookies', []):
            try:
                # Remove problematic fields
                cookie_clean = {k: v for k, v in cookie.items()
                              if k not in ['sameSite', 'storeId', 'hostOnly']}
                driver.add_cookie(cookie_clean)
            except Exception as e:
                print(f"Could not add cookie {cookie.get('name')}: {e}")

        return True

    except Exception as e:
        print(f"Error loading cookies: {e}")
        return False


def cookies_exist(platform: str) -> bool:
    """Check if cookies exist for a platform."""
    return get_cookie_path(platform).exists()


def get_cookie_info(platform: str) -> Optional[Dict]:
    """Get info about saved cookies."""
    cookie_path = get_cookie_path(platform)

    if not cookie_path.exists():
        return None

    try:
        with open(cookie_path, 'r') as f:
            data = json.load(f)

        return {
            'platform': platform,
            'saved_at': data.get('saved_at'),
            'cookie_count': len(data.get('cookies', [])),
            'path': str(cookie_path)
        }
    except:
        return None


def delete_cookies(platform: str) -> bool:
    """Delete saved cookies for a platform."""
    cookie_path = get_cookie_path(platform)

    if cookie_path.exists():
        cookie_path.unlink()
        return True
    return False


# For importing cookies from browser extensions or manual export
def import_cookies_from_json(json_file: str, platform: str) -> bool:
    """
    Import cookies from a JSON file (e.g., exported from browser extension).

    Expected format: array of cookie objects or {"cookies": [...]}
    """
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)

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
                'imported_from': json_file
            }, f, indent=2)

        return True

    except Exception as e:
        print(f"Error importing cookies: {e}")
        return False
