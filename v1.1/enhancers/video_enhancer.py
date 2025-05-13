"""
Module d'amélioration visuelle pour les vidéos TikTok.
Permet d'ajouter du texte, des effets et des animations.
"""

import os
import cv2
import numpy as np
from moviepy import VideoFileClip, TextClip, ColorClip, CompositeVideoClip, concatenate_videoclips, concatenate_audioclips, AudioFileClip
from PIL import Image, ImageDraw, ImageFont
import tempfile
import random
import textwrap
from datetime import datetime

from enhancers.base_enhancer import BaseEnhancer

class VideoEnhancer(BaseEnhancer):
    """Classe pour améliorer les vidéos avec du texte et des effets visuels"""
    
    # Polices par défaut pour le texte
    DEFAULT_FONTS = [
        "Arial", "Verdana", "Helvetica", "Tahoma", "Impact",
        "Comic Sans MS", "Georgia", "Trebuchet MS", "Times New Roman"
    ]
    
    # Couleurs vives populaires sur TikTok
    TIKTOK_COLORS = [
        "#FF0050",  # Rouge TikTok
        "#00F2EA",  # Turquoise TikTok
        "#FFFFFF",  # Blanc
        "#FE2C55",  # Rose TikTok
        "#25F4EE",  # Bleu TikTok
        "#FFFC00",  # Jaune Snapchat
        "#00B2FF",  # Bleu vif
        "#FF3370",  # Rose vif
        "#FFDE59",  # Jaune d'or
        "#8A2BE2"   # Violet
    ]
    
    def __init__(self, temp_dir=None, add_intro=False, add_hashtags=False, add_music=True):
        """
        Initialise l'améliorateur de vidéos
        
        Args:
            temp_dir: Dossier temporaire (optionnel)
            add_intro: Ajouter automatiquement une introduction
            add_hashtags: Ajouter automatiquement des hashtags
            add_music: Ajouter automatiquement de la musique
        """
        # Paramètres par défaut pour les options
        self.default_options = {
            "add_intro": add_intro,
            "add_hashtags": add_hashtags,
            "add_music": add_music
        }
        
        if temp_dir:
            self.temp_dir = temp_dir
        else:
            self.temp_dir = tempfile.mkdtemp()
            
        # Créer le dossier temporaire s'il n'existe pas
        os.makedirs(self.temp_dir, exist_ok=True)
        
        print(f"Dossier temporaire: {self.temp_dir}")
        
        # Vérifier si les polices existent
        self.available_fonts = self._check_fonts()
        
        if not self.available_fonts:
            print("Aucune police disponible, utilisation des polices par défaut")
            self.available_fonts = ["Arial"]
    
    def _check_fonts(self):
        """Vérifie quelles polices sont disponibles sur le système"""
        available_fonts = []
        
        # Essayer de charger chaque police avec PIL
        for font_name in self.DEFAULT_FONTS:
            try:
                # Tester avec une petite taille pour vérifier rapidement
                ImageFont.truetype(font_name, 12)
                available_fonts.append(font_name)
            except (IOError, OSError):
                # Police non disponible
                continue
        
        return available_fonts
    
    def _hex_to_rgb(self, hex_color):
        """Convertit une couleur hexadécimale en RGB"""
        # Supprimer le # si présent
        hex_color = hex_color.lstrip('#')
        
        # Convertir en RGB
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def add_intro_text(self, video_path, output_path=None, text="Regardez jusqu'à la fin! 👀", duration=3.0):
        """
        Ajoute un texte d'introduction au début de la vidéo
        
        Args:
            video_path: Chemin de la vidéo d'origine
            output_path: Chemin de sortie (optionnel)
            text: Texte d'introduction
            duration: Durée de l'introduction en secondes
            
        Returns:
            Le chemin de la vidéo modifiée
        """
        if not output_path:
            # Créer un nom pour la vidéo modifiée
            basename = os.path.basename(video_path)
            name, ext = os.path.splitext(basename)
            output_path = os.path.join(os.path.dirname(video_path), f"{name}_intro{ext}")
        
        try:
            # Charger la vidéo
            video = VideoFileClip(video_path)
            
            # Créer le texte d'intro
            font = random.choice(self.available_fonts)
            color = self._hex_to_rgb(random.choice(self.TIKTOK_COLORS))
            
            txt_clip = TextClip(
                text,
                fontsize=70,
                color="white",
                font=font,
                stroke_color="black",
                stroke_width=1.5
            )
            
            # Centrer le texte et ajouter des effets
            txt_clip = (
                txt_clip
                .set_position('center')
                .set_duration(duration)
                .crossfadein(0.5)
                .crossfadeout(0.5)
            )
            
            # Créer une vidéo d'introduction avec un fond noir
            w, h = video.size
            color_clip = ColorClip(size=(w, h), color=(0, 0, 0))
            color_clip = color_clip.set_duration(duration)
            
            # Superposer le texte sur le fond noir
            intro_clip = CompositeVideoClip([color_clip, txt_clip])
            
            # Assembler l'intro et la vidéo
            final_clip = concatenate_videoclips([intro_clip, video])
            
            # Si la durée dépasse 61 secondes, couper à 61 secondes
            if final_clip.duration > 61.0:
                excess = final_clip.duration - 61.0
                # Couper l'excédent de la vidéo principale, pas de l'intro
                video = video.subclip(0, video.duration - excess)
                final_clip = concatenate_videoclips([intro_clip, video])
            
            # Écrire la vidéo finale
            print(f"Écriture de la vidéo avec introduction: {output_path}")
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )
            
            # Fermer les clips
            video.close()
            final_clip.close()
            
            print(f"Vidéo avec introduction créée: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Erreur lors de l'ajout de l'introduction: {e}")
            return None
    
    def add_hashtag_overlay(self, video_path, output_path=None, hashtags=None):
        """
        Ajoute des hashtags en superposition sur la vidéo
        
        Args:
            video_path: Chemin de la vidéo d'origine
            output_path: Chemin de sortie (optionnel)
            hashtags: Liste de hashtags (sans le #)
            
        Returns:
            Le chemin de la vidéo modifiée
        """
        if not hashtags:
            hashtags = ["fyp", "viral", "foryou", "tiktok"]
        
        if not output_path:
            # Créer un nom pour la vidéo modifiée
            basename = os.path.basename(video_path)
            name, ext = os.path.splitext(basename)
            output_path = os.path.join(os.path.dirname(video_path), f"{name}_hashtags{ext}")
        
        try:
            # Charger la vidéo
            video = VideoFileClip(video_path)
            
            # Créer une chaîne de hashtags
            hashtag_text = " ".join([f"#{tag}" for tag in hashtags])
            
            # Limiter la longueur
            if len(hashtag_text) > 50:
                hashtag_text = hashtag_text[:47] + "..."
            
            # Créer le clip de texte des hashtags
            font = random.choice(self.available_fonts)
            color = random.choice(self.TIKTOK_COLORS)
            
            txt_clip = TextClip(
                hashtag_text,
                fontsize=30,
                color="white",
                font=font,
                stroke_color="black",
                stroke_width=1
            )
            
            # Positionner en bas de l'écran
            txt_clip = (
                txt_clip
                .set_position(('center', 'bottom'))
                .set_duration(video.duration)
                .margin(bottom=20, opacity=0)
                .crossfadein(0.5)
            )
            
            # Superposer le texte sur la vidéo
            final_clip = CompositeVideoClip([video, txt_clip])
            
            # Écrire la vidéo finale
            print(f"Écriture de la vidéo avec hashtags: {output_path}")
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )
            
            # Fermer les clips
            video.close()
            final_clip.close()
            
            print(f"Vidéo avec hashtags créée: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Erreur lors de l'ajout des hashtags: {e}")
            return None
    
    def add_call_to_action(self, video_path, output_path=None, text="Abonnez-vous! 👆", start_time=None):
        """
        Ajoute un appel à l'action à la fin de la vidéo
        
        Args:
            video_path: Chemin de la vidéo d'origine
            output_path: Chemin de sortie (optionnel)
            text: Texte d'appel à l'action
            start_time: Moment d'apparition (en secondes depuis la fin)
            
        Returns:
            Le chemin de la vidéo modifiée
        """
        if not output_path:
            # Créer un nom pour la vidéo modifiée
            basename = os.path.basename(video_path)
            name, ext = os.path.splitext(basename)
            output_path = os.path.join(os.path.dirname(video_path), f"{name}_cta{ext}")
        
        try:
            # Charger la vidéo
            video = VideoFileClip(video_path)
            
            # Définir le moment d'apparition si non spécifié
            if start_time is None:
                # Par défaut, 5 secondes avant la fin
                start_time = max(0, video.duration - 5)
            
            # Créer le clip de texte
            font = random.choice(self.available_fonts)
            color = self._hex_to_rgb(random.choice(self.TIKTOK_COLORS))
            
            txt_clip = TextClip(
                text,
                fontsize=60,
                color="white",
                font=font,
                stroke_color="black",
                stroke_width=1.5
            )
            
            # Positionner en haut de l'écran
            txt_clip = (
                txt_clip
                .set_position(('center', 0.2))  # 20% depuis le haut
                .set_start(start_time)
                .set_duration(video.duration - start_time)
                .crossfadein(0.5)
            )
            
            # Superposer le texte sur la vidéo
            final_clip = CompositeVideoClip([video, txt_clip])
            
            # Écrire la vidéo finale
            print(f"Écriture de la vidéo avec appel à l'action: {output_path}")
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )
            
            # Fermer les clips
            video.close()
            final_clip.close()
            
            print(f"Vidéo avec appel à l'action créée: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Erreur lors de l'ajout de l'appel à l'action: {e}")
            return None
    
    def add_viral_music(self, video_path, output_path, music_file=None):
        """Ajoute une musique virale à la vidéo"""
        try:
            # Charger la vidéo
            video = VideoFileClip(video_path)
            
            # Si aucun fichier de musique n'est spécifié, utiliser les sons de la simulation
            if not music_file:
                print("Pas de musique spécifiée, la vidéo gardera sa piste audio originale")
                return video_path
            
            # Charger la musique
            music = AudioFileClip(music_file)

            # Boucler la musique si nécessaire
            if music.duration < video.duration:
                repeats = int(video.duration / music.duration) + 1
                music_looped = concatenate_audioclips([music] * repeats)
            else:
                music_looped = music

            # Découper proprement après la boucle
            music_final = music_looped.subclipped(0, video.duration)

            # Ajouter à la vidéo
            final = video.with_audio(music_final)
            
            # Écrire la vidéo
            final.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac'
            )
            
            # Fermer les clips
            video.close()
            final.close()
            
            print(f"Musique ajoutée: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Erreur lors de l'ajout de la musique: {e}")
            return video_path
    
    def enhance_video(self, video_path, output_path, options):
        """
        Améliore une vidéo avec plusieurs effets
        
        Args:
            video_path: Chemin de la vidéo d'origine
            output_path: Chemin de sortie
            options: Dictionnaire d'options d'amélioration (intro_text, hashtags, cta_text, etc.)
            
        Returns:
            Le chemin de la vidéo modifiée
        """
        # Fusionner avec les options par défaut
        full_options = self.default_options.copy()
        if options:
            full_options.update(options)
        
        # Vérifier que le fichier d'entrée existe
        if not os.path.exists(video_path):
            print(f"ERREUR: Le fichier vidéo d'entrée n'existe pas: {video_path}")
            return None
            
        # Si output_path n'est pas fourni, créer un nom par défaut
        if not output_path:
            basename = os.path.basename(video_path)
            name, ext = os.path.splitext(basename)
            output_path = os.path.join(os.path.dirname(video_path), f"{name}_enhanced{ext}")
        
        try:
            # Chemins temporaires pour les étapes intermédiaires
            temp_intro_path = os.path.join(self.temp_dir, "temp_intro.mp4")
            temp_hashtags_path = os.path.join(self.temp_dir, "temp_hashtags.mp4")
            temp_cta_path = os.path.join(self.temp_dir, "temp_cta.mp4")
            
            current_path = video_path
            
            # 1. Ajouter l'introduction si activé
            if full_options.get("add_intro", False):
                intro_text = full_options.get("intro_text", "Regardez jusqu'à la fin! 👀")
                intro_result = self.add_intro_text(current_path, temp_intro_path, intro_text)
                if intro_result:
                    current_path = intro_result
            
            # 2. Ajouter les hashtags si activé
            if full_options.get("add_hashtags", False):
                hashtags = full_options.get("hashtags", ["fyp", "viral", "foryou"])
                hashtag_result = self.add_hashtag_overlay(current_path, temp_hashtags_path, hashtags)
                if hashtag_result:
                    current_path = hashtag_result
            
            # 3. Ajouter l'appel à l'action si activé
            if full_options.get("add_cta", False):
                cta_text = full_options.get("cta_text", "Abonnez-vous! 👆")
                cta_result = self.add_call_to_action(current_path, temp_cta_path, cta_text)
                if cta_result:
                    current_path = cta_result
            
            # 4. Ajouter la musique si activé
            if options.get("add_music", True):
                music_file = options.get("music_file")
                if music_file:
                    music_result = self.add_viral_music(current_path, output_path, music_file)
                    if music_result:
                        current_path = music_result

            # Copier ou renommer le fichier final
            if current_path != output_path:
                import shutil
                shutil.copy2(current_path, output_path)
                print(f"Vidéo finale copiée vers: {output_path}")
            
            # Nettoyer les fichiers temporaires
            for temp_file in [temp_intro_path, temp_hashtags_path, temp_cta_path]:
                if os.path.exists(temp_file) and temp_file != output_path:
                    os.remove(temp_file)
            
            return output_path
            
        except Exception as e:
            print(f"Erreur lors de l'amélioration de la vidéo: {e}")
            import traceback
            traceback.print_exc()
            return video_path  # Retourner la vidéo originale en cas d'erreur