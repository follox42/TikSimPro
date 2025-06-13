# src/video_generators/base_video_generator.py
"""
Enhanced base class for video generators with built-in recording and utilities
"""

import os
import time
import logging
import pygame
import subprocess
import threading
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple, Callable
from queue import Queue, Full
from pathlib import Path

from src.core.data_pipeline import TrendData, AudioEvent, VideoMetadata

logger = logging.getLogger("TikSimPro")

class IVideoGenerator(ABC):
    """Interface for video generators with built-in recording capabilities"""
    
    def __init__(self, width: int = 1080, height: int = 1920, fps: int = 60, 
                 duration: float = 30.0, output_path: str = "output/video.mp4"):
        # Basic video parameters
        self.width = width
        self.height = height
        self.fps = fps
        self.duration = duration
        self.output_path = output_path
        
        # Recording state
        self.current_frame = 0
        self.total_frames = int(fps * duration)
        self.recording = False
        
        # Pygame setup
        self.screen = None
        self.clock = None
        self.recording_surface = None
        
        # FFmpeg recording
        self.ffmpeg_process = None
        self.frame_queue = None
        self.recording_thread = None
        
        # Metadata and events
        self.audio_events = []
        self.metadata = None
        self.start_time = 0
        
        # Performance tracking
        self.performance_stats = {
            "frames_rendered": 0,
            "average_fps": 0,
            "render_time": 0
        }
    
    def setup_pygame(self, display_scale: float = 0.5) -> bool:
        """Initialize pygame with optional display scaling"""
        try:
            pygame.init()
            display_width = int(self.width * display_scale)
            display_height = int(self.height * display_scale)
            
            self.screen = pygame.display.set_mode((display_width, display_height))
            pygame.display.set_caption(f"{self.__class__.__name__} - TikSimPro")
            
            self.recording_surface = pygame.Surface((self.width, self.height))
            self.clock = pygame.time.Clock()
            
            logger.info(f"Pygame initialized: {self.width}x{self.height} (display: {display_width}x{display_height})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize pygame: {e}")
            return False
    
    def setup_ffmpeg_recording(self, use_gpu: bool = True) -> bool:
        """Setup FFmpeg for direct video recording"""
        try:
            # Find FFmpeg
            ffmpeg_path = self._find_ffmpeg()
            if not ffmpeg_path:
                logger.error("FFmpeg not found")
                return False
            
            # Choose encoder
            if use_gpu:
                encoder, preset = self._get_gpu_encoder()
            else:
                encoder, preset = "libx264", "ultrafast"
            
            # Build FFmpeg command
            cmd = [
                ffmpeg_path, '-y',
                '-f', 'rawvideo', '-vcodec', 'rawvideo',
                '-pix_fmt', 'rgb24', '-s', f'{self.width}x{self.height}',
                '-r', str(self.fps), '-i', '-',
                '-c:v', encoder, '-preset', preset,
                '-pix_fmt', 'yuv420p', self.output_path
            ]
            
            self.ffmpeg_process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            
            # Setup frame queue and thread
            self.frame_queue = Queue(maxsize=100)
            self.recording_thread = threading.Thread(target=self._recording_worker, daemon=True)
            self.recording_thread.start()
            
            logger.info(f"FFmpeg recording setup: {encoder}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup FFmpeg: {e}")
            return False
    
    def _find_ffmpeg(self) -> Optional[str]:
        """Find FFmpeg executable"""
        import shutil
        return shutil.which('ffmpeg') or shutil.which('ffmpeg.exe')
    
    def _get_gpu_encoder(self) -> Tuple[str, str]:
        """Get best available GPU encoder"""
        try:
            result = subprocess.run([self._find_ffmpeg(), '-encoders'], 
                                  capture_output=True, text=True)
            encoders = result.stdout
            
            if 'h264_nvenc' in encoders:
                return 'h264_nvenc', 'p1'
            elif 'h264_amf' in encoders:
                return 'h264_amf', 'balanced'
            elif 'h264_qsv' in encoders:
                return 'h264_qsv', 'medium'
            else:
                return 'libx264', 'ultrafast'
                
        except:
            return 'libx264', 'ultrafast'
    
    def _recording_worker(self):
        """Worker thread for FFmpeg frame feeding"""
        while True:
            frame_data = self.frame_queue.get()
            if frame_data is None:
                break
            try:
                self.ffmpeg_process.stdin.write(frame_data)
            except:
                break
        
        if self.ffmpeg_process.stdin:
            self.ffmpeg_process.stdin.close()
    
    def start_recording(self) -> bool:
        """Start the recording process"""
        if not self.setup_ffmpeg_recording():
            return False
        
        self.recording = True
        self.start_time = time.time()
        self.current_frame = 0
        
        logger.info(f"Recording started: {self.total_frames} frames")
        return True
    
    def record_frame(self, surface: pygame.Surface) -> bool:
        """Record a single frame"""
        if not self.recording:
            return False
        
        try:
            # Convert pygame surface to raw RGB data
            frame_data = pygame.image.tostring(surface, 'RGB')
            
            # Add to queue (non-blocking)
            try:
                self.frame_queue.put_nowait(frame_data)
            except Full:
                # Queue full, drop oldest frame
                try:
                    self.frame_queue.get_nowait()
                    self.frame_queue.put_nowait(frame_data)
                except:
                    pass
            
            self.current_frame += 1
            return True
            
        except Exception as e:
            logger.error(f"Frame recording failed: {e}")
            return False
    
    def stop_recording(self) -> bool:
        """Stop recording and finalize video"""
        if not self.recording:
            return False
        
        self.recording = False
        
        # Signal recording thread to stop
        self.frame_queue.put(None)
        
        # Wait for FFmpeg to finish
        if self.recording_thread:
            self.recording_thread.join(timeout=30)
        
        if self.ffmpeg_process:
            try:
                self.ffmpeg_process.wait(timeout=30)
                return_code = self.ffmpeg_process.returncode
                if return_code == 0:
                    logger.info(f"Recording completed: {self.output_path}")
                    return True
                else:
                    logger.error(f"FFmpeg failed with code: {return_code}")
                    return False
            except subprocess.TimeoutExpired:
                self.ffmpeg_process.kill()
                logger.error("FFmpeg timeout")
                return False
        
        return False
    
    def update_display(self, scale_surface: bool = True):
        """Update the pygame display with optional scaling"""
        if not self.screen or not self.recording_surface:
            return
        
        if scale_surface:
            # Scale recording surface to display size
            scaled = pygame.transform.scale(self.recording_surface, self.screen.get_size())
            self.screen.blit(scaled, (0, 0))
        else:
            self.screen.blit(self.recording_surface, (0, 0))
        
        pygame.display.flip()
    
    def handle_events(self) -> bool:
        """Handle pygame events, return False if quit requested"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_SPACE:
                    # Pause/resume recording
                    self.recording = not self.recording
                    logger.info(f"Recording {'resumed' if self.recording else 'paused'}")
        return True
    
    def add_audio_event(self, event_type: str, position: Tuple[float, float] = None, 
                       params: Dict[str, Any] = None):
        """Add an audio event at current time"""
        current_time = self.current_frame / self.fps
        event = AudioEvent(
            event_type=event_type,
            time=current_time,
            position=position,
            params=params or {}
        )
        self.audio_events.append(event)
    
    def get_progress(self) -> float:
        """Get recording progress (0.0 to 1.0)"""
        if self.total_frames == 0:
            return 0.0
        return min(1.0, self.current_frame / self.total_frames)
    
    def is_finished(self) -> bool:
        """Check if recording is complete"""
        return self.current_frame >= self.total_frames
    
    def update_performance_stats(self):
        """Update performance statistics"""
        if self.start_time > 0:
            elapsed = time.time() - self.start_time
            self.performance_stats["frames_rendered"] = self.current_frame
            self.performance_stats["render_time"] = elapsed
            if elapsed > 0:
                self.performance_stats["average_fps"] = self.current_frame / elapsed
    
    def cleanup(self):
        """Clean up resources"""
        if self.recording:
            self.stop_recording()
        
        if self.screen:
            pygame.quit()
        
        self.update_performance_stats()
        logger.info(f"Cleanup completed. Stats: {self.performance_stats}")
    
    # Abstract methods that subclasses must implement
    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> bool:
        """Configure the generator with specific parameters"""
        pass
    
    @abstractmethod
    def apply_trend_data(self, trend_data: TrendData) -> None:
        """Apply trend data to the generator"""
        pass
    
    @abstractmethod
    def render_frame(self, surface: pygame.Surface, frame_number: int, dt: float) -> bool:
        """Render a single frame to the surface"""
        pass
    
    @abstractmethod
    def initialize_simulation(self) -> bool:
        """Initialize the simulation objects and state"""
        pass
    
    # Default implementations
    def set_output_path(self, path: str) -> None:
        """Set the output path for the video"""
        self.output_path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
    
    def generate(self) -> Optional[str]:
        """Generate the complete video"""
        try:
            # Setup
            if not self.setup_pygame():
                return None
            
            if not self.initialize_simulation():
                return None
            
            if not self.start_recording():
                return None
            
            # Main render loop
            dt = 1.0 / self.fps
            
            while not self.is_finished():
                # Handle events
                if not self.handle_events():
                    break
                
                # Clear surface
                self.recording_surface.fill((0, 0, 0))
                
                # Render frame
                if not self.render_frame(self.recording_surface, self.current_frame, dt):
                    logger.error(f"Frame rendering failed at frame {self.current_frame}")
                    break
                
                # Record frame
                self.record_frame(self.recording_surface)
                
                # Update display
                self.update_display()
                
                # Control frame rate
                self.clock.tick(self.fps)
                
                # Log progress
                if self.current_frame % (self.fps * 5) == 0:  # Every 5 seconds
                    progress = self.get_progress() * 100
                    logger.info(f"Progress: {progress:.1f}% ({self.current_frame}/{self.total_frames})")
            
            # Finalize
            success = self.stop_recording()
            self.cleanup()
            
            if success and os.path.exists(self.output_path):
                return self.output_path
            
            return None
            
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            self.cleanup()
            return None
    
    def get_audio_events(self) -> List[AudioEvent]:
        """Get all audio events"""
        return self.audio_events
    
    def get_metadata(self) -> VideoMetadata:
        """Get video metadata"""
        if not self.metadata:
            self.metadata = VideoMetadata(
                width=self.width,
                height=self.height,
                fps=self.fps,
                duration=self.duration,
                frame_count=self.current_frame,
                file_path=self.output_path,
                creation_timestamp=time.time()
            )
        return self.metadata