# src/analytics/performance_scraper.py
"""
PerformanceScraper - Scrape video performance metrics from YouTube and TikTok.
Uses Selenium for reliable scraping of dynamic content.
"""

import re
import time
import random
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger("TikSimPro")


@dataclass
class YouTubeMetrics:
    """YouTube video metrics."""
    video_id: str
    video_url: str
    title: Optional[str] = None
    views: int = 0
    likes: int = 0
    comments: int = 0
    published_at: Optional[str] = None
    duration: Optional[str] = None
    scraped_at: datetime = None

    def __post_init__(self):
        if self.scraped_at is None:
            self.scraped_at = datetime.now()


@dataclass
class TikTokMetrics:
    """TikTok video metrics."""
    video_id: str
    video_url: str
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    description: Optional[str] = None
    scraped_at: datetime = None

    def __post_init__(self):
        if self.scraped_at is None:
            self.scraped_at = datetime.now()


class PerformanceScraper:
    """
    Scrape performance metrics from YouTube and TikTok using Selenium.

    Usage:
        scraper = PerformanceScraper(headless=True, use_cookies=True)
        yt_metrics = scraper.scrape_youtube_video("dQw4w9WgXcQ")
        tt_metrics = scraper.scrape_tiktok_video("https://tiktok.com/@user/video/123")
        scraper.close()
    """

    def __init__(self, headless: bool = True, user_data_dir: Optional[str] = None, use_cookies: bool = True):
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.use_cookies = use_cookies
        self.driver: Optional[webdriver.Chrome] = None
        self._cookies_loaded = {'youtube': False, 'tiktok': False}
        self._setup_driver()

    def _setup_driver(self):
        """Setup Chrome driver with options."""
        options = Options()

        if self.headless:
            options.add_argument("--headless=new")

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")

        # Use user data dir for cookies/login persistence
        if self.user_data_dir:
            options.add_argument(f"--user-data-dir={self.user_data_dir}")

        # Anti-detection
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # User agent
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            logger.info("Chrome driver initialized for scraping")
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {e}")
            raise

    def _load_platform_cookies(self, platform: str) -> bool:
        """Load cookies for a platform if available and not already loaded."""
        if not self.use_cookies:
            return False

        if self._cookies_loaded.get(platform):
            return True

        try:
            from src.analytics.cookie_manager import load_cookies, cookies_exist

            if cookies_exist(platform):
                success = load_cookies(self.driver, platform)
                if success:
                    self._cookies_loaded[platform] = True
                    logger.info(f"Loaded {platform} cookies successfully")
                    self._random_delay(1, 2)  # Wait for cookies to take effect
                    return True
                else:
                    logger.warning(f"Failed to load {platform} cookies")
            else:
                logger.info(f"No {platform} cookies found")

        except Exception as e:
            logger.warning(f"Error loading {platform} cookies: {e}")

        return False

    def save_current_cookies(self, platform: str) -> str:
        """Save current browser cookies for a platform."""
        try:
            from src.analytics.cookie_manager import save_cookies
            path = save_cookies(self.driver, platform)
            logger.info(f"Saved {platform} cookies to {path}")
            return path
        except Exception as e:
            logger.error(f"Error saving cookies: {e}")
            return ""

    def _random_delay(self, min_sec: float = 1.0, max_sec: float = 3.0):
        """Add random delay to avoid detection."""
        time.sleep(random.uniform(min_sec, max_sec))

    def _handle_cookie_consent(self):
        """Handle YouTube/TikTok cookie consent popups."""
        try:
            # YouTube consent buttons
            consent_selectors = [
                "button[aria-label*='Accept']",
                "button[aria-label*='Accepter']",
                "button[aria-label*='consent']",
                "ytd-button-renderer#button[aria-label*='Accept']",
                "button.yt-spec-button-shape-next--call-to-action",
                "[aria-label*='Accept all']",
                "[aria-label*='Tout accepter']",
                "button:has-text('Accept all')",
                "button:has-text('I agree')",
                "#yDmH0d button",  # Google consent
            ]

            for selector in consent_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            button.click()
                            logger.info(f"Clicked consent button: {selector}")
                            self._random_delay(1, 2)
                            return True
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"No consent popup found: {e}")
        return False

    def _save_debug_screenshot(self, name: str = "debug"):
        """Save a debug screenshot."""
        try:
            import os
            os.makedirs("/app/data", exist_ok=True)
            screenshot_path = f"/app/data/{name}_{int(time.time())}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Debug screenshot saved: {screenshot_path}")

            # Also log page source length
            page_len = len(self.driver.page_source)
            logger.info(f"Page source length: {page_len} chars")
        except Exception as e:
            logger.warning(f"Could not save debug screenshot: {e}")

    def _handle_tiktok_consent(self):
        """Handle TikTok cookie consent and login popups."""
        try:
            # TikTok consent/cookie buttons
            consent_selectors = [
                "button[data-e2e='gdpr-accept-btn']",
                "[class*='cookie'] button",
                "button:has-text('Accept all')",
                "button:has-text('Accept cookies')",
                "button:has-text('I agree')",
                "[class*='DivCookieModalContainer'] button",
                "tiktok-cookie-banner button",
            ]

            for selector in consent_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            button.click()
                            logger.info(f"Clicked TikTok consent button: {selector}")
                            self._random_delay(1, 2)
                            return True
                except Exception:
                    continue

            # Also try to close any login popup
            close_selectors = [
                "[data-e2e='modal-close-inner-button']",
                "[class*='CloseButton']",
                "button[aria-label='Close']",
            ]

            for selector in close_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            button.click()
                            logger.info(f"Closed TikTok popup: {selector}")
                            self._random_delay(0.5, 1)
                except Exception:
                    continue

        except Exception as e:
            logger.debug(f"No TikTok consent popup found: {e}")
        return False

    def _parse_count(self, text: str) -> int:
        """Parse count string like '1.5M' or '12K' to integer."""
        if not text:
            return 0

        text = text.strip().upper().replace(",", "").replace(" ", "")

        # Remove any non-numeric suffix text
        text = re.sub(r'[^0-9.KMB]', '', text)

        try:
            if 'B' in text:
                return int(float(text.replace('B', '')) * 1_000_000_000)
            elif 'M' in text:
                return int(float(text.replace('M', '')) * 1_000_000)
            elif 'K' in text:
                return int(float(text.replace('K', '')) * 1_000)
            else:
                return int(float(text))
        except (ValueError, AttributeError):
            return 0

    # ==================== YOUTUBE ====================

    def scrape_youtube_video(self, video_id_or_url: str) -> Optional[YouTubeMetrics]:
        """
        Scrape metrics for a single YouTube video.

        Args:
            video_id_or_url: Either video ID (dQw4w9WgXcQ) or full URL

        Returns:
            YouTubeMetrics or None if failed
        """
        # Extract video ID
        if "youtube.com" in video_id_or_url or "youtu.be" in video_id_or_url:
            match = re.search(r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})', video_id_or_url)
            video_id = match.group(1) if match else video_id_or_url
        else:
            video_id = video_id_or_url

        url = f"https://www.youtube.com/watch?v={video_id}"

        try:
            logger.info(f"Scraping YouTube video: {video_id}")

            # Load cookies if not already loaded
            self._load_platform_cookies('youtube')

            self.driver.get(url)
            self._random_delay(2, 4)

            # Handle cookie consent if it appears (only if not logged in)
            if not self._cookies_loaded.get('youtube'):
                self._handle_cookie_consent()

            # Wait for page load - try multiple elements
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "info-contents"))
                )
            except TimeoutException:
                # Try alternative wait
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-watch-metadata, #above-the-fold, #meta"))
                    )
                except TimeoutException:
                    logger.warning(f"Timeout waiting for video page: {video_id}")

            metrics = YouTubeMetrics(
                video_id=video_id,
                video_url=url
            )

            # Title - try multiple selectors for different YouTube layouts
            title_selectors = [
                "h1.ytd-video-primary-info-renderer yt-formatted-string",
                "h1.style-scope.ytd-watch-metadata",
                "h1 yt-formatted-string",
                "#title h1",
                "ytd-watch-metadata h1",
                "#above-the-fold h1",
                "yt-formatted-string.ytd-watch-metadata",
                "#title yt-formatted-string",
            ]
            for selector in title_selectors:
                try:
                    title_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if title_elem and title_elem.text:
                        metrics.title = title_elem.text.strip()
                        logger.info(f"Found title with selector: {selector}")
                        break
                except NoSuchElementException:
                    continue

            # Views - use JavaScript to find the correct element with "views" or "vues" text
            try:
                views_js = self.driver.execute_script("""
                    // Look for elements containing view count
                    const selectors = [
                        'ytd-video-view-count-renderer span',
                        'span.view-count',
                        '#info-contents span',
                        '#count span'
                    ];

                    for (const sel of selectors) {
                        const elems = document.querySelectorAll(sel);
                        for (const el of elems) {
                            const text = el.innerText || '';
                            // Match patterns like "123M views", "1.5M de vues", "10 000 vues"
                            if (text.match(/\\d.*?(view|vue|visionnage)/i)) {
                                return text;
                            }
                        }
                    }

                    // Fallback: look for any element with view count pattern
                    const allSpans = document.querySelectorAll('#above-the-fold span, ytd-watch-metadata span');
                    for (const span of allSpans) {
                        const text = span.innerText || '';
                        if (text.match(/^[\\d,.\s]+[KMB]?\\s*(view|vue)/i)) {
                            return text;
                        }
                    }

                    return null;
                """)
                if views_js:
                    # Extract just the number part
                    views_clean = re.sub(r'(view|vue|visionnage).*', '', views_js, flags=re.IGNORECASE).strip()
                    views_clean = views_clean.replace('\xa0', '').replace(' ', '')
                    metrics.views = self._parse_count(views_clean)
                    logger.info(f"Found views via JS: {metrics.views} (from: {views_js[:50]})")
            except Exception as e:
                logger.warning(f"JS views extraction failed: {e}")

            # Fallback with CSS selectors
            if metrics.views == 0:
                views_selectors = [
                    "ytd-video-view-count-renderer span.view-count",
                    "#info ytd-video-view-count-renderer span",
                    "span.view-count.ytd-video-view-count-renderer",
                ]
                for selector in views_selectors:
                    try:
                        views_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        views_text = views_elem.text
                        if views_text and ("view" in views_text.lower() or "vue" in views_text.lower()):
                            views_clean = re.sub(r'(view|vue).*', '', views_text, flags=re.IGNORECASE).strip()
                            metrics.views = self._parse_count(views_clean.replace(' ', ''))
                            if metrics.views > 0:
                                logger.info(f"Found views with selector: {selector} = {metrics.views}")
                                break
                    except NoSuchElementException:
                        continue

            # Likes - use JavaScript to find likes count
            try:
                likes_js = self.driver.execute_script("""
                    // Look for like button with aria-label containing the count
                    const likePatterns = ['like', 'aime', 'j'];

                    // Method 1: Check button aria-labels
                    const buttons = document.querySelectorAll('button[aria-label]');
                    for (const btn of buttons) {
                        const label = (btn.getAttribute('aria-label') || '').toLowerCase();
                        // Check if it's a like button (not dislike)
                        const isLikeBtn = likePatterns.some(p => label.includes(p)) && !label.includes('dislike') && !label.includes('pas');
                        if (isLikeBtn) {
                            // Extract number from label
                            const match = label.match(/([\\d\\s.,]+)\\s*[km]?\\s*(like|aime)/i) || label.match(/([\\d\\s.,]+[km]?)(?!.*dislike)/i);
                            if (match) {
                                return match[1].trim();
                            }
                        }
                    }

                    // Method 2: Check segmented like button text content
                    const segmented = document.querySelector('ytd-segmented-like-dislike-button-renderer, #segmented-like-button');
                    if (segmented) {
                        const likeBtn = segmented.querySelector('button:first-child, [aria-label*="like"], [aria-label*="aime"]');
                        if (likeBtn) {
                            // Check for visible text in the button
                            const textEl = likeBtn.querySelector('.yt-spec-button-shape-next__button-text-content, #text, span');
                            if (textEl && textEl.innerText) {
                                const num = textEl.innerText.match(/[\\d\\s.,]+[KMB]?/i);
                                if (num) return num[0];
                            }
                            // Check aria-label
                            const ariaLabel = likeBtn.getAttribute('aria-label') || '';
                            const match = ariaLabel.match(/([\\d\\s.,]+[KMB]?)/i);
                            if (match) return match[1];
                        }
                    }

                    // Method 3: Look for like count in toggle buttons
                    const toggleBtns = document.querySelectorAll('ytd-toggle-button-renderer button, #top-level-buttons-computed button');
                    for (const btn of toggleBtns) {
                        const label = btn.getAttribute('aria-label') || '';
                        if (label.toLowerCase().includes('like') && !label.toLowerCase().includes('dislike')) {
                            const match = label.match(/([\\d\\s.,]+[KMB]?)/i);
                            if (match) return match[1];
                        }
                    }

                    return null;
                """)

                if likes_js:
                    likes_clean = likes_js.replace('\xa0', '').replace(' ', '').replace(',', '')
                    metrics.likes = self._parse_count(likes_clean)
                    logger.info(f"Found likes via JS: {metrics.likes} (from: {likes_js})")

            except Exception as e:
                logger.warning(f"JS likes extraction failed: {e}")

            # Comments count
            try:
                # Scroll to load comments section
                self.driver.execute_script("window.scrollBy(0, 500)")
                self._random_delay(1, 2)

                comments_elem = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "#count .count-text span"
                )
                metrics.comments = self._parse_count(comments_elem.text)
            except NoSuchElementException:
                pass

            logger.info(f"YouTube metrics: {metrics.views} views, {metrics.likes} likes")
            return metrics

        except TimeoutException:
            logger.error(f"Timeout scraping YouTube video: {video_id}")
            return None
        except Exception as e:
            logger.error(f"Error scraping YouTube video: {e}")
            return None

    def scrape_youtube_channel_videos(self, channel_url: str, limit: int = 10) -> List[YouTubeMetrics]:
        """
        Scrape metrics for videos from a YouTube channel.

        Args:
            channel_url: Channel URL (youtube.com/c/... or youtube.com/@...)
            limit: Maximum number of videos to scrape

        Returns:
            List of YouTubeMetrics
        """
        try:
            # Navigate to channel videos tab
            if "/videos" not in channel_url:
                channel_url = channel_url.rstrip("/") + "/videos"

            logger.info(f"Scraping YouTube channel: {channel_url}")

            # Load cookies first if available
            self._load_platform_cookies('youtube')

            self.driver.get(channel_url)
            self._random_delay(3, 5)

            # Handle cookie consent (only if not logged in)
            if not self._cookies_loaded.get('youtube'):
                self._handle_cookie_consent()
                self._random_delay(2, 3)

            # Save debug screenshot
            self._save_debug_screenshot("youtube_channel")

            # Try multiple selectors for video grid (YouTube changes their UI frequently)
            video_selectors = [
                "ytd-rich-item-renderer a#thumbnail",
                "ytd-grid-video-renderer a#thumbnail",
                "#video-title-link",
                "a.ytd-thumbnail",
                "#contents ytd-rich-item-renderer a[href*='/watch']",
                "#items ytd-grid-video-renderer a[href*='/watch']",
            ]

            video_elements = []
            video_ids = set()  # Initialize early for JS extraction

            # Wait for page to load with any video container
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#contents, #items, ytd-rich-grid-renderer"))
                )
            except TimeoutException:
                logger.warning("Timeout waiting for video grid, trying anyway...")

            # Scroll to load more videos
            for _ in range(min(limit // 4, 5)):
                self.driver.execute_script("window.scrollBy(0, 1000)")
                self._random_delay(0.5, 1)

            # Try each selector until we find videos
            for selector in video_selectors:
                try:
                    video_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if video_elements:
                        logger.info(f"Found {len(video_elements)} videos with selector: {selector}")
                        break
                except Exception:
                    continue

            if not video_elements:
                logger.warning("No video elements found with any selector")
                # Try to get any links containing /watch?v=
                all_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/watch?v=']")
                video_elements = all_links[:limit * 2]  # Get extra in case of duplicates

                # If still nothing, try JavaScript extraction
                if not video_elements:
                    logger.info("Attempting JavaScript extraction...")
                    try:
                        js_links = self.driver.execute_script("""
                            return Array.from(document.querySelectorAll('a'))
                                .map(a => a.href)
                                .filter(h => h && h.includes('/watch?v='))
                                .slice(0, 50);
                        """)
                        if js_links:
                            logger.info(f"JavaScript found {len(js_links)} video links")
                            for link in js_links[:limit * 2]:
                                match = re.search(r'v=([a-zA-Z0-9_-]{11})', link)
                                if match:
                                    video_ids.add(match.group(1))
                    except Exception as e:
                        logger.warning(f"JavaScript extraction failed: {e}")

            # Add from video_elements (if we got any from CSS selectors)
            for elem in video_elements:
                try:
                    href = elem.get_attribute("href")
                    if href and "/watch?v=" in href:
                        match = re.search(r'v=([a-zA-Z0-9_-]{11})', href)
                        if match:
                            video_ids.add(match.group(1))
                except Exception:
                    continue

            video_ids = list(video_ids)[:limit]
            logger.info(f"Found {len(video_ids)} unique video IDs")

            # Scrape each video
            results = []
            for video_id in video_ids:
                metrics = self.scrape_youtube_video(video_id)
                if metrics:
                    results.append(metrics)
                self._random_delay(2, 4)

            logger.info(f"Scraped {len(results)} YouTube videos from channel")
            return results

        except Exception as e:
            logger.error(f"Error scraping YouTube channel: {e}")
            return []

    # ==================== TIKTOK ====================

    def scrape_tiktok_video(self, video_url: str) -> Optional[TikTokMetrics]:
        """
        Scrape metrics for a single TikTok video.

        Args:
            video_url: Full TikTok video URL

        Returns:
            TikTokMetrics or None if failed
        """
        try:
            # Extract video ID from URL
            match = re.search(r'/video/(\d+)', video_url)
            video_id = match.group(1) if match else video_url.split("/")[-1]

            logger.info(f"Scraping TikTok video: {video_id}")
            self.driver.get(video_url)
            self._random_delay(3, 5)

            metrics = TikTokMetrics(
                video_id=video_id,
                video_url=video_url
            )

            # Wait for video to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-e2e='like-count']"))
                )
            except TimeoutException:
                # Try alternative selector
                pass

            # Likes
            try:
                like_elem = self.driver.find_element(By.CSS_SELECTOR, "[data-e2e='like-count']")
                metrics.likes = self._parse_count(like_elem.text)
            except NoSuchElementException:
                try:
                    like_elem = self.driver.find_element(By.CSS_SELECTOR, "strong[data-e2e='like-count']")
                    metrics.likes = self._parse_count(like_elem.text)
                except NoSuchElementException:
                    pass

            # Comments
            try:
                comment_elem = self.driver.find_element(By.CSS_SELECTOR, "[data-e2e='comment-count']")
                metrics.comments = self._parse_count(comment_elem.text)
            except NoSuchElementException:
                pass

            # Shares
            try:
                share_elem = self.driver.find_element(By.CSS_SELECTOR, "[data-e2e='share-count']")
                metrics.shares = self._parse_count(share_elem.text)
            except NoSuchElementException:
                pass

            # Saves/Favorites
            try:
                save_elem = self.driver.find_element(By.CSS_SELECTOR, "[data-e2e='undefined-count']")
                metrics.saves = self._parse_count(save_elem.text)
            except NoSuchElementException:
                pass

            # Views (usually in video player)
            try:
                # Try to get from page title or other elements
                view_elem = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "[data-e2e='video-views'], strong[data-e2e='video-views']"
                )
                metrics.views = self._parse_count(view_elem.text)
            except NoSuchElementException:
                pass

            # Description
            try:
                desc_elem = self.driver.find_element(By.CSS_SELECTOR, "[data-e2e='browse-video-desc']")
                metrics.description = desc_elem.text[:500]  # Limit description length
            except NoSuchElementException:
                pass

            logger.info(f"TikTok metrics: {metrics.views} views, {metrics.likes} likes")
            return metrics

        except Exception as e:
            logger.error(f"Error scraping TikTok video: {e}")
            return None

    def scrape_tiktok_profile(self, profile_url: str, limit: int = 10) -> List[TikTokMetrics]:
        """
        Scrape metrics for videos from a TikTok profile.

        Args:
            profile_url: Profile URL (tiktok.com/@username)
            limit: Maximum number of videos to scrape

        Returns:
            List of TikTokMetrics
        """
        try:
            logger.info(f"Scraping TikTok profile: {profile_url}")

            # Load cookies if available
            self._load_platform_cookies('tiktok')

            self.driver.get(profile_url)
            self._random_delay(4, 6)

            # Handle cookie consent (only if not logged in)
            if not self._cookies_loaded.get('tiktok'):
                self._handle_tiktok_consent()
                self._random_delay(2, 3)

            # Save debug screenshot
            self._save_debug_screenshot("tiktok_profile")

            # Try multiple selectors for video grid (TikTok changes their UI frequently)
            video_selectors = [
                "[data-e2e='user-post-item'] a",
                "[data-e2e='user-post-item-list'] a",
                "div[class*='DivItemContainer'] a",
                "div[class*='video-feed'] a[href*='/video/']",
                "a[href*='/@'][href*='/video/']",
            ]

            video_elements = []

            # Wait for page to load with any video container
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-e2e*='post'], [class*='video'], [class*='Video']"))
                )
            except TimeoutException:
                logger.warning("Timeout waiting for TikTok video grid, trying anyway...")

            # Scroll to load more
            for _ in range(min(limit // 6, 5)):
                self.driver.execute_script("window.scrollBy(0, 1000)")
                self._random_delay(1, 2)

            # Try each selector until we find videos
            for selector in video_selectors:
                try:
                    video_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if video_elements:
                        logger.info(f"Found {len(video_elements)} videos with selector: {selector}")
                        break
                except Exception:
                    continue

            if not video_elements:
                logger.warning("No video elements found with any selector")
                # Try to get any links containing /video/
                all_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/video/']")
                video_elements = all_links[:limit * 2]

            video_urls = set()
            for elem in video_elements:
                try:
                    href = elem.get_attribute("href")
                    if href and "/video/" in href:
                        video_urls.add(href)
                except Exception:
                    continue

            # If still nothing, try JavaScript extraction
            if not video_urls:
                logger.info("Attempting JavaScript extraction for TikTok...")
                try:
                    js_links = self.driver.execute_script("""
                        return Array.from(document.querySelectorAll('a'))
                            .map(a => a.href)
                            .filter(h => h && h.includes('/video/'))
                            .slice(0, 50);
                    """)
                    if js_links:
                        logger.info(f"JavaScript found {len(js_links)} video links")
                        for link in js_links[:limit * 2]:
                            if "/video/" in link:
                                video_urls.add(link)
                except Exception as e:
                    logger.warning(f"JavaScript extraction failed: {e}")

            video_urls = list(video_urls)[:limit]
            logger.info(f"Found {len(video_urls)} unique video URLs")

            # Scrape each video
            results = []
            for url in video_urls:
                metrics = self.scrape_tiktok_video(url)
                if metrics:
                    results.append(metrics)
                self._random_delay(3, 5)  # Longer delay for TikTok

            logger.info(f"Scraped {len(results)} TikTok videos from profile")
            return results

        except Exception as e:
            logger.error(f"Error scraping TikTok profile: {e}")
            return []

    # ==================== UTILITIES ====================

    def scrape_all_platforms(self, youtube_id: Optional[str] = None,
                             tiktok_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Scrape metrics from multiple platforms at once.

        Returns:
            Dict with 'youtube' and 'tiktok' keys containing metrics
        """
        results = {}

        if youtube_id:
            results['youtube'] = self.scrape_youtube_video(youtube_id)

        if tiktok_url:
            results['tiktok'] = self.scrape_tiktok_video(tiktok_url)

        return results

    def close(self):
        """Close the browser driver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("Scraper closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# ==================== MAIN TEST ====================

if __name__ == "__main__":
    print("Testing PerformanceScraper...")
    print("Note: This requires Chrome and ChromeDriver to be installed.")

    # Test parse_count
    scraper = PerformanceScraper.__new__(PerformanceScraper)
    scraper.driver = None

    assert scraper._parse_count("1.5M") == 1_500_000
    assert scraper._parse_count("12K") == 12_000
    assert scraper._parse_count("1,234") == 1234
    assert scraper._parse_count("5.2B") == 5_200_000_000
    print("Parse count tests passed!")

    # To test actual scraping, uncomment below:
    # with PerformanceScraper(headless=True) as scraper:
    #     # Test YouTube
    #     yt = scraper.scrape_youtube_video("dQw4w9WgXcQ")
    #     if yt:
    #         print(f"YouTube: {yt.views} views, {yt.likes} likes")
    #
    #     # Test TikTok (replace with actual URL)
    #     # tt = scraper.scrape_tiktok_video("https://www.tiktok.com/@example/video/123")
    #     # if tt:
    #     #     print(f"TikTok: {tt.views} views, {tt.likes} likes")

    print("\nAll tests passed!")
