#!/usr/bin/env python3
"""
Test script for the AI Content Manager / Learning System
Run: python3 test_learning_system.py
"""

import os
import sys
import logging

# Load .env file
from dotenv import load_dotenv
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TikSimPro")


def test_database():
    """Test the video database."""
    print("\n" + "=" * 60)
    print("TEST 1: Video Database")
    print("=" * 60)

    from src.core.video_database import VideoDatabase, VideoRecord, MetricsRecord

    # Use test database
    db = VideoDatabase(db_path="data/test_tiksimpro.db")

    # Create a test video record
    record = VideoRecord(
        generator_name="GravityFallsSimulator",
        generator_params={"gravity": 1850, "restitution": 1.0, "ball_size": 12},
        audio_mode="maximum_punch",
        audio_params={"progressive_build": True},
        video_path="/tmp/test_video.mp4",
        duration=60,
        fps=60,
        width=1080,
        height=1920,
        validation_score=0.85
    )

    video_id = db.save_video(record)
    print(f"  Video saved with ID: {video_id}")

    # Add some metrics
    metrics = MetricsRecord(
        video_id=video_id,
        platform="youtube",
        views=1500,
        likes=120,
        comments=25,
        shares=15
    )
    db.add_metrics(metrics)
    print(f"  Metrics added: {metrics.views} views, {metrics.likes} likes")

    # Get all videos
    videos = db.get_all_videos()
    print(f"  Total videos in DB: {len(videos)}")

    # Get best performers
    best = db.get_best_performers(limit=5)
    print(f"  Best performers: {len(best)}")

    # Get AI context
    context = db.get_context_for_ai()
    print(f"  AI Context: {context['total_videos']} videos")
    if context.get('performance_by_generator'):
        print("  Performance by generator:")
        for gen, stats in context['performance_by_generator'].items():
            print(f"    - {gen}: {stats['video_count']} videos, avg views: {stats['avg_views']:.0f}")

    print("  ✓ Database test PASSED")
    return db


def test_git_versioning():
    """Test git versioning."""
    print("\n" + "=" * 60)
    print("TEST 2: Git Versioning")
    print("=" * 60)

    from src.core.git_versioning import GitVersioning

    git = GitVersioning()

    commit = git.get_current_commit()
    print(f"  Current commit: {commit[:8]}...")

    branch = git.get_current_branch()
    print(f"  Current branch: {branch}")

    recent = git.get_recent_commits(3)
    print(f"  Recent commits:")
    for c in recent:
        print(f"    - [{c['hash'][:7]}] {c['message'][:50]}...")

    print("  ✓ Git versioning test PASSED")


def test_validator():
    """Test video validator."""
    print("\n" + "=" * 60)
    print("TEST 3: Video Validator")
    print("=" * 60)

    from src.validators import VideoValidator
    from glob import glob

    validator = VideoValidator()

    # Find a real video to test
    video_patterns = [
        "videos/final_*.mp4",
        "output/final_*.mp4",
        "test_outputs/*.mp4"
    ]

    video_path = None
    for pattern in video_patterns:
        matches = glob(pattern)
        if matches:
            video_path = matches[0]
            break

    if video_path:
        print(f"  Testing with: {video_path}")
        result = validator.validate(video_path, expect_audio=True)
        print(f"  Passed: {result.passed}")
        print(f"  Score: {result.score:.2f}")
        print(f"  Checks: {result.checks}")
        if result.warnings:
            print(f"  Warnings: {result.warnings}")
    else:
        print("  No video found to test, testing with non-existent file...")
        result = validator.validate("/tmp/nonexistent.mp4")
        print(f"  Passed (expected False): {result.passed}")
        print(f"  Errors: {result.errors}")

    print("  ✓ Validator test PASSED")


def test_ai_decision():
    """Test AI decision maker."""
    print("\n" + "=" * 60)
    print("TEST 4: AI Decision Maker")
    print("=" * 60)

    from src.ai import AIDecisionMaker
    import json

    # Load config
    config_ranges = {}
    if os.path.exists("config.json"):
        with open("config.json", 'r') as f:
            config_ranges = json.load(f)
        print(f"  Loaded config.json")

    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        print(f"  API key found: {api_key[:10]}...")
    else:
        print("  No API key - using fallback mode")

    maker = AIDecisionMaker(api_key=api_key)

    # Get context from real DB if available
    from src.core.video_database import VideoDatabase
    db = VideoDatabase()
    context = db.get_context_for_ai()

    print(f"  Context: {context['total_videos']} videos in history")

    # Get decision
    decision = maker.decide_next_params(context, config_ranges)

    print(f"\n  AI Decision:")
    print(f"    Generator: {decision.generator_name}")
    print(f"    Strategy: {decision.strategy}")
    print(f"    Confidence: {decision.confidence:.2f}")
    print(f"    Audio mode: {decision.audio_mode}")
    print(f"    Params: {decision.generator_params}")
    print(f"    Reasoning: {decision.reasoning}")

    print("  ✓ AI Decision test PASSED")
    return decision


