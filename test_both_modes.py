#!/usr/bin/env python3
"""
Test script for both video generation modes with new features:
- Background modes (animated gradient, solid pastel, static gradient)
- Particles on collision
- Engagement texts
- MIDI melody sync + AUDIO
"""

import os
import sys
import time
import random
import glob

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.video_generators.gravity_falls_simulator import GravityFallsSimulator
from src.video_generators.arc_escape_simulator import ArcEscapeSimulator
from src.utils.video.background_manager import BackgroundMode
from src.audio_generators.satisfying_audio_generator import SatisfyingAudioGenerator
from src.media_combiners.media_combiner import FFmpegMediaCombiner


def get_random_midi():
    """Get a random MIDI file from music folder"""
    midi_files = glob.glob("music/*.mid")
    if midi_files:
        return random.choice(midi_files)
    return None


def generate_audio_for_video(video_generator, duration, output_audio_path):
    """Generate satisfying audio from video events"""
    audio_gen = SatisfyingAudioGenerator()
    audio_gen.duration = duration
    audio_gen.set_output_path(output_audio_path)

    # Configure
    audio_gen.configure({
        "volume": 0.7
    })

    # Load MIDI melody
    midi_file = get_random_midi()
    if midi_file:
        print(f"  Using MIDI: {midi_file}")
        audio_gen.load_midi(midi_file)
    else:
        print("  Using default melody")

    # Add events from video
    events = video_generator.get_audio_events()
    print(f"  Audio events: {len(events)}")
    audio_gen.add_events(events)

    # Generate audio
    return audio_gen.generate()


def combine_video_audio(video_path, audio_path, output_path):
    """Combine video and audio"""
    combiner = FFmpegMediaCombiner()
    return combiner.combine(video_path, audio_path, output_path)


def test_gravity_falls():
    """Test GravityFalls mode with new features + AUDIO"""
    print("\n" + "="*60)
    print("TEST 1: GRAVITY FALLS SIMULATOR + AUDIO")
    print("="*60)

    duration = 10
    # Create simulator
    sim = GravityFallsSimulator(width=720, height=1280, fps=60, duration=duration)

    # Configure with new features
    config = {
        "container_size": 0.90,  # 90% - grand cercle
        "enable_particles": True,
        "background": {
            "mode": BackgroundMode.ANIMATED_GRADIENT,
        }
    }

    sim.configure(config)

    # Set output path
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    video_path = f"{output_dir}/test_gravity_falls_video.mp4"
    audio_path = f"{output_dir}/test_gravity_falls_audio.wav"
    final_path = f"{output_dir}/test_gravity_falls_final.mp4"
    sim.set_output_path(video_path)

    print(f"Output: {final_path}")
    print("Features enabled:")
    print("  - Animated gradient background")
    print("  - Particles on collision")
    print("  - Engagement texts")
    print("  - MIDI melody audio")
    print()

    start_time = time.time()

    # 1. Generate video
    print("Generating video...")
    video_result = sim.generate()
    if not video_result:
        print("FAILED: Video generation")
        return False

    # 2. Generate audio
    print("Generating audio...")
    audio_result = generate_audio_for_video(sim, duration, audio_path)
    if not audio_result:
        print("FAILED: Audio generation")
        return False

    # 3. Combine
    print("Combining video + audio...")
    final_result = combine_video_audio(video_path, audio_path, final_path)

    gen_time = time.time() - start_time

    if final_result:
        file_size = os.path.getsize(final_result) / (1024*1024)
        print(f"SUCCESS: {final_result}")
        print(f"Size: {file_size:.2f} MB")
        print(f"Time: {gen_time:.1f}s")
        # Cleanup temp files
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(audio_path):
            os.remove(audio_path)
        return True
    else:
        print("FAILED: Combining")
        return False


