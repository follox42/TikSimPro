# src/pipelines/learning_pipeline.py
"""
LearningPipeline - Autonomous learning loop for viral content generation.
Generates, validates, publishes, scrapes performance, and learns from results.
"""

import os
import time
import json
import logging
import schedule
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field

from src.core.video_database import VideoDatabase, VideoRecord, MetricsRecord
from src.core.git_versioning import GitVersioning
from src.validators.video_validator import VideoValidator, ValidationResult
from src.ai.decision_maker import AIDecisionMaker, AIDecision
from src.analytics.performance_scraper import PerformanceScraper

logger = logging.getLogger("TikSimPro")


@dataclass
class LoopConfig:
    """Configuration for the learning loop."""
    # Generation
    output_dir: str = "videos"
    video_duration: int = 60
    video_dimensions: List[int] = field(default_factory=lambda: [1080, 1920])
    fps: int = 60

    # Validation
    min_validation_score: float = 0.7
    skip_validation: bool = False

    # Publishing
    auto_publish: bool = True
    publish_platforms: List[str] = field(default_factory=lambda: ["youtube", "tiktok"])

    # AI
    use_ai_decisions: bool = True
    ai_strategy_hint: Optional[str] = None  # "exploit", "explore", "experiment"

    # Scraping
    scrape_interval_hours: int = 1
    scrape_on_startup: bool = False

    # Loop
    loop_interval_minutes: int = 60  # Time between video generations
    max_videos_per_day: int = 24
    max_consecutive_failures: int = 3


