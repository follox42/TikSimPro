#!/usr/bin/env python3
"""
🎵 Générateur de Sons Ultra-Avancé - TikSimPro
Démonstrateur de toutes les capacités du nouveau système de génération audio

Ce fichier montre comment utiliser le nouveau AdvancedSoundGenerator pour créer 
tous types de sons avec harmoniques, turbulences, filtres et effets.
"""

import numpy as np
import pygame
import json
import os
from typing import Dict, List, Any
from src.audio_generators.simple_midi_audio_generator import AdvancedSoundGenerator

def demo_basic_waveforms():
    """Démontre les différentes formes d'ondes de base"""
    print("🎵 Démonstration des formes d'ondes de base...")
    
    generator = AdvancedSoundGenerator()
    
    waveforms = ["sine", "square", "sawtooth", "triangle", "pulse", "noise", "pink_noise", "brown_noise"]
    
    for waveform in waveforms:
        print(f"   Génération: {waveform}")
        samples = int(generator.sample_rate * 1.0)  # 1 seconde
        wave = generator.generate_waveform(waveform, 440.0, samples)
        
        # Sauvegarde pour écoute
        filename = f"temp/demo_waveform_{waveform}.wav"
        save_audio_to_wav(wave, filename, generator.sample_rate)

def demo_harmonics_system():
    """Démontre le système d'harmoniques avancé"""
    print("🎵 Démonstration du système d'harmoniques...")
    
    generator = AdvancedSoundGenerator()
    frequency = 440.0  # La 440Hz
    duration = 2.0
    samples = int(generator.sample_rate * duration)
    
    # Son de base
    fundamental = generator.generate_waveform("sine", frequency, samples)
    
    # Configuration d'harmoniques complexes
    harmonics_config = [
        {"harmonic": 2, "amplitude": 0.5, "waveform": "sine", "phase": 0},
        {"harmonic": 3, "amplitude": 0.3, "waveform": "triangle", "phase": 0.25},
        {"harmonic": 4, "amplitude": 0.2, "waveform": "square", "phase": 0.5},
        {"harmonic": 5, "amplitude": 0.15, "waveform": "sine", "phase": 0.75},
        {"harmonic": 6, "amplitude": 0.1, "waveform": "sawtooth", "phase": 0},
    ]
    
    # Génération avec harmoniques
    harmonized = generator.add_harmonics(fundamental, frequency, samples, harmonics_config)
    
    # Ajout de sous-harmoniques
    subharmonics_config = [
        {"divisor": 2, "amplitude": 0.2, "waveform": "sine"},
        {"divisor": 3, "amplitude": 0.1, "waveform": "triangle"},
    ]
    
    with_subharmonics = generator.add_subharmonics(harmonized, frequency, samples, subharmonics_config)
    
    save_audio_to_wav(with_subharmonics, "temp/demo_harmonics_complex.wav", generator.sample_rate)

def demo_advanced_envelopes():
    """Démontre les enveloppes avancées"""
    print("🎵 Démonstration des enveloppes avancées...")
    
    generator = AdvancedSoundGenerator()
    samples = int(generator.sample_rate * 3.0)
    
    # Enveloppe ADSR classique
    envelope_adsr = generator.create_adsr_envelope(
        samples, 
        attack_ms=100, 
        decay_ms=300, 
        sustain_level=0.6, 
        release_ms=800,
        curve_type="exponential"
    )
    
    # Enveloppe personnalisée avec points de contrôle
    envelope_custom = generator.create_custom_envelope(samples, [
        (0.0, 0.0),     # Début silencieux
        (0.1, 1.0),     # Montée rapide
        (0.2, 0.3),     # Chute
        (0.4, 0.8),     # Remontée
        (0.7, 0.5),     # Plateau
        (1.0, 0.0)      # Fin silencieuse
    ])
    
    # Application aux signaux
    signal = generator.generate_waveform("sine", 523.25, samples)  # Do5
    
    signal_adsr = signal * envelope_adsr
    signal_custom = signal * envelope_custom
    
    save_audio_to_wav(signal_adsr, "temp/demo_envelope_adsr.wav", generator.sample_rate)
    save_audio_to_wav(signal_custom, "temp/demo_envelope_custom.wav", generator.sample_rate)

