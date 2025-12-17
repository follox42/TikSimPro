# src/video_generators/random_generator.py
"""
RandomVideoGenerator - Sélecteur aléatoire de générateurs avec paramètres variables
"""

import random
import logging
from typing import Dict, Any, Optional, List, Union

from src.video_generators.base_video_generator import IVideoGenerator
from src.core.data_pipeline import TrendData
from src.core.plugin_manager import PluginManager

logger = logging.getLogger("TikSimPro")


class RandomVideoGenerator(IVideoGenerator):
    """
    Méta-générateur qui sélectionne aléatoirement un générateur
    et applique des paramètres aléatoires selon la configuration.

    Configuration JSON supportée:
    - min/max: {"gravity": {"min": 1500, "max": 2500}}
    - values: {"restitution": {"values": [0.95, 1.0, 1.02]}}
    """

    # Générateurs disponibles par défaut
    DEFAULT_GENERATORS = ["GravityFallsSimulator", "ArcEscapeSimulator"]

    def __init__(self, width: int = 1080, height: int = 1920,
                 fps: int = 60, duration: float = 30.0):
        super().__init__(width, height, fps, duration)

        # Configuration par générateur
        self.generator_configs: Dict[str, Dict[str, Any]] = {}

        # Liste des générateurs à utiliser
        self.available_generators: List[str] = self.DEFAULT_GENERATORS.copy()

        # Générateur actuellement sélectionné
        self.selected_generator: Optional[IVideoGenerator] = None
        self.selected_generator_name: str = ""
        self.selected_params: Dict[str, Any] = {}

        # Plugin manager pour charger les générateurs
        self.plugin_manager = PluginManager("src", ["video_generators"])

        logger.info("RandomVideoGenerator initialisé")

    def configure(self, config: Dict[str, Any]) -> bool:
        """
        Configure le RandomVideoGenerator.

        Args:
            config: Configuration avec structure:
                {
                    "generators": ["GravityFallsSimulator", "ArcEscapeSimulator"],
                    "GravityFallsSimulator": {
                        "gravity": {"min": 1500, "max": 2500},
                        "restitution": {"values": [0.95, 1.0, 1.02]},
                        ...
                    },
                    "ArcEscapeSimulator": {...}
                }
        """
        try:
            # Liste des générateurs à utiliser
            if "generators" in config:
                self.available_generators = config["generators"]

            # Configuration par générateur
            for gen_name in self.available_generators:
                if gen_name in config:
                    self.generator_configs[gen_name] = config[gen_name]

            logger.info(f"RandomVideoGenerator configuré avec {len(self.available_generators)} générateurs: {self.available_generators}")
            return True

        except Exception as e:
            logger.error(f"Erreur configuration RandomVideoGenerator: {e}")
            return False

    def _resolve_param(self, param_config: Union[Dict, Any]) -> Any:
        """
        Résout un paramètre selon sa configuration.

        Args:
            param_config: Soit une valeur directe, soit:
                - {"min": X, "max": Y} pour un range
                - {"values": [a, b, c]} pour une liste de choix

        Returns:
            Valeur résolue
        """
        if not isinstance(param_config, dict):
            return param_config

        if "min" in param_config and "max" in param_config:
            # Range aléatoire
            min_val = param_config["min"]
            max_val = param_config["max"]

            # Détecter si c'est un float ou int
            if isinstance(min_val, float) or isinstance(max_val, float):
                return random.uniform(min_val, max_val)
            else:
                return random.randint(min_val, max_val)

        elif "values" in param_config:
            # Choix parmi une liste
            return random.choice(param_config["values"])

        # Valeur directe si structure non reconnue
        return param_config

    def _resolve_all_params(self, generator_name: str) -> Dict[str, Any]:
        """
        Résout tous les paramètres pour un générateur.

        Returns:
            Dictionnaire de paramètres résolus
        """
        resolved = {}

        if generator_name in self.generator_configs:
            for param_name, param_config in self.generator_configs[generator_name].items():
                resolved[param_name] = self._resolve_param(param_config)

        return resolved

    def _select_and_create_generator(self) -> bool:
        """
        Sélectionne aléatoirement un générateur et le crée.

        Returns:
            True si succès, False sinon
        """
        try:
            # Sélectionner un générateur aléatoirement
            self.selected_generator_name = random.choice(self.available_generators)
            logger.info(f"Générateur sélectionné: {self.selected_generator_name}")

            # Résoudre les paramètres
            self.selected_params = self._resolve_all_params(self.selected_generator_name)
            logger.info(f"Paramètres résolus: {self.selected_params}")

            # Charger la classe du générateur
            generator_class = self.plugin_manager.get_plugin(
                self.selected_generator_name,
                IVideoGenerator
            )

            if generator_class is None:
                logger.error(f"Générateur {self.selected_generator_name} non trouvé")
                return False

            # Créer l'instance avec les paramètres de base
            self.selected_generator = generator_class(
                width=self.width,
                height=self.height,
                fps=self.fps,
                duration=self.duration
            )

            # Configurer avec les paramètres aléatoires résolus
            self.selected_generator.configure(self.selected_params)
            self.selected_generator.set_output_path(self.output_path)

            return True

        except Exception as e:
            logger.error(f"Erreur création générateur: {e}")
            import traceback
            traceback.print_exc()
            return False

    def apply_trend_data(self, trend_data: TrendData) -> None:
        """Applique les données de tendance au générateur sélectionné"""
        if self.selected_generator:
            self.selected_generator.apply_trend_data(trend_data)

    def initialize_simulation(self) -> bool:
        """Initialise en sélectionnant et créant le générateur"""
        if not self._select_and_create_generator():
            return False

        return self.selected_generator.initialize_simulation()

    def render_frame(self, surface, frame_number: int, dt: float) -> bool:
        """Délègue au générateur sélectionné"""
        if self.selected_generator:
            return self.selected_generator.render_frame(surface, frame_number, dt)
        return False

    def generate(self) -> Optional[str]:
        """
        Génère une vidéo avec un générateur aléatoire.

        Returns:
            Chemin vers la vidéo générée
        """
        try:
            # Sélectionner et créer le générateur
            if not self._select_and_create_generator():
                return None

            logger.info(f"=== RANDOM VIDEO GENERATOR ===")
            logger.info(f"Générateur: {self.selected_generator_name}")
            logger.info(f"Paramètres: {self.selected_params}")
            logger.info(f"==============================")

            # Déléguer la génération
            return self.selected_generator.generate()

        except Exception as e:
            logger.error(f"Erreur génération RandomVideoGenerator: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_audio_events(self):
        """Récupère les événements audio du générateur sélectionné"""
        if self.selected_generator and hasattr(self.selected_generator, 'audio_events'):
            return self.selected_generator.audio_events
        return []

    def get_selected_info(self) -> Dict[str, Any]:
        """
        Retourne les informations sur la sélection actuelle.

        Returns:
            Dict avec générateur et paramètres sélectionnés
        """
        return {
            "generator": self.selected_generator_name,
            "params": self.selected_params
        }


# Configuration par défaut recommandée
DEFAULT_RANDOM_CONFIG = {
    "generators": ["GravityFallsSimulator", "ArcEscapeSimulator"],

    "GravityFallsSimulator": {
        "gravity": {"min": 1500, "max": 2200},
        "restitution": {"values": [0.95, 1.0, 1.02]},
        "ball_size": {"min": 12, "max": 18},
        "container_size": {"values": [0.3, 0.35, 0.4]},
        "min_velocity": {"min": 150, "max": 250}
    },

    "ArcEscapeSimulator": {
        "layer_count": {"min": 15, "max": 25},
        "gap_size_deg": {"values": [45, 55, 65]},
        "wall_thickness": {"min": 18, "max": 26},
        "rotation_speed": {"min": 1.0, "max": 2.0},
        "gravity": {"min": 1500, "max": 2000},
        "ball_size": {"min": 12, "max": 16}
    }
}


if __name__ == "__main__":
    print("Test RandomVideoGenerator")

    gen = RandomVideoGenerator(width=720, height=1280, fps=60, duration=10)
    gen.configure(DEFAULT_RANDOM_CONFIG)
    gen.set_output_path("output/random_test.mp4")

    result = gen.generate()
    if result:
        print(f"Vidéo générée: {result}")
        print(f"Info: {gen.get_selected_info()}")
    else:
        print("Échec de génération")
