#!/usr/bin/env python3
"""
Script pour scraper et télécharger des sons depuis MyInstants.com
Scrape dynamiquement les pages pour obtenir les derniers sons

Usage:
  python scripts/download_viral_sounds.py                    # Liste les sons scrapés (sans télécharger)
  python scripts/download_viral_sounds.py --download         # Télécharge les sons manquants
  python scripts/download_viral_sounds.py --pages 5          # Scrape 5 pages (défaut: 3)
  python scripts/download_viral_sounds.py --category fr      # Catégorie: fr, trending, recent, top
  python scripts/download_viral_sounds.py --local            # Liste seulement les sons déjà téléchargés
"""

import requests
from bs4 import BeautifulSoup
from pathlib import Path
import subprocess
import time
import wave
import argparse
import json
import re

BASE_DIR = Path(__file__).parent.parent
SOUNDS_DIR = BASE_DIR / "sounds" / "viral"

def get_cache_file(category: str) -> Path:
    """Cache séparé par catégorie"""
    return SOUNDS_DIR / f".sounds_cache_{category}.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# URLs de base MyInstants
MYINSTANTS_URLS = {
    "trending": "https://www.myinstants.com/en/trending/",
    "recent": "https://www.myinstants.com/en/recent/",
    "top": "https://www.myinstants.com/en/top/",
    "fr": "https://www.myinstants.com/en/index/fr/",
    "us": "https://www.myinstants.com/en/index/us/",
    "br": "https://www.myinstants.com/en/index/br/",
    "es": "https://www.myinstants.com/en/index/es/",
    "de": "https://www.myinstants.com/en/index/de/",
    "funny": "https://www.myinstants.com/en/search/?name=funny",
    "meme": "https://www.myinstants.com/en/search/?name=meme",
    "animal": "https://www.myinstants.com/en/search/?name=animal",
    "bass": "https://www.myinstants.com/en/search/?name=bass",
}


def get_wav_duration(file_path: str) -> float:
    """Retourne la durée d'un fichier WAV en secondes"""
    try:
        with wave.open(file_path, 'rb') as wav:
            return wav.getnframes() / float(wav.getframerate())
    except:
        return 0.0


def slugify(name: str) -> str:
    """Convertit un nom en slug pour fichier"""
    name = name.lower().strip()
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '_', name)
    return name[:50]  # Limite à 50 caractères


def scrape_page(url: str) -> list:
    """Scrape une page MyInstants et retourne les sons trouvés"""
    sounds = []
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            return sounds

        html = response.text

        # Méthode 1: Extraire via regex sur onclick="play('/media/sounds/...', ..., 'nom-id')"
        # Format: play('/media/sounds/xxx.mp3', 'loader-xxx', 'nom-id')
        pattern = r"onclick=\"play\('(/media/sounds/[^']+\.mp3)', '[^']+', '([^']+)'\)\""
        matches = re.findall(pattern, html)

        seen = set()
        for sound_path, sound_id in matches:
            # Extrait le nom du sound_id (enlève le suffixe -1234)
            name = re.sub(r'-\d+$', '', sound_id)
            if name in seen:
                continue
            seen.add(name)

            sound_url = "https://www.myinstants.com" + sound_path
            title = name.replace('-', ' ').title()

            sounds.append({
                'name': slugify(name),
                'title': title,
                'url': sound_url
            })

        # Méthode 2 (fallback): Chercher tous les /media/sounds/*.mp3 uniques
        if not sounds:
            mp3_pattern = r'/media/sounds/([^"\']+)\.mp3'
            mp3_matches = re.findall(mp3_pattern, html)
            seen_urls = set()
            for mp3_name in mp3_matches:
                if mp3_name in seen_urls:
                    continue
                seen_urls.add(mp3_name)

                sound_url = f"https://www.myinstants.com/media/sounds/{mp3_name}.mp3"
                sounds.append({
                    'name': slugify(mp3_name),
                    'title': mp3_name.replace('-', ' ').replace('_', ' ').title(),
                    'url': sound_url
                })

    except Exception as e:
        print(f"  [ERR] Scrape failed: {e}")

    return sounds


def scrape_myinstants(category: str = "trending", pages: int = 3) -> list:
    """Scrape plusieurs pages de MyInstants"""
    all_sounds = []
    seen_names = set()

    base_url = MYINSTANTS_URLS.get(category, MYINSTANTS_URLS["trending"])

    print(f"\n  Scraping MyInstants ({category})...")

    for page in range(1, pages + 1):
        if "search" in base_url:
            url = f"{base_url}&page={page}"
        else:
            url = f"{base_url}?page={page}"

        print(f"  Page {page}/{pages}...", end=" ", flush=True)
        sounds = scrape_page(url)

        new_count = 0
        for s in sounds:
            if s['name'] not in seen_names:
                seen_names.add(s['name'])
                all_sounds.append(s)
                new_count += 1

        print(f"{new_count} nouveaux sons")
        time.sleep(0.5)

    return all_sounds


def load_cache(category: str) -> dict:
    """Charge le cache des sons pour une catégorie"""
    cache_file = get_cache_file(category)
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"sounds": [], "last_update": "", "category": category}