def demo_modulations_and_turbulence():
    """Démontre les modulations et turbulences"""
    print("🎵 Démonstration des modulations et turbulences...")
    
    generator = AdvancedSoundGenerator()
    duration = 4.0
    samples = int(generator.sample_rate * duration)
    
    # Signal de base
    signal = generator.generate_waveform("sine", 440.0, samples)
    
    # Modulation de fréquence (vibrato)
    fm_signal = generator.add_frequency_modulation(signal, 5.0, 0.1, samples)
    
    # Modulation d'amplitude (tremolo)
    am_signal = generator.add_amplitude_modulation(signal, 3.0, 0.2, samples)
    
    # Turbulences complexes
    turbulence_config = {
        "noise_type": "pink",
        "noise_amount": 0.08,
        "flutter_rate": 2.5,
        "flutter_depth": 0.03,
        "wow_rate": 0.4,
        "wow_depth": 0.015
    }
    
    turbulent_signal = generator.add_turbulence(signal, turbulence_config)
    
    save_audio_to_wav(fm_signal, "temp/demo_modulation_fm.wav", generator.sample_rate)
    save_audio_to_wav(am_signal, "temp/demo_modulation_am.wav", generator.sample_rate)
    save_audio_to_wav(turbulent_signal, "temp/demo_turbulence.wav", generator.sample_rate)

def demo_filters():
    """Démontre les différents filtres"""
    print("🎵 Démonstration des filtres...")
    
    generator = AdvancedSoundGenerator()
    duration = 3.0
    samples = int(generator.sample_rate * duration)
    
    # Signal riche en harmoniques
    signal = (generator.generate_waveform("square", 220, samples) * 0.3 +
              generator.generate_waveform("sawtooth", 440, samples) * 0.4 +
              generator.generate_waveform("sine", 880, samples) * 0.3)
    
    # Différents filtres
    lowpass = generator.apply_lowpass_filter(signal, 800, resonance=0.7)
    highpass = generator.apply_highpass_filter(signal, 300)
    bandpass = generator.apply_bandpass_filter(signal, 300, 1000)
    notch = generator.apply_notch_filter(signal, 440, q_factor=15)
    
    save_audio_to_wav(signal, "temp/demo_filter_original.wav", generator.sample_rate)
    save_audio_to_wav(lowpass, "temp/demo_filter_lowpass.wav", generator.sample_rate)
    save_audio_to_wav(highpass, "temp/demo_filter_highpass.wav", generator.sample_rate)
    save_audio_to_wav(bandpass, "temp/demo_filter_bandpass.wav", generator.sample_rate)
    save_audio_to_wav(notch, "temp/demo_filter_notch.wav", generator.sample_rate)

def demo_effects():
    """Démontre les effets audio"""
    print("🎵 Démonstration des effets...")
    
    generator = AdvancedSoundGenerator()
    duration = 2.0
    samples = int(generator.sample_rate * duration)
    
    # Signal de base (corde pincée)
    signal = generator.generate_waveform("triangle", 330, samples)
    envelope = generator.create_adsr_envelope(samples, 5, 200, 0.3, 500)
    signal *= envelope
    
    # Différents effets
    reverb = generator.apply_reverb(signal, room_size=0.8, wet_level=0.4)
    delay = generator.apply_delay(signal, delay_ms=150, feedback=0.4, wet_level=0.3)
    chorus = generator.apply_chorus(signal, rate=1.5, depth=0.03, mix=0.5)
    distortion = generator.apply_distortion(signal, drive=3.0, tone=0.7)
    bitcrusher = generator.apply_bitcrusher(signal, bits=6, sample_rate_reduction=2)
    
    save_audio_to_wav(signal, "temp/demo_effect_dry.wav", generator.sample_rate)
    save_audio_to_wav(reverb, "temp/demo_effect_reverb.wav", generator.sample_rate)
    save_audio_to_wav(delay, "temp/demo_effect_delay.wav", generator.sample_rate)
    save_audio_to_wav(chorus, "temp/demo_effect_chorus.wav", generator.sample_rate)
    save_audio_to_wav(distortion, "temp/demo_effect_distortion.wav", generator.sample_rate)
    save_audio_to_wav(bitcrusher, "temp/demo_effect_bitcrusher.wav", generator.sample_rate)