class LearningPipeline:
    """
    Autonomous learning pipeline for viral content generation.

    The loop:
    1. AI decides parameters based on past performance
    2. Generate video with decided parameters
    3. Validate video quality
    4. Publish to platforms (if validation passes)
    5. Scrape performance metrics periodically
    6. Repeat and learn

    Usage:
        pipeline = LearningPipeline()
        pipeline.set_components(trend_analyzer, video_generator, audio_generator, ...)
        pipeline.configure(config_ranges)

        # Run once
        result = pipeline.run_once()

        # Or run continuous loop
        pipeline.start_loop()
    """

    def __init__(self,
                 loop_config: Optional[LoopConfig] = None,
                 anthropic_api_key: Optional[str] = None):
        """
        Initialize learning pipeline.

        Args:
            loop_config: Configuration for the learning loop
            anthropic_api_key: Anthropic API key for AI decisions
        """
        self.config = loop_config or LoopConfig()

        # Core components
        self.db = VideoDatabase()
        self.validator = VideoValidator(required_score=self.config.min_validation_score)
        self.ai = AIDecisionMaker(api_key=anthropic_api_key)
        self.scraper = None  # Lazy init

        # Git versioning
        try:
            self.git = GitVersioning()
        except ValueError:
            self.git = None
            logger.warning("Git versioning disabled (not a git repository)")

        # Pipeline components (set via setters)
        self.trend_analyzer = None
        self.video_generator = None
        self.audio_generator = None
        self.media_combiner = None
        self.video_enhancer = None
        self.publishers = {}

        # Config ranges (from config.json)
        self.config_ranges = {}

        # State
        self._running = False
        self._loop_thread = None
        self._scrape_thread = None
        self._videos_today = 0
        self._last_reset_date = datetime.now().date()
        self._consecutive_failures = 0

        # Callbacks
        self._on_video_generated: Optional[Callable] = None
        self._on_video_published: Optional[Callable] = None
        self._on_metrics_scraped: Optional[Callable] = None

        os.makedirs(self.config.output_dir, exist_ok=True)
        logger.info("LearningPipeline initialized")

    # ===== COMPONENT SETTERS =====

    def set_trend_analyzer(self, analyzer):
        self.trend_analyzer = analyzer

    def set_video_generator(self, generator):
        self.video_generator = generator

    def set_audio_generator(self, generator):
        self.audio_generator = generator

    def set_media_combiner(self, combiner):
        self.media_combiner = combiner

    def set_video_enhancer(self, enhancer):
        self.video_enhancer = enhancer

    def add_publisher(self, platform: str, publisher):
        self.publishers[platform] = publisher

    def set_components(self,
                       trend_analyzer=None,
                       video_generator=None,
                       audio_generator=None,
                       media_combiner=None,
                       video_enhancer=None,
                       publishers: Dict = None):
        """Set all components at once."""
        if trend_analyzer:
            self.trend_analyzer = trend_analyzer
        if video_generator:
            self.video_generator = video_generator
        if audio_generator:
            self.audio_generator = audio_generator
        if media_combiner:
            self.media_combiner = media_combiner
        if video_enhancer:
            self.video_enhancer = video_enhancer
        if publishers:
            self.publishers = publishers

    def configure(self, config_ranges: Dict[str, Any]):
        """
        Configure parameter ranges for AI decisions.

        Args:
            config_ranges: Parameter ranges from config.json
        """
        self.config_ranges = config_ranges
        logger.info(f"Configured with {len(config_ranges.get('params', {}))} parameter sets")

    # ===== MAIN LOOP =====

    def run_once(self) -> Optional[str]:
        """
        Run a single iteration of the learning loop.

        Returns:
            Path to generated video, or None if failed
        """
        logger.info("=" * 60)
        logger.info("Starting learning loop iteration...")
        logger.info("=" * 60)

        # Check daily limit
        self._check_daily_reset()
        if self._videos_today >= self.config.max_videos_per_day:
            logger.warning(f"Daily limit reached ({self.config.max_videos_per_day} videos)")
            return None

        try:
            # ===== STEP 1: AI DECISION =====
            logger.info("Step 1/5: Getting AI decision for parameters...")
            decision = self._get_ai_decision()
            logger.info(f"  Generator: {decision.generator_name}")
            logger.info(f"  Strategy: {decision.strategy} (confidence: {decision.confidence:.2f})")
            logger.info(f"  Reasoning: {decision.reasoning}")

            # ===== STEP 2: GENERATE VIDEO =====
            logger.info("Step 2/5: Generating video...")
            video_path, video_record = self._generate_video(decision)

            if not video_path:
                self._handle_failure("Video generation failed")
                return None

            logger.info(f"  Video generated: {video_path}")

            # ===== STEP 3: VALIDATE =====
            logger.info("Step 3/5: Validating video...")
            validation = self._validate_video(video_path)

            if not validation.passed and not self.config.skip_validation:
                self._handle_failure(f"Validation failed (score: {validation.score:.2f})")
                # Save to DB anyway for learning
                self._save_to_database(video_record, validation, published=False)
                return None

            logger.info(f"  Validation: {'PASSED' if validation.passed else 'SKIPPED'} (score: {validation.score:.2f})")

            # ===== STEP 4: SAVE TO DATABASE =====
            logger.info("Step 4/5: Saving to database...")
            video_id = self._save_to_database(video_record, validation, published=False)
            logger.info(f"  Saved with ID: {video_id}")

            # ===== STEP 5: PUBLISH =====
            if self.config.auto_publish and self.publishers:
                logger.info("Step 5/5: Publishing...")
                self._publish_video(video_path, video_id, decision)
            else:
                logger.info("Step 5/5: Skipping publish (disabled or no publishers)")

            # Success
            self._consecutive_failures = 0
            self._videos_today += 1

            logger.info("=" * 60)
            logger.info(f"Loop iteration completed successfully!")
            logger.info(f"  Video: {video_path}")
            logger.info(f"  Videos today: {self._videos_today}/{self.config.max_videos_per_day}")
            logger.info("=" * 60)

            # Callback
            if self._on_video_generated:
                self._on_video_generated(video_path, video_id)

            return video_path

        except Exception as e:
            logger.error(f"Loop iteration failed: {e}")
            self._handle_failure(str(e))
            return None

    def start_loop(self, blocking: bool = True):
        """
        Start the continuous learning loop.

        Args:
            blocking: If True, blocks current thread. If False, runs in background.
        """
        if self._running:
            logger.warning("Loop already running")
            return

        self._running = True
        logger.info(f"Starting learning loop (interval: {self.config.loop_interval_minutes} min)")

        # Start scraping scheduler in background
        self._start_scraping_scheduler()

        if blocking:
            self._run_loop()
        else:
            self._loop_thread = threading.Thread(target=self._run_loop, daemon=True)
            self._loop_thread.start()

    def stop_loop(self):
        """Stop the learning loop."""
        self._running = False
        logger.info("Learning loop stopped")

    def _run_loop(self):
        """Internal loop runner."""
        # Initial scrape if configured
        if self.config.scrape_on_startup:
            self._scrape_all_videos()

        while self._running:
            try:
                self.run_once()
            except Exception as e:
                logger.error(f"Loop error: {e}")

            if self._running:
                logger.info(f"Next iteration in {self.config.loop_interval_minutes} minutes...")
                time.sleep(self.config.loop_interval_minutes * 60)

    # ===== STEP IMPLEMENTATIONS =====

    def _get_ai_decision(self) -> AIDecision:
        """Get AI decision for next video parameters."""
        if not self.config.use_ai_decisions:
            return self.ai._fallback_decision(self.config_ranges)

        # Get context from database
        context = self.db.get_context_for_ai()

        # Get decision from AI
        decision = self.ai.decide_next_params(
            context=context,
            config_ranges=self.config_ranges,
            strategy_hint=self.config.ai_strategy_hint
        )

        # Save decision to database
        self.db.save_ai_decision(
            context=context,
            decision={
                'generator_name': decision.generator_name,
                'generator_params': decision.generator_params,
                'audio_mode': decision.audio_mode,
                'confidence': decision.confidence,
                'strategy': decision.strategy
            },
            reasoning=decision.reasoning
        )

        return decision

    def _generate_video(self, decision: AIDecision) -> tuple:
        """
        Generate video with decided parameters.

        Returns:
            Tuple of (video_path, VideoRecord) or (None, None) if failed
        """
        from src.utils.temp_file_manager import TempFileManager
        import shutil

        temp_manager = TempFileManager(
            base_temp_dir="temp",
            auto_cleanup=True,
            keep_on_error=True
        )

        try:
            timestamp = int(time.time())

            # Configure generator with AI-decided params
            if hasattr(self.video_generator, 'configure'):
                self.video_generator.configure(decision.generator_params)

            # Get trends
            trend_data = None
            if self.trend_analyzer:
                trend_data = self.trend_analyzer.get_trend_analysis()

            # Generate video
            video_file = temp_manager.create_video_file("video_gen", "mp4", "raw")
            self.video_generator.set_output_path(str(video_file))

            if trend_data:
                self.video_generator.apply_trend_data(trend_data)

            result_video = self.video_generator.generate()

            # Check result
            current_video = result_video if result_video and os.path.exists(result_video) else str(video_file)
            if not os.path.exists(current_video):
                return None, None

            # Generate audio if available
            audio_file = None
            if self.audio_generator:
                audio_file = temp_manager.create_audio_file("audio_gen", "wav")
                self.audio_generator.set_output_path(str(audio_file))
                self.audio_generator.set_duration(self.config.video_duration)

                # Set audio mode from AI decision
                if hasattr(self.audio_generator, 'set_mode'):
                    self.audio_generator.set_mode(decision.audio_mode)

                if trend_data:
                    self.audio_generator.apply_trend_data(trend_data)

                if hasattr(self.video_generator, 'get_audio_events'):
                    events = self.video_generator.get_audio_events()
                    self.audio_generator.add_events(events)

                audio_result = self.audio_generator.generate()
                if not (audio_result and os.path.exists(audio_result)):
                    audio_file = None

            # Combine audio
            if audio_file and self.media_combiner:
                combined_file = temp_manager.create_video_file("combined", "mp4", "combined")
                combined_result = self.media_combiner.combine(
                    current_video, str(audio_file), str(combined_file)
                )
                if combined_result and os.path.exists(combined_result):
                    current_video = combined_result

            # Enhance
            if self.video_enhancer:
                enhanced_file = temp_manager.create_video_file("enhanced", "mp4", "enhanced")
                hashtags = trend_data.popular_hashtags[:8] if trend_data else ["fyp", "viral"]
                options = {
                    "add_intro": True,
                    "add_hashtags": True,
                    "add_cta": True,
                    "intro_text": "Watch this!",
                    "hashtags": hashtags,
                    "cta_text": "Follow for more!"
                }
                enhanced_result = self.video_enhancer.enhance(
                    current_video, str(enhanced_file), options
                )
                if enhanced_result and os.path.exists(enhanced_result):
                    current_video = enhanced_result

            # Copy to final output
            final_path = os.path.join(self.config.output_dir, f"final_{timestamp}.mp4")
            shutil.copy2(current_video, final_path)

            if not os.path.exists(final_path):
                return None, None

            # Create video record
            video_record = VideoRecord(
                generator_name=decision.generator_name,
                generator_params=decision.generator_params,
                audio_mode=decision.audio_mode,
                audio_params=decision.audio_params,
                video_path=final_path,
                duration=self.config.video_duration,
                fps=self.config.fps,
                width=self.config.video_dimensions[0],
                height=self.config.video_dimensions[1],
                git_commit=self.git.get_current_commit() if self.git else None,
                midi_file=getattr(self.audio_generator, 'selected_midi_path', None) if self.audio_generator else None
            )

            return final_path, video_record

        except Exception as e:
            logger.error(f"Video generation error: {e}")
            temp_manager.mark_error()
            return None, None

    def _validate_video(self, video_path: str) -> ValidationResult:
        """Validate video before publishing."""
        audio_events = None
        if self.video_generator and hasattr(self.video_generator, 'get_audio_events'):
            audio_events = self.video_generator.get_audio_events()

        return self.validator.validate(
            video_path=video_path,
            expected_duration=self.config.video_duration,
            expected_width=self.config.video_dimensions[0],
            expected_height=self.config.video_dimensions[1],
            expected_fps=self.config.fps,
            expect_audio=self.audio_generator is not None,
            audio_events=audio_events
        )

    def _save_to_database(self,
                          video_record: VideoRecord,
                          validation: ValidationResult,
                          published: bool) -> int:
        """Save video to database."""
        video_record.validation_score = validation.score
        video_record.validation_details = validation.to_dict()

        return self.db.save_video(video_record)

    def _publish_video(self, video_path: str, video_id: int, decision: AIDecision):
        """Publish video to platforms."""
        # Get caption/hashtags from trend data or AI
        caption = decision.reasoning[:100] if decision.reasoning else "Amazing physics simulation!"
        hashtags = ["physics", "simulation", "viral", "fyp", "satisfying"]

        for platform in self.config.publish_platforms:
            if platform not in self.publishers:
                continue

            try:
                publisher = self.publishers[platform]
                result = publisher.publish(video_path, caption, hashtags)

                if result:
                    logger.info(f"Published to {platform}")

                    # Extract platform video ID
                    platform_video_id = None
                    if isinstance(result, dict):
                        platform_video_id = result.get('video_id') or result.get('id')
                    elif isinstance(result, str):
                        platform_video_id = result

                    # Update database
                    self.db.update_video_publication(
                        video_id, platform, platform_video_id or "unknown"
                    )

                    # Callback
                    if self._on_video_published:
                        self._on_video_published(video_id, platform, platform_video_id)
                else:
                    logger.error(f"Failed to publish to {platform}")

            except Exception as e:
                logger.error(f"Publishing error for {platform}: {e}")

    # ===== SCRAPING =====

    def _start_scraping_scheduler(self):
        """Start background scraping scheduler."""
        if self.config.scrape_interval_hours <= 0:
            return

        def run_scheduler():
            schedule.every(self.config.scrape_interval_hours).hours.do(self._scrape_all_videos)
            while self._running:
                schedule.run_pending()
                time.sleep(60)

        self._scrape_thread = threading.Thread(target=run_scheduler, daemon=True)
        self._scrape_thread.start()
        logger.info(f"Scraping scheduler started (every {self.config.scrape_interval_hours} hours)")

    def _scrape_all_videos(self):
        """Scrape metrics for all published videos."""
        logger.info("Starting metrics scraping...")

        if self.scraper is None:
            self.scraper = PerformanceScraper(headless=True)

        try:
            # Get videos from last 7 days
            week_ago = datetime.now() - timedelta(days=7)
            videos = self.db.get_all_videos(limit=100)

            scraped_count = 0
            for video in videos:
                if not video.platform_video_id or not video.platform:
                    continue

                try:
                    metrics = None

                    if video.platform == "youtube":
                        yt_metrics = self.scraper.scrape_youtube_video(video.platform_video_id)
                        if yt_metrics:
                            metrics = MetricsRecord(
                                video_id=video.id,
                                views=yt_metrics.views,
                                likes=yt_metrics.likes,
                                comments=yt_metrics.comments
                            )

                    elif video.platform == "tiktok":
                        tt_metrics = self.scraper.scrape_tiktok_video(video.platform_video_id)
                        if tt_metrics:
                            metrics = MetricsRecord(
                                video_id=video.id,
                                views=tt_metrics.views,
                                likes=tt_metrics.likes,
                                comments=tt_metrics.comments,
                                shares=tt_metrics.shares
                            )

                    if metrics:
                        self.db.add_metrics(metrics)
                        scraped_count += 1

                    # Rate limiting
                    time.sleep(2)

                except Exception as e:
                    logger.error(f"Error scraping video {video.id}: {e}")

            logger.info(f"Scraped metrics for {scraped_count} videos")

            # Callback
            if self._on_metrics_scraped:
                self._on_metrics_scraped(scraped_count)

        except Exception as e:
            logger.error(f"Scraping error: {e}")

    def scrape_now(self):
        """Trigger immediate scraping."""
        self._scrape_all_videos()

    # ===== UTILITIES =====

    def _check_daily_reset(self):
        """Reset daily counter if it's a new day."""
        today = datetime.now().date()
        if today > self._last_reset_date:
            self._videos_today = 0
            self._last_reset_date = today
            logger.info("Daily counter reset")

    def _handle_failure(self, reason: str):
        """Handle a failure in the loop."""
        self._consecutive_failures += 1
        logger.warning(f"Failure {self._consecutive_failures}/{self.config.max_consecutive_failures}: {reason}")

        if self._consecutive_failures >= self.config.max_consecutive_failures:
            logger.error("Too many consecutive failures, stopping loop")
            self.stop_loop()

    # ===== CALLBACKS =====

    def on_video_generated(self, callback: Callable):
        """Set callback for when video is generated."""
        self._on_video_generated = callback

    def on_video_published(self, callback: Callable):
        """Set callback for when video is published."""
        self._on_video_published = callback

    def on_metrics_scraped(self, callback: Callable):
        """Set callback for when metrics are scraped."""
        self._on_metrics_scraped = callback

    # ===== ANALYSIS =====

    def get_ai_analysis(self) -> str:
        """Get AI analysis of current performance."""
        context = self.db.get_context_for_ai()
        return self.ai.analyze_performance(context)

    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        context = self.db.get_context_for_ai()
        return {
            'total_videos': context.get('total_videos', 0),
            'videos_today': self._videos_today,
            'max_videos_per_day': self.config.max_videos_per_day,
            'consecutive_failures': self._consecutive_failures,
            'running': self._running,
            'performance_by_generator': context.get('performance_by_generator', {}),
            'best_performers': len(context.get('best_performers', []))
        }

    def get_database(self) -> VideoDatabase:
        """Get database instance."""
        return self.db