def save_cache(category: str, sounds: list):
    """Sauvegarde le cache pour une catégorie"""
    SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
    cache = {
        "sounds": sounds,
        "category": category,
        "last_update": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(get_cache_file(category), 'w') as f:
        json.dump(cache, f, indent=2)


def get_local_sounds() -> list:
    """Liste les sons déjà téléchargés"""
    sounds = []
    if not SOUNDS_DIR.exists():
        return sounds

    for wav in SOUNDS_DIR.glob("*.wav"):
        duration = get_wav_duration(str(wav))
        size_kb = wav.stat().st_size / 1024
        sounds.append({
            'name': wav.stem,
            'path': str(wav),
            'duration': duration,
            'size_kb': size_kb
        })

    return sorted(sounds, key=lambda x: x['name'])


def download_sound(name: str, url: str) -> bool:
    """Télécharge et convertit un son"""
    SOUNDS_DIR.mkdir(parents=True, exist_ok=True)

    mp3_path = SOUNDS_DIR / f"{name}.mp3"
    wav_path = SOUNDS_DIR / f"{name}.wav"

    if wav_path.exists():
        return True  # Déjà là

    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            return False

        with open(mp3_path, 'wb') as f:
            f.write(response.content)

        # Convertit en WAV
        try:
            subprocess.run([
                'ffmpeg', '-y', '-i', str(mp3_path),
                '-ar', '44100', '-ac', '2', '-acodec', 'pcm_s16le',
                str(wav_path)
            ], capture_output=True, check=True)
            mp3_path.unlink()
            return True
        except:
            # Garde le MP3 si conversion échoue
            return True

    except Exception as e:
        return False


def main():
    parser = argparse.ArgumentParser(description="Scraper MyInstants - Sons viraux")
    parser.add_argument("--download", "-d", action="store_true", help="Télécharge les sons manquants")
    parser.add_argument("--pages", "-p", type=int, default=3, help="Nombre de pages à scraper (défaut: 3)")
    parser.add_argument("--category", "-c", default="trending",
                       choices=list(MYINSTANTS_URLS.keys()),
                       help="Catégorie: trending, recent, top, fr, us, br, es, de, funny, meme, animal, bass")
    parser.add_argument("--local", "-l", action="store_true", help="Liste seulement les sons locaux")
    parser.add_argument("--refresh", "-r", action="store_true", help="Force le re-scrape (ignore cache)")
    args = parser.parse_args()

    print("=" * 65)
    print("  MYINSTANTS SCRAPER - Sons Viraux")
    print("=" * 65)

    # Sons locaux
    local_sounds = get_local_sounds()
    local_names = {s['name'] for s in local_sounds}

    if args.local:
        print(f"\n  SONS TÉLÉCHARGÉS ({len(local_sounds)}):")
        print("-" * 65)
        for s in local_sounds:
            print(f"  {s['name']:40} {s['duration']:5.1f}s  {s['size_kb']:7.1f}KB")
        print("=" * 65)
        return

    # Scrape ou charge cache (par catégorie)
    cache = load_cache(args.category)
    if args.refresh or not cache["sounds"]:
        print(f"\n  Catégorie: {args.category}")
        scraped = scrape_myinstants(args.category, args.pages)
        # Fusionne avec le cache existant
        existing_names = {s['name'] for s in cache["sounds"]}
        for s in scraped:
            if s['name'] not in existing_names:
                cache["sounds"].append(s)
        save_cache(args.category, cache["sounds"])
        print(f"  Cache [{args.category}] mis à jour: {len(cache['sounds'])} sons")

    all_sounds = cache["sounds"]

    # Sépare téléchargés / à télécharger
    downloaded = []
    to_download = []
    for s in all_sounds:
        if s['name'] in local_names:
            downloaded.append(s)
        else:
            to_download.append(s)

    # Affichage
    print(f"\n  RÉSUMÉ:")
    print(f"    - Sons dans le cache: {len(all_sounds)}")
    print(f"    - Déjà téléchargés:   {len(downloaded)}")
    print(f"    - À télécharger:      {len(to_download)}")

    if to_download:
        print(f"\n  SONS DISPONIBLES (non téléchargés):")
        print("-" * 65)
        for i, s in enumerate(to_download[:50], 1):  # Limite affichage à 50
            print(f"  {i:3}. {s['name']:45} {s['title'][:30]}")
        if len(to_download) > 50:
            print(f"  ... et {len(to_download) - 50} autres")

    if args.download and to_download:
        print(f"\n  TÉLÉCHARGEMENT ({len(to_download)} sons)...")
        print("-" * 65)
        success = 0
        failed = 0
        for s in to_download:
            print(f"  [DL] {s['name'][:40]}...", end=" ", flush=True)
            if download_sound(s['name'], s['url']):
                wav = SOUNDS_DIR / f"{s['name']}.wav"
                if wav.exists():
                    dur = get_wav_duration(str(wav))
                    print(f"OK ({dur:.1f}s)")
                else:
                    print("OK (MP3)")
                success += 1
            else:
                print("ERREUR")
                failed += 1
            time.sleep(0.3)

        print(f"\n  TERMINÉ: {success} OK, {failed} échecs")

    # Affiche sons locaux avec durées
    local_sounds = get_local_sounds()  # Refresh
    if local_sounds:
        print(f"\n  SONS LOCAUX ({len(local_sounds)}):")
        print("-" * 65)
        for s in local_sounds:
            print(f"  {s['name']:40} {s['duration']:5.1f}s  {s['size_kb']:7.1f}KB")

    print("=" * 65)


if __name__ == "__main__":
    main()