def demo_complete_instruments():
    """Démontre la création d'instruments complets"""
    print("🎵 Démonstration d'instruments complets...")
    
    generator = AdvancedSoundGenerator()
    
    # 1. Piano synthétique avancé
    piano_config = {
        "frequency": 261.63,  # Do4
        "duration": 3.0,
        "volume": 0.8,
        "waveform": "triangle",
        "harmonics": [
            {"harmonic": 2, "amplitude": 0.4, "waveform": "sine"},
            {"harmonic": 3, "amplitude": 0.2, "waveform": "triangle"},
            {"harmonic": 4, "amplitude": 0.1, "waveform": "sine"},
            {"harmonic": 5, "amplitude": 0.05, "waveform": "sine"}
        ],
        "envelope": {
            "type": "adsr",
            "attack_ms": 5,
            "decay_ms": 300,
            "sustain_level": 0.4,
            "release_ms": 800,
            "curve_type": "exponential"
        },
        "filters": [
            {"type": "lowpass", "cutoff": 2000, "resonance": 0.3}
        ],
        "effects": [
            {"type": "reverb", "room_size": 0.3, "wet_level": 0.2}
        ]
    }
    
    piano_sound = generator.generate_advanced_sound(piano_config)
    save_audio_to_wav(piano_sound, "temp/demo_instrument_piano.wav", generator.sample_rate)
    
    # 2. Synthé lead spatial
    lead_config = {
        "frequency": 440.0,
        "duration": 4.0,
        "volume": 0.7,
        "waveform": "sawtooth",
        "harmonics": [
            {"harmonic": 1.5, "amplitude": 0.3, "waveform": "square"},
            {"harmonic": 2.2, "amplitude": 0.2, "waveform": "sine"}
        ],
        "envelope": {
            "type": "adsr",
            "attack_ms": 50,
            "decay_ms": 100,
            "sustain_level": 0.7,
            "release_ms": 1000,
            "curve_type": "exponential"
        },
        "modulation": {
            "fm_frequency": 6.0,
            "fm_depth": 0.05,
            "am_frequency": 4.0,
            "am_depth": 0.1
        },
        "filters": [
            {"type": "lowpass", "cutoff": 1500, "resonance": 0.8}
        ],
        "effects": [
            {"type": "chorus", "rate": 0.8, "depth": 0.02, "mix": 0.4},
            {"type": "delay", "delay_ms": 125, "feedback": 0.2, "wet_level": 0.3},
            {"type": "reverb", "room_size": 0.7, "wet_level": 0.4}
        ]
    }
    
    lead_sound = generator.generate_advanced_sound(lead_config)
    save_audio_to_wav(lead_sound, "temp/demo_instrument_lead.wav", generator.sample_rate)
    
    # 3. Percussion organique
    perc_config = {
        "frequency": 120.0,
        "duration": 1.5,
        "volume": 0.9,
        "waveform": "noise",
        "subharmonics": [
            {"divisor": 2, "amplitude": 0.4, "waveform": "sine"}
        ],
        "envelope": {
            "type": "custom",
            "points": [(0, 0), (0.01, 1), (0.05, 0.3), (0.3, 0.1), (1, 0)]
        },
        "turbulence": {
            "noise_type": "brown",
            "noise_amount": 0.3
        },
        "filters": [
            {"type": "bandpass", "low_freq": 80, "high_freq": 300}
        ],
        "effects": [
            {"type": "distortion", "drive": 1.5, "tone": 0.3},
            {"type": "reverb", "room_size": 0.4, "wet_level": 0.3}
        ]
    }
    
    perc_sound = generator.generate_advanced_sound(perc_config)
    save_audio_to_wav(perc_sound, "temp/demo_instrument_percussion.wav", generator.sample_rate)

