# src/utils/temp_file_manager.py
"""
Temporary file manager for TikSimPro
Efficiently manages temporary files at each pipeline step
"""

import os
import shutil
import tempfile
import logging
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from contextlib import contextmanager
from datetime import datetime
import threading

logger = logging.getLogger("TikSimPro")

class TempFileManager:
    """
    Centralized temporary file manager for TikSimPro pipeline
    
    Organizes files by steps and manages automatic cleanup
    """
    
    def __init__(self, 
                 base_temp_dir: Optional[str] = None,
                 auto_cleanup: bool = True,
                 keep_on_error: bool = True,
                 max_age_hours: int = 24):
        """
        Initialize temporary file manager
        
        Args:
            base_temp_dir: Base directory (default: temp/)
            auto_cleanup: Auto cleanup at the end
            keep_on_error: Keep files on error (for debugging)
            max_age_hours: Maximum age of files before cleanup (hours)
        """
        self.base_temp_dir = Path(base_temp_dir) if base_temp_dir else Path("temp")
        self.auto_cleanup = auto_cleanup
        self.keep_on_error = keep_on_error
        self.max_age_hours = max_age_hours
        
        # Unique session to avoid collisions
        self.session_id = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"
        self.session_dir = self.base_temp_dir / f"session_{self.session_id}"
        
        # Track created files and directories
        self.created_files: List[Path] = []
        self.created_dirs: List[Path] = []
        self.step_dirs: Dict[str, Path] = {}
        
        # States
        self.is_initialized = False
        self.cleanup_done = False
        self.has_errors = False
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Initialize
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize base directories"""
        try:
            # Create session directory
            self.session_dir.mkdir(parents=True, exist_ok=True)
            self.created_dirs.append(self.session_dir)
            
            # Clean old sessions
            self._cleanup_old_sessions()
            
            self.is_initialized = True
            logger.info(f"TempFileManager initialized: {self.session_dir}")
            
        except Exception as e:
            logger.error(f"TempFileManager initialization error: {e}")
            raise
    
    def _cleanup_old_sessions(self) -> None:
        """Clean expired old sessions"""
        if not self.base_temp_dir.exists():
            return
            
        try:
            current_time = time.time()
            max_age_seconds = self.max_age_hours * 3600
            
            for item in self.base_temp_dir.iterdir():
                if item.is_dir() and item.name.startswith("session_"):
                    # Extract timestamp from name
                    try:
                        timestamp_str = item.name.split("_")[1]
                        timestamp = int(timestamp_str)
                        
                        if current_time - timestamp > max_age_seconds:
                            shutil.rmtree(item, ignore_errors=True)
                            logger.debug(f"Expired session removed: {item.name}")
                    except (ValueError, IndexError):
                        # Invalid name format, ignore
                        continue
                        
        except Exception as e:
            logger.warning(f"Old sessions cleanup error: {e}")
    
    def get_step_dir(self, step_name: str) -> Path:
        """
        Get or create directory for a pipeline step
        
        Args:
            step_name: Step name (e.g. "trend_analysis", "video_generation")
            
        Returns:
            Path of the step directory
        """
        with self._lock:
            if step_name not in self.step_dirs:
                step_dir = self.session_dir / step_name
                step_dir.mkdir(exist_ok=True)
                self.step_dirs[step_name] = step_dir
                self.created_dirs.append(step_dir)
                
            return self.step_dirs[step_name]
    
    def create_temp_file(self, 
                        step_name: str, 
                        filename: str, 
                        extension: str = "",
                        unique: bool = True) -> Path:
        """
        Create temporary file for a step
        
        Args:
            step_name: Step name
            filename: Base filename
            extension: Extension (with or without dot)
            unique: Add unique suffix to avoid collisions
            
        Returns:
            Path of temporary file
        """
        step_dir = self.get_step_dir(step_name)
        
        # Normalize extension
        if extension and not extension.startswith('.'):
            extension = f".{extension}"
        
        # Generate unique name if requested
        if unique:
            unique_suffix = f"_{uuid.uuid4().hex[:8]}"
            base_name = filename + unique_suffix
        else:
            base_name = filename
        
        file_path = step_dir / (base_name + extension)
        
        # Track the file
        with self._lock:
            self.created_files.append(file_path)
        
        logger.debug(f"Temporary file created: {file_path}")
        return file_path
    
    def create_frame_sequence_dir(self, step_name: str = "video_generation") -> Path:
        """Create directory for frame sequence"""
        frame_dir = self.get_step_dir(step_name) / "frames"
        frame_dir.mkdir(exist_ok=True)
        return frame_dir
    
    def create_audio_file(self, step_name: str = "audio_generation", 
                         format: str = "wav") -> Path:
        """Create temporary audio file"""
        return self.create_temp_file(step_name, "audio", f".{format}")
    
    def create_video_file(self, step_name: str, 
                         format: str = "mp4", 
                         quality: str = "temp") -> Path:
        """Create temporary video file"""
        filename = f"video_{quality}"
        return self.create_temp_file(step_name, filename, f".{format}")
    
    def create_config_file(self, step_name: str, config_name: str) -> Path:
        """Create temporary config file"""
        return self.create_temp_file(step_name, config_name, ".json")
    
    def create_cache_file(self, step_name: str, cache_key: str) -> Path:
        """Create temporary cache file"""
        return self.create_temp_file(step_name, f"cache_{cache_key}", ".pkl")
    
    def get_size_mb(self) -> float:
        """Calculate total size of temporary files in MB"""
        total_size = 0
        
        for file_path in self.created_files:
            if file_path.exists():
                total_size += file_path.stat().st_size
        
        return total_size / (1024 * 1024)
    
    def list_files(self, step_name: Optional[str] = None) -> List[Path]:
        """
        List created files
        
        Args:
            step_name: Filter by step (None = all)
            
        Returns:
            List of files
        """
        if step_name is None:
            return self.created_files.copy()
        
        step_dir = self.step_dirs.get(step_name)
        if not step_dir:
            return []
        
        return [f for f in self.created_files if str(f).startswith(str(step_dir))]
    
    def cleanup_step(self, step_name: str) -> None:
        """Clean files from a specific step"""
        step_files = self.list_files(step_name)
        
        for file_path in step_files:
            try:
                if file_path.exists():
                    if file_path.is_file():
                        file_path.unlink()
                    elif file_path.is_dir():
                        shutil.rmtree(file_path)
                    
                # Remove from tracking list
                with self._lock:
                    if file_path in self.created_files:
                        self.created_files.remove(file_path)
                        
            except Exception as e:
                logger.warning(f"Error deleting {file_path}: {e}")
        
        # Remove step directory if empty
        step_dir = self.step_dirs.get(step_name)
        if step_dir and step_dir.exists():
            try:
                if not any(step_dir.iterdir()):
                    step_dir.rmdir()
                    with self._lock:
                        if step_dir in self.created_dirs:
                            self.created_dirs.remove(step_dir)
                        del self.step_dirs[step_name]
            except:
                pass
        
        logger.debug(f"Step cleanup '{step_name}' completed")
    
    def cleanup_all(self, force: bool = False) -> None:
        """
        Clean all temporary files
        
        Args:
            force: Force cleanup even if keep_on_error=True and errors occurred
        """
        if self.cleanup_done:
            return
        
        # Check if we should keep files on error
        if self.has_errors and self.keep_on_error and not force:
            logger.info("Temporary files preserved for debugging (errors detected)")
            return
        
        try:
            size_mb = self.get_size_mb()
            file_count = len(self.created_files)
            
            # Delete all tracked files
            for file_path in self.created_files.copy():
                try:
                    if file_path.exists():
                        if file_path.is_file():
                            file_path.unlink()
                        elif file_path.is_dir():
                            shutil.rmtree(file_path)
                except Exception as e:
                    logger.warning(f"Error deleting {file_path}: {e}")
            
            # Delete session directory
            if self.session_dir.exists():
                shutil.rmtree(self.session_dir, ignore_errors=True)
            
            self.cleanup_done = True
            logger.info(f"Cleanup completed: {file_count} files, {size_mb:.1f} MB freed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def mark_error(self) -> None:
        """Mark that an error occurred (for keep_on_error)"""
        self.has_errors = True
        logger.debug("Error marked - temporary files will be preserved")
    
    def get_stats(self) -> Dict[str, Any]:
        """Return statistics about temporary files"""
        total_files = len(self.created_files)
        total_size_mb = self.get_size_mb()
        
        step_stats = {}
        for step_name in self.step_dirs:
            step_files = self.list_files(step_name)
            step_size = sum(f.stat().st_size for f in step_files if f.exists()) / (1024 * 1024)
            step_stats[step_name] = {
                "files": len(step_files),
                "size_mb": round(step_size, 2)
            }
        
        return {
            "session_id": self.session_id,
            "total_files": total_files,
            "total_size_mb": round(total_size_mb, 2),
            "has_errors": self.has_errors,
            "cleanup_done": self.cleanup_done,
            "steps": step_stats
        }
    
    # Context manager for use with 'with'
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Mark error if exception
        if exc_type is not None:
            self.mark_error()
        
        # Clean if auto_cleanup enabled
        if self.auto_cleanup:
            self.cleanup_all()
    
    def __del__(self):
        """Final cleanup on object destruction"""
        if not self.cleanup_done and self.auto_cleanup:
            self.cleanup_all()


# ===== SPECIALIZED CONTEXT MANAGERS =====

@contextmanager
def temp_video_processing(base_dir: str = "temp"):
    """Context manager for temporary video processing"""
    manager = TempFileManager(base_dir, auto_cleanup=True)
    try:
        yield manager
    except Exception as e:
        manager.mark_error()
        raise
    finally:
        if not manager.has_errors:
            manager.cleanup_all()

@contextmanager
def temp_pipeline_step(step_name: str, base_dir: str = "temp"):
    """Context manager for a pipeline step"""
    manager = TempFileManager(base_dir, auto_cleanup=False)
    try:
        step_dir = manager.get_step_dir(step_name)
        yield manager, step_dir
    except Exception as e:
        manager.mark_error()
        raise
    finally:
        # Clean only this step
        manager.cleanup_step(step_name)


# ===== UTILITIES =====

def cleanup_all_temp_files(base_dir: str = "temp", max_age_hours: int = 1) -> None:
    """Utility to clean all old temporary files"""
    base_path = Path(base_dir)
    if not base_path.exists():
        return
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    cleaned_count = 0
    cleaned_size = 0
    
    try:
        for item in base_path.iterdir():
            if item.is_dir() and item.name.startswith("session_"):
                try:
                    # Check age via timestamp in name
                    timestamp_str = item.name.split("_")[1]
                    timestamp = int(timestamp_str)
                    
                    if current_time - timestamp > max_age_seconds:
                        # Calculate size before deletion
                        size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                        cleaned_size += size
                        
                        shutil.rmtree(item, ignore_errors=True)
                        cleaned_count += 1
                        
                except (ValueError, IndexError, OSError):
                    continue
        
        if cleaned_count > 0:
            size_mb = cleaned_size / (1024 * 1024)
            logger.info(f"Global cleanup: {cleaned_count} sessions, {size_mb:.1f} MB freed")
            
    except Exception as e:
        logger.warning(f"Global cleanup error: {e}")