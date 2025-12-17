# src/core/git_versioning.py
"""
GitVersioning - Automatic git versioning for tracking code changes.
Enables rollback and performance tracking by code version.
"""

import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

logger = logging.getLogger("TikSimPro")


class GitVersioning:
    """
    Git version control utilities for TikSimPro.

    Usage:
        git = GitVersioning()
        commit_hash = git.get_current_commit()
        git.auto_commit("Added new feature")
        git.rollback_to("abc123")
    """

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()

        if not (self.repo_path / ".git").exists():
            raise ValueError(f"Not a git repository: {self.repo_path}")

    def _run_git(self, *args, check: bool = True) -> subprocess.CompletedProcess:
        """Run a git command."""
        cmd = ["git", "-C", str(self.repo_path)] + list(args)
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check
        )

    # ==================== COMMIT INFO ====================

    def get_current_commit(self) -> str:
        """Get the current commit hash (short)."""
        result = self._run_git("rev-parse", "--short", "HEAD")
        return result.stdout.strip()

    def get_current_commit_full(self) -> str:
        """Get the current commit hash (full)."""
        result = self._run_git("rev-parse", "HEAD")
        return result.stdout.strip()

    def get_commit_message(self, commit_hash: str = "HEAD") -> str:
        """Get commit message for a specific commit."""
        result = self._run_git("log", "-1", "--format=%s", commit_hash)
        return result.stdout.strip()

    def get_commit_date(self, commit_hash: str = "HEAD") -> datetime:
        """Get commit date for a specific commit."""
        result = self._run_git("log", "-1", "--format=%ci", commit_hash)
        date_str = result.stdout.strip()
        # Parse git date format: 2024-01-15 10:30:00 +0100
        return datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S")

    def get_commit_info(self, commit_hash: str = "HEAD") -> Dict[str, Any]:
        """Get full info for a commit."""
        return {
            'hash': self.get_current_commit() if commit_hash == "HEAD" else commit_hash[:7],
            'hash_full': self.get_current_commit_full() if commit_hash == "HEAD" else commit_hash,
            'message': self.get_commit_message(commit_hash),
            'date': self.get_commit_date(commit_hash)
        }

    # ==================== STATUS ====================

    def get_status(self) -> Dict[str, List[str]]:
        """Get current git status."""
        result = self._run_git("status", "--porcelain")
        lines = result.stdout.strip().split("\n") if result.stdout.strip() else []

        status = {
            'modified': [],
            'added': [],
            'deleted': [],
            'untracked': []
        }

        for line in lines:
            if not line:
                continue
            status_code = line[:2]
            file_path = line[3:]

            if 'M' in status_code:
                status['modified'].append(file_path)
            elif 'A' in status_code:
                status['added'].append(file_path)
            elif 'D' in status_code:
                status['deleted'].append(file_path)
            elif '?' in status_code:
                status['untracked'].append(file_path)

        return status

    def has_changes(self) -> bool:
        """Check if there are uncommitted changes."""
        status = self.get_status()
        return any(len(files) > 0 for files in status.values())

    def get_changed_files(self, since_commit: str) -> List[str]:
        """Get list of files changed since a specific commit."""
        result = self._run_git("diff", "--name-only", since_commit, "HEAD")
        files = result.stdout.strip().split("\n") if result.stdout.strip() else []
        return [f for f in files if f]

    # ==================== COMMITS ====================

    def auto_commit(self, message: str, add_all: bool = True) -> Optional[str]:
        """
        Automatically commit changes.

        Args:
            message: Commit message
            add_all: Whether to add all changes (git add .)

        Returns:
            Commit hash if successful, None if no changes
        """
        if not self.has_changes():
            logger.info("No changes to commit")
            return None

        try:
            if add_all:
                self._run_git("add", ".")

            # Commit
            self._run_git("commit", "-m", message)

            commit_hash = self.get_current_commit()
            logger.info(f"Auto-committed: {commit_hash} - {message}")
            return commit_hash

        except subprocess.CalledProcessError as e:
            logger.error(f"Git commit failed: {e.stderr}")
            return None

    def commit_video_generation(self, generator_name: str, params: Dict[str, Any]) -> Optional[str]:
        """Create a commit specifically for video generation changes."""
        message = f"[auto] Video generated: {generator_name}\n\nParams: {params}"
        return self.auto_commit(message)

    # ==================== BRANCHES ====================

    def get_current_branch(self) -> str:
        """Get current branch name."""
        result = self._run_git("branch", "--show-current")
        return result.stdout.strip()

    def get_branches(self) -> List[str]:
        """Get list of all branches."""
        result = self._run_git("branch", "-a")
        branches = result.stdout.strip().split("\n")
        return [b.strip().replace("* ", "") for b in branches if b]

    # ==================== HISTORY ====================

    def get_recent_commits(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get recent commits."""
        result = self._run_git(
            "log", f"-{n}",
            "--format=%H|%h|%s|%ci"
        )
        lines = result.stdout.strip().split("\n") if result.stdout.strip() else []

        commits = []
        for line in lines:
            if not line:
                continue
            parts = line.split("|")
            if len(parts) >= 4:
                commits.append({
                    'hash_full': parts[0],
                    'hash': parts[1],
                    'message': parts[2],
                    'date': datetime.strptime(parts[3][:19], "%Y-%m-%d %H:%M:%S")
                })
        return commits

    def get_commits_between(self, start_commit: str, end_commit: str = "HEAD") -> List[Dict[str, Any]]:
        """Get commits between two points."""
        result = self._run_git(
            "log", f"{start_commit}..{end_commit}",
            "--format=%H|%h|%s|%ci"
        )
        lines = result.stdout.strip().split("\n") if result.stdout.strip() else []

        commits = []
        for line in lines:
            if not line:
                continue
            parts = line.split("|")
            if len(parts) >= 4:
                commits.append({
                    'hash_full': parts[0],
                    'hash': parts[1],
                    'message': parts[2],
                    'date': datetime.strptime(parts[3][:19], "%Y-%m-%d %H:%M:%S")
                })
        return commits

    # ==================== ROLLBACK ====================

    def rollback_to(self, commit_hash: str, hard: bool = False) -> bool:
        """
        Rollback to a specific commit.

        Args:
            commit_hash: Commit to rollback to
            hard: If True, discards all changes (dangerous)

        Returns:
            True if successful
        """
        try:
            if hard:
                self._run_git("reset", "--hard", commit_hash)
                logger.warning(f"Hard reset to {commit_hash}")
            else:
                self._run_git("reset", "--soft", commit_hash)
                logger.info(f"Soft reset to {commit_hash}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Rollback failed: {e.stderr}")
            return False

    def revert_commit(self, commit_hash: str) -> Optional[str]:
        """
        Revert a specific commit (creates a new commit that undoes changes).

        Args:
            commit_hash: Commit to revert

        Returns:
            New commit hash if successful
        """
        try:
            self._run_git("revert", "--no-edit", commit_hash)
            new_commit = self.get_current_commit()
            logger.info(f"Reverted {commit_hash}, new commit: {new_commit}")
            return new_commit

        except subprocess.CalledProcessError as e:
            logger.error(f"Revert failed: {e.stderr}")
            return None

    # ==================== TAGS ====================

    def create_tag(self, tag_name: str, message: str = None) -> bool:
        """Create a git tag."""
        try:
            if message:
                self._run_git("tag", "-a", tag_name, "-m", message)
            else:
                self._run_git("tag", tag_name)
            logger.info(f"Created tag: {tag_name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Tag creation failed: {e.stderr}")
            return False

    def tag_best_performer(self, video_id: int, metric: str, value: float) -> bool:
        """Tag current commit as best performer."""
        tag_name = f"best-{metric}-v{video_id}"
        message = f"Best {metric}: {value} (video {video_id})"
        return self.create_tag(tag_name, message)

    # ==================== DIFF ====================

    def get_diff(self, commit1: str = "HEAD~1", commit2: str = "HEAD") -> str:
        """Get diff between two commits."""
        result = self._run_git("diff", commit1, commit2, check=False)
        return result.stdout

    def get_file_at_commit(self, file_path: str, commit_hash: str) -> Optional[str]:
        """Get file contents at a specific commit."""
        try:
            result = self._run_git("show", f"{commit_hash}:{file_path}")
            return result.stdout
        except subprocess.CalledProcessError:
            return None


# ==================== MAIN TEST ====================

if __name__ == "__main__":
    print("Testing GitVersioning...")

    git = GitVersioning()

    print(f"Current commit: {git.get_current_commit()}")
    print(f"Current branch: {git.get_current_branch()}")
    print(f"Has changes: {git.has_changes()}")

    status = git.get_status()
    print(f"Status: {status}")

    recent = git.get_recent_commits(5)
    print(f"\nRecent commits:")
    for commit in recent:
        print(f"  {commit['hash']} - {commit['message'][:50]}")

    print("\nAll tests passed!")