def demo_extreme_sound_design():
    """Démontre la création de sons complètement innovants"""
    print("🎵 Démonstration de sound design extrême...")
    
    generator = AdvancedSoundGenerator()
    
    # 1. Son "alien" complexe
    alien_config = {
        "frequency": 333.0,
        "duration": 5.0,
        "volume": 0.6,
        "waveform": "square",
        "harmonics": [
            {"harmonic": 1.618, "amplitude": 0.4, "waveform": "triangle"},  # Golden ratio
            {"harmonic": 2.718, "amplitude": 0.3, "waveform": "sawtooth"}, # e
            {"harmonic": 3.14159, "amplitude": 0.2, "waveform": "sine"}    # π
        ],
        "subharmonics": [
            {"divisor": 1.732, "amplitude": 0.2, "waveform": "noise"}      # √3
        ],
        "envelope": {
            "type": "custom",
            "points": [
                (0, 0), (0.1, 0.3), (0.15, 1), (0.3, 0.2), 
                (0.5, 0.8), (0.7, 0.1), (0.85, 0.6), (1, 0)
            ]
        },
        "modulation": {
            "fm_frequency": 7.3,
            "fm_depth": 0.2,
            "am_frequency": 2.7,
            "am_depth": 0.3
        },
        "turbulence": {
            "noise_type": "pink",
            "noise_amount": 0.15,
            "flutter_rate": 11.0,
            "flutter_depth": 0.08,
            "wow_rate": 0.6,
            "wow_depth": 0.04
        },
        "filters": [
            {"type": "bandpass", "low_freq": 200, "high_freq": 2000},
            {"type": "notch", "notch_freq": 800, "q_factor": 20}
        ],
        "effects": [
            {"type": "chorus", "rate": 0.3, "depth": 0.05, "mix": 0.6},
            {"type": "distortion", "drive": 1.8, "tone": 0.8},
            {"type": "delay", "delay_ms": 333, "feedback": 0.5, "wet_level": 0.4},
            {"type": "reverb", "room_size": 0.9, "wet_level": 0.6}
        ]
    }
    
    alien_sound = generator.generate_advanced_sound(alien_config)
    save_audio_to_wav(alien_sound, "temp/demo_extreme_alien.wav", generator.sample_rate)
    
    # 2. Texture sonore évolutive
    texture_config = {
        "frequency": 55.0,  # A1 très grave
        "duration": 8.0,
        "volume": 0.5,
        "waveform": "brown_noise",
        "harmonics": [
            {"harmonic": 2, "amplitude": 0.6, "waveform": "sine"},
            {"harmonic": 4, "amplitude": 0.4, "waveform": "triangle"},
            {"harmonic": 8, "amplitude": 0.2, "waveform": "square"},
            {"harmonic": 16, "amplitude": 0.1, "waveform": "pulse"}
        ],
        "envelope": {
            "type": "custom",
            "points": [
                (0, 0), (0.2, 0.1), (0.4, 0.3), (0.6, 0.8), 
                (0.7, 0.4), (0.8, 0.9), (0.9, 0.2), (1, 0)
            ]
        },
        "modulation": {
            "fm_frequency": 0.1,
            "fm_depth": 0.3,
            "am_frequency": 0.05,
            "am_depth": 0.5
        },
        "turbulence": {
            "noise_type": "pink",
            "noise_amount": 0.4,
            "flutter_rate": 0.2,
            "flutter_depth": 0.1,
            "wow_rate": 0.05,
            "wow_depth": 0.2
        },
        "filters": [
            {"type": "lowpass", "cutoff": 500, "resonance": 0.9}
        ],
        "effects": [
            {"type": "bitcrusher", "bits": 4, "sample_rate_reduction": 3},
            {"type": "reverb", "room_size": 1.0, "wet_level": 0.8}
        ]
    }
    
    texture_sound = generator.generate_advanced_sound(texture_config)
    save_audio_to_wav(texture_sound, "temp/demo_extreme_texture.wav", generator.sample_rate)

