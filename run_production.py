#!/usr/bin/env python3
"""
Production Script - Generate satisfying videos in a loop

Usage:
    python run_production.py                    # Run once
    python run_production.py --loop 10          # Run 10 times
    python run_production.py --loop -1          # Run forever
    python run_production.py --mode arc         # Only ArcEscape
    python run_production.py --mode gravity     # Only GravityFalls
    python run_production.py --duration 60      # 60 second videos

Configuration: config/production_config.py
"""

import os
import sys
import time
import argparse
import logging
import random
from datetime import datetime
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.video_generators.gravity_falls_simulator import GravityFallsSimulator
from src.video_generators.arc_escape_simulator import ArcEscapeSimulator
from src.audio_generators.satisfying_audio_generator import SatisfyingAudioGenerator
from src.media_combiners.media_combiner import FFmpegMediaCombiner

# Import config
from config.production_config import (
    VIDEO_CONFIG, OUTPUT_CONFIG,
    get_random_mode, get_random_background, get_random_midi,
    get_config_for_mode, get_audio_config,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Production")


def generate_video(mode: str, duration: int, output_name: str) -> Optional[str]:
    """
    Generate a single video with audio

    Args:
        mode: "gravity" or "arc"
        duration: Duration in seconds
        output_name: Output filename (without extension)

    Returns:
        Path to final video or None if failed
    """
    os.makedirs(OUTPUT_CONFIG["output_dir"], exist_ok=True)
    os.makedirs(OUTPUT_CONFIG["temp_dir"], exist_ok=True)

    # Paths
    video_path = f"{OUTPUT_CONFIG['temp_dir']}/{output_name}_video.mp4"
    audio_path = f"{OUTPUT_CONFIG['temp_dir']}/{output_name}_audio.wav"
    final_path = f"{OUTPUT_CONFIG['output_dir']}/{output_name}.mp4"

    # Get config from production_config
    video_config = get_config_for_mode(mode)
    audio_config = get_audio_config()
    bg_mode = video_config.get("background", {}).get("mode")

    try:
        # ===== CREATE VIDEO GENERATOR =====
        if mode == "gravity":
            logger.info(f"Creating GravityFalls video ({duration}s)")
            sim = GravityFallsSimulator(
                width=VIDEO_CONFIG["width"],
                height=VIDEO_CONFIG["height"],
                fps=VIDEO_CONFIG["fps"],
                duration=duration
            )

        elif mode == "arc":
            logger.info(f"Creating ArcEscape video ({duration}s)")
            sim = ArcEscapeSimulator(
                width=VIDEO_CONFIG["width"],
                height=VIDEO_CONFIG["height"],
                fps=VIDEO_CONFIG["fps"],
                duration=duration
            )

        else:
            logger.error(f"Unknown mode: {mode}")
            return None

        # Configure and generate video
        sim.configure(video_config)
        sim.set_output_path(video_path)

        bg_name = bg_mode.value if bg_mode else "default"
        logger.info(f"Background: {bg_name}")
        video_result = sim.generate()

        if not video_result or not os.path.exists(video_path):
            logger.error("Video generation failed")
            return None

        video_size = os.path.getsize(video_path) / (1024*1024)
        logger.info(f"Video generated: {video_size:.1f} MB")

        # ===== GENERATE AUDIO =====
        logger.info("Generating audio...")
        audio_gen = SatisfyingAudioGenerator()
        audio_gen.duration = duration
        audio_gen.set_output_path(audio_path)

        # Configure with random sounds from config
        audio_gen.configure(audio_config)
        logger.info(f"Sounds: bounce={audio_config['bounce_sound']['name']}, passage={audio_config['passage_sound']['name']}")

        # Load MIDI
        midi_file = get_random_midi()
        if midi_file:
            logger.info(f"MIDI: {os.path.basename(midi_file)}")
            audio_gen.load_midi(midi_file)

        # Add video events
        events = sim.get_audio_events()
        logger.info(f"Audio events: {len(events)}")
        audio_gen.add_events(events)

        audio_result = audio_gen.generate()
        if not audio_result or not os.path.exists(audio_path):
            logger.warning("Audio generation failed, using video only")
            import shutil
            shutil.copy2(video_path, final_path)
        else:
            # ===== COMBINE VIDEO + AUDIO =====
            logger.info("Combining video + audio...")
            combiner = FFmpegMediaCombiner()
            combine_result = combiner.combine(video_path, audio_path, final_path)

            if not combine_result or not os.path.exists(final_path):
                logger.warning("Combine failed, using video only")
                import shutil
                shutil.copy2(video_path, final_path)

        # Cleanup temp files
        for temp_file in [video_path, audio_path]:
            if os.path.exists(temp_file):
                os.remove(temp_file)

        # Final result
        if os.path.exists(final_path):
            final_size = os.path.getsize(final_path) / (1024*1024)
            logger.info(f"SUCCESS: {final_path} ({final_size:.1f} MB)")
            return final_path
        else:
            logger.error("Final video not created")
            return None

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_production(loop_count: int = 1, mode: str = "random", duration: int = 60):
    """
    Run production video generation

    Args:
        loop_count: Number of videos to generate (-1 for infinite)
        mode: "gravity", "arc", or "random"
        duration: Video duration in seconds
    """
    logger.info("="*60)
    logger.info("PRODUCTION VIDEO GENERATION")
    logger.info("="*60)
    logger.info(f"Mode: {mode}")
    logger.info(f"Duration: {duration}s")
    logger.info(f"Loop count: {'infinite' if loop_count == -1 else loop_count}")
    logger.info("="*60)

    count = 0
    success_count = 0

    while loop_count == -1 or count < loop_count:
        count += 1

        # Select mode
        if mode == "random":
            current_mode = random.choice(["gravity", "arc"])
        else:
            current_mode = mode

        # Generate unique name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"{current_mode}_{timestamp}"

        logger.info(f"\n--- Video {count}/{loop_count if loop_count > 0 else '∞'} ---")

        start_time = time.time()
        result = generate_video(current_mode, duration, output_name)
        elapsed = time.time() - start_time

        if result:
            success_count += 1
            logger.info(f"Completed in {elapsed:.1f}s")
        else:
            logger.error(f"Failed after {elapsed:.1f}s")

        # Stats
        logger.info(f"Success rate: {success_count}/{count} ({100*success_count/count:.0f}%)")

        # Small delay between videos
        if loop_count != 1 and (loop_count == -1 or count < loop_count):
            time.sleep(2)

    logger.info("\n" + "="*60)
    logger.info("PRODUCTION COMPLETE")
    logger.info(f"Total: {count} videos, {success_count} successful")
    logger.info("="*60)


def main():
    parser = argparse.ArgumentParser(description="Production Video Generator")
    parser.add_argument("--loop", type=int, default=1,
                        help="Number of videos to generate (-1 for infinite)")
    parser.add_argument("--mode", choices=["gravity", "arc", "random"], default="random",
                        help="Video mode")
    parser.add_argument("--duration", type=int, default=60,
                        help="Video duration in seconds")

    args = parser.parse_args()

    run_production(
        loop_count=args.loop,
        mode=args.mode,
        duration=args.duration
    )


if __name__ == "__main__":
    main()
