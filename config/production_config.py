# config/production_config.py
"""
Configuration flexible pour la production de vidéos

Modifie ces valeurs selon tes préférences!
"""

from src.utils.video.background_manager import BackgroundMode


# ============================================================
# CONFIGURATION GENERALE
# ============================================================

VIDEO_CONFIG = {
    "width": 1080,
    "height": 1920,
    "fps": 60,
    "duration": 60,  # Durée par défaut en secondes
}

OUTPUT_CONFIG = {
    "output_dir": "output/production",
    "temp_dir": "temp",
}


# ============================================================
# CHOIX DES MODES VIDEO
# ============================================================

# Quels modes peuvent être générés? (random choisira parmi ceux-ci)
ENABLED_MODES = [
    "gravity",  # GravityFalls - balle qui grandit
    "arc",      # ArcEscape - balle qui s'échappe
]

# Poids pour le random (plus = plus probable)
MODE_WEIGHTS = {
    "gravity": 1,
    "arc": 1,
}


# ============================================================
# CHOIX DES BACKGROUNDS
# ============================================================

# Quels backgrounds peuvent être utilisés?
ENABLED_BACKGROUNDS = [
    BackgroundMode.ANIMATED_GRADIENT,  # Dégradé animé arc-en-ciel
    BackgroundMode.SOLID_PASTEL,       # Couleur pastel unie
    BackgroundMode.STATIC_GRADIENT,    # Dégradé fixe
]

# Poids pour le random
BACKGROUND_WEIGHTS = {
    BackgroundMode.ANIMATED_GRADIENT: 2,  # Plus probable
    BackgroundMode.SOLID_PASTEL: 1,
    BackgroundMode.STATIC_GRADIENT: 1,
}


# ============================================================
# CHOIX DE LA MUSIQUE MIDI
# ============================================================

# Dossier des fichiers MIDI
MIDI_DIR = "music"

# Liste spécifique de MIDI à utiliser (laisser vide = tous)
# Si tu veux uniquement certains fichiers:
ENABLED_MIDI_FILES = [
    # "Europe_Final_Countdown.mid",
    # "Journey_Dont_Stop_Believin.mid",
    # "Rick_Astley_Never_Gonna_Give_You_Up.mid",
]

# MIDI à exclure (si ENABLED_MIDI_FILES est vide)
EXCLUDED_MIDI_FILES = [
    # "fichier_nul.mid",
]


# ============================================================
# CONFIG GRAVITYFALLS
# ============================================================

GRAVITY_FALLS_CONFIG = {
    # Cercle container
    "container_size": 0.90,       # 70% à 98% de l'écran

    # Physique de la balle
    "gravity": 1500,              # Gravité (plus = tombe vite)
    "restitution": 0.85,          # Rebond (< 1 = perd énergie, > 1 = gagne)
    "ball_size": 12,              # Taille initiale
    "growth_rate": 0.8,           # Croissance par rebond

    # Effets visuels
    "enable_particles": True,     # Particules sur collision
}


# ============================================================
# CONFIG ARC ESCAPE
# ============================================================

ARC_ESCAPE_CONFIG = {
    # Layers
    "layer_count": 25,            # Nombre de layers (plus = plus long)
    "spacing": 28,                # Espacement entre layers
    "gap_size_deg": 50,           # Taille du trou (degrés)
    "rotation_speed": 1.2,        # Vitesse de rotation

    # Physique
    "gravity": 1200.0,            # Gravité
    "restitution": 1.02,          # > 1 = gagne énergie au rebond
    "air_resistance": 0.9998,     # Résistance (plus proche de 1 = moins)
    "max_velocity": 1400.0,       # Vitesse max
    "min_velocity": 300.0,        # Vitesse min (boost si en dessous!)
    "jitter_strength": 40.0,      # Chaos au rebond

    # Balle
    "ball_size": 14,
}


# ============================================================
# CONFIG AUDIO - SONS SATISFAISANTS
# ============================================================

AUDIO_CONFIG = {
    "volume": 0.7,                # Volume master (0-1)
    "sample_rate": 44100,         # Qualité audio
}