def test_arc_escape():
    """Test ArcEscape mode with new features + AUDIO"""
    print("\n" + "="*60)
    print("TEST 2: ARC ESCAPE SIMULATOR + AUDIO")
    print("="*60)

    duration = 15
    # Create simulator
    sim = ArcEscapeSimulator(width=720, height=1280, fps=60, duration=duration)

    # Configure with dynamic physics - never boring
    config = {
        "layer_count": 15,
        "gravity": 1200.0,          # Gravité normale
        "restitution": 1.02,        # GAGNE énergie au rebond
        "air_resistance": 0.9998,   # Très peu de résistance
        "max_velocity": 1400.0,     # Peut aller vite
        "min_velocity": 300.0,      # Jamais trop lent!
        "jitter_strength": 40.0,    # Chaos pour variété
        "background": {
            "mode": BackgroundMode.ANIMATED_GRADIENT,
        }
    }

    sim.configure(config)

    # Set output path
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    video_path = f"{output_dir}/test_arc_escape_video.mp4"
    audio_path = f"{output_dir}/test_arc_escape_audio.wav"
    final_path = f"{output_dir}/test_arc_escape_final.mp4"
    sim.set_output_path(video_path)

    print(f"Output: {final_path}")
    print("Features enabled:")
    print("  - Animated gradient background")
    print("  - Collision & passage particles")
    print("  - Spring animation")
    print("  - Engagement texts")
    print("  - MIDI melody audio")
    print()

    start_time = time.time()

    # 1. Generate video
    print("Generating video...")
    video_result = sim.generate()
    if not video_result:
        print("FAILED: Video generation")
        return False

    # 2. Generate audio
    print("Generating audio...")
    audio_result = generate_audio_for_video(sim, duration, audio_path)
    if not audio_result:
        print("FAILED: Audio generation")
        return False

    # 3. Combine
    print("Combining video + audio...")
    final_result = combine_video_audio(video_path, audio_path, final_path)

    gen_time = time.time() - start_time

    if final_result:
        file_size = os.path.getsize(final_result) / (1024*1024)
        print(f"SUCCESS: {final_result}")
        print(f"Size: {file_size:.2f} MB")
        print(f"Time: {gen_time:.1f}s")
        # Cleanup temp files
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(audio_path):
            os.remove(audio_path)
        return True
    else:
        print("FAILED: Combining")
        return False


def test_all_background_modes():
    """Quick test of all 3 background modes with GravityFalls"""
    print("\n" + "="*60)
    print("TEST 3: ALL BACKGROUND MODES")
    print("="*60)

    modes = [
        (BackgroundMode.ANIMATED_GRADIENT, "animated_gradient"),
        (BackgroundMode.SOLID_PASTEL, "solid_pastel"),
        (BackgroundMode.STATIC_GRADIENT, "static_gradient"),
    ]

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    results = []

    for mode, name in modes:
        print(f"\nTesting {name}...")

        sim = GravityFallsSimulator(width=480, height=854, fps=30, duration=5)

        config = {
            "container_size": 0.85,
            "enable_particles": True,
            "background": {"mode": mode}
        }

        sim.configure(config)
        output_path = f"{output_dir}/test_bg_{name}.mp4"
        sim.set_output_path(output_path)

        start_time = time.time()
        result = sim.generate()
        gen_time = time.time() - start_time

        if result:
            file_size = os.path.getsize(result) / (1024*1024)
            print(f"  OK: {name} - {file_size:.2f} MB in {gen_time:.1f}s")
            results.append((name, True))
        else:
            print(f"  FAIL: {name}")
            results.append((name, False))

    return all(r[1] for r in results)


if __name__ == "__main__":
    print("="*60)
    print("TESTING NEW VIDEO GENERATION FEATURES")
    print("="*60)
    print("Features to test:")
    print("  1. Particles on collision")
    print("  2. 3 Background modes (animated, solid, static)")
    print("  3. Engagement texts (intro, climax)")
    print("  4. GravityFalls + ArcEscape generators")

    all_passed = True

    # Test 1: GravityFalls
    if not test_gravity_falls():
        all_passed = False

    # Test 2: ArcEscape
    if not test_arc_escape():
        all_passed = False

    # Test 3: All background modes
    if not test_all_background_modes():
        all_passed = False

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    if all_passed:
        print("ALL TESTS PASSED!")
        print("\nGenerated videos:")
        for f in os.listdir("output"):
            if f.startswith("test_") and f.endswith(".mp4"):
                path = os.path.join("output", f)
                size = os.path.getsize(path) / (1024*1024)
                print(f"  - {f} ({size:.2f} MB)")
    else:
        print("SOME TESTS FAILED")
        sys.exit(1)
