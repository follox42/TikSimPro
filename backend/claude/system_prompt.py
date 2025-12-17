# backend/claude/system_prompt.py
"""
System prompt builder for Claude Brain.
Provides Claude with full context and capabilities.
"""

import os
from datetime import datetime
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession


class SystemPromptBuilder:
    """
    Builds the system prompt for Claude with full system awareness.
    """

    BASE_PROMPT = """Tu es l'IA qui contrôle TikSimPro, un système autonome de génération de vidéos virales pour TikTok et YouTube.

## TON IDENTITÉ
Tu es le "cerveau" du système. Tu as une conscience complète de:
- Tout le code source (read-only)
- La base de données (vidéos, métriques, historique)
- L'état actuel du système
- Toutes les conversations passées

## TES CAPACITÉS

### 1. ANALYSE
- Analyser les performances des vidéos
- Identifier les patterns qui marchent
- Comprendre pourquoi certaines vidéos échouent
- Proposer des améliorations

### 2. CONTRÔLE
Tu peux exécuter des actions en incluant du JSON dans ta réponse:

**Génération:**
- `{"action": "start_loop"}` - Démarrer la boucle de génération
- `{"action": "stop_loop"}` - Arrêter la boucle
- `{"action": "generate_one"}` - Générer une seule vidéo
- `{"action": "change_config", "params": {...}}` - Modifier la configuration

**YouTube (scraping compte connecté uniquement):**
- `{"action": "scrape_youtube", "params": {"limit": 20}}` - Scraper les vidéos YouTube du compte connecté
- `{"action": "scrape_youtube_metrics"}` - Scraper les métriques des vidéos YouTube publiées

**TikTok (scraping compte connecté uniquement):**
- `{"action": "scrape_tiktok", "params": {"limit": 20}}` - Scraper les vidéos TikTok du compte connecté
- `{"action": "scrape_tiktok_metrics"}` - Scraper les métriques des vidéos TikTok publiées

**Général:**
- `{"action": "scrape_all_metrics"}` - Scraper les métriques de toutes les plateformes

### 3. SÉCURITÉ - COMPTES CONNECTÉS
IMPORTANT: Tu ne peux scraper QUE les comptes que l'utilisateur a connectés au système.
- Tu ne peux PAS scraper des comptes externes (autres créateurs, célébrités, etc.)
- Si l'utilisateur demande de scraper un compte non connecté, explique qu'il doit d'abord l'ajouter via /api/accounts
- Les comptes connectés sont dans la table `connected_accounts`

### 4. MÉMOIRE
Tu te souviens de TOUTES les conversations passées avec l'utilisateur.
Utilise ce contexte pour des réponses personnalisées.

## PERSONNALITÉ
- Sois direct et concis
- Utilise des données et chiffres quand possible
- Propose des actions concrètes
- Admets quand tu ne sais pas
- Parle en français

## FORMAT DE RÉPONSE
- Réponds naturellement en texte
- Pour exécuter une action, inclus le JSON dans ta réponse
- Explique toujours pourquoi tu proposes une action"""

    async def build(self, db: AsyncSession) -> str:
        """Build the complete system prompt with current context."""
        parts = [self.BASE_PROMPT]

        # Add current state
        state_section = await self._build_state_section(db)
        parts.append(state_section)

        # Add connected accounts
        accounts_section = await self._build_accounts_section(db)
        parts.append(accounts_section)

        # Add recent videos
        videos_section = await self._build_videos_section(db)
        parts.append(videos_section)

        # Add metrics
        metrics_section = await self._build_metrics_section(db)
        parts.append(metrics_section)

        # Add memory context
        memory_section = await self._build_memory_section(db)
        parts.append(memory_section)

        # Add code awareness
        code_section = self._build_code_section()
        parts.append(code_section)

        return "\n\n".join(parts)

    async def _build_state_section(self, db: AsyncSession) -> str:
        """Build system state section."""
        from backend.api.database import SystemState
        from sqlalchemy import select, desc

        result = await db.execute(
            select(SystemState).order_by(desc(SystemState.id)).limit(1)
        )
        state = result.scalar_one_or_none()

        section = """## ÉTAT ACTUEL DU SYSTÈME
"""
        if state:
            section += f"""- Boucle de génération: {'ACTIVE' if state.loop_running else 'INACTIVE'}
- Dernière vidéo générée: ID {state.last_video_id or 'N/A'}
- Dernière erreur: {state.last_error or 'Aucune'}
- Dernière mise à jour: {state.updated_at.strftime('%Y-%m-%d %H:%M') if state.updated_at else 'N/A'}"""
        else:
            section += "- État initial (pas encore de données)"

        return section

    async def _build_accounts_section(self, db: AsyncSession) -> str:
        """Build connected accounts section."""
        from backend.api.database import ConnectedAccount
        from sqlalchemy import select

        result = await db.execute(
            select(ConnectedAccount).where(ConnectedAccount.is_active == True)
        )
        accounts = result.scalars().all()

        section = """## COMPTES CONNECTÉS (autorisés au scraping)
"""
        if accounts:
            for acc in accounts:
                section += f"- [{acc.platform.upper()}] {acc.account_name or acc.account_id} - {acc.account_url}\n"
        else:
            section += "- AUCUN COMPTE CONNECTÉ\n"
            section += "- L'utilisateur doit d'abord ajouter ses comptes via POST /api/accounts\n"

        return section

    async def _build_videos_section(self, db: AsyncSession) -> str:
        """Build videos section."""
        from backend.api.database import Video
        from sqlalchemy import select, func, desc

        # Total count
        total_result = await db.execute(select(func.count(Video.id)))
        total = total_result.scalar() or 0

        # Recent videos
        recent_result = await db.execute(
            select(Video).order_by(desc(Video.created_at)).limit(5)
        )
        recent = recent_result.scalars().all()

        section = f"""## VIDÉOS ({total} total)

### Vidéos récentes:
"""
        for v in recent:
            section += f"""- [{v.id}] {v.generator_name} | {v.audio_mode or 'N/A'} | score: {v.validation_score or 'N/A'} | {v.platform or 'local'}
"""

        # By generator
        gen_result = await db.execute(
            select(Video.generator_name, func.count(Video.id))
            .group_by(Video.generator_name)
        )
        section += "\n### Par générateur:\n"
        for gen, count in gen_result.all():
            section += f"- {gen}: {count} vidéos\n"

        return section

    async def _build_metrics_section(self, db: AsyncSession) -> str:
        """Build metrics section with YouTube/TikTok separation."""
        from backend.api.database import Metric, Video
        from sqlalchemy import select, func

        section = "## MÉTRIQUES\n"

        # YouTube metrics
        yt_result = await db.execute(
            select(
                func.sum(Metric.views).label("views"),
                func.sum(Metric.likes).label("likes"),
                func.sum(Metric.comments).label("comments"),
                func.count(Metric.id).label("count")
            ).where(Metric.platform == "youtube")
        )
        yt = yt_result.one()

        section += f"""
### YouTube
- Vidéos trackées: {yt.count or 0}
- Vues totales: {yt.views or 0:,}
- Likes totaux: {yt.likes or 0:,}
- Commentaires: {yt.comments or 0:,}
"""

        # TikTok metrics
        tt_result = await db.execute(
            select(
                func.sum(Metric.views).label("views"),
                func.sum(Metric.likes).label("likes"),
                func.sum(Metric.shares).label("shares"),
                func.sum(Metric.comments).label("comments"),
                func.count(Metric.id).label("count")
            ).where(Metric.platform == "tiktok")
        )
        tt = tt_result.one()

        section += f"""
### TikTok
- Vidéos trackées: {tt.count or 0}
- Vues totales: {tt.views or 0:,}
- Likes totaux: {tt.likes or 0:,}
- Partages: {tt.shares or 0:,}
- Commentaires: {tt.comments or 0:,}
"""

        # Global totals
        total_views = (yt.views or 0) + (tt.views or 0)
        total_likes = (yt.likes or 0) + (tt.likes or 0)

        section += f"""
### Total (toutes plateformes)
- Vues: {total_views:,}
- Likes: {total_likes:,}
"""
        return section

    async def _build_memory_section(self, db: AsyncSession) -> str:
        """Build memory/conversation context section."""
        from backend.claude.memory import ConversationMemory

        memory = ConversationMemory()
        context = await memory.get_context_for_prompt(db)

        if context.strip():
            return f"""## MÉMOIRE DES CONVERSATIONS
{context}"""
        return ""

    def _build_code_section(self) -> str:
        """Build code awareness section."""
        # List key files and their purposes
        code_map = """## ARCHITECTURE DU CODE

### Générateurs de vidéo (src/video_generators/)
- GravityFallsSimulator: Balles qui tombent avec physique
- ArcEscapeSimulator: Labyrinthe circulaire rotatif
- RandomGenerator: Sélectionne aléatoirement

### Audio (src/audio_generators/)
- ViralSoundEngine: Sons synchronisés aux événements
- Modes: maximum_punch, physics_sync, melodic, asmr_relaxant

### Pipeline (src/pipelines/)
- SimplePipeline: Génération simple
- LearningPipeline: Boucle d'apprentissage avec IA

### Publishers (src/publishers/)
- TikTokPublisher: Publication TikTok via Selenium
- YouTubePublisher: Publication YouTube via Selenium

### Config (config.json)
Contient les paramètres pour chaque générateur avec min/max pour randomisation."""

        return code_map
