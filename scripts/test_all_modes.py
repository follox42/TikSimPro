#!/usr/bin/env python3
"""
Test script - Generate videos for each video generator and audio mode
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ['SDL_VIDEODRIVER'] = 'dummy'

from src.video_generators.gravity_falls_simulator import GravityFallsSimulator
from src.video_generators.arc_escape_simulator import ArcEscapeSimulator
from src.audio_generators.viral_audio.viral_sound_engine import ViralSoundEngine
from src.media_combiners.media_combiner import FFmpegMediaCombiner
from src.core.data_pipeline import AudioEvent

OUTPUT_DIR = "test_outputs"
DURATION = 10  # 10 secondes pour les tests
FPS = 60
WIDTH = 720
HEIGHT = 1280

def generate_test_events(count=50):
    """Generate fake collision events for audio testing"""
    events = []
    for i in range(count):
        events.append(AudioEvent(
            time=i * (DURATION / count),
            event_type='collision',
            params={
                'velocity_magnitude': 500 + i * 30,
                'bounce_count': i + 1,
                'ball_size': 15 + i * 0.5
            }
        ))
    return events

def test_gravity_falls():
    """Test GravityFallsSimulator with new physics"""
    print("\n" + "="*50)
    print("TEST: GravityFallsSimulator (bigger container)")
    print("="*50)

    sim = GravityFallsSimulator(width=WIDTH, height=HEIGHT, fps=FPS, duration=DURATION)
    sim.configure({
        'gravity': 1800,
        'restitution': 1.0,
        'ball_size': 12,
        'container_size': 0.48  # Maximum - presque tout l'écran
    })

    output_video = f"{OUTPUT_DIR}/gravity_falls_new_physics.mp4"
    sim.set_output_path(output_video)
    sim.generate()

    # Check if file exists
    if os.path.exists(output_video) and os.path.getsize(output_video) > 100000:
        print(f"Video generated: {output_video}")
        return output_video, sim.audio_events if sim.audio_events else generate_test_events()
    return None, []

def test_arc_escape():
    """Test ArcEscapeSimulator"""
    print("\n" + "="*50)
    print("TEST: ArcEscapeSimulator")
    print("="*50)

    sim = ArcEscapeSimulator(width=WIDTH, height=HEIGHT, fps=FPS, duration=DURATION)
    sim.configure({
        'layer_count': 20,
        'gap_size_deg': 55,
        'rotation_speed': 1.5
    })

    output_video = f"{OUTPUT_DIR}/arc_escape.mp4"
    sim.set_output_path(output_video)
    sim.generate()

    # Check if file exists
    if os.path.exists(output_video) and os.path.getsize(output_video) > 100000:
        print(f"Video generated: {output_video}")
        return output_video, sim.audio_events if sim.audio_events else generate_test_events()
    return None, []

def test_audio_mode(mode: str, events: list, video_path: str):
    """Test a specific audio mode"""
    print(f"\n--- Audio Mode: {mode} ---")

    engine = ViralSoundEngine(mode=mode, music_folder="./music")
    engine.set_duration(DURATION)

    audio_path = f"{OUTPUT_DIR}/audio_{mode}.wav"
    engine.set_output_path(audio_path)
    engine.add_events(events)

    result = engine.generate()
    if result and os.path.exists(result):
        print(f"Audio generated: {result}")

        # Combine video + audio
        video_name = os.path.basename(video_path).replace('.mp4', '')
        output_final = f"{OUTPUT_DIR}/final_{video_name}_{mode}.mp4"
        combiner = FFmpegMediaCombiner()
        combined = combiner.combine(video_path, audio_path, output_final)
        if combined and os.path.exists(combined):
            print(f"Final video: {combined}")
            return combined
    return None

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("="*60)
    print("  TESTING ALL VIDEO GENERATORS AND AUDIO MODES")
    print("="*60)

    results = []

    # Test 1: GravityFalls with each audio mode
    video_gf, events_gf = test_gravity_falls()
    if video_gf:
        for audio_mode in ['maximum_punch', 'physics_sync', 'melodic']:
            final = test_audio_mode(audio_mode, list(events_gf), video_gf)
            if final:
                results.append(final)

    # Test 2: ArcEscape with asmr audio
    video_arc, events_arc = test_arc_escape()
    if video_arc:
        final = test_audio_mode('asmr_relaxant', list(events_arc), video_arc)
        if final:
            results.append(final)

    print("\n" + "="*60)
    print("  RESULTS")
    print("="*60)
    for r in results:
        size_mb = os.path.getsize(r) / (1024*1024)
        print(f"  - {r} ({size_mb:.1f} MB)")

    print(f"\nTotal: {len(results)} videos generated in {OUTPUT_DIR}/")

if __name__ == "__main__":
    main()
