#!/usr/bin/env python3
"""
Script d'authentification pour TikTok et YouTube
Lance les navigateurs pour que tu puisses te connecter et sauvegarder les cookies

Usage: python scripts/setup_auth.py [--tiktok] [--youtube] [--all]
"""

import os
import sys
import time
import logging
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SetupAuth")


def check_display():
    """Vérifie si un display est disponible"""
    display = os.environ.get('DISPLAY')
    if not display:
        print("""
⚠️  Aucun DISPLAY détecté!

Sur un serveur distant, lance d'abord:
    ./scripts/start_vnc.sh start

Puis accède via ton navigateur à:
    http://<IP_TAILSCALE>:6080/vnc.html

Ensuite relance ce script avec:
    DISPLAY=:99 python scripts/setup_auth.py
""")
        return False
    return True


def setup_tiktok():
    """Configure l'authentification TikTok"""
    print("\n" + "="*60)
    print("🎵 CONFIGURATION TIKTOK")
    print("="*60)

    try:
        from src.utils.connectors.tiktok_connector import TikTokConnector

        connector = TikTokConnector(
            cookies_file="tiktok_cookies.pkl",
            headless=False  # On veut voir le navigateur!
        )

        print("""
📋 Instructions:
1. Une fenêtre Chrome va s'ouvrir
2. Connecte-toi à ton compte TikTok CRÉATEUR
3. Une fois connecté, les cookies seront sauvegardés automatiquement
4. Tu pourras ensuite utiliser le mode headless

Appuie sur Entrée pour continuer...""")
        input()

        if connector.authenticate():
            print("\n✅ TikTok authentifié avec succès!")
            print(f"   Cookies sauvegardés dans: tiktok_cookies.pkl")
            return True
        else:
            print("\n❌ Échec de l'authentification TikTok")
            return False

    except Exception as e:
        logger.error(f"Erreur TikTok: {e}")
        return False


def setup_youtube():
    """Configure l'authentification YouTube"""
    print("\n" + "="*60)
    print("📺 CONFIGURATION YOUTUBE")
    print("="*60)

    try:
        from src.publishers.youtube_publisher import YouTubePublisher

        publisher = YouTubePublisher(
            credentials_file="youtube_cookies.pkl",
            headless=False,
            auto_close=False
        )

        print("""
📋 Instructions:
1. Une fenêtre Chrome va s'ouvrir sur YouTube Studio
2. Connecte-toi à ton compte Google/YouTube
3. Assure-toi d'avoir accès à YouTube Studio
4. Une fois connecté, les cookies seront sauvegardés

Appuie sur Entrée pour continuer...""")
        input()

        if publisher.authenticate():
            print("\n✅ YouTube authentifié avec succès!")
            print(f"   Cookies sauvegardés dans: youtube_cookies.pkl")
            return True
        else:
            print("\n❌ Échec de l'authentification YouTube")
            return False

    except Exception as e:
        logger.error(f"Erreur YouTube: {e}")
        return False


def check_existing_auth():
    """Vérifie si des authentifications existent déjà"""
    print("\n📊 Status des authentifications:\n")

    tiktok_cookies = Path("tiktok_cookies.pkl")
    youtube_cookies = Path("youtube_cookies.pkl")

    if tiktok_cookies.exists():
        size = tiktok_cookies.stat().st_size
        mtime = time.ctime(tiktok_cookies.stat().st_mtime)
        print(f"  ✅ TikTok: {tiktok_cookies} ({size} bytes, {mtime})")
    else:
        print(f"  ❌ TikTok: Non configuré")

    if youtube_cookies.exists():
        size = youtube_cookies.stat().st_size
        mtime = time.ctime(youtube_cookies.stat().st_mtime)
        print(f"  ✅ YouTube: {youtube_cookies} ({size} bytes, {mtime})")
    else:
        print(f"  ❌ YouTube: Non configuré")

    return tiktok_cookies.exists(), youtube_cookies.exists()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Configuration authentification")
    parser.add_argument("--tiktok", action="store_true", help="Configurer TikTok")
    parser.add_argument("--youtube", action="store_true", help="Configurer YouTube")
    parser.add_argument("--all", action="store_true", help="Configurer tout")
    parser.add_argument("--status", action="store_true", help="Voir le status")

    args = parser.parse_args()

    print("""
╔════════════════════════════════════════════════════════════╗
║          TikSimPro - Configuration Authentification         ║
╚════════════════════════════════════════════════════════════╝
""")

    # Vérifier le status existant
    tiktok_ok, youtube_ok = check_existing_auth()

    if args.status:
        return

    # Si aucune option, afficher le menu
    if not (args.tiktok or args.youtube or args.all):
        print("""
Options:
  python scripts/setup_auth.py --status   # Voir status
  python scripts/setup_auth.py --tiktok   # Configurer TikTok
  python scripts/setup_auth.py --youtube  # Configurer YouTube
  python scripts/setup_auth.py --all      # Configurer tout
""")
        return

    # Vérifier le display
    if not check_display():
        return

    results = {}

    if args.all or args.tiktok:
        results['tiktok'] = setup_tiktok()

    if args.all or args.youtube:
        results['youtube'] = setup_youtube()

    # Résumé
    print("\n" + "="*60)
    print("📋 RÉSUMÉ")
    print("="*60)

    for platform, success in results.items():
        status = "✅ OK" if success else "❌ ÉCHEC"
        print(f"  {platform.upper()}: {status}")

    if all(results.values()):
        print("""
🎉 Configuration terminée!

Tu peux maintenant:
1. Activer le mode headless dans config.json (optionnel)
2. Lancer le scheduler: python scripts/scheduler.py --daemon
3. Ou tester une publication: python main.py --publish
""")


if __name__ == "__main__":
    main()