def create_preset_library():
    """Crée une bibliothèque de presets avancés"""
    print("🎵 Création de la bibliothèque de presets...")
    
    presets = {
        "ultra_satisfying_bounce": {
            "name": "Ultra Satisfying Bounce",
            "description": "Rebond ultra-satisfaisant avec harmoniques dorées",
            "config": {
                "frequency": 440.0,
                "duration": 0.8,
                "volume": 0.7,
                "waveform": "sine",
                "harmonics": [
                    {"harmonic": 1.618, "amplitude": 0.3, "waveform": "sine"},
                    {"harmonic": 2.618, "amplitude": 0.2, "waveform": "triangle"}
                ],
                "envelope": {
                    "type": "adsr",
                    "attack_ms": 2,
                    "decay_ms": 80,
                    "sustain_level": 0.4,
                    "release_ms": 300,
                    "curve_type": "exponential"
                },
                "modulation": {
                    "fm_frequency": 8.0,
                    "fm_depth": 0.03
                },
                "turbulence": {
                    "noise_type": "pink",
                    "noise_amount": 0.01
                },
                "effects": [
                    {"type": "reverb", "room_size": 0.2, "wet_level": 0.15}
                ]
            }
        },
        
        "crystalline_magic": {
            "name": "Crystalline Magic",
            "description": "Son cristallin magique avec harmoniques complexes",
            "config": {
                "frequency": 523.25,
                "duration": 2.0,
                "volume": 0.6,
                "waveform": "sine",
                "harmonics": [
                    {"harmonic": 2.1, "amplitude": 0.4, "waveform": "sine"},
                    {"harmonic": 3.3, "amplitude": 0.2, "waveform": "sine"},
                    {"harmonic": 4.7, "amplitude": 0.15, "waveform": "triangle"},
                    {"harmonic": 6.1, "amplitude": 0.1, "waveform": "sine"}
                ],
                "envelope": {
                    "type": "adsr",
                    "attack_ms": 5,
                    "decay_ms": 400,
                    "sustain_level": 0.3,
                    "release_ms": 800,
                    "curve_type": "exponential"
                },
                "modulation": {
                    "am_frequency": 3.0,
                    "am_depth": 0.08
                },
                "effects": [
                    {"type": "chorus", "rate": 0.5, "depth": 0.02, "mix": 0.3},
                    {"type": "reverb", "room_size": 0.8, "wet_level": 0.5}
                ]
            }
        },
        
        "organic_bubble": {
            "name": "Organic Bubble Pop",
            "description": "Bulle organique qui éclate avec texture naturelle",
            "config": {
                "frequency": 300.0,
                "duration": 0.3,
                "volume": 0.8,
                "waveform": "sine",
                "harmonics": [
                    {"harmonic": 1.5, "amplitude": 0.4, "waveform": "triangle"}
                ],
                "envelope": {
                    "type": "custom",
                    "points": [(0, 0), (0.02, 1), (0.1, 0.2), (1, 0)]
                },
                "turbulence": {
                    "noise_type": "pink",
                    "noise_amount": 0.2,
                    "flutter_rate": 15.0,
                    "flutter_depth": 0.1
                },
                "filters": [
                    {"type": "highpass", "cutoff": 200}
                ],
                "effects": [
                    {"type": "reverb", "room_size": 0.3, "wet_level": 0.2}
                ]
            }
        },
        
        "deep_wobble": {
            "name": "Deep Wobble Bass",
            "description": "Basse profonde avec wobble intense",
            "config": {
                "frequency": 80.0,
                "duration": 2.0,
                "volume": 0.9,
                "waveform": "sawtooth",
                "harmonics": [
                    {"harmonic": 2, "amplitude": 0.5, "waveform": "square"},
                    {"harmonic": 3, "amplitude": 0.3, "waveform": "triangle"}
                ],
                "envelope": {
                    "type": "adsr",
                    "attack_ms": 10,
                    "decay_ms": 100,
                    "sustain_level": 0.8,
                    "release_ms": 200,
                    "curve_type": "exponential"
                },
                "modulation": {
                    "fm_frequency": 4.0,
                    "fm_depth": 0.5
                },
                "filters": [
                    {"type": "lowpass", "cutoff": 300, "resonance": 0.8}
                ],
                "effects": [
                    {"type": "distortion", "drive": 2.0, "tone": 0.3}
                ]
            }
        },
        
        "space_pad": {
            "name": "Ethereal Space Pad",
            "description": "Nappe spatiale éthérée et évolutive",
            "config": {
                "frequency": 220.0,
                "duration": 6.0,
                "volume": 0.4,
                "waveform": "triangle",
                "harmonics": [
                    {"harmonic": 1.5, "amplitude": 0.4, "waveform": "sine"},
                    {"harmonic": 2.3, "amplitude": 0.3, "waveform": "triangle"},
                    {"harmonic": 3.7, "amplitude": 0.2, "waveform": "sine"}
                ],
                "envelope": {
                    "type": "adsr",
                    "attack_ms": 800,
                    "decay_ms": 500,
                    "sustain_level": 0.7,
                    "release_ms": 2000,
                    "curve_type": "exponential"
                },
                "modulation": {
                    "am_frequency": 0.3,
                    "am_depth": 0.2,
                    "fm_frequency": 0.1,
                    "fm_depth": 0.05
                },
                "filters": [
                    {"type": "lowpass", "cutoff": 1000, "resonance": 0.3}
                ],
                "effects": [
                    {"type": "chorus", "rate": 0.2, "depth": 0.03, "mix": 0.6},
                    {"type": "reverb", "room_size": 0.9, "wet_level": 0.7}
                ]
            }
        }
    }
    
    # Sauvegarde des presets
    os.makedirs("sound_presets", exist_ok=True)
    with open("sound_presets/advanced_presets.json", "w", encoding="utf-8") as f:
        json.dump(presets, f, indent=2, ensure_ascii=False)
    
    print("✅ Bibliothèque de presets sauvegardée dans sound_presets/advanced_presets.json")
    
    # Génération d'exemples de chaque preset
    generator = AdvancedSoundGenerator()
    for preset_name, preset_data in presets.items():
        print(f"   Génération: {preset_data['name']}")
        sound = generator.generate_advanced_sound(preset_data['config'])
        save_audio_to_wav(sound, f"temp/preset_{preset_name}.wav", generator.sample_rate)

