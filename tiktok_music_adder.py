"""
Module pour ajouter de vraies musiques populaires à vos vidéos TikTok
"""

import os
import moviepy as mpy
import requests
import random
from pytube import YouTube
import re

class MusicAdder:
    """Ajoute de vraies musiques populaires aux vidéos TikTok"""
    
    # Liste de musiques populaires sur TikTok avec leurs liens YouTube
    POPULAR_SONGS = [
        {
            "title": "Lovely Day - Bill Withers",
            "url": "https://www.youtube.com/watch?v=bEeaS6fuUoA",
            "duration": 254
        },
        {
            "title": "Runaway - AURORA",
            "url": "https://www.youtube.com/watch?v=d_HlPboLRL8",
            "duration": 249
        },
        {
            "title": "Blinding Lights - The Weeknd",
            "url": "https://www.youtube.com/watch?v=fHI8X4OXluQ",
            "duration": 203
        },
        {
            "title": "STAY - The Kid LAROI & Justin Bieber",
            "url": "https://www.youtube.com/watch?v=kTJczUoc26U",
            "duration": 141
        },
        {
            "title": "Heat Waves - Glass Animals",
            "url": "https://www.youtube.com/watch?v=mRD0-GxqHVo",
            "duration": 235
        },
        {
            "title": "Yonaguni - Bad Bunny",
            "url": "https://www.youtube.com/watch?v=doLMt10ytHY",
            "duration": 205
        },
        {
            "title": "Levitating - Dua Lipa",
            "url": "https://www.youtube.com/watch?v=TUVcZfQe-Kw",
            "duration": 231
        },
        {
            "title": "Lo Vas A Olvidar - Billie Eilish & ROSALÍA",
            "url": "https://www.youtube.com/watch?v=8eGQ-xcbwXs",
            "duration": 218
        },
        {
            "title": "Running Up That Hill - Kate Bush",
            "url": "https://www.youtube.com/watch?v=wp43OdtAAkM",
            "duration": 300
        },
        {
            "title": "Calm Down - Rema & Selena Gomez",
            "url": "https://www.youtube.com/watch?v=WcIcVapfqXw",
            "duration": 239
        }
    ]
    
    def __init__(self):
        """Initialise le module d'ajout de musique"""
        self.music_dir = "music"
        if not os.path.exists(self.music_dir):
            os.makedirs(self.music_dir)
        
        print(f"Dossier de musique: {self.music_dir}")
    
    def download_music(self, song_info, output_path=None):
        """
        Télécharge une musique depuis YouTube
        
        Args:
            song_info: Dictionnaire contenant les infos de la chanson
            output_path: Chemin de sortie (optionnel)
            
        Returns:
            Le chemin du fichier téléchargé
        """
        title = song_info["title"]
        url = song_info["url"]
        
        # Nettoyer le titre pour en faire un nom de fichier valide
        clean_title = re.sub(r'[^\w\s-]', '', title)
        clean_title = re.sub(r'[\s-]+', '_', clean_title)
        
        if not output_path:
            output_path = os.path.join(self.music_dir, f"{clean_title}.mp3")
        
        # Vérifier si le fichier existe déjà
        if os.path.exists(output_path):
            print(f"La musique '{title}' existe déjà: {output_path}")
            return output_path
        
        print(f"Téléchargement de la musique '{title}' depuis YouTube...")
        
        try:
            # Télécharger la vidéo depuis YouTube
            yt = YouTube(url)
            
            # Obtenir uniquement l'audio
            audio_stream = yt.streams.filter(only_audio=True).first()
            
            if not audio_stream:
                raise Exception("Aucun flux audio trouvé")
            
            # Télécharger dans un fichier temporaire
            temp_file = audio_stream.download(
                output_path=self.music_dir,
                filename=f"temp_{clean_title}"
            )
            
            # Convertir en MP3 avec moviepy
            audio_clip = mpy.AudioFileClip(temp_file)
            audio_clip.write_audiofile(output_path, logger=None)
            
            # Supprimer le fichier temporaire
            os.remove(temp_file)
            
            print(f"Musique téléchargée: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Erreur lors du téléchargement de la musique '{title}': {e}")
            return None
    
    def get_random_music(self):
        """
        Obtient une musique populaire aléatoire
        
        Returns:
            Dictionnaire contenant les infos et le chemin de la musique
        """
        song_info = random.choice(self.POPULAR_SONGS)
        
        # Nettoyer le titre pour en faire un nom de fichier valide
        title = song_info["title"]
        clean_title = re.sub(r'[^\w\s-]', '', title)
        clean_title = re.sub(r'[\s-]+', '_', clean_title)
        
        file_path = os.path.join(self.music_dir, f"{clean_title}.mp3")
        
        # Télécharger si nécessaire
        if not os.path.exists(file_path):
            file_path = self.download_music(song_info)
        
        if file_path:
            return {
                "info": song_info,
                "path": file_path
            }
        else:
            # Réessayer avec une autre chanson
            return self.get_random_music()
    
    def add_music_to_video(self, video_path, output_path=None, song_info=None):
        """
        Ajoute une musique à une vidéo
        
        Args:
            video_path: Chemin de la vidéo d'origine
            output_path: Chemin de sortie (optionnel)
            song_info: Info de la chanson à utiliser (optionnel)
            
        Returns:
            Le chemin de la vidéo avec musique
        """
        if not output_path:
            # Créer un nom pour la vidéo avec musique
            basename = os.path.basename(video_path)
            name, ext = os.path.splitext(basename)
            output_path = os.path.join(os.path.dirname(video_path), f"{name}_music{ext}")
        
        # Obtenir une musique si non spécifiée
        if not song_info:
            song = self.get_random_music()
            if not song:
                print("Impossible d'obtenir une musique")
                return None
            music_path = song["path"]
            song_title = song["info"]["title"]
        else:
            music_path = self.download_music(song_info)
            if not music_path:
                print(f"Impossible de télécharger la musique: {song_info['title']}")
                return None
            song_title = song_info["title"]
        
        try:
            print(f"Ajout de la musique '{song_title}' à la vidéo...")
            
            # Charger la vidéo
            video = mpy.VideoFileClip(video_path)
            
            # Charger la musique
            music = mpy.AudioFileClip(music_path)
            
            # Ajuster la longueur de la musique à celle de la vidéo
            if music.duration > video.duration:
                music = music.subclip(0, video.duration)
            else:
                # Répéter la musique si nécessaire
                repeats = int(video.duration / music.duration) + 1
                music = mpy.concatenate_audioclips([music] * repeats)
                music = music.subclip(0, video.duration)
            
            # Régler le volume de la musique
            music = music.volumex(0.7)  # 70% du volume original
            
            # Ajouter la musique à la vidéo
            video = video.set_audio(music)
            
            # Écrire la vidéo finale
            print(f"Écriture de la vidéo avec musique: {output_path}")
            video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )
            
            # Fermer les clips
            video.close()
            music.close()
            
            print(f"Vidéo avec musique créée: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Erreur lors de l'ajout de musique à la vidéo: {e}")
            return None
    
    def list_available_songs(self):
        """
        Affiche la liste des musiques populaires disponibles
        
        Returns:
            La liste des informations des chansons
        """
        print("\nMusiques populaires disponibles:")
        print("-" * 50)
        
        for i, song in enumerate(self.POPULAR_SONGS):
            duration_min = song["duration"] // 60
            duration_sec = song["duration"] % 60
            print(f"{i+1}. {song['title']} ({duration_min}:{duration_sec:02d})")
        
        print("-" * 50)
        return self.POPULAR_SONGS
    
    def choose_song(self):
        """
        Permet à l'utilisateur de choisir une musique
        
        Returns:
            Les informations de la chanson choisie
        """
        songs = self.list_available_songs()
        
        while True:
            try:
                choice = input("\nChoisissez une musique (1-10) ou 'r' pour aléatoire: ")
                
                if choice.lower() == 'r':
                    return random.choice(songs)
                
                index = int(choice) - 1
                if 0 <= index < len(songs):
                    return songs[index]
                else:
                    print(f"Veuillez entrer un nombre entre 1 et {len(songs)}")
            except ValueError:
                print("Veuillez entrer un nombre valide")


# Exemple d'utilisation
if __name__ == "__main__":
    # Exemple d'utilisation simple
    music_adder = MusicAdder()
    
    # Montrer les musiques disponibles
    music_adder.list_available_songs()
    
    # Demander à l'utilisateur de choisir une vidéo
    video_path = input("Entrez le chemin de la vidéo à modifier: ")
    
    if os.path.exists(video_path):
        # Permettre à l'utilisateur de choisir une musique
        song_info = music_adder.choose_song()
        
        # Ajouter la musique à la vidéo
        output_path = music_adder.add_music_to_video(video_path, song_info=song_info)
        
        if output_path:
            print(f"\nVidéo créée avec succès: {output_path}")
    else:
        print(f"Le fichier {video_path} n'existe pas")