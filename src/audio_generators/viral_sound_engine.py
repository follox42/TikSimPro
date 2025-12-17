# src/audio_generators/viral_sound_engine.py
"""
Wrapper to expose ViralSoundEngine to the plugin system
This creates a subclass so the plugin manager can discover it
"""

from .viral_audio.viral_sound_engine import ViralSoundEngine as _ViralSoundEngine


class ViralSoundEngine(_ViralSoundEngine):
    """
    Viral Sound Engine - Creates satisfying, viral-optimized sounds for physics videos.

    Modes:
    - maximum_punch: Bass-heavy, satisfying thuds
    - asmr_relaxant: 5kHz presence for tingle effect

    Features:
    - 5-layer architecture (Sub, Body, Presence, Air, Tail)
    - Velocity-mapped dynamics
    - Progressive build system
    """
    pass


__all__ = ['ViralSoundEngine']
