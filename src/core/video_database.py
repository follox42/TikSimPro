# src/core/video_database.py
"""
VideoDatabase - SQLite database for tracking generated videos and their performance.
Stores all generation parameters, metrics, and enables learning from results.
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger("TikSimPro")


@dataclass
class VideoRecord:
    """Record of a generated video with all its parameters."""
    generator_name: str
    generator_params: Dict[str, Any]
    audio_mode: str
    audio_params: Dict[str, Any]
    video_path: str
    duration: float
    fps: int
    width: int
    height: int
    git_commit: Optional[str] = None
    midi_file: Optional[str] = None
    validation_score: Optional[float] = None
    validation_details: Optional[Dict[str, Any]] = None
    published_at: Optional[datetime] = None
    platform: Optional[str] = None
    platform_video_id: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass
class MetricsRecord:
    """Performance metrics scraped from platforms."""
    video_id: int
    platform: str
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    watch_time_avg: Optional[float] = None
    retention_rate: Optional[float] = None
    engagement_rate: Optional[float] = None
    id: Optional[int] = None
    scraped_at: Optional[datetime] = None


@dataclass
class AIDecisionRecord:
    """Record of AI decision for parameter selection."""
    context: Dict[str, Any]
    decision: Dict[str, Any]
    reasoning: str
    id: Optional[int] = None
    created_at: Optional[datetime] = None


class VideoDatabase:
    """
    SQLite database for tracking videos, metrics, and AI decisions.

    Usage:
        db = VideoDatabase()
        video_id = db.save_video(VideoRecord(...))
        db.add_metrics(video_id, MetricsRecord(...))
        best = db.get_best_performers(limit=10)
    """

    def __init__(self, db_path: str = "data/tiksimpro.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database tables."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Videos table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                git_commit TEXT,
                generator_name TEXT NOT NULL,
                generator_params JSON,
                audio_mode TEXT,
                audio_params JSON,
                midi_file TEXT,
                video_path TEXT,
                duration REAL,
                fps INTEGER,
                width INTEGER,
                height INTEGER,
                validation_score REAL,
                validation_details JSON,
                published_at TIMESTAMP,
                platform TEXT,
                platform_video_id TEXT
            )
        """)

        # Metrics table (scraped performance data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER NOT NULL,
                platform TEXT NOT NULL,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                saves INTEGER DEFAULT 0,
                watch_time_avg REAL,
                retention_rate REAL,
                engagement_rate REAL,
                FOREIGN KEY (video_id) REFERENCES videos (id)
            )
        """)

        # AI decisions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                context JSON,
                decision JSON,
                reasoning TEXT
            )
        """)

        # Git versions table (track code changes)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS git_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                commit_hash TEXT UNIQUE NOT NULL,
                commit_message TEXT,
                commit_date TIMESTAMP,
                files_changed JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_created ON videos(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_platform ON videos(platform)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_video ON metrics(video_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_scraped ON metrics(scraped_at)")

        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")

    # ==================== VIDEO CRUD ====================

    def save_video(self, video: VideoRecord) -> int:
        """Save a video record and return its ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO videos (
                git_commit, generator_name, generator_params, audio_mode,
                audio_params, midi_file, video_path, duration, fps, width, height,
                validation_score, validation_details, published_at, platform, platform_video_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            video.git_commit,
            video.generator_name,
            json.dumps(video.generator_params),
            video.audio_mode,
            json.dumps(video.audio_params),
            video.midi_file,
            video.video_path,
            video.duration,
            video.fps,
            video.width,
            video.height,
            video.validation_score,
            json.dumps(video.validation_details) if video.validation_details else None,
            video.published_at.isoformat() if video.published_at else None,
            video.platform,
            video.platform_video_id
        ))

        video_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"Saved video {video_id}: {video.generator_name}")
        return video_id

    def get_video(self, video_id: int) -> Optional[VideoRecord]:
        """Get a video by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_video(row)
        return None

    def get_all_videos(self, limit: int = 100, offset: int = 0) -> List[VideoRecord]:
        """Get all videos, most recent first."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM videos ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_video(row) for row in rows]

    def get_videos_by_generator(self, generator_name: str, limit: int = 50) -> List[VideoRecord]:
        """Get videos by generator name."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM videos WHERE generator_name = ? ORDER BY created_at DESC LIMIT ?",
            (generator_name, limit)
        )
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_video(row) for row in rows]

    def get_videos_by_git_commit(self, commit_hash: str) -> List[VideoRecord]:
        """Get videos generated with a specific git commit."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM videos WHERE git_commit = ? ORDER BY created_at DESC",
            (commit_hash,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_video(row) for row in rows]

    def update_video_publication(self, video_id: int, platform: str, platform_video_id: str):
        """Update video with publication info."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE videos
            SET published_at = CURRENT_TIMESTAMP, platform = ?, platform_video_id = ?
            WHERE id = ?
        """, (platform, platform_video_id, video_id))
        conn.commit()
        conn.close()
        logger.info(f"Updated video {video_id} publication: {platform}/{platform_video_id}")

    def _row_to_video(self, row: sqlite3.Row) -> VideoRecord:
        """Convert database row to VideoRecord."""
        return VideoRecord(
            id=row['id'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            git_commit=row['git_commit'],
            generator_name=row['generator_name'],
            generator_params=json.loads(row['generator_params']) if row['generator_params'] else {},
            audio_mode=row['audio_mode'],
            audio_params=json.loads(row['audio_params']) if row['audio_params'] else {},
            midi_file=row['midi_file'],
            video_path=row['video_path'],
            duration=row['duration'],
            fps=row['fps'],
            width=row['width'],
            height=row['height'],
            validation_score=row['validation_score'],
            validation_details=json.loads(row['validation_details']) if row['validation_details'] else None,
            published_at=datetime.fromisoformat(row['published_at']) if row['published_at'] else None,
            platform=row['platform'],
            platform_video_id=row['platform_video_id']
        )

    # ==================== METRICS CRUD ====================

    def add_metrics(self, metrics: MetricsRecord) -> int:
        """Add performance metrics for a video."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Calculate engagement rate if not provided
        engagement_rate = metrics.engagement_rate
        if engagement_rate is None and metrics.views > 0:
            engagement_rate = (metrics.likes + metrics.comments + metrics.shares) / metrics.views

        cursor.execute("""
            INSERT INTO metrics (
                video_id, platform, views, likes, comments, shares, saves,
                watch_time_avg, retention_rate, engagement_rate
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metrics.video_id,
            metrics.platform,
            metrics.views,
            metrics.likes,
            metrics.comments,
            metrics.shares,
            metrics.saves,
            metrics.watch_time_avg,
            metrics.retention_rate,
            engagement_rate
        ))

        metrics_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"Added metrics {metrics_id} for video {metrics.video_id}: {metrics.views} views")
        return metrics_id

    def get_latest_metrics(self, video_id: int) -> Optional[MetricsRecord]:
        """Get the most recent metrics for a video."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM metrics WHERE video_id = ? ORDER BY scraped_at DESC LIMIT 1",
            (video_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_metrics(row)
        return None

    def get_metrics_history(self, video_id: int) -> List[MetricsRecord]:
        """Get all metrics history for a video."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM metrics WHERE video_id = ? ORDER BY scraped_at ASC",
            (video_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_metrics(row) for row in rows]

    def _row_to_metrics(self, row: sqlite3.Row) -> MetricsRecord:
        """Convert database row to MetricsRecord."""
        return MetricsRecord(
            id=row['id'],
            video_id=row['video_id'],
            platform=row['platform'],
            scraped_at=datetime.fromisoformat(row['scraped_at']) if row['scraped_at'] else None,
            views=row['views'],
            likes=row['likes'],
            comments=row['comments'],
            shares=row['shares'],
            saves=row['saves'],
            watch_time_avg=row['watch_time_avg'],
            retention_rate=row['retention_rate'],
            engagement_rate=row['engagement_rate']
        )

    # ==================== ANALYSIS ====================

    def get_best_performers(self, metric: str = 'engagement_rate', limit: int = 10) -> List[Dict[str, Any]]:
        """Get best performing videos by a specific metric."""
        valid_metrics = ['views', 'likes', 'comments', 'engagement_rate', 'retention_rate']
        if metric not in valid_metrics:
            metric = 'engagement_rate'

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT v.*, m.views, m.likes, m.comments, m.shares, m.engagement_rate, m.retention_rate
            FROM videos v
            JOIN (
                SELECT video_id, MAX(scraped_at) as latest
                FROM metrics
                GROUP BY video_id
            ) latest_m ON v.id = latest_m.video_id
            JOIN metrics m ON m.video_id = latest_m.video_id AND m.scraped_at = latest_m.latest
            ORDER BY m.{metric} DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            results.append({
                'video': self._row_to_video(row),
                'metrics': {
                    'views': row['views'],
                    'likes': row['likes'],
                    'comments': row['comments'],
                    'shares': row['shares'],
                    'engagement_rate': row['engagement_rate'],
                    'retention_rate': row['retention_rate']
                }
            })
        return results

    def get_performance_by_generator(self) -> Dict[str, Dict[str, float]]:
        """Get average performance metrics grouped by generator."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                v.generator_name,
                COUNT(DISTINCT v.id) as video_count,
                AVG(m.views) as avg_views,
                AVG(m.likes) as avg_likes,
                AVG(m.engagement_rate) as avg_engagement
            FROM videos v
            JOIN (
                SELECT video_id, MAX(scraped_at) as latest
                FROM metrics
                GROUP BY video_id
            ) latest_m ON v.id = latest_m.video_id
            JOIN metrics m ON m.video_id = latest_m.video_id AND m.scraped_at = latest_m.latest
            GROUP BY v.generator_name
        """)
        rows = cursor.fetchall()
        conn.close()

        return {
            row['generator_name']: {
                'video_count': row['video_count'],
                'avg_views': row['avg_views'],
                'avg_likes': row['avg_likes'],
                'avg_engagement': row['avg_engagement']
            }
            for row in rows
        }

    def get_performance_by_git_version(self) -> Dict[str, Dict[str, float]]:
        """Get average performance grouped by git commit."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                v.git_commit,
                COUNT(DISTINCT v.id) as video_count,
                AVG(m.views) as avg_views,
                AVG(m.engagement_rate) as avg_engagement
            FROM videos v
            JOIN (
                SELECT video_id, MAX(scraped_at) as latest
                FROM metrics
                GROUP BY video_id
            ) latest_m ON v.id = latest_m.video_id
            JOIN metrics m ON m.video_id = latest_m.video_id AND m.scraped_at = latest_m.latest
            WHERE v.git_commit IS NOT NULL
            GROUP BY v.git_commit
            ORDER BY MAX(v.created_at) DESC
        """)
        rows = cursor.fetchall()
        conn.close()

        return {
            row['git_commit']: {
                'video_count': row['video_count'],
                'avg_views': row['avg_views'],
                'avg_engagement': row['avg_engagement']
            }
            for row in rows
        }

    # ==================== AI DECISIONS ====================

    def save_ai_decision(self, decision: AIDecisionRecord) -> int:
        """Save an AI decision record."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO ai_decisions (context, decision, reasoning)
            VALUES (?, ?, ?)
        """, (
            json.dumps(decision.context),
            json.dumps(decision.decision),
            decision.reasoning
        ))

        decision_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"Saved AI decision {decision_id}")
        return decision_id

    def get_ai_decisions(self, limit: int = 20) -> List[AIDecisionRecord]:
        """Get recent AI decisions."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM ai_decisions ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        conn.close()

        return [
            AIDecisionRecord(
                id=row['id'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                context=json.loads(row['context']) if row['context'] else {},
                decision=json.loads(row['decision']) if row['decision'] else {},
                reasoning=row['reasoning']
            )
            for row in rows
        ]

    # ==================== GIT VERSIONS ====================

    def save_git_version(self, commit_hash: str, commit_message: str,
                         commit_date: datetime, files_changed: List[str]):
        """Save git version info."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR IGNORE INTO git_versions (commit_hash, commit_message, commit_date, files_changed)
                VALUES (?, ?, ?, ?)
            """, (
                commit_hash,
                commit_message,
                commit_date.isoformat(),
                json.dumps(files_changed)
            ))
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # Already exists
        finally:
            conn.close()

    # ==================== CONTEXT FOR AI ====================

    def get_context_for_ai(self, n_recent: int = 10, n_best: int = 5) -> Dict[str, Any]:
        """
        Get comprehensive context for AI decision making.

        Returns:
            Dict with recent videos, best performers, performance by generator, etc.
        """
        return {
            'recent_videos': [
                {
                    'generator': v.generator_name,
                    'params': v.generator_params,
                    'audio_mode': v.audio_mode,
                    'metrics': asdict(self.get_latest_metrics(v.id)) if self.get_latest_metrics(v.id) else None
                }
                for v in self.get_all_videos(limit=n_recent)
            ],
            'best_performers': self.get_best_performers(limit=n_best),
            'performance_by_generator': self.get_performance_by_generator(),
            'performance_by_version': self.get_performance_by_git_version(),
            'total_videos': self._get_count('videos'),
            'total_metrics': self._get_count('metrics')
        }

    def _get_count(self, table: str) -> int:
        """Get row count for a table."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        conn.close()
        return count


# ==================== MAIN TEST ====================

if __name__ == "__main__":
    print("Testing VideoDatabase...")

    db = VideoDatabase("data/test_tiksimpro.db")

    # Test save video
    video = VideoRecord(
        generator_name="GravityFallsSimulator",
        generator_params={"gravity": 1800, "restitution": 1.0},
        audio_mode="maximum_punch",
        audio_params={"progressive_build": True},
        video_path="videos/test.mp4",
        duration=30.0,
        fps=60,
        width=1080,
        height=1920,
        git_commit="abc123"
    )

    video_id = db.save_video(video)
    print(f"Saved video ID: {video_id}")

    # Test add metrics
    metrics = MetricsRecord(
        video_id=video_id,
        platform="youtube",
        views=1500,
        likes=120,
        comments=15,
        shares=8
    )

    metrics_id = db.add_metrics(metrics)
    print(f"Saved metrics ID: {metrics_id}")

    # Test get video
    retrieved = db.get_video(video_id)
    print(f"Retrieved video: {retrieved.generator_name}")

    # Test get context
    context = db.get_context_for_ai()
    print(f"Context for AI: {len(context['recent_videos'])} recent videos")

    print("\nAll tests passed!")
