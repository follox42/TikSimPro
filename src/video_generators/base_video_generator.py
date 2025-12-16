# src/video_generators/base_video_generator.py
"""
Base class interface for all video generators.
"""

import os
import time
import logging
import pygame
import subprocess
import threading
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple, Callable
from queue import Queue, Full, Empty
from pathlib import Path
import numpy as np

from src.core.data_pipeline import TrendData, AudioEvent, VideoMetadata

logger = logging.getLogger("TikSimPro")

class IVideoGenerator(ABC):
    """Interface for video generators with HIGH PERFORMANCE recording capabilities"""
    
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
        
        # HIGH PERFORMANCE FFmpeg recording
        self.ffmpeg_process = None
        self.frame_queue = None
        self.recording_thread = None
        
        # Performance optimization flags
        self.headless_mode = True  # HEADLESS for maximum FPS
        self.fast_mode = True      # Skip frame rate limiting
        self.buffer_size = 60      # Much bigger buffer for smoother encoding
        self.use_numpy = True      # Fast array operations
        
        # Metadata and events
        self.audio_events = []
        self.metadata = None
        self.start_time = 0
        
        self.center = (width // 2, height // 2)
        
        # === CORRECTION ICI ===
        if not pygame.font.get_init():
            pygame.font.init()
            
        # Création de la police (Taille 60, gras)
        # On utilise une police système par défaut pour éviter les erreurs de fichier manquant
        self.font = pygame.font.SysFont("arial", 60, bold=True)

        # Performance tracking
        self.performance_stats = {
            "frames_rendered": 0,
            "average_fps": 0,
            "render_time": 0,
            "encoding_fps": 0
        }
    
    def setup_pygame(self, display_scale: float = 0.3) -> bool:
        """Initialize pygame with PERFORMANCE optimizations"""
        try:
            os.environ["SDL_AUDIODRIVER"] = "dummy"
            
            # Si tu es sur un serveur sans écran, ceci évite aussi les erreurs d'affichage
            if self.headless_mode:
                os.environ["SDL_VIDEODRIVER"] = "dummy"
            
            pygame.init()

            # === CORRECTION ICI ===
            if not pygame.font.get_init():
                pygame.font.init()
                
            # Création de la police (Taille 60, gras)
            # On utilise une police système par défaut pour éviter les erreurs de fichier manquant
            self.font = pygame.font.SysFont("arial", 60, bold=True)
            
            # Optimize pygame for performance
            pygame.mixer.quit()  # Disable audio mixer
            pygame.font.quit()   # Disable fonts initially
            
            if not self.headless_mode:
                # Smaller display for better performance
                display_width = int(self.width * display_scale)
                display_height = int(self.height * display_scale)
                self.screen = pygame.display.set_mode((display_width, display_height))
                pygame.display.set_caption(f"{self.__class__.__name__} - TikSimPro [FAST MODE]")
            
            # Recording surface - this is where the magic happens
            self.recording_surface = pygame.Surface((self.width, self.height))
            self.clock = pygame.time.Clock()
            
            logger.info(f"Pygame PERFORMANCE mode initialized: {self.width}x{self.height}")
            logger.info(f"Headless mode: {self.headless_mode}, Fast mode: {self.fast_mode}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize pygame: {e}")
            return False
    
    def setup_ffmpeg_recording(self, use_gpu: bool = True) -> bool:
        """Setup HIGH PERFORMANCE FFmpeg recording"""
        try:
            # Find FFmpeg
            ffmpeg_path = self._find_ffmpeg()
            if not ffmpeg_path:
                logger.error("FFmpeg not found")
                return False
            
            # Get the BEST encoder available
            encoder, preset, extra_args = self._get_best_encoder(False)  # Stable CPU encoder
            
            # Build OPTIMIZED FFmpeg command
            cmd = [
                ffmpeg_path, '-y',
                
                # Input settings - optimized for speed
                '-f', 'rawvideo', '-vcodec', 'rawvideo',
                '-pix_fmt', 'rgb24', '-s', f'{self.width}x{self.height}',
                '-r', str(self.fps), '-i', '-',
                
                # Output settings - optimized for speed
                '-c:v', encoder,
                '-preset', preset,
                '-pix_fmt', 'yuv420p',
                
                # Performance optimizations
                '-threads', '0',  # Use all CPU cores
                '-bf', '0',       # No B-frames for speed
                '-g', str(self.fps),  # GOP size = fps
                
            ] + extra_args + [self.output_path]
            
            logger.info(f"FFmpeg command: {' '.join(cmd)}")
            
            # Start FFmpeg process with optimized buffer
            self.ffmpeg_process = subprocess.Popen(
                cmd, 
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                bufsize=1024*1024  # 1MB buffer
            )
            
            # Verify FFmpeg started properly
            if self.ffmpeg_process.poll() is not None:
                logger.error("FFmpeg failed to start")
                return False
            
            # Setup HIGH PERFORMANCE frame queue and thread
            self.frame_queue = Queue(maxsize=self.buffer_size)
            self.recording_thread = threading.Thread(
                target=self._high_performance_recording_worker, 
                daemon=True,
                name="FastFFmpegWriter"
            )
            self.recording_thread.start()
            
            logger.info(f"HIGH PERFORMANCE FFmpeg setup: {encoder} with {preset}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup FFmpeg: {e}")
            return False
    
    def _find_ffmpeg(self) -> Optional[str]:
        """Find FFmpeg executable"""
        import shutil
        return shutil.which('ffmpeg') or shutil.which('ffmpeg.exe')
    
    def _get_best_encoder(self, use_gpu: bool = False) -> Tuple[str, str, List[str]]:
        """Get BEST available encoder for maximum speed"""
        try:
            result = subprocess.run([self._find_ffmpeg(), '-encoders'], 
                                  capture_output=True, text=True, timeout=5)
            encoders = result.stdout
            
            if use_gpu:
                # NVIDIA (best performance) - ULTRA FAST settings
                if 'h264_nvenc' in encoders:
                    return 'h264_nvenc', 'llhq', [
                        '-b:v', '2000k',      # Even lower bitrate for stability
                        '-maxrate', '3000k',  # Lower max bitrate
                        '-bufsize', '4000k',  # Even smaller buffer
                        '-rc', 'cbr',         # Constant bitrate
                        '-rc-lookahead', '0', # No lookahead for speed
                        '-2pass', '0',        # Disable 2-pass for speed
                    ]
                
                # AMD - ULTRA FAST settings
                elif 'h264_amf' in encoders:
                    return 'h264_amf', 'speed', [
                        '-b:v', '3000k',
                        '-maxrate', '4000k',
                        '-rc', 'cbr',
                        '-quality', 'speed',
                        '-usage', 'ultralowlatency',
                    ]
                
                # Intel QuickSync - ULTRA FAST settings
                elif 'h264_qsv' in encoders:
                    return 'h264_qsv', 'veryfast', [
                        '-b:v', '3000k',
                        '-maxrate', '4000k',
                        '-look_ahead', '0',
                        '-low_power', '1',
                    ]
            
            # Fallback to CPU with MAXIMUM speed settings
            return 'libx264', 'superfast', [
                '-crf', '18',           # Even lower quality for max speed
                '-tune', 'zerolatency', # Zero latency
                '-x264-params', 'ref=1:me=dia:subme=1:analyse=none:trellis=0:no-cabac:aq-mode=0:scenecut=0',
            ]
                
        except Exception as e:
            logger.warning(f"Encoder detection failed: {e}")
            return 'libx264', 'ultrafast', ['-crf', '28']
    
    def _high_performance_recording_worker(self):
        """HIGH PERFORMANCE worker thread for FFmpeg frame feeding"""
        frames_written = 0
        start_time = time.time()
        
        try:
            while True:
                try:
                    # Get frame with short timeout to avoid blocking
                    frame_data = self.frame_queue.get(timeout=1.0)
                    if frame_data is None:
                        break
                    
                    # Check if FFmpeg process is still alive
                    if self.ffmpeg_process.poll() is not None:
                        logger.error("FFmpeg process died unexpectedly")
                        break
                    
                    # Write frame to FFmpeg as fast as possible
                    self.ffmpeg_process.stdin.write(frame_data)
                    self.ffmpeg_process.stdin.flush()  # Force flush each frame
                    frames_written += 1
                    
                    # Update encoding FPS every 60 frames
                    if frames_written % 60 == 0:
                        elapsed = time.time() - start_time
                        if elapsed > 0:
                            encoding_fps = frames_written / elapsed
                            self.performance_stats["encoding_fps"] = encoding_fps
                            if frames_written % 300 == 0:  # Log every 300 frames
                                logger.debug(f"Encoding FPS: {encoding_fps:.1f}")
                    
                except Empty:
                    # Timeout - check if we should continue
                    if not self.recording:
                        break
                    continue
                except Exception as e:
                    logger.error(f"Frame writing error: {e}")
                    break
        
        finally:
            if self.ffmpeg_process and self.ffmpeg_process.stdin:
                try:
                    if not self.ffmpeg_process.stdin.closed:
                        self.ffmpeg_process.stdin.flush()
                        self.ffmpeg_process.stdin.close()
                except:
                    pass
            
            final_fps = frames_written / (time.time() - start_time) if time.time() > start_time else 0
            logger.info(f"Recording worker finished: {frames_written} frames, {final_fps:.1f} encoding FPS")
    
    def start_recording(self) -> bool:
        """Start HIGH PERFORMANCE recording"""
        if not self.setup_ffmpeg_recording():
            return False
        
        self.recording = True
        self.start_time = time.time()
        self.current_frame = 0
        
        logger.info(f"HIGH PERFORMANCE recording started: {self.total_frames} frames")
        logger.info(f"Target: {self.fps} FPS, Duration: {self.duration}s")
        return True
    
    def record_frame(self, surface: pygame.Surface) -> bool:
        """Record frame with MAXIMUM SPEED optimizations"""
        if not self.recording:
            return False
        
        try:
            if self.use_numpy:
                # ULTRA FAST numpy conversion
                frame_array = pygame.surfarray.array3d(surface)
                # Transpose for correct orientation (pygame uses (width, height, channels))
                frame_array = np.transpose(frame_array, (1, 0, 2))
                # Convert to bytes
                frame_data = frame_array.astype(np.uint8).tobytes()
            else:
                # Standard pygame conversion (slower)
                frame_data = pygame.image.tostring(surface, 'RGB')
            
            # Add to queue NON-BLOCKING for maximum speed
            try:
                self.frame_queue.put_nowait(frame_data)
            except Full:
                # Queue full - FORCE space by dropping oldest frame
                try:
                    self.frame_queue.get_nowait()  # Drop oldest
                    self.frame_queue.put_nowait(frame_data)  # Add new
                except Empty:
                    pass  # Queue became empty, just continue
            
            self.current_frame += 1
            return True
            
        except Exception as e:
            logger.error(f"Frame recording failed: {e}")
            return False
    
    def stop_recording(self) -> bool:
        """Stop recording with proper cleanup"""
        if not self.recording:
            return False
        
        self.recording = False
        logger.info("Stopping recording and finalizing video...")
        
        # Signal recording thread to stop
        try:
            self.frame_queue.put(None, timeout=5.0)
        except Full:
            logger.warning("Queue full when trying to signal stop")
        
        # Wait for recording thread with reasonable timeout
        if self.recording_thread:
            self.recording_thread.join(timeout=60)
            if self.recording_thread.is_alive():
                logger.warning("Recording thread did not finish in time")
        
        # Wait for FFmpeg to finish
        if self.ffmpeg_process:
            try:
                # Close stdin first to signal end of input
                if self.ffmpeg_process.stdin and not self.ffmpeg_process.stdin.closed:
                    self.ffmpeg_process.stdin.close()
                
                stdout, stderr = self.ffmpeg_process.communicate(timeout=60)
                return_code = self.ffmpeg_process.returncode
                
                # Add delay for file system
                time.sleep(0.5)
                
                if return_code == 0:
                    file_size = os.path.getsize(self.output_path) / (1024*1024) if os.path.exists(self.output_path) else 0
                    logger.info(f"Recording completed successfully: {self.output_path} ({file_size:.1f} MB)")
                    return True
                else:
                    logger.error(f"FFmpeg failed with return code: {return_code}")
                    if stderr:
                        logger.error(f"FFmpeg stderr: {stderr.decode()}")
                    return False
                    
            except subprocess.TimeoutExpired:
                logger.error("FFmpeg timeout - killing process")
                self.ffmpeg_process.kill()
                return False
        
        return False
    
    def update_display(self, scale_surface: bool = True):
        """Update display ONLY if not in headless mode"""
        if self.headless_mode or not self.screen or not self.recording_surface:
            return  # Skip display updates for MAXIMUM SPEED
        
        if scale_surface:
            scaled = pygame.transform.scale(self.recording_surface, self.screen.get_size())
            self.screen.blit(scaled, (0, 0))
        else:
            self.screen.blit(self.recording_surface, (0, 0))
        
        pygame.display.flip()
    
    def handle_events(self) -> bool:
        """Handle events EFFICIENTLY"""
        if self.headless_mode:
            return True  # Skip event handling for MAXIMUM SPEED
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_SPACE:
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
        stats = self.performance_stats
        logger.info(f"Final performance stats:")
        logger.info(f"  Frames rendered: {stats['frames_rendered']}")
        logger.info(f"  Average render FPS: {stats['average_fps']:.1f}")
        logger.info(f"  Encoding FPS: {stats['encoding_fps']:.1f}")
        logger.info(f"  Total time: {stats['render_time']:.1f}s")
    
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
        directory = os.path.dirname(path)
        # Only try to create directories if a directory path is actually provided
        if directory:
            os.makedirs(directory, exist_ok=True)
    
    def set_performance_mode(self, headless: bool = True, fast: bool = True, use_numpy: bool = True):
        """Configure performance settings"""
        self.headless_mode = headless
        self.fast_mode = fast
        self.use_numpy = use_numpy
        logger.info(f"Performance mode: headless={headless}, fast={fast}, numpy={use_numpy}")
    
    def generate(self) -> Optional[str]:
        """Generate the complete video with MAXIMUM PERFORMANCE"""
        try:
            logger.info("Starting HIGH PERFORMANCE video generation...")
            
            # Setup with performance optimizations
            if not self.setup_pygame():
                return None
            
            if not self.initialize_simulation():
                return None
            
            if not self.start_recording():
                return None
            
            # HIGH SPEED render loop
            dt = 1.0 / self.fps
            last_progress_time = time.time()
            
            while not self.is_finished():
                # Handle events ONLY if not headless
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
                
                # Update display ONLY if not headless
                if not self.headless_mode:
                    self.update_display()
                
                # Frame rate control ONLY if not in fast mode
                if not self.fast_mode:
                    self.clock.tick(self.fps)
                
                # Progress logging (reduced frequency for performance)
                current_time = time.time()
                if current_time - last_progress_time >= 5.0:  # Every 5 seconds
                    progress = self.get_progress() * 100
                    self.update_performance_stats()
                    render_fps = self.performance_stats["average_fps"]
                    encoding_fps = self.performance_stats["encoding_fps"]
                    
                    logger.info(f"Progress: {progress:.1f}% ({self.current_frame}/{self.total_frames}) | "
                              f"Render: {render_fps:.1f} FPS | Encoding: {encoding_fps:.1f} FPS")
                    last_progress_time = current_time
            
            # Finalize
            logger.info("Finalizing video...")
            success = self.stop_recording()
            
            # Cleanup
            self.cleanup()
            
            # Check if video was actually created despite errors
            if os.path.exists(self.output_path):
                file_size = os.path.getsize(self.output_path) / (1024*1024)
                if file_size > 0.1:  # File has content
                    logger.info(f"Video generated successfully: {self.output_path} ({file_size:.1f} MB)")
                    return self.output_path
                else:
                    logger.error(f"Video file is empty: {self.output_path}")
            
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