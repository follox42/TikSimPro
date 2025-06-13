# media/media_combiner.py
"""
Combineur de médias pour fusionner vidéo et audio
"""

import os
import logging
from typing import Optional
import subprocess
from pathlib import Path

from src.media_combiners.base_media_combiner import IMediaCombiner

logger = logging.getLogger("TikSimPro")

class FFmpegMediaCombiner(IMediaCombiner):
    """
    Combineur de médias utilisant FFmpeg pour fusionner vidéo et audio
    """
    
    def __init__(self):
        """Initialise le combineur de médias"""
        # Vérifier que FFmpeg est disponible
        self.ffmpeg_path = self._find_ffmpeg()
        if not self.ffmpeg_path:
            logger.warning("FFmpeg non trouvé, certaines fonctionnalités seront limitées")
    
    def _find_ffmpeg(self) -> Optional[str]:
        """
        Recherche l'exécutable FFmpeg sur le système
        
        Returns:
            Chemin de FFmpeg, ou None si non trouvé
        """
        # Liste des emplacements possibles
        ffmpeg_paths = [
            "ffmpeg",
            "ffmpeg.exe",
            "/usr/bin/ffmpeg",
            "/usr/local/bin/ffmpeg",
            "C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe",
            os.path.expanduser("~/ffmpeg/bin/ffmpeg"),
        ]
        
        # Essayer chaque emplacement
        for path in ffmpeg_paths:
            try:
                # Vérifier si le fichier existe
                if os.path.isfile(path):
                    return path
                
                # Sinon, essayer d'exécuter la commande
                result = subprocess.run([path, "-version"], 
                                      capture_output=True, 
                                      text=True,
                                      check=False)
                if result.returncode == 0:
                    return path
            except:
                continue
        
        return None
    
    def combine(self, video_path: str, audio_path: str, output_path: str) -> Optional[str]:
        """
        Combine une vidéo et une piste audio
        
        Args:
            video_path: Chemin de la vidéo
            audio_path: Chemin de la piste audio
            output_path: Chemin du fichier de sortie
            
        Returns:
            Chemin du fichier combiné, ou None en cas d'échec
        """
        # Vérifier que les fichiers existent
        if not os.path.exists(video_path):
            logger.error(f"Fichier vidéo non trouvé: {video_path}")
            return None
        
        if not os.path.exists(audio_path):
            logger.error(f"Fichier audio non trouvé: {audio_path}")
            return None
        
        # Vérifier que FFmpeg est disponible
        if not self.ffmpeg_path:
            logger.error("FFmpeg non disponible, impossible de combiner les médias")
            return None
        
        try:
            # Créer le répertoire de sortie si nécessaire
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # Construire la commande FFmpeg
            cmd = [
                self.ffmpeg_path,
                "-y",  # Écraser le fichier de sortie si existe
                "-i", video_path,  # Fichier vidéo
                "-i", audio_path,  # Fichier audio
                "-c:v", "copy",  # Copier le codec vidéo
                "-c:a", "aac",  # Codec audio AAC
                "-b:a", "192k",  # Bitrate audio
                "-shortest",  # Utiliser la durée la plus courte
                output_path
            ]
            
            # Exécuter la commande
            logger.info(f"Combinaison de {video_path} et {audio_path} en {output_path}")
            result = subprocess.run(cmd, 
                                  capture_output=True, 
                                  text=True,
                                  check=False)
            
            # Vérifier le résultat
            if result.returncode != 0:
                logger.error(f"Erreur FFmpeg: {result.stderr}")
                return None
            
            # Vérifier que le fichier a bien été créé
            if not os.path.exists(output_path):
                logger.error(f"Fichier de sortie non créé: {output_path}")
                return None
            
            logger.info(f"Combinaison réussie: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la combinaison des médias: {e}")
            return None


class MoviePyMediaCombiner(IMediaCombiner):
    """
    Combineur de médias utilisant MoviePy pour fusionner vidéo et audio
    """
    
    def combine(self, video_path: str, audio_path: str, output_path: str) -> Optional[str]:
        """
        Combine une vidéo et une piste audio
        
        Args:
            video_path: Chemin de la vidéo
            audio_path: Chemin de la piste audio
            output_path: Chemin du fichier de sortie
            
        Returns:
            Chemin du fichier combiné, ou None en cas d'échec
        """
        # Vérifier que les fichiers existent
        if not os.path.exists(video_path):
            logger.error(f"Fichier vidéo non trouvé: {video_path}")
            return None
        
        if not os.path.exists(audio_path):
            logger.error(f"Fichier audio non trouvé: {audio_path}")
            return None
        
        try:
            # Importer MoviePy
            from moviepy.editor import VideoFileClip, AudioFileClip
            
            # Créer le répertoire de sortie si nécessaire
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # Charger la vidéo et l'audio
            logger.info(f"Chargement de la vidéo: {video_path}")
            video = VideoFileClip(video_path)
            
            logger.info(f"Chargement de l'audio: {audio_path}")
            audio = AudioFileClip(audio_path)
            
            # Ajuster la durée de l'audio si nécessaire
            if audio.duration > video.duration:
                logger.info(f"Audio ({audio.duration}s) plus long que la vidéo ({video.duration}s), ajustement...")
                audio = audio.subclip(0, video.duration)
            
            # Combiner la vidéo et l'audio
            logger.info("Combinaison des médias...")
            final_clip = video.set_audio(audio)
            
            # Exporter la vidéo finale
            logger.info(f"Exportation de la vidéo: {output_path}")
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                bitrate='5000k',
                threads=4,
                preset='medium'
            )
            
            # Fermer les clips
            video.close()
            audio.close()
            final_clip.close()
            
            logger.info(f"Combinaison réussie: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la combinaison des médias: {e}")
            
            # Tentative avec FFmpeg si MoviePy échoue
            logger.info("Tentative avec FFmpeg...")
            ffmpeg_combiner = FFmpegMediaCombiner()
            return ffmpeg_combiner.combine(video_path, audio_path, output_path)


def create_media_combiner() -> IMediaCombiner:
    """
    Crée une instance du combineur de médias approprié
    
    Returns:
        Instance de IMediaCombiner
    """
    # Essayer d'abord avec FFmpeg
    ffmpeg_combiner = FFmpegMediaCombiner()
    if ffmpeg_combiner.ffmpeg_path:
        logger.info("Utilisation du combineur FFmpeg")
        return ffmpeg_combiner
    
    # Sinon, utiliser MoviePy
    logger.info("Utilisation du combineur MoviePy")
    return MoviePyMediaCombiner()