#!/usr/bin/env python3
"""
TikSimPro Scheduler - Publication automatique 2x par jour
Usage: python scripts/scheduler.py [--test] [--times "09:00,18:00"]
"""

import os
import sys
import time
import logging
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scheduler.log', encoding='utf-8')
    ]
)
logger = logging.getLogger("Scheduler")

class TikSimProScheduler:
    """Planificateur pour TikSimPro"""

    def __init__(self, publish_times: list = None, platforms: list = None):
        """
        Args:
            publish_times: Liste des heures de publication ["09:00", "18:00"]
            platforms: Liste des plateformes ["tiktok", "youtube"]
        """
        self.publish_times = publish_times or ["09:00", "14:00", "19:00"]
        self.platforms = platforms or ["tiktok", "youtube"]
        self.project_dir = Path(__file__).parent.parent
        self.last_run = {}

        logger.info(f"Scheduler initialisé")
        logger.info(f"Heures de publication: {self.publish_times}")
        logger.info(f"Plateformes: {self.platforms}")

    def should_run(self, scheduled_time: str) -> bool:
        """Vérifie si on doit lancer une publication"""
        now = datetime.now()
        today_key = f"{now.strftime('%Y-%m-%d')}_{scheduled_time}"

        # Déjà exécuté aujourd'hui à cette heure?
        if today_key in self.last_run:
            return False

        # Est-ce l'heure?
        hour, minute = map(int, scheduled_time.split(':'))
        scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # Fenêtre de 5 minutes après l'heure prévue
        if scheduled <= now <= scheduled + timedelta(minutes=5):
            return True

        return False

    def cleanup_chrome_profiles(self):
        """Nettoie les profils Chrome avant de lancer le pipeline"""
        try:
            cleanup_script = self.project_dir / "scripts" / "cleanup_chrome.py"
            if cleanup_script.exists():
                logger.info("🧹 Nettoyage des profils Chrome...")
                subprocess.run([sys.executable, str(cleanup_script)], timeout=10)
        except Exception as e:
            logger.warning(f"Impossible de nettoyer les profils Chrome: {e}")

    def run_pipeline(self) -> bool:
        """Lance le pipeline TikSimPro"""
        logger.info("🚀 Lancement du pipeline TikSimPro...")
        
        # Nettoyer les profils Chrome avant de commencer
        self.cleanup_chrome_profiles()

        try:
            # S'assurer qu'on a un DISPLAY
            display = os.environ.get('DISPLAY', ':99')
            env = os.environ.copy()
            env['DISPLAY'] = display

            # Lancer main.py avec logs en temps réel
            process = subprocess.Popen(
                [sys.executable, 'main.py', '--publish'],
                cwd=str(self.project_dir),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Afficher les logs en temps réel
            output_lines = []
            for line in process.stdout:
                line = line.rstrip()
                if line:
                    logger.info(f"  {line}")
                    output_lines.append(line)

            process.wait(timeout=1800)

            if process.returncode == 0:
                logger.info("✅ Pipeline terminé avec succès")
                return True
            else:
                logger.error(f"❌ Pipeline échoué (code: {process.returncode})")
                return False

        except subprocess.TimeoutExpired:
            logger.error("❌ Pipeline timeout (30 minutes)")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur pipeline: {e}")
            return False

    def mark_as_run(self, scheduled_time: str):
        """Marque une heure comme exécutée"""
        today_key = f"{datetime.now().strftime('%Y-%m-%d')}_{scheduled_time}"
        self.last_run[today_key] = datetime.now()

        # Nettoyer les anciennes entrées (plus de 2 jours)
        cutoff = datetime.now() - timedelta(days=2)
        self.last_run = {
            k: v for k, v in self.last_run.items()
            if v > cutoff
        }

    def run_once(self) -> bool:
        """Lance une seule fois immédiatement"""
        logger.info("🎬 Lancement manuel unique...")
        return self.run_pipeline()

    def run_forever(self):
        """Boucle principale du scheduler"""
        logger.info("=" * 60)
        logger.info("🕐 TikSimPro Scheduler démarré")
        logger.info(f"   Publications prévues: {self.publish_times}")
        logger.info("   Ctrl+C pour arrêter")
        logger.info("=" * 60)

        while True:
            try:
                for scheduled_time in self.publish_times:
                    if self.should_run(scheduled_time):
                        logger.info(f"⏰ Heure de publication: {scheduled_time}")

                        if self.run_pipeline():
                            self.mark_as_run(scheduled_time)
                            logger.info(f"✅ Publication {scheduled_time} terminée")
                        else:
                            logger.error(f"❌ Publication {scheduled_time} échouée")
                            # On marque quand même pour ne pas réessayer en boucle
                            self.mark_as_run(scheduled_time)

                # Attendre 30 secondes avant de revérifier
                time.sleep(30)

            except KeyboardInterrupt:
                logger.info("\n🛑 Scheduler arrêté par l'utilisateur")
                break
            except Exception as e:
                logger.error(f"Erreur dans la boucle: {e}")
                time.sleep(60)  # Attendre 1 minute en cas d'erreur


def setup_systemd_service():
    """Génère un fichier service systemd"""
    service_content = f"""[Unit]
Description=TikSimPro Auto Publisher
After=network.target

[Service]
Type=simple
User={os.environ.get('USER', 'root')}
WorkingDirectory={Path(__file__).parent.parent}
Environment=DISPLAY=:99
ExecStartPre=/bin/bash -c '{Path(__file__).parent}/start_vnc.sh start'
ExecStart=/usr/bin/python3 {Path(__file__)} --daemon
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
"""

    service_path = Path("/tmp/tiksimpro.service")
    service_path.write_text(service_content)

    print(f"""
📋 Fichier service systemd généré: {service_path}

Pour installer:
    sudo cp {service_path} /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable tiksimpro
    sudo systemctl start tiksimpro

Pour voir les logs:
    sudo journalctl -u tiksimpro -f
""")


def test_authentication(platform: str):
    """Teste l'authentification pour une plateforme"""
    print(f"\n🔐 Test d'authentification: {platform}\n")

    if platform in ["tiktok", "all"]:
        print("=" * 50)
        print("📱 TikTok - Connexion...")
        print("=" * 50)
        try:
            from src.utils.connectors.tiktok_connector import TikTokConnector
            connector = TikTokConnector(headless=False)
            if connector.authenticate():
                print("✅ TikTok: Authentification réussie!")
            else:
                print("❌ TikTok: Échec de l'authentification")
        except Exception as e:
            print(f"❌ TikTok erreur: {e}")

    if platform in ["youtube", "all"]:
        print("\n" + "=" * 50)
        print("📺 YouTube - Connexion...")
        print("=" * 50)
        try:
            from src.publishers.youtube_publisher import YouTubePublisher
            publisher = YouTubePublisher(headless=False, auto_close=False)
            if publisher._setup_browser():
                if publisher._load_cookies():
                    print("✅ YouTube: Authentification réussie!")
                else:
                    print("⏳ YouTube: Connectez-vous manuellement dans le navigateur...")
                    publisher.driver.get("https://studio.youtube.com")
                    input("Appuyez sur Entrée une fois connecté...")
                    publisher._save_cookies()
                    print("✅ YouTube: Cookies sauvegardés!")
        except Exception as e:
            print(f"❌ YouTube erreur: {e}")

    print("\n✅ Test terminé!\n")


def setup_cron():
    """Affiche les instructions pour cron"""
    project_dir = Path(__file__).parent.parent

    print(f"""
📋 Configuration Cron pour 3 publications par jour:

Éditer crontab: crontab -e

Ajouter ces lignes:
# TikSimPro - Publication à 9h, 14h et 19h
0 9 * * * cd {project_dir} && DISPLAY=:99 /usr/bin/python3 main.py --publish >> /var/log/tiksimpro.log 2>&1
0 14 * * * cd {project_dir} && DISPLAY=:99 /usr/bin/python3 main.py --publish >> /var/log/tiksimpro.log 2>&1
0 19 * * * cd {project_dir} && DISPLAY=:99 /usr/bin/python3 main.py --publish >> /var/log/tiksimpro.log 2>&1

Note: Assure-toi que le VNC est démarré:
    {project_dir}/scripts/start_vnc.sh start
""")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TikSimPro Scheduler")
    parser.add_argument("--test", action="store_true", help="Lancer une fois immédiatement")
    parser.add_argument("--daemon", action="store_true", help="Mode daemon (boucle infinie)")
    parser.add_argument("--auth", type=str, choices=["tiktok", "youtube", "all"],
                       help="Tester l'authentification (tiktok, youtube, all)")
    parser.add_argument("--times", type=str, default="09:00,14:00,19:00",
                       help="Heures de publication (ex: '09:00,14:00,19:00')")
    parser.add_argument("--setup-systemd", action="store_true", help="Générer fichier systemd")
    parser.add_argument("--setup-cron", action="store_true", help="Afficher config cron")

    args = parser.parse_args()

    if args.setup_systemd:
        setup_systemd_service()
        sys.exit(0)

    if args.setup_cron:
        setup_cron()
        sys.exit(0)

    if args.auth:
        test_authentication(args.auth)
        sys.exit(0)

    times = args.times.split(',')
    scheduler = TikSimProScheduler(publish_times=times)

    if args.test:
        success = scheduler.run_once()
        sys.exit(0 if success else 1)
    elif args.daemon:
        scheduler.run_forever()
    else:
        # Mode interactif
        print("""
🎬 TikSimPro Scheduler

Options:
  python scripts/scheduler.py --test              # Test une publication maintenant
  python scripts/scheduler.py --daemon            # Lancer en mode continu
  python scripts/scheduler.py --auth tiktok       # Connecter TikTok
  python scripts/scheduler.py --auth youtube      # Connecter YouTube
  python scripts/scheduler.py --auth all          # Connecter les deux
  python scripts/scheduler.py --setup-cron        # Voir config cron
  python scripts/scheduler.py --setup-systemd     # Générer service systemd
""")
