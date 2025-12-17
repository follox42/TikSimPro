#!/usr/bin/env python3
"""
TikSimPro - Learning Loop Runner
Boucle d'apprentissage autonome avec dashboard en temps réel

Usage:
    python3 run_learning_loop.py              # Mode interactif
    python3 run_learning_loop.py --auto       # Mode automatique (boucle)
    python3 run_learning_loop.py --status     # Voir le status actuel
    python3 run_learning_loop.py --analyze    # Analyse Claude des perfs
"""

import os
import sys
import json
import time
import argparse
import logging
from datetime import datetime, timedelta
from typing import Optional

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('learning_loop.log')
    ]
)
logger = logging.getLogger("TikSimPro")


class LearningLoopRunner:
    """Runner interactif pour la boucle d'apprentissage."""

    def __init__(self):
        self.pipeline = None
        self.config = None
        self._setup_pipeline()

    def _setup_pipeline(self):
        """Configure la pipeline avec tous les composants."""
        from src.pipelines import LearningPipeline, LoopConfig

        # Load config
        with open("config.json", 'r') as f:
            self.config = json.load(f)

        # Create loop config
        loop_config = LoopConfig(
            output_dir="videos",
            video_duration=self.config.get("video_duration", 60),
            video_dimensions=[1080, 1920],
            fps=60,
            min_validation_score=0.6,
            auto_publish=False,  # Changé manuellement si besoin
            use_ai_decisions=True,
            scrape_interval_hours=1,
            loop_interval_minutes=30,
            max_videos_per_day=24,
            max_consecutive_failures=3
        )

        # Create pipeline
        self.pipeline = LearningPipeline(
            loop_config=loop_config,
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
        self.pipeline.configure(self.config)

        # Setup components
        self._setup_components()

        print("Pipeline initialisée avec succès!")

    def _setup_components(self):
        """Configure les composants de génération."""
        try:
            # Trend Analyzer
            from src.trend_analyzers.gemini_trend_analyzer import GeminiTrendAnalyzer
            self.pipeline.set_trend_analyzer(GeminiTrendAnalyzer())
            print("  ✓ Trend Analyzer (Gemini)")
        except Exception as e:
            print(f"  ✗ Trend Analyzer: {e}")

        try:
            # Video Generator - Random qui choisit entre les générateurs
            from src.video_generators.random_generator import RandomVideoGenerator
            self.pipeline.set_video_generator(RandomVideoGenerator(
                width=1080,
                height=1920,
                fps=60,
                duration=self.config.get("video_duration", 60)
            ))
            print("  ✓ Video Generator (Random)")
        except Exception as e:
            print(f"  ✗ Video Generator: {e}")

        try:
            # Audio Generator
            from src.audio_generators.viral_sound_engine import ViralSoundEngine
            self.pipeline.set_audio_generator(ViralSoundEngine())
            print("  ✓ Audio Generator (ViralSound)")
        except Exception as e:
            print(f"  ✗ Audio Generator: {e}")

        try:
            # Media Combiner
            from src.media_combiners.ffmpeg_combiner import FFmpegCombiner
            self.pipeline.set_media_combiner(FFmpegCombiner())
            print("  ✓ Media Combiner (FFmpeg)")
        except Exception as e:
            print(f"  ✗ Media Combiner: {e}")

        # Publishers (désactivés par défaut)
        # self._setup_publishers()

    def _setup_publishers(self):
        """Configure les publishers (optionnel)."""
        try:
            from src.publishers.youtube_publisher import YouTubePublisher
            from src.publishers.tiktok_publisher import TikTokPublisher

            # YouTube
            yt = YouTubePublisher()
            if yt.is_authenticated():
                self.pipeline.add_publisher("youtube", yt)
                print("  ✓ YouTube Publisher")

            # TikTok
            tt = TikTokPublisher()
            if tt.is_authenticated():
                self.pipeline.add_publisher("tiktok", tt)
                print("  ✓ TikTok Publisher")

        except Exception as e:
            print(f"  ✗ Publishers: {e}")

    def show_dashboard(self):
        """Affiche le dashboard complet."""
        self._clear_screen()
        print("=" * 70)
        print("  TIKSIMPRO - AI CONTENT MANAGER DASHBOARD")
        print("=" * 70)

        # Stats générales
        stats = self.pipeline.get_stats()
        print(f"\n{'─' * 70}")
        print("  STATISTIQUES GENERALES")
        print(f"{'─' * 70}")
        print(f"  Videos totales:     {stats['total_videos']}")
        print(f"  Videos aujourd'hui: {stats['videos_today']}/{stats['max_videos_per_day']}")
        print(f"  Echecs consécutifs: {stats['consecutive_failures']}")
        print(f"  Boucle active:      {'OUI' if stats['running'] else 'NON'}")

        # Performance par générateur
        if stats.get('performance_by_generator'):
            print(f"\n{'─' * 70}")
            print("  PERFORMANCE PAR GENERATEUR")
            print(f"{'─' * 70}")
            for gen, perf in stats['performance_by_generator'].items():
                print(f"  {gen}:")
                print(f"    Videos: {perf['video_count']} | Moy. vues: {perf['avg_views']:.0f} | Engagement: {perf['avg_engagement']:.4f}")

        # Dernières vidéos
        self._show_recent_videos()

        # Meilleurs performers
        self._show_best_performers()

        print(f"\n{'─' * 70}")
        print("  ACTIONS DISPONIBLES")
        print(f"{'─' * 70}")
        print("  [1] Générer UNE vidéo")
        print("  [2] Lancer la boucle automatique")
        print("  [3] Voir l'analyse Claude")
        print("  [4] Scraper les métriques maintenant")
        print("  [5] Lister toutes les vidéos")
        print("  [6] Rafraîchir le dashboard")
        print("  [7] Activer/Désactiver la publication")
        print("  [Q] Quitter")
        print("=" * 70)

    def _show_recent_videos(self):
        """Affiche les vidéos récentes."""
        db = self.pipeline.get_database()
        videos = db.get_all_videos(limit=5)

        if videos:
            print(f"\n{'─' * 70}")
            print("  VIDEOS RECENTES")
            print(f"{'─' * 70}")
            for v in videos:
                status = "✓" if v.validation_score and v.validation_score >= 0.7 else "○"
                pub = f"[{v.platform}]" if v.platform else "[local]"
                print(f"  {status} [{v.id}] {v.generator_name} | {v.audio_mode} | {pub}")
                if v.generator_params:
                    params_str = ", ".join(f"{k}={v}" for k, v in list(v.generator_params.items())[:3])
                    print(f"      Params: {params_str}...")

    def _show_best_performers(self):
        """Affiche les meilleurs performers."""
        db = self.pipeline.get_database()
        best = db.get_best_performers(limit=3)

        if best:
            print(f"\n{'─' * 70}")
            print("  TOP PERFORMERS")
            print(f"{'─' * 70}")
            for i, item in enumerate(best, 1):
                v = item.get('video')
                m = item.get('metrics', {})
                if v:
                    print(f"  #{i} [{v.id}] {v.generator_name}")
                    print(f"      Vues: {m.get('views', 0)} | Likes: {m.get('likes', 0)} | Engagement: {m.get('engagement_rate', 0):.4f}")

    def _clear_screen(self):
        """Efface l'écran."""
        os.system('clear' if os.name != 'nt' else 'cls')

    def generate_one(self):
        """Génère une seule vidéo avec affichage détaillé."""
        print("\n" + "=" * 70)
        print("  GENERATION D'UNE VIDEO")
        print("=" * 70)

        # Étape 1: Décision IA
        print("\n[1/5] Demande de décision à Claude...")
        decision = self.pipeline._get_ai_decision()

        print(f"\n  ╔══════════════════════════════════════════════════════════════════╗")
        print(f"  ║  DECISION CLAUDE                                                  ║")
        print(f"  ╠══════════════════════════════════════════════════════════════════╣")
        print(f"  ║  Générateur: {decision.generator_name:<50} ║")
        print(f"  ║  Stratégie:  {decision.strategy:<50} ║")
        print(f"  ║  Confiance:  {decision.confidence:.0%:<50} ║")
        print(f"  ║  Audio:      {decision.audio_mode:<50} ║")
        print(f"  ╠══════════════════════════════════════════════════════════════════╣")
        print(f"  ║  Paramètres:                                                      ║")
        for k, v in decision.generator_params.items():
            print(f"  ║    {k}: {v:<56} ║")
        print(f"  ╠══════════════════════════════════════════════════════════════════╣")
        print(f"  ║  Raisonnement:                                                    ║")
        # Word wrap reasoning
        reasoning = decision.reasoning
        while reasoning:
            line = reasoning[:60]
            reasoning = reasoning[60:]
            print(f"  ║  {line:<62} ║")
        print(f"  ╚══════════════════════════════════════════════════════════════════╝")

        # Confirmation
        confirm = input("\n  Continuer avec cette décision? (O/n): ").strip().lower()
        if confirm == 'n':
            print("  Génération annulée.")
            return None

        # Lancer la génération
        print("\n[2/5] Génération de la vidéo...")
        start_time = time.time()

        result = self.pipeline.run_once()

        elapsed = time.time() - start_time

        if result:
            print(f"\n  ✓ Vidéo générée avec succès!")
            print(f"    Fichier: {result}")
            print(f"    Temps: {elapsed:.1f}s")

            # Montrer les stats mises à jour
            video_id = self.pipeline.get_database().get_all_videos(limit=1)[0].id
            print(f"    ID en base: {video_id}")
        else:
            print(f"\n  ✗ Échec de la génération")

        return result

    def run_auto_loop(self):
        """Lance la boucle automatique."""
        print("\n" + "=" * 70)
        print("  BOUCLE AUTOMATIQUE")
        print("=" * 70)
        print(f"\n  Intervalle: {self.pipeline.config.loop_interval_minutes} minutes")
        print(f"  Max/jour:   {self.pipeline.config.max_videos_per_day} vidéos")
        print(f"  Publication: {'ACTIVEE' if self.pipeline.config.auto_publish else 'DESACTIVEE'}")
        print("\n  Appuie sur Ctrl+C pour arrêter la boucle")

        confirm = input("\n  Démarrer la boucle? (o/N): ").strip().lower()
        if confirm != 'o':
            print("  Boucle annulée.")
            return

        print("\n  Démarrage de la boucle...")

        try:
            iteration = 0
            while True:
                iteration += 1
                print(f"\n{'═' * 70}")
                print(f"  ITERATION #{iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'═' * 70}")

                result = self.pipeline.run_once()

                if result:
                    print(f"\n  ✓ Vidéo #{iteration} générée: {result}")
                else:
                    print(f"\n  ✗ Échec de l'itération #{iteration}")

                # Stats
                stats = self.pipeline.get_stats()
                print(f"\n  Stats: {stats['videos_today']}/{stats['max_videos_per_day']} aujourd'hui")

                if stats['videos_today'] >= stats['max_videos_per_day']:
                    print("\n  Limite quotidienne atteinte. Pause jusqu'à demain...")
                    # Calculer temps jusqu'à minuit
                    now = datetime.now()
                    tomorrow = now.replace(hour=0, minute=0, second=0) + timedelta(days=1)
                    sleep_seconds = (tomorrow - now).seconds
                    time.sleep(sleep_seconds)
                else:
                    print(f"\n  Prochaine génération dans {self.pipeline.config.loop_interval_minutes} minutes...")
                    time.sleep(self.pipeline.config.loop_interval_minutes * 60)

        except KeyboardInterrupt:
            print("\n\n  Boucle arrêtée par l'utilisateur.")

    def show_claude_analysis(self):
        """Demande à Claude une analyse des performances."""
        print("\n" + "=" * 70)
        print("  ANALYSE CLAUDE DES PERFORMANCES")
        print("=" * 70)

        print("\n  Analyse en cours...")

        analysis = self.pipeline.get_ai_analysis()

        print(f"\n{'─' * 70}")
        print(analysis)
        print(f"{'─' * 70}")

        input("\n  Appuie sur Entrée pour continuer...")

    def scrape_now(self):
        """Lance le scraping immédiat."""
        print("\n" + "=" * 70)
        print("  SCRAPING DES METRIQUES")
        print("=" * 70)

        db = self.pipeline.get_database()
        videos = db.get_all_videos(limit=50)

        published = [v for v in videos if v.platform_video_id]

        if not published:
            print("\n  Aucune vidéo publiée à scraper.")
            input("\n  Appuie sur Entrée pour continuer...")
            return

        print(f"\n  {len(published)} vidéos publiées à scraper...")

        confirm = input("  Lancer le scraping? (o/N): ").strip().lower()
        if confirm != 'o':
            return

        print("\n  Scraping en cours (cela peut prendre du temps)...")
        self.pipeline.scrape_now()

        print("\n  ✓ Scraping terminé!")
        input("\n  Appuie sur Entrée pour continuer...")

    def list_all_videos(self):
        """Liste toutes les vidéos."""
        print("\n" + "=" * 70)
        print("  LISTE DE TOUTES LES VIDEOS")
        print("=" * 70)

        db = self.pipeline.get_database()
        videos = db.get_all_videos(limit=100)

        if not videos:
            print("\n  Aucune vidéo en base.")
        else:
            print(f"\n  {len(videos)} vidéos trouvées:\n")

            for v in videos:
                pub_status = f"[{v.platform}:{v.platform_video_id[:8]}...]" if v.platform_video_id else "[local]"
                val_status = f"val:{v.validation_score:.2f}" if v.validation_score else "val:N/A"

                print(f"  [{v.id:3}] {v.created_at.strftime('%Y-%m-%d %H:%M')}")
                print(f"        {v.generator_name} | {v.audio_mode} | {val_status} | {pub_status}")

                # Params
                if v.generator_params:
                    params = ", ".join(f"{k}={val}" for k, val in list(v.generator_params.items())[:4])
                    print(f"        Params: {params}")

                # Metrics
                metrics = db.get_metrics_history(v.id)
                if metrics:
                    latest = metrics[-1]
                    print(f"        Metrics: {latest.views} vues, {latest.likes} likes, {latest.comments} comments")

                print()

        input("\n  Appuie sur Entrée pour continuer...")

    def toggle_publish(self):
        """Active/désactive la publication."""
        current = self.pipeline.config.auto_publish
        self.pipeline.config.auto_publish = not current

        status = "ACTIVEE" if self.pipeline.config.auto_publish else "DESACTIVEE"
        print(f"\n  Publication: {status}")

        if self.pipeline.config.auto_publish:
            print("  ⚠️  Les prochaines vidéos seront publiées automatiquement!")
            self._setup_publishers()

        input("\n  Appuie sur Entrée pour continuer...")

    def run_interactive(self):
        """Lance le mode interactif."""
        while True:
            self.show_dashboard()

            choice = input("\n  Choix: ").strip().upper()

            if choice == '1':
                self.generate_one()
                input("\n  Appuie sur Entrée pour continuer...")
            elif choice == '2':
                self.run_auto_loop()
            elif choice == '3':
                self.show_claude_analysis()
            elif choice == '4':
                self.scrape_now()
            elif choice == '5':
                self.list_all_videos()
            elif choice == '6':
                continue  # Refresh
            elif choice == '7':
                self.toggle_publish()
            elif choice == 'Q':
                print("\n  Au revoir!")
                break
            else:
                print("\n  Choix invalide.")
                time.sleep(1)


def main():
    parser = argparse.ArgumentParser(description="TikSimPro Learning Loop")
    parser.add_argument('--auto', action='store_true', help='Mode boucle automatique')
    parser.add_argument('--status', action='store_true', help='Afficher le status')
    parser.add_argument('--analyze', action='store_true', help='Analyse Claude')
    parser.add_argument('--generate', action='store_true', help='Générer une vidéo')
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("  TIKSIMPRO - AI CONTENT MANAGER")
    print("=" * 70)
    print("\n  Initialisation...")

    runner = LearningLoopRunner()

    if args.auto:
        runner.run_auto_loop()
    elif args.status:
        runner.show_dashboard()
    elif args.analyze:
        runner.show_claude_analysis()
    elif args.generate:
        runner.generate_one()
    else:
        runner.run_interactive()


if __name__ == "__main__":
    main()
