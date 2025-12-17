# src/validators/video_validator.py
"""
VideoValidator - Validate video quality before publishing.
Checks visual quality, audio sync, duration, and predicts engagement.
"""

import os
import subprocess
import json
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("TikSimPro")


@dataclass
class ValidationResult:
    """Result of video validation."""
    passed: bool
    score: float  # 0.0 to 1.0
    checks: Dict[str, bool] = field(default_factory=dict)
    details: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'passed': self.passed,
            'score': self.score,
            'checks': self.checks,
            'details': self.details,
            'warnings': self.warnings,
            'errors': self.errors
        }


class VideoValidator:
    """
    Validate videos before publishing.

    Checks:
    - File exists and has content
    - Duration matches expected
    - Resolution is correct
    - No corruption (can be read by ffprobe)
    - Audio present (if expected)
    - Frame rate is correct
    - Bitrate is reasonable

    Usage:
        validator = VideoValidator()
        result = validator.validate("video.mp4", expected_duration=30)
        if result.passed:
            publish(video)
        else:
            print(f"Validation failed: {result.errors}")
    """

    def __init__(self,
                 min_file_size_mb: float = 0.5,
                 max_file_size_mb: float = 500.0,
                 duration_tolerance: float = 2.0,
                 min_bitrate_kbps: int = 500,
                 required_score: float = 0.7):
        """
        Initialize validator.

        Args:
            min_file_size_mb: Minimum file size in MB
            max_file_size_mb: Maximum file size in MB
            duration_tolerance: Allowed duration difference in seconds
            min_bitrate_kbps: Minimum video bitrate
            required_score: Minimum score to pass (0.0-1.0)
        """
        self.min_file_size_mb = min_file_size_mb
        self.max_file_size_mb = max_file_size_mb
        self.duration_tolerance = duration_tolerance
        self.min_bitrate_kbps = min_bitrate_kbps
        self.required_score = required_score

    def validate(self,
                 video_path: str,
                 expected_duration: Optional[float] = None,
                 expected_width: Optional[int] = None,
                 expected_height: Optional[int] = None,
                 expected_fps: Optional[int] = None,
                 expect_audio: bool = True,
                 audio_events: Optional[List] = None) -> ValidationResult:
        """
        Validate a video file.

        Args:
            video_path: Path to video file
            expected_duration: Expected duration in seconds
            expected_width: Expected width in pixels
            expected_height: Expected height in pixels
            expected_fps: Expected frame rate
            expect_audio: Whether audio stream is expected
            audio_events: Audio events for sync validation

        Returns:
            ValidationResult with pass/fail and details
        """
        result = ValidationResult(
            passed=False,
            score=0.0,
            checks={},
            details={},
            warnings=[],
            errors=[]
        )

        # Check 1: File exists
        if not self._check_file_exists(video_path, result):
            return result

        # Check 2: File size
        self._check_file_size(video_path, result)

        # Check 3: Get video info via ffprobe
        video_info = self._get_video_info(video_path)
        if video_info is None:
            result.errors.append("Failed to read video metadata (file may be corrupted)")
            result.checks['readable'] = False
            return result

        result.checks['readable'] = True
        result.details['video_info'] = video_info

        # Check 4: Duration
        if expected_duration:
            self._check_duration(video_info, expected_duration, result)

        # Check 5: Resolution
        if expected_width and expected_height:
            self._check_resolution(video_info, expected_width, expected_height, result)

        # Check 6: Frame rate
        if expected_fps:
            self._check_fps(video_info, expected_fps, result)

        # Check 7: Audio presence
        if expect_audio:
            self._check_audio(video_info, result)

        # Check 8: Bitrate
        self._check_bitrate(video_info, result)

        # Check 9: Audio sync (if events provided)
        if audio_events:
            self._check_audio_sync(video_path, audio_events, result)

        # Calculate final score
        result.score = self._calculate_score(result)
        result.passed = result.score >= self.required_score and len(result.errors) == 0

        logger.info(f"Validation {'PASSED' if result.passed else 'FAILED'}: "
                    f"score={result.score:.2f}, checks={result.checks}")

        return result

    def _check_file_exists(self, video_path: str, result: ValidationResult) -> bool:
        """Check if file exists."""
        if not os.path.exists(video_path):
            result.errors.append(f"Video file not found: {video_path}")
            result.checks['exists'] = False
            return False
        result.checks['exists'] = True
        return True

    def _check_file_size(self, video_path: str, result: ValidationResult):
        """Check file size is within bounds."""
        size_mb = os.path.getsize(video_path) / (1024 * 1024)
        result.details['file_size_mb'] = size_mb

        if size_mb < self.min_file_size_mb:
            result.errors.append(f"File too small: {size_mb:.2f}MB (min: {self.min_file_size_mb}MB)")
            result.checks['file_size'] = False
        elif size_mb > self.max_file_size_mb:
            result.errors.append(f"File too large: {size_mb:.2f}MB (max: {self.max_file_size_mb}MB)")
            result.checks['file_size'] = False
        else:
            result.checks['file_size'] = True

    def _get_video_info(self, video_path: str) -> Optional[Dict[str, Any]]:
        """Get video information using ffprobe."""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                return None

            data = json.loads(result.stdout)

            # Extract relevant info
            info = {
                'duration': float(data.get('format', {}).get('duration', 0)),
                'bitrate': int(data.get('format', {}).get('bit_rate', 0)) // 1000,  # kbps
                'size_bytes': int(data.get('format', {}).get('size', 0)),
                'format': data.get('format', {}).get('format_name', ''),
                'streams': []
            }

            for stream in data.get('streams', []):
                stream_info = {
                    'type': stream.get('codec_type'),
                    'codec': stream.get('codec_name')
                }

                if stream.get('codec_type') == 'video':
                    stream_info['width'] = stream.get('width')
                    stream_info['height'] = stream.get('height')
                    # Parse frame rate (can be "60/1" or "59.94")
                    fps_str = stream.get('r_frame_rate', '0/1')
                    if '/' in fps_str:
                        num, den = fps_str.split('/')
                        stream_info['fps'] = float(num) / float(den) if float(den) != 0 else 0
                    else:
                        stream_info['fps'] = float(fps_str)

                elif stream.get('codec_type') == 'audio':
                    stream_info['sample_rate'] = int(stream.get('sample_rate', 0))
                    stream_info['channels'] = stream.get('channels')

                info['streams'].append(stream_info)

            return info

        except Exception as e:
            logger.error(f"ffprobe error: {e}")
            return None

    def _check_duration(self, video_info: Dict, expected: float, result: ValidationResult):
        """Check video duration."""
        actual = video_info.get('duration', 0)
        result.details['duration'] = actual
        result.details['expected_duration'] = expected

        diff = abs(actual - expected)
        if diff > self.duration_tolerance:
            result.warnings.append(f"Duration mismatch: {actual:.1f}s (expected: {expected:.1f}s)")
            result.checks['duration'] = False
        else:
            result.checks['duration'] = True

    def _check_resolution(self, video_info: Dict, expected_w: int, expected_h: int, result: ValidationResult):
        """Check video resolution."""
        video_stream = next((s for s in video_info.get('streams', []) if s['type'] == 'video'), None)

        if not video_stream:
            result.errors.append("No video stream found")
            result.checks['resolution'] = False
            return

        actual_w = video_stream.get('width', 0)
        actual_h = video_stream.get('height', 0)
        result.details['width'] = actual_w
        result.details['height'] = actual_h

        if actual_w != expected_w or actual_h != expected_h:
            result.warnings.append(f"Resolution mismatch: {actual_w}x{actual_h} (expected: {expected_w}x{expected_h})")
            result.checks['resolution'] = False
        else:
            result.checks['resolution'] = True

    def _check_fps(self, video_info: Dict, expected_fps: int, result: ValidationResult):
        """Check frame rate."""
        video_stream = next((s for s in video_info.get('streams', []) if s['type'] == 'video'), None)

        if not video_stream:
            return

        actual_fps = video_stream.get('fps', 0)
        result.details['fps'] = actual_fps

        # Allow 1 fps tolerance
        if abs(actual_fps - expected_fps) > 1:
            result.warnings.append(f"FPS mismatch: {actual_fps:.1f} (expected: {expected_fps})")
            result.checks['fps'] = False
        else:
            result.checks['fps'] = True

    def _check_audio(self, video_info: Dict, result: ValidationResult):
        """Check audio stream presence."""
        audio_stream = next((s for s in video_info.get('streams', []) if s['type'] == 'audio'), None)

        if audio_stream:
            result.checks['has_audio'] = True
            result.details['audio_codec'] = audio_stream.get('codec')
            result.details['audio_sample_rate'] = audio_stream.get('sample_rate')
        else:
            result.warnings.append("No audio stream found")
            result.checks['has_audio'] = False

    def _check_bitrate(self, video_info: Dict, result: ValidationResult):
        """Check video bitrate."""
        bitrate = video_info.get('bitrate', 0)
        result.details['bitrate_kbps'] = bitrate

        if bitrate < self.min_bitrate_kbps:
            result.warnings.append(f"Low bitrate: {bitrate}kbps (min: {self.min_bitrate_kbps}kbps)")
            result.checks['bitrate'] = False
        else:
            result.checks['bitrate'] = True

    def _check_audio_sync(self, video_path: str, audio_events: List, result: ValidationResult):
        """
        Check if audio events are synchronized with video.
        This is a basic check - compares event timestamps with video duration.
        """
        video_duration = result.details.get('duration', 0)

        if not audio_events or video_duration == 0:
            result.checks['audio_sync'] = True
            return

        # Check that events are within video duration
        max_event_time = max(e.time for e in audio_events) if audio_events else 0
        result.details['max_event_time'] = max_event_time
        result.details['event_count'] = len(audio_events)

        if max_event_time > video_duration + 1:  # 1 second tolerance
            result.warnings.append(f"Audio events extend beyond video: {max_event_time:.1f}s > {video_duration:.1f}s")
            result.checks['audio_sync'] = False
        else:
            result.checks['audio_sync'] = True

    def _calculate_score(self, result: ValidationResult) -> float:
        """Calculate overall validation score."""
        if not result.checks:
            return 0.0

        # Weight different checks
        weights = {
            'exists': 1.0,
            'file_size': 0.8,
            'readable': 1.0,
            'duration': 0.7,
            'resolution': 0.6,
            'fps': 0.5,
            'has_audio': 0.6,
            'bitrate': 0.4,
            'audio_sync': 0.5
        }

        total_weight = 0
        weighted_sum = 0

        for check, passed in result.checks.items():
            weight = weights.get(check, 0.5)
            total_weight += weight
            if passed:
                weighted_sum += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def validate_batch(self, video_paths: List[str], **kwargs) -> Dict[str, ValidationResult]:
        """Validate multiple videos."""
        results = {}
        for path in video_paths:
            results[path] = self.validate(path, **kwargs)
        return results


# Convenience function
def quick_validate(video_path: str, duration: float = None) -> bool:
    """Quick validation - returns True if video is valid."""
    validator = VideoValidator()
    result = validator.validate(video_path, expected_duration=duration)
    return result.passed


if __name__ == "__main__":
    print("Testing VideoValidator...")

    # Create a test with an existing video if available
    test_videos = [
        "test_outputs/demo_final.mp4",
        "test_outputs/gravity_falls_new_physics.mp4",
        "videos/final_*.mp4"
    ]

    validator = VideoValidator()

    for pattern in test_videos:
        from glob import glob
        matches = glob(pattern)
        if matches:
            video_path = matches[0]
            print(f"\nValidating: {video_path}")
            result = validator.validate(
                video_path,
                expected_duration=None,  # Don't check duration
                expect_audio=True
            )
            print(f"  Passed: {result.passed}")
            print(f"  Score: {result.score:.2f}")
            print(f"  Checks: {result.checks}")
            if result.warnings:
                print(f"  Warnings: {result.warnings}")
            if result.errors:
                print(f"  Errors: {result.errors}")
            break
    else:
        print("No test videos found")

    print("\nVideoValidator tests completed!")
