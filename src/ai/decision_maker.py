# src/ai/decision_maker.py
"""
AIDecisionMaker - Uses Claude to analyze performance and decide next parameters.
Learns from video performance to optimize future generations.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger("TikSimPro")


@dataclass
class AIDecision:
    """Result of AI decision making."""
    generator_name: str
    generator_params: Dict[str, Any]
    audio_mode: str
    audio_params: Dict[str, Any]
    reasoning: str
    confidence: float  # 0.0 to 1.0
    strategy: str  # "exploit", "explore", "experiment"
    raw_response: Optional[str] = None


class AIDecisionMaker:
    """
    AI-powered decision maker for video generation parameters.

    Uses Claude to analyze past performance and decide optimal parameters
    for the next video generation.

    Usage:
        maker = AIDecisionMaker(api_key="sk-...")
        context = db.get_context_for_ai()
        decision = maker.decide_next_params(context, config_ranges)
        # Use decision.generator_params for next video
    """

    SYSTEM_PROMPT = """Tu es un expert en optimisation de contenu viral pour TikTok et YouTube Shorts.

Ton rôle est d'analyser les performances des vidéos générées et de décider les meilleurs paramètres pour la prochaine vidéo.

Tu reçois:
1. Les données de performance des vidéos récentes (vues, likes, engagement)
2. Les meilleurs performers historiques
3. Les ranges de paramètres disponibles

Tu dois retourner un JSON avec:
- generator_name: le générateur à utiliser
- generator_params: les paramètres spécifiques
- audio_mode: le mode audio
- reasoning: ton explication courte
- confidence: ta confiance (0.0-1.0)
- strategy: "exploit" (utiliser ce qui marche), "explore" (essayer variations), ou "experiment" (tester nouveau)

Règles importantes:
- Si peu de données, privilégie l'exploration
- Si un pattern marche bien, l'exploiter mais avec variations
- Toujours justifier tes choix
- Les paramètres doivent être dans les ranges fournis"""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize AI Decision Maker.

        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
            model: Claude model to use
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
        self._client = None

        if not self.api_key:
            logger.warning("No Anthropic API key provided - AI decisions will use fallback")

    def _get_client(self):
        """Lazy load Anthropic client."""
        if self._client is None and self.api_key:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                logger.error("anthropic package not installed. Run: pip install anthropic")
                return None
        return self._client

    def decide_next_params(self,
                           context: Dict[str, Any],
                           config_ranges: Dict[str, Any],
                           strategy_hint: Optional[str] = None) -> AIDecision:
        """
        Decide the parameters for the next video generation.

        Args:
            context: Context from VideoDatabase.get_context_for_ai()
            config_ranges: Available parameter ranges from config.json
            strategy_hint: Optional hint ("exploit", "explore", "experiment")

        Returns:
            AIDecision with chosen parameters
        """
        client = self._get_client()

        if client is None:
            logger.warning("Using fallback decision (no API client)")
            return self._fallback_decision(config_ranges)

        try:
            # Build the prompt
            prompt = self._build_prompt(context, config_ranges, strategy_hint)

            # Call Claude
            response = client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=self.SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse response
            response_text = response.content[0].text
            decision = self._parse_response(response_text, config_ranges)
            decision.raw_response = response_text

            logger.info(f"AI Decision: {decision.generator_name} with strategy '{decision.strategy}'")
            return decision

        except Exception as e:
            logger.error(f"AI decision failed: {e}")
            return self._fallback_decision(config_ranges)

    def _build_prompt(self,
                      context: Dict[str, Any],
                      config_ranges: Dict[str, Any],
                      strategy_hint: Optional[str]) -> str:
        """Build the prompt for Claude."""
        prompt_parts = []

        # Add context summary
        prompt_parts.append("## Données de Performance\n")

        total_videos = context.get('total_videos', 0)
        prompt_parts.append(f"Total vidéos générées: {total_videos}\n")

        # Recent videos
        recent = context.get('recent_videos', [])
        if recent:
            prompt_parts.append("\n### Vidéos Récentes (les plus récentes en premier):\n")
            for i, v in enumerate(recent[:5]):
                metrics = v.get('metrics') or {}
                prompt_parts.append(
                    f"{i+1}. {v['generator']} | mode audio: {v['audio_mode']} | "
                    f"vues: {metrics.get('views', 'N/A')} | "
                    f"engagement: {metrics.get('engagement_rate', 'N/A')}\n"
                    f"   params: {json.dumps(v['params'], ensure_ascii=False)[:100]}...\n"
                )
        else:
            prompt_parts.append("\nAucune vidéo récente (première génération)\n")

        # Best performers
        best = context.get('best_performers', [])
        if best:
            prompt_parts.append("\n### Meilleurs Performers:\n")
            for i, item in enumerate(best[:3]):
                v = item.get('video')
                m = item.get('metrics', {})
                if v:
                    prompt_parts.append(
                        f"{i+1}. {v.generator_name} | "
                        f"vues: {m.get('views', 0)} | engagement: {m.get('engagement_rate', 0):.4f}\n"
                    )

        # Performance by generator
        by_gen = context.get('performance_by_generator', {})
        if by_gen:
            prompt_parts.append("\n### Performance par Générateur:\n")
            for gen, stats in by_gen.items():
                prompt_parts.append(
                    f"- {gen}: {stats['video_count']} vidéos, "
                    f"moy. vues: {stats['avg_views']:.0f}, "
                    f"moy. engagement: {stats['avg_engagement']:.4f}\n"
                )

        # Config ranges
        prompt_parts.append("\n## Paramètres Disponibles\n")
        prompt_parts.append(f"```json\n{json.dumps(config_ranges, indent=2, ensure_ascii=False)}\n```\n")

        # Strategy hint
        if strategy_hint:
            prompt_parts.append(f"\n## Indication de Stratégie\nPréférence: {strategy_hint}\n")

        # Request
        prompt_parts.append("""
