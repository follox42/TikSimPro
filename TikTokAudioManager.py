import os
import re
import yt_dlp
import librosa
import numpy as np
from youtubesearchpython import VideosSearch
import logging

logger = logging.getLogger("TikTokAudioManager")

class TikTokAudioManager:
    def __init__(self, downloads_dir="downloads"):
        self.downloads_dir = downloads_dir
        os.makedirs(downloads_dir, exist_ok=True)

    def sanitize_filename(self, title):
        """Nettoie un titre pour créer un nom de fichier valide"""
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
        safe_title = safe_title.strip().replace(' ', '_')[:100]
        return safe_title

    def search_and_download_song(self, query):
        """Recherche et télécharge la chanson en mp3"""
        logger.info(f"Recherche sur YouTube : {query}")

        # Recherche la vidéo
        search = VideosSearch(query, limit=1)
        results = search.result()

        if not results['result']:
            raise Exception(f"Aucun résultat trouvé pour {query}")

        video_url = results['result'][0]['link']
        video_title = results['result'][0]['title']
        logger.info(f"Vidéo trouvée : {video_title} ({video_url})")

        # Nettoyage du nom de fichier
        safe_title = self.sanitize_filename(video_title)
        output_template = os.path.join(self.downloads_dir, f"{safe_title}.%(ext)s")
        output_file = os.path.join(self.downloads_dir, f"{safe_title}.mp3")

        # Options yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': False,
            'ffmpeg_location': r'C:\Program Files\ffmpeg\bin' 
        }

        # Télécharger la musique
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        # Vérification que le fichier existe bien
        if not os.path.exists(output_file):
            raise FileNotFoundError(f"Le fichier audio n'a pas été trouvé : {output_file}")

        logger.info(f"Musique téléchargée : {output_file}")
        return output_file

    def extract_melody(self, audio_file):
        """Extrait la mélodie d'un fichier audio en notes"""
        logger.info(f"Extraction de la mélodie : {audio_file}")

        # Charger l'audio
        y, sr = librosa.load(audio_file, sr=None)

        # Détection des hauteurs de fréquence
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)

        melody_notes = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                melody_notes.append(pitch)

        logger.info(f"Nombre de notes extraites : {len(melody_notes)}")
        return melody_notes
