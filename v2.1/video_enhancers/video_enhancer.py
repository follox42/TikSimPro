# video_enhancers/video_enhancer.py
"""
Améliorateur de vidéo pour TikSimPro
Ajoute des effets, textes, et transitions pour rendre la vidéo plus attrayante
"""

import os
import time
import logging
import tempfile
import random
import textwrap
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path

from core.interfaces import IVideoEnhancer

logger = logging.getLogger("TikSimPro")

class VideoEnhancer(IVideoEnhancer):
    """
    Améliorateur qui ajoute des effets, textes et transitions aux vidéos
    """
    
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
    
    def __init__(self, add_intro = True, add_hashtags = True, add_cta = True, add_music = True, temp_dir: Optional[str] = None):
        """
        Initialise l'améliorateur de vidéos
        
        Args:
            temp_dir: Dossier temporaire (optionnel)
        """
        if temp_dir:
            self.temp_dir = temp_dir
        else:
            self.temp_dir = tempfile.mkdtemp()
            
        # Params
        self.add_intro = add_intro
        self.add_hashtags = add_hashtags
        self.add_cta = add_cta
        self.add_music = add_music

        # Créer le dossier temporaire s'il n'existe pas
        os.makedirs(self.temp_dir, exist_ok=True)
        
        logger.info(f"VideoEnhancer initialisé: {self.temp_dir}")
        
        # Vérifier si les dépendances sont disponibles
        self._check_dependencies()
    
    def _check_dependencies(self) -> None:
        """Vérifie si les dépendances sont disponibles"""
        try:
            import cv2
            import moviepy.editor
            from PIL import Image, ImageDraw, ImageFont
            logger.info("Dépendances disponibles: OpenCV, MoviePy, PIL")
        except ImportError as e:
            logger.warning(f"Dépendance manquante: {e}")
            logger.warning("Certaines fonctionnalités peuvent être limitées.")
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """
        Convertit une couleur hexadécimale en RGB
        
        Args:
            hex_color: Couleur au format hexadécimal (#RRGGBB)
            
        Returns:
            Tuple RGB (r, g, b)
        """
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _is_font_available(self, font_name: str) -> bool:
        """
        Vérifie si une police est disponible sur le système
        
        Args:
            font_name: Nom de la police
            
        Returns:
            True si la police est disponible, False sinon
        """
        try:
            from PIL import ImageFont
            # Tester avec une petite taille pour vérifier rapidement
            ImageFont.truetype(font_name, 12)
            return True
        except (IOError, OSError):
            return False
    
    def _get_available_fonts(self) -> List[str]:
        """
        Récupère les polices disponibles sur le système
        
        Returns:
            Liste des polices disponibles
        """
        available_fonts = []
        
        for font_name in self.DEFAULT_FONTS:
            if self._is_font_available(font_name):
                available_fonts.append(font_name)
        
        if not available_fonts:
            logger.warning("Aucune police disponible, utilisation de Arial par défaut")
            available_fonts = ["Arial"]
        
        return available_fonts
    
    def enhance(self, video_path: str, output_path: str, options: Dict[str, Any]) -> Optional[str]:
        """
        Améliore une vidéo avec des effets visuels et textuels
        
        Args:
            video_path: Chemin de la vidéo à améliorer
            output_path: Chemin du fichier de sortie
            options: Options d'amélioration
            
        Returns:
            Chemin de la vidéo améliorée, ou None en cas d'échec
        """
        if not os.path.exists(video_path):
            logger.error(f"Fichier vidéo non trouvé: {video_path}")
            return None
        
        try:
            # Créer le répertoire de sortie si nécessaire
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # Lire les options
            add_intro = options.get("add_intro", False)
            add_hashtags = options.get("add_hashtags", False)
            add_cta = options.get("add_cta", False)
            add_music = options.get("add_music", False)
            
            intro_text = options.get("intro_text", "Watch this to the end! 👀")
            hashtags = options.get("hashtags", ["fyp", "viral", "foryou"])
            cta_text = options.get("cta_text", "Follow for more! 👆")
            music_file = options.get("music_file", None)
            
            # Chemins des fichiers temporaires
            temp_intro_path = os.path.join(self.temp_dir, "temp_intro.mp4")
            temp_hashtags_path = os.path.join(self.temp_dir, "temp_hashtags.mp4")
            temp_cta_path = os.path.join(self.temp_dir, "temp_cta.mp4")
            
            # Chemin actuel de la vidéo (sera mis à jour à chaque étape)
            current_path = video_path
            
            # Appliquer les améliorations en séquence
            logger.info("Application des améliorations...")
            
            # 1. Ajouter l'introduction si activé
            if add_intro and self.add_intro:
                intro_result = self._add_intro_text(current_path, temp_intro_path, intro_text)
                if intro_result:
                    current_path = intro_result
                    logger.info(f"Introduction ajoutée: {intro_text}")
            
            # 2. Ajouter les hashtags si activé
            if add_hashtags and self.add_hashtags:
                hashtag_result = self._add_hashtag_overlay(current_path, temp_hashtags_path, hashtags)
                if hashtag_result:
                    current_path = hashtag_result
                    logger.info(f"Hashtags ajoutés: {hashtags}")
            
            # 3. Ajouter l'appel à l'action si activé
            if add_cta and self.add_cta:
                cta_result = self._add_call_to_action(current_path, temp_cta_path, cta_text)
                if cta_result:
                    current_path = cta_result
                    logger.info(f"Appel à l'action ajouté: {cta_text}")
            
            # 4. Ajouter la musique si activé
            if add_music and music_file and os.path.exists(music_file) and self.add_music:
                music_result = self._add_music(current_path, output_path, music_file)
                if music_result:
                    current_path = music_result
                    logger.info(f"Musique ajoutée: {music_file}")
            
            # Si le chemin actuel n'est pas le chemin de sortie, copier le fichier
            if current_path != output_path:
                import shutil
                shutil.copy2(current_path, output_path)
                logger.info(f"Vidéo finale copiée vers: {output_path}")
            
            # Nettoyer les fichiers temporaires
            for temp_file in [temp_intro_path, temp_hashtags_path, temp_cta_path]:
                if os.path.exists(temp_file) and temp_file != output_path:
                    os.remove(temp_file)
            
            logger.info(f"Amélioration terminée: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erreur lors de l'amélioration de la vidéo: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _add_intro_text(self, video_path: str, output_path: str, 
                        text: str = "Watch this to the end! 👀", 
                        duration: float = 3.0) -> Optional[str]:
        """
        Ajoute un texte d'introduction au début de la vidéo
        
        Args:
            video_path: Chemin de la vidéo d'origine
            output_path: Chemin de sortie
            text: Texte d'introduction
            duration: Durée de l'introduction en secondes
            
        Returns:
            Chemin de la vidéo modifiée, ou None en cas d'échec
        """
        try:
            # Importer MoviePy
            from moviepy.editor import VideoFileClip, TextClip, ColorClip, CompositeVideoClip, concatenate_videoclips
            from PIL import ImageFont
            
            # Charger la vidéo
            video = VideoFileClip(video_path)
            
            # Sélectionner une police aléatoire parmi celles disponibles
            available_fonts = self._get_available_fonts()
            font = random.choice(available_fonts)
            
            # Sélectionner une couleur aléatoire
            color = random.choice(self.TIKTOK_COLORS)
            color_rgb = self._hex_to_rgb(color)
            
            # Créer le texte d'intro
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
            
            return output_path
            
        except Exception as e:
            logger.exception(f"Erreur lors de l'ajout de l'introduction: {e}")
            return None
    
    def _add_hashtag_overlay(self, video_path: str, output_path: str, 
                           hashtags: Optional[List[str]] = None) -> Optional[str]:
        """
        Ajoute des hashtags en superposition sur la vidéo
        
        Args:
            video_path: Chemin de la vidéo d'origine
            output_path: Chemin de sortie
            hashtags: Liste de hashtags (sans le #)
            
        Returns:
            Chemin de la vidéo modifiée, ou None en cas d'échec
        """
        if not hashtags:
            hashtags = ["fyp", "viral", "foryou", "tiktok"]
        
        try:
            # Importer MoviePy
            from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
            
            # Charger la vidéo
            video = VideoFileClip(video_path)
            
            # Créer une chaîne de hashtags
            hashtag_text = " ".join([f"#{tag}" for tag in hashtags])
            
            # Limiter la longueur
            if len(hashtag_text) > 50:
                hashtag_text = hashtag_text[:47] + "..."
            
            # Sélectionner une police aléatoire parmi celles disponibles
            available_fonts = self._get_available_fonts()
            font = random.choice(available_fonts)
            
            # Sélectionner une couleur aléatoire
            color = random.choice(self.TIKTOK_COLORS)
            
            # Créer le clip de texte des hashtags
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
            
            return output_path
            
        except Exception as e:
            logger.exception(f"Erreur lors de l'ajout des hashtags: {e}")
            return None
    
    def _add_call_to_action(self, video_path: str, output_path: str, 
                           text: str = "Follow for more! 👆", 
                           start_time: Optional[float] = None) -> Optional[str]:
        """
        Ajoute un appel à l'action à la fin de la vidéo
        
        Args:
            video_path: Chemin de la vidéo d'origine
            output_path: Chemin de sortie
            text: Texte d'appel à l'action
            start_time: Moment d'apparition (en secondes depuis la fin)
            
        Returns:
            Chemin de la vidéo modifiée, ou None en cas d'échec
        """
        try:
            # Importer MoviePy
            from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
            
            # Charger la vidéo
            video = VideoFileClip(video_path)
            
            # Définir le moment d'apparition si non spécifié
            if start_time is None:
                # Par défaut, 5 secondes avant la fin
                start_time = max(0, video.duration - 5)
            
            # Sélectionner une police aléatoire parmi celles disponibles
            available_fonts = self._get_available_fonts()
            font = random.choice(available_fonts)
            
            # Sélectionner une couleur aléatoire
            color = random.choice(self.TIKTOK_COLORS)
            color_rgb = self._hex_to_rgb(color)
            
            # Créer le clip de texte
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
            
            return output_path
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de l'appel à l'action: {e}")
            return None
    
    def _add_music(self, video_path: str, output_path: str, 
                 music_file: str) -> Optional[str]:
        """
        Ajoute une musique à la vidéo
        
        Args:
            video_path: Chemin de la vidéo d'origine
            output_path: Chemin de sortie
            music_file: Chemin du fichier audio
            
        Returns:
            Chemin de la vidéo modifiée, ou None en cas d'échec
        """
        if not os.path.exists(music_file):
            logger.error(f"Fichier audio non trouvé: {music_file}")
            return None
        
        try:
            # Importer MoviePy
            from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips
            
            # Charger la vidéo
            video = VideoFileClip(video_path)
            
            # Charger la musique
            music = AudioFileClip(music_file)
            
            # Boucler la musique si nécessaire
            if music.duration < video.duration:
                repeats = int(video.duration / music.duration) + 1
                music_looped = concatenate_audioclips([music] * repeats)
            else:
                music_looped = music
            
            # Découper proprement après la boucle
            music_final = music_looped.subclip(0, video.duration)
            
            # Ajouter à la vidéo
            final = video.set_audio(music_final)
            
            # Écrire la vidéo
            final.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac'
            )
            
            # Fermer les clips
            video.close()
            final.close()
            
            return output_path
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de la musique: {e}")
            return None