import os
import yt_dlp
from youtubesearchpython import VideosSearch

class TikTokYouTubeDownloader:
    def __init__(self, temp_dir="audio_temp"):
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)

    def search_youtube(self, query, limit=1):
        search = VideosSearch(query, limit=limit)
        results = search.result()['result']
        if results:
            video_url = results[0]['link']
            print(f"Found: {results[0]['title']} - {video_url}")
            return video_url
        else:
            print("No video found.")
            return None

    def download_audio(self, url, filename="music.mp3"):
        output_path = os.path.join(self.temp_dir, filename)

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return output_path

    def get_tiktok_song_mp3(self, song_title):
        video_url = self.search_youtube(song_title + " official audio")
        if video_url:
            return self.download_audio(video_url, filename=song_title.replace(" ", "_") + ".mp3")
        else:
            return None