# ============================================================
# PRESETS DE SONS DISPONIBLES
# ============================================================

# Chaque preset définit le caractère du son
SOUND_PRESETS = {
    # Pop satisfaisant - court et punchy
    "satisfying_pop": {
        "base_freq": 220.0,
        "attack_ms": 2.0,
        "decay_ms": 80.0,
        "release_ms": 120.0,
        "sub_bass_amount": 0.4,
        "brightness": 0.6,
        "harmonics": [2.0, 3.0, 4.0],
        "noise_amount": 0.08,
        "pitch_drop": 0.15,
    },

    # Chime doux - résonant
    "gentle_chime": {
        "base_freq": 523.25,
        "attack_ms": 5.0,
        "decay_ms": 150.0,
        "release_ms": 300.0,
        "sub_bass_amount": 0.1,
        "brightness": 0.8,
        "harmonics": [2.0, 3.0, 4.5, 6.0],
        "noise_amount": 0.02,
        "pitch_drop": 0.0,
    },

    # Thud profond - basse
    "deep_thud": {
        "base_freq": 80.0,
        "attack_ms": 3.0,
        "decay_ms": 60.0,
        "release_ms": 100.0,
        "sub_bass_amount": 0.7,
        "brightness": 0.3,
        "harmonics": [2.0],
        "noise_amount": 0.15,
        "pitch_drop": 0.3,
    },

    # Bubble pop - ASMR
    "bubble_pop": {
        "base_freq": 400.0,
        "attack_ms": 1.0,
        "decay_ms": 40.0,
        "release_ms": 80.0,
        "sub_bass_amount": 0.2,
        "brightness": 0.7,
        "harmonics": [2.0, 3.0],
        "noise_amount": 0.1,
        "pitch_drop": 0.2,
    },

    # Crystal ting - aigu brillant
    "crystal_ting": {
        "base_freq": 880.0,
        "attack_ms": 2.0,
        "decay_ms": 200.0,
        "release_ms": 400.0,
        "sub_bass_amount": 0.05,
        "brightness": 0.9,
        "harmonics": [2.1, 3.3, 4.7],
        "noise_amount": 0.01,
        "pitch_drop": -0.05,
    },

    # Marimba doux
    "soft_marimba": {
        "base_freq": 330.0,
        "attack_ms": 3.0,
        "decay_ms": 100.0,
        "release_ms": 200.0,
        "sub_bass_amount": 0.3,
        "brightness": 0.5,
        "harmonics": [2.0, 4.0],
        "noise_amount": 0.03,
        "pitch_drop": 0.08,
    },

    # Pluck guitare
    "guitar_pluck": {
        "base_freq": 196.0,
        "attack_ms": 1.0,
        "decay_ms": 120.0,
        "release_ms": 250.0,
        "sub_bass_amount": 0.25,
        "brightness": 0.65,
        "harmonics": [2.0, 3.0, 4.0, 5.0],
        "noise_amount": 0.05,
        "pitch_drop": 0.05,
    },

    # Water drop - goutte d'eau
    "water_drop": {
        "base_freq": 600.0,
        "attack_ms": 1.0,
        "decay_ms": 50.0,
        "release_ms": 100.0,
        "sub_bass_amount": 0.15,
        "brightness": 0.75,
        "harmonics": [2.0],
        "noise_amount": 0.12,
        "pitch_drop": 0.25,
    },
}


# ============================================================
# CHOIX DES SONS PAR ACTION
# ============================================================

# Sons autorisés pour les REBONDS/COLLISIONS
BOUNCE_SOUNDS = [
    "satisfying_pop",
    "bubble_pop",
    "deep_thud",
    "soft_marimba",
]

# Poids (plus = plus probable)
BOUNCE_SOUND_WEIGHTS = {
    "satisfying_pop": 3,
    "bubble_pop": 2,
    "deep_thud": 1,
    "soft_marimba": 2,
}

# Sons autorisés pour les PASSAGES (ArcEscape)
PASSAGE_SOUNDS = [
    "gentle_chime",
    "crystal_ting",
    "water_drop",
    "guitar_pluck",
]