## Ta Décision

Analyse les données et décide les paramètres optimaux pour la prochaine vidéo.

Réponds UNIQUEMENT avec un JSON valide dans ce format:
```json
{
    "generator_name": "GravityFallsSimulator ou ArcEscapeSimulator",
    "generator_params": {
        "gravity": 1800,
        "restitution": 1.0,
        ...
    },
    "audio_mode": "maximum_punch",
    "audio_params": {},
    "reasoning": "Explication courte de ton choix",
    "confidence": 0.75,
    "strategy": "exploit"
}
```
""")

        return "".join(prompt_parts)

    def _parse_response(self, response_text: str, config_ranges: Dict[str, Any]) -> AIDecision:
        """Parse Claude's response into an AIDecision."""
        try:
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")

            json_str = response_text[json_start:json_end]
            data = json.loads(json_str)

            # Validate and extract
            generator_name = data.get('generator_name', 'GravityFallsSimulator')
            generator_params = data.get('generator_params', {})
            audio_mode = data.get('audio_mode', 'random')
            audio_params = data.get('audio_params', {})
            reasoning = data.get('reasoning', 'No reasoning provided')
            confidence = float(data.get('confidence', 0.5))
            strategy = data.get('strategy', 'explore')

            # Validate params are within ranges
            generator_params = self._validate_params(generator_name, generator_params, config_ranges)

            return AIDecision(
                generator_name=generator_name,
                generator_params=generator_params,
                audio_mode=audio_mode,
                audio_params=audio_params,
                reasoning=reasoning,
                confidence=min(1.0, max(0.0, confidence)),
                strategy=strategy
            )

        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            return self._fallback_decision(config_ranges)

    def _validate_params(self,
                         generator_name: str,
                         params: Dict[str, Any],
                         config_ranges: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clamp parameters to allowed ranges."""
        validated = {}
        gen_config = config_ranges.get('params', {}).get(generator_name, {})

        for key, value in params.items():
            if key in gen_config:
                range_spec = gen_config[key]
                if isinstance(range_spec, dict):
                    if 'min' in range_spec and 'max' in range_spec:
                        # Clamp to range
                        validated[key] = max(range_spec['min'], min(range_spec['max'], value))
                    elif 'values' in range_spec:
                        # Must be in list
                        if value in range_spec['values']:
                            validated[key] = value
                        else:
                            validated[key] = range_spec['values'][0]
                else:
                    validated[key] = value
            else:
                validated[key] = value

        return validated

    def _fallback_decision(self, config_ranges: Dict[str, Any]) -> AIDecision:
        """Generate a fallback decision when AI is unavailable."""
        import random

        generators = config_ranges.get('params', {}).get('generators', ['GravityFallsSimulator'])
        generator_name = random.choice(generators)

        # Get random params from config
        gen_config = config_ranges.get('params', {}).get(generator_name, {})
        params = {}

        for key, spec in gen_config.items():
            if isinstance(spec, dict):
                if 'min' in spec and 'max' in spec:
                    if isinstance(spec['min'], float):
                        params[key] = random.uniform(spec['min'], spec['max'])
                    else:
                        params[key] = random.randint(spec['min'], spec['max'])
                elif 'values' in spec:
                    params[key] = random.choice(spec['values'])

        audio_modes = ['maximum_punch', 'physics_sync', 'melodic', 'asmr_relaxant']

        return AIDecision(
            generator_name=generator_name,
            generator_params=params,
            audio_mode=random.choice(audio_modes),
            audio_params={},
            reasoning="Fallback random selection (AI unavailable)",
            confidence=0.3,
            strategy="explore"
        )

    def analyze_performance(self, context: Dict[str, Any]) -> str:
        """
        Get AI analysis of current performance without making a decision.

        Args:
            context: Context from VideoDatabase.get_context_for_ai()

        Returns:
            Analysis text from Claude
        """
        client = self._get_client()
        if client is None:
            return "AI analysis unavailable (no API key)"

        try:
            prompt = f"""Analyse ces données de performance de vidéos virales:

{json.dumps(context, indent=2, ensure_ascii=False, default=str)}

Fournis:
1. Un résumé des tendances observées
2. Ce qui semble marcher le mieux
3. Ce qui pourrait être amélioré
4. Des recommandations pour les prochaines vidéos

Sois concis et actionnable."""

            response = client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return f"Analysis failed: {e}"


if __name__ == "__main__":
    print("Testing AIDecisionMaker...")

    # Test with mock config
    config_ranges = {
        "params": {
            "generators": ["GravityFallsSimulator", "ArcEscapeSimulator"],
            "GravityFallsSimulator": {
                "gravity": {"min": 1500, "max": 2200},
                "restitution": {"values": [0.95, 1.0, 1.02]},
                "ball_size": {"min": 10, "max": 15}
            },
            "ArcEscapeSimulator": {
                "layer_count": {"min": 15, "max": 25},
                "rotation_speed": {"min": 1.0, "max": 2.0}
            }
        }
    }

    context = {
        "total_videos": 5,
        "recent_videos": [
            {"generator": "GravityFallsSimulator", "audio_mode": "maximum_punch",
             "params": {"gravity": 1800}, "metrics": {"views": 1500, "engagement_rate": 0.08}}
        ],
        "best_performers": [],
        "performance_by_generator": {
            "GravityFallsSimulator": {"video_count": 3, "avg_views": 1200, "avg_engagement": 0.07}
        }
    }

    maker = AIDecisionMaker()

    # Test fallback (no API key)
    print("\nTesting fallback decision (no API):")
    decision = maker._fallback_decision(config_ranges)
    print(f"  Generator: {decision.generator_name}")
    print(f"  Params: {decision.generator_params}")
    print(f"  Audio: {decision.audio_mode}")
    print(f"  Strategy: {decision.strategy}")
    print(f"  Confidence: {decision.confidence}")

    print("\nAIDecisionMaker tests completed!")
