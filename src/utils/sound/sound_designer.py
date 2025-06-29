#!/usr/bin/env python3
"""
🎵 TikSimPro Sound Designer
Interface graphique pour créer et tester des sons ASMR satisfaisants
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pygame
import numpy as np
import json
import os
import threading
import time
from typing import Dict, List, Any
import random

# Import du générateur de sons avancé
from src.audio_generators.simple_midi_audio_generator import AdvancedSoundGenerator

# Import pour MIDI
try:
    import mido
    MIDO_AVAILABLE = True
except ImportError:
    MIDO_AVAILABLE = False

class SoundDesignerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎵 TikSimPro Sound Designer Ultra-Complet")
        self.root.geometry("1200x700")
        self.root.configure(bg='#2b2b2b')
        
        # Initialisation audio
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self.sound_generator = AdvancedSoundGenerator(sample_rate=44100)
        
        # Configuration actuelle
        self.current_config = {
            "name": "Nouveau Son",
            "type": "satisfying_bounce",
            "frequency_range": [200, 800],
            "duration": 0.5,
            "volume": 0.5,
            "envelope": {
                "attack_ms": 5.0,
                "decay_ms": 50.0,
                "sustain_level": 0.7,
                "release_ms": 100.0
            },
            "effects": {
                "reverb": 0.2,
                "compression": 0.7,
                "eq_boost": 1.0
            }
        }
        
        # Configurations sauvegardées
        self.saved_configs = []
        self.load_configs()
        
        # État MIDI
        self.midi_playing = False
        self.midi_thread = None
        self.selected_midi_file = None
        
        # Interface
        self.setup_ui()
        
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Titre
        title_label = ttk.Label(main_frame, text="🎵 Sound Designer Ultra-Complet - Tous Paramètres", font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 15))
        
        # Frame principal avec scroll
        canvas = tk.Canvas(main_frame, height=400)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas et scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Frame pour presets à droite
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        # Configuration de l'interface unique
        self.setup_complete_interface()
        self.setup_presets_panel(right_frame)
        
        # === CONTRÔLES DE LECTURE ===
        self.setup_playback_controls(main_frame)
        
    def setup_complete_interface(self):
        """Interface complète avec tous les paramètres"""
        parent = self.scrollable_frame
        
        # === CONFIGURATION DE BASE ===
        base_frame = ttk.LabelFrame(parent, text="🎵 Configuration de Base", padding=10)
        base_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Nom du son
        ttk.Label(base_frame, text="Nom du son:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W)
        self.name_var = tk.StringVar(value=self.current_config["name"])
        name_entry = ttk.Entry(base_frame, textvariable=self.name_var, font=('Arial', 9))
        name_entry.grid(row=0, column=1, columnspan=3, sticky=tk.EW, pady=(5, 0))
        name_entry.bind('<KeyRelease>', self.on_config_change)
        
        # Type de son et forme d'onde
        ttk.Label(base_frame, text="Type:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.type_var = tk.StringVar(value=self.current_config["type"])
        type_combo = ttk.Combobox(base_frame, textvariable=self.type_var, values=[
            "satisfying_bounce", "asmr_pop", "soft_chime", 
            "water_drop", "gentle_pluck", "crystal_ting", "advanced_custom"
        ], state="readonly", width=15)
        type_combo.grid(row=1, column=1, sticky=tk.EW, pady=(10, 0))
        type_combo.bind('<<ComboboxSelected>>', self.on_config_change)
        
        ttk.Label(base_frame, text="Forme d'onde:").grid(row=1, column=2, sticky=tk.W, padx=(20, 5), pady=(10, 0))
        self.waveform_var = tk.StringVar(value="sine")
        waveform_combo = ttk.Combobox(base_frame, textvariable=self.waveform_var, values=[
            "sine", "square", "sawtooth", "triangle", "pulse", "noise", "pink_noise", "brown_noise"
        ], state="readonly", width=12)
        waveform_combo.grid(row=1, column=3, sticky=tk.EW, pady=(10, 0))
        waveform_combo.bind('<<ComboboxSelected>>', self.on_config_change)
        
        base_frame.columnconfigure(1, weight=1)
        base_frame.columnconfigure(3, weight=1)
        
        # === FRÉQUENCE ET VOLUME ===
        freq_vol_frame = ttk.LabelFrame(parent, text="🎼 Fréquence & Volume", padding=10)
        freq_vol_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Fréquences
        ttk.Label(freq_vol_frame, text="Grave (Hz):").grid(row=0, column=0, sticky=tk.W)
        self.freq_min_var = tk.DoubleVar(value=self.current_config["frequency_range"][0])
        freq_min_scale = ttk.Scale(freq_vol_frame, from_=50, to=500, variable=self.freq_min_var, 
                                 orient=tk.HORIZONTAL, command=self.on_config_change)
        freq_min_scale.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0))
        self.freq_min_label = ttk.Label(freq_vol_frame, text="200 Hz")
        self.freq_min_label.grid(row=0, column=2, padx=(10, 0))
        
        ttk.Label(freq_vol_frame, text="Aigu (Hz):").grid(row=0, column=3, sticky=tk.W, padx=(20, 0))
        self.freq_max_var = tk.DoubleVar(value=self.current_config["frequency_range"][1])
        freq_max_scale = ttk.Scale(freq_vol_frame, from_=200, to=2000, variable=self.freq_max_var,
                                 orient=tk.HORIZONTAL, command=self.on_config_change)
        freq_max_scale.grid(row=0, column=4, sticky=tk.EW, padx=(10, 0))
        self.freq_max_label = ttk.Label(freq_vol_frame, text="800 Hz")
        self.freq_max_label.grid(row=0, column=5, padx=(10, 0))
        
        # Volume et durée
        ttk.Label(freq_vol_frame, text="Volume:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.volume_var = tk.DoubleVar(value=self.current_config["volume"])
        volume_scale = ttk.Scale(freq_vol_frame, from_=0.1, to=1.0, variable=self.volume_var,
                               orient=tk.HORIZONTAL, command=self.on_config_change)
        volume_scale.grid(row=1, column=1, sticky=tk.EW, padx=(10, 0), pady=(10, 0))
        self.volume_label = ttk.Label(freq_vol_frame, text="0.5")
        self.volume_label.grid(row=1, column=2, padx=(10, 0), pady=(10, 0))
        
        ttk.Label(freq_vol_frame, text="Durée (s):").grid(row=1, column=3, sticky=tk.W, padx=(20, 0), pady=(10, 0))
        self.duration_var = tk.DoubleVar(value=self.current_config["duration"])
        duration_scale = ttk.Scale(freq_vol_frame, from_=0.1, to=3.0, variable=self.duration_var,
                                 orient=tk.HORIZONTAL, command=self.on_config_change)
        duration_scale.grid(row=1, column=4, sticky=tk.EW, padx=(10, 0), pady=(10, 0))
        self.duration_label = ttk.Label(freq_vol_frame, text="0.5s")
        self.duration_label.grid(row=1, column=5, padx=(10, 0), pady=(10, 0))
        
        freq_vol_frame.columnconfigure(1, weight=1)
        freq_vol_frame.columnconfigure(4, weight=1)
        
        # === HARMONIQUES ===
        harm_frame = ttk.LabelFrame(parent, text="🎼 Harmoniques & Sous-Harmoniques", padding=10)
        harm_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Harmoniques principales
        ttk.Label(harm_frame, text="Harmonique 2:").grid(row=0, column=0, sticky=tk.W)
        self.harm2_var = tk.DoubleVar(value=0.0)
        harm2_scale = ttk.Scale(harm_frame, from_=0, to=1, variable=self.harm2_var, 
                               orient=tk.HORIZONTAL, command=self.on_config_change)
        harm2_scale.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0))
        self.harm2_label = ttk.Label(harm_frame, text="0.0")
        self.harm2_label.grid(row=0, column=2, padx=(10, 0))
        
        ttk.Label(harm_frame, text="Harmonique 3:").grid(row=0, column=3, sticky=tk.W, padx=(20, 0))
        self.harm3_var = tk.DoubleVar(value=0.0)
        harm3_scale = ttk.Scale(harm_frame, from_=0, to=1, variable=self.harm3_var,
                               orient=tk.HORIZONTAL, command=self.on_config_change)
        harm3_scale.grid(row=0, column=4, sticky=tk.EW, padx=(10, 0))
        self.harm3_label = ttk.Label(harm_frame, text="0.0")
        self.harm3_label.grid(row=0, column=5, padx=(10, 0))
        
        # Harmoniques spéciales
        ttk.Label(harm_frame, text="Harmonique π:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.harm_pi_var = tk.DoubleVar(value=0.0)
        harm_pi_scale = ttk.Scale(harm_frame, from_=0, to=0.5, variable=self.harm_pi_var,
                                 orient=tk.HORIZONTAL, command=self.on_config_change)
        harm_pi_scale.grid(row=1, column=1, sticky=tk.EW, padx=(10, 0), pady=(10, 0))
        self.harm_pi_label = ttk.Label(harm_frame, text="0.0")
        self.harm_pi_label.grid(row=1, column=2, padx=(10, 0), pady=(10, 0))
        
        ttk.Label(harm_frame, text="Golden Ratio:").grid(row=1, column=3, sticky=tk.W, padx=(20, 0), pady=(10, 0))
        self.harm_golden_var = tk.DoubleVar(value=0.0)
        harm_golden_scale = ttk.Scale(harm_frame, from_=0, to=0.5, variable=self.harm_golden_var,
                                     orient=tk.HORIZONTAL, command=self.on_config_change)
        harm_golden_scale.grid(row=1, column=4, sticky=tk.EW, padx=(10, 0), pady=(10, 0))
        self.harm_golden_label = ttk.Label(harm_frame, text="0.0")
        self.harm_golden_label.grid(row=1, column=5, padx=(10, 0), pady=(10, 0))
        
        harm_frame.columnconfigure(1, weight=1)
        harm_frame.columnconfigure(4, weight=1)
        
        # === ENVELOPPE ADSR ===
        env_frame = ttk.LabelFrame(parent, text="📈 Enveloppe ADSR", padding=10)
        env_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Attack et Decay
        ttk.Label(env_frame, text="Attack (ms):").grid(row=0, column=0, sticky=tk.W)
        self.attack_var = tk.DoubleVar(value=self.current_config["envelope"]["attack_ms"])
        attack_scale = ttk.Scale(env_frame, from_=0.1, to=200, variable=self.attack_var,
                               orient=tk.HORIZONTAL, command=self.on_config_change)
        attack_scale.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0))
        self.attack_label = ttk.Label(env_frame, text="5ms")
        self.attack_label.grid(row=0, column=2, padx=(10, 0))
        
        ttk.Label(env_frame, text="Release (ms):").grid(row=0, column=3, sticky=tk.W, padx=(20, 0))
        self.release_var = tk.DoubleVar(value=self.current_config["envelope"]["release_ms"])
        release_scale = ttk.Scale(env_frame, from_=10, to=1000, variable=self.release_var,
                                orient=tk.HORIZONTAL, command=self.on_config_change)
        release_scale.grid(row=0, column=4, sticky=tk.EW, padx=(10, 0))
        self.release_label = ttk.Label(env_frame, text="100ms")
        self.release_label.grid(row=0, column=5, padx=(10, 0))
        
        env_frame.columnconfigure(1, weight=1)
        env_frame.columnconfigure(4, weight=1)
        
        # === MODULATIONS ===
        mod_frame = ttk.LabelFrame(parent, text="🎛️ Modulations FM & AM", padding=10)
        mod_frame.pack(fill=tk.X, pady=(0, 10))
        
        # FM
        ttk.Label(mod_frame, text="FM Rate (Hz):").grid(row=0, column=0, sticky=tk.W)
        self.fm_rate_var = tk.DoubleVar(value=0.0)
        fm_rate_scale = ttk.Scale(mod_frame, from_=0, to=20, variable=self.fm_rate_var, 
                                 orient=tk.HORIZONTAL, command=self.on_config_change)
        fm_rate_scale.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0))
        self.fm_rate_label = ttk.Label(mod_frame, text="0.0 Hz")
        self.fm_rate_label.grid(row=0, column=2, padx=(10, 0))
        
        ttk.Label(mod_frame, text="FM Depth:").grid(row=0, column=3, sticky=tk.W, padx=(20, 0))
        self.fm_depth_var = tk.DoubleVar(value=0.0)
        fm_depth_scale = ttk.Scale(mod_frame, from_=0, to=0.5, variable=self.fm_depth_var,
                                  orient=tk.HORIZONTAL, command=self.on_config_change)
        fm_depth_scale.grid(row=0, column=4, sticky=tk.EW, padx=(10, 0))
        self.fm_depth_label = ttk.Label(mod_frame, text="0.0")
        self.fm_depth_label.grid(row=0, column=5, padx=(10, 0))
        
        # AM
        ttk.Label(mod_frame, text="AM Rate (Hz):").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.am_rate_var = tk.DoubleVar(value=0.0)
        am_rate_scale = ttk.Scale(mod_frame, from_=0, to=15, variable=self.am_rate_var,
                                 orient=tk.HORIZONTAL, command=self.on_config_change)
        am_rate_scale.grid(row=1, column=1, sticky=tk.EW, padx=(10, 0), pady=(10, 0))
        self.am_rate_label = ttk.Label(mod_frame, text="0.0 Hz")
        self.am_rate_label.grid(row=1, column=2, padx=(10, 0), pady=(10, 0))
        
        ttk.Label(mod_frame, text="AM Depth:").grid(row=1, column=3, sticky=tk.W, padx=(20, 0), pady=(10, 0))
        self.am_depth_var = tk.DoubleVar(value=0.0)
        am_depth_scale = ttk.Scale(mod_frame, from_=0, to=0.8, variable=self.am_depth_var,
                                  orient=tk.HORIZONTAL, command=self.on_config_change)
        am_depth_scale.grid(row=1, column=4, sticky=tk.EW, padx=(10, 0), pady=(10, 0))
        self.am_depth_label = ttk.Label(mod_frame, text="0.0")
        self.am_depth_label.grid(row=1, column=5, padx=(10, 0), pady=(10, 0))
        
        mod_frame.columnconfigure(1, weight=1)
        mod_frame.columnconfigure(4, weight=1)
        
        # === TURBULENCES ===
        turb_frame = ttk.LabelFrame(parent, text="🌪️ Turbulences & Texture", padding=10)
        turb_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(turb_frame, text="Bruit:").grid(row=0, column=0, sticky=tk.W)
        self.noise_var = tk.DoubleVar(value=0.0)
        noise_scale = ttk.Scale(turb_frame, from_=0, to=0.4, variable=self.noise_var, 
                               orient=tk.HORIZONTAL, command=self.on_config_change)
        noise_scale.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0))
        self.noise_label = ttk.Label(turb_frame, text="0.0")
        self.noise_label.grid(row=0, column=2, padx=(10, 0))
        
        ttk.Label(turb_frame, text="Flutter:").grid(row=0, column=3, sticky=tk.W, padx=(20, 0))
        self.flutter_var = tk.DoubleVar(value=0.0)
        flutter_scale = ttk.Scale(turb_frame, from_=0, to=0.1, variable=self.flutter_var,
                                 orient=tk.HORIZONTAL, command=self.on_config_change)
        flutter_scale.grid(row=0, column=4, sticky=tk.EW, padx=(10, 0))
        self.flutter_label = ttk.Label(turb_frame, text="0.0")
        self.flutter_label.grid(row=0, column=5, padx=(10, 0))
        
        turb_frame.columnconfigure(1, weight=1)
        turb_frame.columnconfigure(4, weight=1)
        
        # === FILTRES ===
        filt_frame = ttk.LabelFrame(parent, text="🎚️ Filtres", padding=10)
        filt_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(filt_frame, text="Lowpass (Hz):").grid(row=0, column=0, sticky=tk.W)
        self.lowpass_var = tk.DoubleVar(value=22000)
        lowpass_scale = ttk.Scale(filt_frame, from_=100, to=22000, variable=self.lowpass_var, 
                                 orient=tk.HORIZONTAL, command=self.on_config_change)
        lowpass_scale.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0))
        self.lowpass_label = ttk.Label(filt_frame, text="22000 Hz")
        self.lowpass_label.grid(row=0, column=2, padx=(10, 0))
        
        ttk.Label(filt_frame, text="Résonance:").grid(row=0, column=3, sticky=tk.W, padx=(20, 0))
        self.resonance_var = tk.DoubleVar(value=0.0)
        resonance_scale = ttk.Scale(filt_frame, from_=0, to=1.5, variable=self.resonance_var,
                                   orient=tk.HORIZONTAL, command=self.on_config_change)
        resonance_scale.grid(row=0, column=4, sticky=tk.EW, padx=(10, 0))
        self.resonance_label = ttk.Label(filt_frame, text="0.0")
        self.resonance_label.grid(row=0, column=5, padx=(10, 0))
        
        filt_frame.columnconfigure(1, weight=1)
        filt_frame.columnconfigure(4, weight=1)
        
        # === EFFETS ===
        fx_frame = ttk.LabelFrame(parent, text="✨ Effets Audio", padding=10)
        fx_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Reverb et Delay
        ttk.Label(fx_frame, text="Reverb:").grid(row=0, column=0, sticky=tk.W)
        self.reverb_var = tk.DoubleVar(value=0.0)
        reverb_scale = ttk.Scale(fx_frame, from_=0, to=1, variable=self.reverb_var, 
                               orient=tk.HORIZONTAL, command=self.on_config_change)
        reverb_scale.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0))
        self.reverb_label = ttk.Label(fx_frame, text="0.0")
        self.reverb_label.grid(row=0, column=2, padx=(10, 0))
        
        ttk.Label(fx_frame, text="Delay:").grid(row=0, column=3, sticky=tk.W, padx=(20, 0))
        self.delay_var = tk.DoubleVar(value=0.0)
        delay_scale = ttk.Scale(fx_frame, from_=0, to=1, variable=self.delay_var,
                               orient=tk.HORIZONTAL, command=self.on_config_change)
        delay_scale.grid(row=0, column=4, sticky=tk.EW, padx=(10, 0))
        self.delay_label = ttk.Label(fx_frame, text="0.0")
        self.delay_label.grid(row=0, column=5, padx=(10, 0))
        
        # Chorus et Distortion
        ttk.Label(fx_frame, text="Chorus:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.chorus_var = tk.DoubleVar(value=0.0)
        chorus_scale = ttk.Scale(fx_frame, from_=0, to=1, variable=self.chorus_var,
                                orient=tk.HORIZONTAL, command=self.on_config_change)
        chorus_scale.grid(row=1, column=1, sticky=tk.EW, padx=(10, 0), pady=(10, 0))
        self.chorus_label = ttk.Label(fx_frame, text="0.0")
        self.chorus_label.grid(row=1, column=2, padx=(10, 0), pady=(10, 0))
        
        ttk.Label(fx_frame, text="Distortion:").grid(row=1, column=3, sticky=tk.W, padx=(20, 0), pady=(10, 0))
        self.distortion_var = tk.DoubleVar(value=0.0)
        distortion_scale = ttk.Scale(fx_frame, from_=0, to=1, variable=self.distortion_var,
                                    orient=tk.HORIZONTAL, command=self.on_config_change)
        distortion_scale.grid(row=1, column=4, sticky=tk.EW, padx=(10, 0), pady=(10, 0))
        self.distortion_label = ttk.Label(fx_frame, text="0.0")
        self.distortion_label.grid(row=1, column=5, padx=(10, 0), pady=(10, 0))
        
        fx_frame.columnconfigure(1, weight=1)
        fx_frame.columnconfigure(4, weight=1)
        

        
    def setup_presets_panel(self, parent):
        """Configuration du panneau des presets"""
        
        presets_frame = ttk.LabelFrame(parent, text="💾 Presets Sauvegardés", padding=10)
        presets_frame.pack(fill=tk.BOTH, expand=True)
        
        # Liste des presets
        self.presets_listbox = tk.Listbox(presets_frame, height=15, font=('Arial', 9))
        self.presets_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.presets_listbox.bind('<<ListboxSelect>>', self.load_preset)
        
        # Boutons de gestion des presets
        buttons_frame = ttk.Frame(presets_frame)
        buttons_frame.pack(fill=tk.X)
        
        save_btn = ttk.Button(buttons_frame, text="💾 Sauvegarder", command=self.save_current_config)
        save_btn.pack(fill=tk.X, pady=(0, 5))
        
        delete_btn = ttk.Button(buttons_frame, text="🗑️ Supprimer", command=self.delete_preset)
        delete_btn.pack(fill=tk.X, pady=(0, 5))
        
        export_btn = ttk.Button(buttons_frame, text="📤 Exporter JSON", command=self.export_configs)
        export_btn.pack(fill=tk.X, pady=(0, 5))
        
        import_btn = ttk.Button(buttons_frame, text="📥 Importer JSON", command=self.import_configs)
        import_btn.pack(fill=tk.X)
        
        self.update_presets_list()
        
    def setup_playback_controls(self, parent):
        """Configuration des contrôles de lecture"""
        
        playback_frame = ttk.LabelFrame(parent, text="🎮 Test & Lecture", padding=10)
        playback_frame.pack(fill=tk.X, pady=(20, 0))
        
        buttons_frame = ttk.Frame(playback_frame)
        buttons_frame.pack()
        
        # Boutons de test
        test_btn = ttk.Button(buttons_frame, text="🎵 Tester le Son Ultra-Complet", command=self.test_advanced_sound)
        test_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        random_btn = ttk.Button(buttons_frame, text="🎲 CONFIGURATION FOLLE", command=self.generate_random_sound)
        random_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Boutons MIDI
        midi_file_btn = ttk.Button(buttons_frame, text="📁 Choisir MIDI", command=self.select_midi_file)
        midi_file_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.midi_btn = ttk.Button(buttons_frame, text="🎼 Play MIDI", command=self.toggle_midi_playback)
        self.midi_btn.pack(side=tk.LEFT)
        
        # Label pour le fichier MIDI sélectionné
        self.midi_file_label = ttk.Label(playback_frame, text="Aucun fichier MIDI sélectionné", font=('Arial', 8))
        self.midi_file_label.pack(pady=(5, 0))
        
        # Indicateur de statut
        self.status_var = tk.StringVar(value="Prêt à tester")
        status_label = ttk.Label(playback_frame, textvariable=self.status_var, font=('Arial', 9, 'italic'))
        status_label.pack(pady=(10, 0))
        
    def on_config_change(self, event=None):
        """Appelé quand la configuration change"""
        self.update_current_config()
        self.update_labels()
        
    def update_current_config(self):
        """Met à jour la configuration actuelle"""
        self.current_config.update({
            "name": self.name_var.get(),
            "type": self.type_var.get(),
            "frequency_range": [int(self.freq_min_var.get()), int(self.freq_max_var.get())],
            "duration": round(self.duration_var.get(), 2),
            "volume": round(self.volume_var.get(), 2),
            "envelope": {
                "attack_ms": round(self.attack_var.get(), 1),
                "decay_ms": 50.0,
                "sustain_level": 0.7,
                "release_ms": round(self.release_var.get(), 1)
            }
        })
        
    def update_labels(self):
        """Met à jour les labels avec les valeurs actuelles"""
        # Labels de base
        self.freq_min_label.config(text=f"{int(self.freq_min_var.get())} Hz")
        self.freq_max_label.config(text=f"{int(self.freq_max_var.get())} Hz")
        self.volume_label.config(text=f"{self.volume_var.get():.2f}")
        self.duration_label.config(text=f"{self.duration_var.get():.2f}s")
        self.attack_label.config(text=f"{self.attack_var.get():.1f}ms")
        self.release_label.config(text=f"{self.release_var.get():.1f}ms")
        
        # Labels harmoniques
        if hasattr(self, 'harm2_label'):
            self.harm2_label.config(text=f"{self.harm2_var.get():.2f}")
        if hasattr(self, 'harm3_label'):
            self.harm3_label.config(text=f"{self.harm3_var.get():.2f}")
        if hasattr(self, 'harm_pi_label'):
            self.harm_pi_label.config(text=f"{self.harm_pi_var.get():.2f}")
        if hasattr(self, 'harm_golden_label'):
            self.harm_golden_label.config(text=f"{self.harm_golden_var.get():.2f}")
            
        # Labels modulations
        if hasattr(self, 'fm_rate_label'):
            self.fm_rate_label.config(text=f"{self.fm_rate_var.get():.1f} Hz")
        if hasattr(self, 'fm_depth_label'):
            self.fm_depth_label.config(text=f"{self.fm_depth_var.get():.2f}")
        if hasattr(self, 'am_rate_label'):
            self.am_rate_label.config(text=f"{self.am_rate_var.get():.1f} Hz")
        if hasattr(self, 'am_depth_label'):
            self.am_depth_label.config(text=f"{self.am_depth_var.get():.2f}")
            
        # Labels turbulences
        if hasattr(self, 'noise_label'):
            self.noise_label.config(text=f"{self.noise_var.get():.2f}")
        if hasattr(self, 'flutter_label'):
            self.flutter_label.config(text=f"{self.flutter_var.get():.3f}")
            
        # Labels filtres
        if hasattr(self, 'lowpass_label'):
            self.lowpass_label.config(text=f"{int(self.lowpass_var.get())} Hz")
        if hasattr(self, 'resonance_label'):
            self.resonance_label.config(text=f"{self.resonance_var.get():.2f}")
            
        # Labels effets
        if hasattr(self, 'reverb_label'):
            self.reverb_label.config(text=f"{self.reverb_var.get():.2f}")
        if hasattr(self, 'delay_label'):
            self.delay_label.config(text=f"{self.delay_var.get():.2f}")
        if hasattr(self, 'chorus_label'):
            self.chorus_label.config(text=f"{self.chorus_var.get():.2f}")
        if hasattr(self, 'distortion_label'):
            self.distortion_label.config(text=f"{self.distortion_var.get():.2f}")
        
    def test_sound(self):
        """Teste le son actuel"""
        self.status_var.set("🎵 Génération du son...")
        self.root.update()
        
        def play_sound():
            try:
                # Génère une fréquence aléatoire dans la plage
                freq_min, freq_max = self.current_config["frequency_range"]
                frequency = random.uniform(freq_min, freq_max)
                
                # Génère le son
                sound_data = self.generate_configured_sound(frequency)
                
                # Joue le son
                self.play_sound_data(sound_data)
                
                self.status_var.set(f"✅ Son joué ({frequency:.1f} Hz)")
                
            except Exception as e:
                self.status_var.set(f"❌ Erreur: {str(e)}")
                
        threading.Thread(target=play_sound, daemon=True).start()
        
    def test_advanced_sound(self):
        """Teste le son avec la configuration avancée complète"""
        self.status_var.set("🔬 Test avancé en cours...")
        self.root.update()
        
        def play_advanced():
            try:
                # Génère une fréquence dans la plage
                freq_min, freq_max = self.current_config["frequency_range"]
                frequency = random.uniform(freq_min, freq_max)
                
                # Configuration avancée complète
                config = {
                    "frequency": frequency,
                    "duration": self.current_config["duration"],
                    "volume": self.current_config["volume"],
                    "waveform": getattr(self, 'waveform_var', tk.StringVar(value="sine")).get()
                }
                
                # Ajoute tous les paramètres avancés
                harmonics = []
                if hasattr(self, 'harm2_var') and self.harm2_var.get() > 0:
                    harmonics.append({"harmonic": 2, "amplitude": self.harm2_var.get(), "waveform": "sine"})
                if hasattr(self, 'harm3_var') and self.harm3_var.get() > 0:
                    harmonics.append({"harmonic": 3, "amplitude": self.harm3_var.get(), "waveform": "triangle"})
                if harmonics:
                    config["harmonics"] = harmonics
                
                # Enveloppe avancée
                config["envelope"] = {
                    "type": "adsr",
                    "attack_ms": self.current_config["envelope"]["attack_ms"],
                    "decay_ms": self.current_config["envelope"].get("decay_ms", 50.0),
                    "sustain_level": self.current_config["envelope"].get("sustain_level", 0.7),
                    "release_ms": self.current_config["envelope"]["release_ms"],
                    "curve_type": "exponential"
                }
                
                # Modulations
                if hasattr(self, 'fm_rate_var') and self.fm_rate_var.get() > 0:
                    config["modulation"] = {
                        "fm_frequency": self.fm_rate_var.get(),
                        "fm_depth": getattr(self, 'fm_depth_var', tk.DoubleVar(value=0.1)).get()
                    }
                
                # Turbulences
                if hasattr(self, 'noise_var') and self.noise_var.get() > 0:
                    config["turbulence"] = {
                        "noise_type": "pink",
                        "noise_amount": self.noise_var.get()
                    }
                
                # Filtres et effets
                filters = []
                if hasattr(self, 'lowpass_var') and self.lowpass_var.get() < 22000:
                    filters.append({"type": "lowpass", "cutoff": self.lowpass_var.get(), "resonance": 0.7})
                if filters:
                    config["filters"] = filters
                
                effects = []
                if hasattr(self, 'reverb_var') and self.reverb_var.get() > 0:
                    effects.append({"type": "reverb", "room_size": 0.5, "wet_level": self.reverb_var.get()})
                if hasattr(self, 'delay_var') and self.delay_var.get() > 0:
                    effects.append({"type": "delay", "delay_ms": 125, "feedback": 0.3, "wet_level": self.delay_var.get()})
                if effects:
                    config["effects"] = effects
                
                # Génère le son avancé
                sound_data = self.sound_generator.generate_advanced_sound(config)
                
                # Joue le son
                self.play_sound_data(sound_data)
                
                self.status_var.set(f"🔬 Son avancé généré ({frequency:.1f} Hz)")
                
            except Exception as e:
                self.status_var.set(f"❌ Erreur avancée: {str(e)}")
                
        threading.Thread(target=play_advanced, daemon=True).start()
        
    def generate_configured_sound(self, frequency):
        """Génère un son ULTRA-COMPLET avec TOUS les paramètres configurés"""
        
        # Configuration COMPLÈTE avec tous les paramètres avancés
        config = {
            "frequency": frequency,
            "duration": self.current_config["duration"],
            "volume": self.current_config["volume"],
            "waveform": getattr(self, 'waveform_var', tk.StringVar(value="sine")).get()
        }
        
        # === HARMONIQUES COMPLÈTES ===
        harmonics = []
        if hasattr(self, 'harm2_var') and self.harm2_var.get() > 0:
            harmonics.append({"harmonic": 2, "amplitude": self.harm2_var.get(), "waveform": "sine"})
        if hasattr(self, 'harm3_var') and self.harm3_var.get() > 0:
            harmonics.append({"harmonic": 3, "amplitude": self.harm3_var.get(), "waveform": "triangle"})
        if hasattr(self, 'harm_pi_var') and self.harm_pi_var.get() > 0:
            harmonics.append({"harmonic": 3.14159, "amplitude": self.harm_pi_var.get(), "waveform": "sine"})
        if hasattr(self, 'harm_golden_var') and self.harm_golden_var.get() > 0:
            harmonics.append({"harmonic": 1.618, "amplitude": self.harm_golden_var.get(), "waveform": "triangle"})
        
        if harmonics:
            config["harmonics"] = harmonics
        
        # === ENVELOPPE AVANCÉE ===
        config["envelope"] = {
            "type": "adsr",
            "attack_ms": self.current_config["envelope"]["attack_ms"],
            "decay_ms": self.current_config["envelope"].get("decay_ms", 50.0),
            "sustain_level": self.current_config["envelope"].get("sustain_level", 0.7),
            "release_ms": self.current_config["envelope"]["release_ms"],
            "curve_type": "exponential"
        }
        
        # === MODULATIONS COMPLÈTES (FM + AM) ===
        modulation = {}
        if hasattr(self, 'fm_rate_var') and self.fm_rate_var.get() > 0:
            modulation["fm_frequency"] = self.fm_rate_var.get()
            modulation["fm_depth"] = getattr(self, 'fm_depth_var', tk.DoubleVar(value=0.1)).get()
        if hasattr(self, 'am_rate_var') and self.am_rate_var.get() > 0:
            modulation["am_frequency"] = self.am_rate_var.get()
            modulation["am_depth"] = getattr(self, 'am_depth_var', tk.DoubleVar(value=0.1)).get()
        if modulation:
            config["modulation"] = modulation
        
        # === TURBULENCES COMPLÈTES ===
        turbulence = {}
        if hasattr(self, 'noise_var') and self.noise_var.get() > 0:
            turbulence["noise_type"] = "pink"
            turbulence["noise_amount"] = self.noise_var.get()
        if hasattr(self, 'flutter_var') and self.flutter_var.get() > 0:
            turbulence["flutter_amount"] = self.flutter_var.get()
            turbulence["flutter_rate"] = 12.0  # Hz par défaut
        if turbulence:
            config["turbulence"] = turbulence
        
        # === FILTRES COMPLETS ===
        filters = []
        if hasattr(self, 'lowpass_var') and self.lowpass_var.get() < 22000:
            resonance = getattr(self, 'resonance_var', tk.DoubleVar(value=0.7)).get()
            filters.append({"type": "lowpass", "cutoff": self.lowpass_var.get(), "resonance": resonance})
        if filters:
            config["filters"] = filters
        
        # === EFFETS COMPLETS ===
        effects = []
        if hasattr(self, 'reverb_var') and self.reverb_var.get() > 0:
            effects.append({"type": "reverb", "room_size": 0.5, "wet_level": self.reverb_var.get()})
        if hasattr(self, 'delay_var') and self.delay_var.get() > 0:
            effects.append({"type": "delay", "delay_ms": 125, "feedback": 0.3, "wet_level": self.delay_var.get()})
        if hasattr(self, 'chorus_var') and self.chorus_var.get() > 0:
            effects.append({"type": "chorus", "rate": 1.5, "depth": 0.002, "wet_level": self.chorus_var.get()})
        if hasattr(self, 'distortion_var') and self.distortion_var.get() > 0:
            effects.append({"type": "distortion", "drive": 5.0, "wet_level": self.distortion_var.get()})
        if effects:
            config["effects"] = effects
        
        # === UTILISE TOUJOURS LE GÉNÉRATEUR AVANCÉ COMPLET ===
        # Plus de différence entre types - TOUS utilisent la config complète !
        return self.sound_generator.generate_advanced_sound(config)
            
    def play_sound_data(self, sound_data):
        """Joue les données audio"""
        # Convertit en format pygame
        sound_data = np.clip(sound_data * 32767, -32768, 32767).astype(np.int16)
        
        # Assure que c'est stéréo (2 canaux) pour pygame
        if len(sound_data.shape) == 1:
            # Mono vers stéréo
            stereo_data = np.column_stack((sound_data, sound_data))
        else:
            stereo_data = sound_data
            
        # Crée un objet sound pygame
        sound = pygame.sndarray.make_sound(stereo_data)
        sound.play()
        
    def generate_random_sound(self):
        """Génère une configuration ULTRA-COMPLÈTE aléatoire avec TOUS les paramètres"""
        self.status_var.set("🎲 Génération aléatoire COMPLÈTE...")
        
        # === RANDOMISATION COMPLÈTE ===
        types = ["satisfying_bounce", "asmr_pop", "soft_chime", "water_drop", "gentle_pluck", "crystal_ting", "advanced_custom"]
        waveforms = ["sine", "square", "sawtooth", "triangle", "pulse", "noise", "pink_noise", "brown_noise"]
        
        # Fréquences aléatoires avec différentes plages possibles
        freq_ranges = [
            [80, 200, 600, 1500],    # Bass range
            [100, 300, 800, 2000],   # Mid range  
            [200, 500, 1200, 3000],  # High-mid range
            [50, 150, 400, 1000],    # Sub-bass range
        ]
        selected_range = random.choice(freq_ranges)
        freq_min = random.randint(selected_range[0], selected_range[1])
        freq_max = random.randint(selected_range[2], selected_range[3])
        
        # === PARAMÈTRES DE BASE ===
        self.name_var.set(f"Son Folie {random.randint(100, 9999)}")
        self.type_var.set(random.choice(types))
        self.waveform_var.set(random.choice(waveforms))
        self.freq_min_var.set(freq_min)
        self.freq_max_var.set(freq_max)
        self.duration_var.set(round(random.uniform(0.1, 2.5), 2))
        self.volume_var.set(round(random.uniform(0.2, 0.9), 2))
        
        # === ENVELOPPE ADSR ALÉATOIRE ===
        self.attack_var.set(round(random.uniform(0.1, 150), 1))
        self.release_var.set(round(random.uniform(10, 800), 1))
        
        # === HARMONIQUES ALÉATOIRES (probabilité de les activer) ===
        if random.random() < 0.6:  # 60% de chance d'avoir harmonique 2
            self.harm2_var.set(round(random.uniform(0.1, 0.8), 2))
        else:
            self.harm2_var.set(0.0)
            
        if random.random() < 0.4:  # 40% de chance d'avoir harmonique 3
            self.harm3_var.set(round(random.uniform(0.1, 0.6), 2))
        else:
            self.harm3_var.set(0.0)
            
        if random.random() < 0.2:  # 20% de chance d'avoir harmonique π (rare)
            self.harm_pi_var.set(round(random.uniform(0.05, 0.3), 2))
        else:
            self.harm_pi_var.set(0.0)
            
        if random.random() < 0.15:  # 15% de chance d'avoir golden ratio (très rare)
            self.harm_golden_var.set(round(random.uniform(0.05, 0.25), 2))
        else:
            self.harm_golden_var.set(0.0)
        
        # === MODULATIONS ALÉATOIRES ===
        if random.random() < 0.5:  # 50% de chance d'avoir FM
            self.fm_rate_var.set(round(random.uniform(0.5, 15), 1))
            self.fm_depth_var.set(round(random.uniform(0.05, 0.4), 2))
        else:
            self.fm_rate_var.set(0.0)
            self.fm_depth_var.set(0.0)
            
        if random.random() < 0.3:  # 30% de chance d'avoir AM
            self.am_rate_var.set(round(random.uniform(0.5, 10), 1))
            self.am_depth_var.set(round(random.uniform(0.1, 0.6), 2))
        else:
            self.am_rate_var.set(0.0)
            self.am_depth_var.set(0.0)
        
        # === TURBULENCES ALÉATOIRES ===
        if random.random() < 0.4:  # 40% de chance d'avoir du bruit
            self.noise_var.set(round(random.uniform(0.01, 0.3), 3))
        else:
            self.noise_var.set(0.0)
            
        if random.random() < 0.25:  # 25% de chance d'avoir du flutter
            self.flutter_var.set(round(random.uniform(0.005, 0.08), 3))
        else:
            self.flutter_var.set(0.0)
        
        # === FILTRES ALÉATOIRES ===
        if random.random() < 0.6:  # 60% de chance d'avoir un filtre lowpass actif
            self.lowpass_var.set(random.randint(800, 18000))
            if random.random() < 0.4:  # 40% de chance d'avoir de la résonance
                self.resonance_var.set(round(random.uniform(0.1, 1.2), 2))
            else:
                self.resonance_var.set(0.0)
        else:
            self.lowpass_var.set(22000)  # Pas de filtre
            self.resonance_var.set(0.0)
        
        # === EFFETS ALÉATOIRES ===
        if random.random() < 0.7:  # 70% de chance d'avoir du reverb
            self.reverb_var.set(round(random.uniform(0.1, 0.8), 2))
        else:
            self.reverb_var.set(0.0)
            
        if random.random() < 0.4:  # 40% de chance d'avoir du delay
            self.delay_var.set(round(random.uniform(0.1, 0.7), 2))
        else:
            self.delay_var.set(0.0)
            
        if random.random() < 0.3:  # 30% de chance d'avoir du chorus
            self.chorus_var.set(round(random.uniform(0.1, 0.6), 2))
        else:
            self.chorus_var.set(0.0)
            
        if random.random() < 0.2:  # 20% de chance d'avoir de la distortion
            self.distortion_var.set(round(random.uniform(0.05, 0.4), 2))
        else:
            self.distortion_var.set(0.0)
        
        # Met à jour la configuration et les labels
        self.update_current_config()
        self.update_labels()
        
        # Test automatique du son généré
        self.status_var.set("🎲 Son aléatoire COMPLET généré ! Test en cours...")
        self.test_advanced_sound()
        
    def select_midi_file(self):
        """Sélectionne un fichier MIDI"""
        filename = filedialog.askopenfilename(
            filetypes=[("MIDI files", "*.mid *.midi"), ("All files", "*.*")],
            title="Choisir un fichier MIDI",
            initialdir="music" if os.path.exists("music") else "."
        )
        if filename:
            self.selected_midi_file = filename
            basename = os.path.basename(filename)
            self.midi_file_label.config(text=f"📄 {basename}")
            self.status_var.set(f"✅ Fichier MIDI sélectionné: {basename}")
            
    def toggle_midi_playback(self):
        """Lance ou arrête la lecture MIDI"""
        if not self.selected_midi_file:
            self.status_var.set("❌ Aucun fichier MIDI sélectionné")
            return
            
        if not MIDO_AVAILABLE:
            self.status_var.set("❌ Module mido non disponible")
            return
            
        if not self.midi_playing:
            # Démarrer la lecture
            self.start_midi_playback()
        else:
            # Arrêter la lecture
            self.stop_midi_playback()
            
    def start_midi_playback(self):
        """Démarre la lecture MIDI"""
        self.midi_playing = True
        self.midi_btn.config(text="⏹️ Stop MIDI")
        self.status_var.set("🎼 Lecture MIDI en cours...")
        
        def play_midi():
            try:
                mid = mido.MidiFile(self.selected_midi_file)
                
                for msg in mid.play():
                    if not self.midi_playing:
                        break
                        
                    # Vérifier que c'est un message note_on avec velocity > 0
                    if (hasattr(msg, 'type') and hasattr(msg, 'velocity') and hasattr(msg, 'note') and
                        getattr(msg, 'type', None) == 'note_on' and getattr(msg, 'velocity', 0) > 0):
                        # Convertit la note MIDI en fréquence
                        frequency = 440 * (2 ** ((getattr(msg, 'note', 69) - 69) / 12))
                        
                        # Vérifie si la fréquence est dans la plage configurée
                        freq_min, freq_max = self.current_config["frequency_range"]
                        if freq_min <= frequency <= freq_max:
                            sound_data = self.generate_configured_sound(frequency)
                            self.play_sound_data(sound_data)
                            
                self.stop_midi_playback()
                
            except Exception as e:
                self.status_var.set(f"❌ Erreur MIDI: {str(e)}")
                self.stop_midi_playback()
                
        self.midi_thread = threading.Thread(target=play_midi, daemon=True)
        self.midi_thread.start()
        
    def stop_midi_playback(self):
        """Arrête la lecture MIDI"""
        self.midi_playing = False
        self.midi_btn.config(text="🎼 Play MIDI")
        self.status_var.set("⏹️ Lecture MIDI arrêtée")
            
    def save_current_config(self):
        """Sauvegarde la configuration actuelle"""
        self.update_current_config()
        
        # Vérifie si le nom existe déjà
        existing_names = [config["name"] for config in self.saved_configs]
        if self.current_config["name"] in existing_names:
            if not messagebox.askyesno("Remplacer", f"Le preset '{self.current_config['name']}' existe déjà. Remplacer?"):
                return
            # Supprime l'ancien
            self.saved_configs = [c for c in self.saved_configs if c["name"] != self.current_config["name"]]
            
        self.saved_configs.append(self.current_config.copy())
        self.save_configs()
        self.update_presets_list()
        self.status_var.set(f"💾 Preset '{self.current_config['name']}' sauvegardé")
        
    def load_preset(self, event=None):
        """Charge un preset sélectionné"""
        selection = self.presets_listbox.curselection()
        if selection:
            index = selection[0]
            config = self.saved_configs[index]
            self.load_config_to_ui(config)
            self.status_var.set(f"📥 Preset '{config['name']}' chargé")
            
    def load_config_to_ui(self, config):
        """Charge une configuration dans l'interface"""
        self.name_var.set(config["name"])
        self.type_var.set(config["type"])
        self.freq_min_var.set(config["frequency_range"][0])
        self.freq_max_var.set(config["frequency_range"][1])
        self.duration_var.set(config["duration"])
        self.volume_var.set(config["volume"])
        self.attack_var.set(config["envelope"]["attack_ms"])
        self.release_var.set(config["envelope"]["release_ms"])
        
        self.current_config = config.copy()
        self.update_labels()
        
    def delete_preset(self):
        """Supprime le preset sélectionné"""
        selection = self.presets_listbox.curselection()
        if selection:
            index = selection[0]
            config_name = self.saved_configs[index]["name"]
            if messagebox.askyesno("Supprimer", f"Supprimer le preset '{config_name}'?"):
                del self.saved_configs[index]
                self.save_configs()
                self.update_presets_list()
                self.status_var.set(f"🗑️ Preset '{config_name}' supprimé")
                
    def update_presets_list(self):
        """Met à jour la liste des presets"""
        self.presets_listbox.delete(0, tk.END)
        for config in self.saved_configs:
            self.presets_listbox.insert(tk.END, f"{config['name']} ({config['type']})")
            
    def save_configs(self):
        """Sauvegarde les configurations dans un fichier JSON"""
        os.makedirs("sound_presets", exist_ok=True)
        with open("sound_presets/custom_sounds.json", "w", encoding="utf-8") as f:
            json.dump(self.saved_configs, f, indent=2, ensure_ascii=False)
            
    def load_configs(self):
        """Charge les configurations depuis le fichier JSON"""
        try:
            if os.path.exists("sound_presets/custom_sounds.json"):
                with open("sound_presets/custom_sounds.json", "r", encoding="utf-8") as f:
                    self.saved_configs = json.load(f)
        except Exception as e:
            print(f"Erreur lors du chargement des configs: {e}")
            self.saved_configs = []
            
    def export_configs(self):
        """Exporte les configurations vers un fichier"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Exporter les presets"
        )
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.saved_configs, f, indent=2, ensure_ascii=False)
            self.status_var.set(f"📤 Presets exportés vers {os.path.basename(filename)}")
            
    def import_configs(self):
        """Importe des configurations depuis un fichier"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Importer des presets"
        )
        if filename:
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    imported_configs = json.load(f)
                self.saved_configs.extend(imported_configs)
                self.save_configs()
                self.update_presets_list()
                self.status_var.set(f"📥 {len(imported_configs)} presets importés")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'importation: {e}")
                
    def run(self):
        """Lance l'interface"""
        self.root.mainloop()

def main():
    """Point d'entrée principal"""
    print("🎵 Lancement du Sound Designer TikSimPro...")
    
    try:
        app = SoundDesignerGUI()
        app.run()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        input("Appuyez sur Entrée pour quitter...")

if __name__ == "__main__":
    main() 