PASSAGE_SOUND_WEIGHTS = {
    "gentle_chime": 3,
    "crystal_ting": 2,
    "water_drop": 1,
    "guitar_pluck": 1,
}


# ============================================================
# HELPERS
# ============================================================

import random
import glob
import os

def get_random_mode() -> str:
    """Retourne un mode aléatoire selon les poids"""
    modes = []
    weights = []
    for mode in ENABLED_MODES:
        modes.append(mode)
        weights.append(MODE_WEIGHTS.get(mode, 1))
    return random.choices(modes, weights=weights)[0]


def get_random_background() -> BackgroundMode:
    """Retourne un background aléatoire selon les poids"""
    bgs = []
    weights = []
    for bg in ENABLED_BACKGROUNDS:
        bgs.append(bg)
        weights.append(BACKGROUND_WEIGHTS.get(bg, 1))
    return random.choices(bgs, weights=weights)[0]


def get_random_midi() -> str:
    """Retourne un fichier MIDI aléatoire"""
    # Si liste spécifique
    if ENABLED_MIDI_FILES:
        midi_files = [os.path.join(MIDI_DIR, f) for f in ENABLED_MIDI_FILES]
        midi_files = [f for f in midi_files if os.path.exists(f)]
    else:
        # Tous les MIDI sauf exclus
        midi_files = glob.glob(f"{MIDI_DIR}/*.mid")
        if EXCLUDED_MIDI_FILES:
            midi_files = [f for f in midi_files
                         if os.path.basename(f) not in EXCLUDED_MIDI_FILES]

    if midi_files:
        return random.choice(midi_files)
    return None


def get_random_bounce_sound() -> tuple:
    """Retourne un son de rebond aléatoire (name, preset)"""
    sounds = []
    weights = []
    for sound in BOUNCE_SOUNDS:
        if sound in SOUND_PRESETS:
            sounds.append(sound)
            weights.append(BOUNCE_SOUND_WEIGHTS.get(sound, 1))

    if sounds:
        name = random.choices(sounds, weights=weights)[0]
        return name, SOUND_PRESETS[name]
    return "satisfying_pop", SOUND_PRESETS["satisfying_pop"]


def get_random_passage_sound() -> tuple:
    """Retourne un son de passage aléatoire (name, preset)"""
    sounds = []
    weights = []
    for sound in PASSAGE_SOUNDS:
        if sound in SOUND_PRESETS:
            sounds.append(sound)
            weights.append(PASSAGE_SOUND_WEIGHTS.get(sound, 1))

    if sounds:
        name = random.choices(sounds, weights=weights)[0]
        return name, SOUND_PRESETS[name]
    return "gentle_chime", SOUND_PRESETS["gentle_chime"]


def get_audio_config() -> dict:
    """Retourne la config audio complète avec sons random"""
    bounce_name, bounce_preset = get_random_bounce_sound()
    passage_name, passage_preset = get_random_passage_sound()

    return {
        "volume": AUDIO_CONFIG["volume"],
        "sample_rate": AUDIO_CONFIG["sample_rate"],
        "bounce_sound": {
            "name": bounce_name,
            "preset": bounce_preset,
        },
        "passage_sound": {
            "name": passage_name,
            "preset": passage_preset,
        },
    }


def get_config_for_mode(mode: str) -> dict:
    """Retourne la config pour un mode donné"""
    if mode == "gravity":
        config = GRAVITY_FALLS_CONFIG.copy()
    elif mode == "arc":
        config = ARC_ESCAPE_CONFIG.copy()
    else:
        config = {}

    # Ajouter background
    config["background"] = {"mode": get_random_background()}

    return config


def print_current_selection():
    """Affiche la sélection actuelle (pour debug)"""
    mode = get_random_mode()
    bg = get_random_background()
    midi = get_random_midi()
    bounce_name, _ = get_random_bounce_sound()
    passage_name, _ = get_random_passage_sound()

    print(f"""
=== SELECTION ALEATOIRE ===
Mode vidéo:     {mode}
Background:     {bg.value}
MIDI:           {os.path.basename(midi) if midi else 'default'}
Son rebond:     {bounce_name}
Son passage:    {passage_name}
===========================
""")