def save_audio_to_wav(audio_data: np.ndarray, filename: str, sample_rate: int):
    """Sauvegarde audio en WAV"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Normalisation
    if np.max(np.abs(audio_data)) > 0:
        audio_data = audio_data / np.max(np.abs(audio_data)) * 0.95
    
    # Conversion en int16
    audio_int16 = (audio_data * 32767).astype(np.int16)
    
    import wave
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes = 16 bits
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int16.tobytes())

def main():
    """Démonstration complète du système de génération audio avancé"""
    print("🎵 Démonstration du Générateur de Sons Ultra-Avancé")
    print("=" * 60)
    
    # Création du dossier temporaire
    os.makedirs("temp", exist_ok=True)
    
    try:
        # Démos progressives
        demo_basic_waveforms()
        demo_harmonics_system()
        demo_advanced_envelopes()
        demo_modulations_and_turbulence()
        demo_filters()
        demo_effects()
        demo_complete_instruments()
        demo_extreme_sound_design()
        
        # Création de la bibliothèque
        create_preset_library()
        
        print("\n✅ Toutes les démonstrations terminées !")
        print(f"📁 Fichiers audio générés dans le dossier 'temp/'")
        print(f"📚 Bibliothèque de presets dans 'sound_presets/advanced_presets.json'")
        
        print("\n🎵 CAPACITÉS DU NOUVEAU SYSTÈME:")
        print("   • Formes d'ondes: sine, square, sawtooth, triangle, pulse, noise, pink, brown")
        print("   • Harmoniques personnalisables avec formes d'ondes mixtes")
        print("   • Sous-harmoniques pour richesse spectrale")
        print("   • Enveloppes ADSR avec courbes (linear, exponential, logarithmic)")
        print("   • Enveloppes personnalisées avec points de contrôle")
        print("   • Modulations: FM (vibrato), AM (tremolo)")
        print("   • Turbulences: bruit, flutter, wow")
        print("   • Filtres: lowpass, highpass, bandpass, notch avec résonance")
        print("   • Effets: reverb, delay, chorus, distortion, bitcrusher")
        print("   • Système de configuration JSON ultra-flexible")
        print("   • Création d'instruments virtuels complets")
        print("   • Sound design expérimental sans limites")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 