def test_learning_pipeline():
    """Test the learning pipeline."""
    print("\n" + "=" * 60)
    print("TEST 5: Learning Pipeline")
    print("=" * 60)

    from src.pipelines import create_learning_pipeline

    pipeline = create_learning_pipeline(
        output_dir="test_outputs",
        auto_publish=False,
        use_ai_decisions=False,  # Use fallback for testing
        max_videos_per_day=10
    )

    print("  Pipeline created")

    stats = pipeline.get_stats()
    print(f"\n  Pipeline Stats:")
    print(f"    Total videos: {stats['total_videos']}")
    print(f"    Videos today: {stats['videos_today']}/{stats['max_videos_per_day']}")
    print(f"    Running: {stats['running']}")
    print(f"    Failures: {stats['consecutive_failures']}")

    # Test AI decision through pipeline
    decision = pipeline._get_ai_decision()
    print(f"\n  Next decision: {decision.generator_name} ({decision.strategy})")

    print("  ✓ Learning Pipeline test PASSED")
    return pipeline


def test_full_generation(pipeline=None):
    """Test full video generation (optional - takes time)."""
    print("\n" + "=" * 60)
    print("TEST 6: Full Generation (Optional)")
    print("=" * 60)

    response = input("  Run full video generation? (y/N): ").strip().lower()
    if response != 'y':
        print("  Skipped")
        return

    if pipeline is None:
        from src.pipelines import create_learning_pipeline
        pipeline = create_learning_pipeline(
            output_dir="test_outputs",
            auto_publish=False,
            use_ai_decisions=False
        )

    # Need to set up components
    print("\n  Setting up components...")

    try:
        # Trend analyzer
        from src.trend_analyzers.gemini_trend_analyzer import GeminiTrendAnalyzer
        pipeline.set_trend_analyzer(GeminiTrendAnalyzer())
        print("    ✓ Trend analyzer")
    except Exception as e:
        print(f"    ✗ Trend analyzer: {e}")
        return

    try:
        # Video generator
        from src.video_generators.random_generator import RandomVideoGenerator
        pipeline.set_video_generator(RandomVideoGenerator(
            width=1080, height=1920, fps=60, duration=30  # Short for testing
        ))
        print("    ✓ Video generator")
    except Exception as e:
        print(f"    ✗ Video generator: {e}")
        return

    try:
        # Audio generator
        from src.audio_generators.viral_sound_engine import ViralSoundEngine
        pipeline.set_audio_generator(ViralSoundEngine())
        print("    ✓ Audio generator")
    except Exception as e:
        print(f"    ✗ Audio generator: {e}")

    try:
        # Media combiner
        from src.media_combiners.ffmpeg_combiner import FFmpegCombiner
        pipeline.set_media_combiner(FFmpegCombiner())
        print("    ✓ Media combiner")
    except Exception as e:
        print(f"    ✗ Media combiner: {e}")

    print("\n  Running one iteration...")
    result = pipeline.run_once()

    if result:
        print(f"\n  ✓ Video generated: {result}")

        # Check in database
        db = pipeline.get_database()
        videos = db.get_all_videos(limit=1)
        if videos:
            v = videos[0]
            print(f"  Saved to DB: ID={v.id}, generator={v.generator_name}")
    else:
        print("\n  ✗ Generation failed (check logs)")


def show_database_contents():
    """Show current database contents."""
    print("\n" + "=" * 60)
    print("DATABASE CONTENTS")
    print("=" * 60)

    from src.core.video_database import VideoDatabase

    db = VideoDatabase()
    videos = db.get_all_videos(limit=20)

    if not videos:
        print("  No videos in database yet")
        return

    print(f"\n  Found {len(videos)} videos:\n")

    for v in videos:
        print(f"  [{v.id}] {v.generator_name}")
        print(f"      Created: {v.created_at}")
        print(f"      Params: {v.generator_params}")
        print(f"      Audio: {v.audio_mode}")
        if v.validation_score:
            print(f"      Validation: {v.validation_score:.2f}")
        if v.platform:
            print(f"      Published: {v.platform} ({v.platform_video_id})")
        print()

    # Show metrics
    context = db.get_context_for_ai()
    if context.get('performance_by_generator'):
        print("\n  Performance Summary:")
        for gen, stats in context['performance_by_generator'].items():
            print(f"    {gen}:")
            print(f"      Videos: {stats['video_count']}")
            print(f"      Avg views: {stats['avg_views']:.0f}")
            print(f"      Avg engagement: {stats['avg_engagement']:.4f}")


def main():
    print("=" * 60)
    print("  AI CONTENT MANAGER - TEST SUITE")
    print("=" * 60)

    print("\nThis will test all components of the learning system.")
    print("Components:")
    print("  1. VideoDatabase - Stores videos and metrics")
    print("  2. GitVersioning - Tracks code versions")
    print("  3. VideoValidator - Validates videos before publish")
    print("  4. AIDecisionMaker - Claude decides parameters")
    print("  5. LearningPipeline - Complete autonomous loop")
    print("  6. Full Generation - Optional end-to-end test")

    input("\nPress Enter to start tests...")

    try:
        # Run tests
        db = test_database()
        test_git_versioning()
        test_validator()
        decision = test_ai_decision()
        pipeline = test_learning_pipeline()

        # Show what's in the database
        show_database_contents()

        # Optional full test
        test_full_generation(pipeline)

        print("\n" + "=" * 60)
        print("  ALL TESTS COMPLETED!")
        print("=" * 60)

        print("\nNext steps:")
        print("  1. Set ANTHROPIC_API_KEY for real AI decisions")
        print("  2. Run 'python3 main.py' with auto_publish=True")
        print("  3. The system will learn from performance!")

    except KeyboardInterrupt:
        print("\n\nTests interrupted.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