# ===== QUICK START =====

def create_learning_pipeline(
    config_path: str = "config.json",
    anthropic_api_key: Optional[str] = None,
    **loop_kwargs
) -> LearningPipeline:
    """
    Create a LearningPipeline with configuration from file.

    Args:
        config_path: Path to config.json
        anthropic_api_key: Anthropic API key
        **loop_kwargs: Override LoopConfig parameters

    Returns:
        Configured LearningPipeline
    """
    # Load config
    config_ranges = {}
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config_ranges = json.load(f)

    # Create loop config
    loop_config = LoopConfig(**loop_kwargs)

    # Create pipeline
    pipeline = LearningPipeline(
        loop_config=loop_config,
        anthropic_api_key=anthropic_api_key
    )

    pipeline.configure(config_ranges)

    return pipeline


if __name__ == "__main__":
    print("Testing LearningPipeline...")

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create pipeline
    pipeline = create_learning_pipeline(
        output_dir="test_outputs",
        auto_publish=False,  # Don't actually publish in test
        use_ai_decisions=False,  # Use fallback in test
        max_videos_per_day=5
    )

    print("\nPipeline created!")
    print(f"Stats: {pipeline.get_stats()}")

    # Test AI decision (fallback)
    print("\nTesting AI decision (fallback)...")
    decision = pipeline._get_ai_decision()
    print(f"  Generator: {decision.generator_name}")
    print(f"  Strategy: {decision.strategy}")
    print(f"  Confidence: {decision.confidence}")

    print("\nLearningPipeline tests completed!")
    print("Note: Full test requires video generator components")
