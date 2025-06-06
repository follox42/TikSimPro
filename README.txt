# TikSimPro - Viral TikTok Content Generator

> **Automated physics simulation video generator for TikTok with built-in publishing capabilities**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Active](https://img.shields.io/badge/Status-Active-green.svg)]()

## 🎯 What is TikSimPro?

TikSimPro is a modular Python system that automatically generates engaging physics simulation videos optimized for TikTok. It creates visually satisfying content like bouncing balls, rotating circles, and other physics-based animations that perform well on social media.

### ✨ Key Features

- **🎨 Physics Simulations**: Generate satisfying visual content with realistic physics
- **🤖 Automated Publishing**: Direct integration with TikTok, YouTube, and Instagram
- **📊 Trend Analysis**: Built-in trend detection for optimal content timing
- **🎵 Audio Generation**: Synchronized sound effects and music
- **⚡ High Performance**: GPU acceleration and optimized rendering
- **🔧 Modular Architecture**: Plugin-based system for easy customization

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- FFmpeg (for video processing)
- Chrome/Chromium (for social media publishing)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/follox42/tiksimpro.git
   cd tiksimpro
   ```

2. **Install dependencies**
   ```bash
   python setup.py
   ```

3. **Initialize configuration**
   ```bash
   python main.py --init
   ```

### Basic Usage

Generate a video with default settings:
```bash
python main.py
```

Generate and auto-publish:
```bash
python main.py --publish
```

Custom parameters:
```bash
python main.py --duration 45 --resolution 1080:1920 --config config_circle.json
```

## 📋 Command Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--config` | `-c` | Configuration file path |
| `--output` | `-o` | Output directory |
| `--duration` | `-d` | Video duration (seconds) |
| `--resolution` | `-r` | Video resolution (width:height) |
| `--publish` | `-p` | Auto-publish to platforms |
| `--init` | `-i` | Create default config |

## 🏗️ Project Structure

```
tiksimpro/
├── core/                  # Core interfaces and utilities
│   ├── interfaces.py        # Abstract base classes
│   ├── config.py            # Configuration manager
│   └── plugin_manager.py    # Plugin system
├── video_generators/      # Video generation modules
├── audio_generators/      # Audio synthesis
├── video_enhancers/
├── media_combiner/        # Combining audio and video    
├── publishers/            # Social media publishers
├── pipeline/              # Processing pipeline
├── config.json            # Default configuration
└── main.py                # Entry point
```

## ⚙️ Configuration

The system uses JSON configuration files. Key sections:

### Video Generator Example
```json
{
  "video_generator": {
    "name": "CircleSimulator",
    "params": {
      "width": 1080,
      "height": 1920,
      "fps": 60,
      "duration": 30,
      "balls": 1,
      "gravity": 500
    }
  }
}
```

### Publishing Example
```json
{
  "publishers": {
    "tiktok": {
      "name": "TikTokPublisher",
      "params": {
        "auto_close": true,
        "headless": false
      },
      "enabled": true
    }
  }
}
```

## 🎬 Simulation Types

### Circle Simulator
Creates rotating circle patterns with physics-based ball interactions.

**Features:**
- Configurable ring count and spacing
- Dynamic gap detection
- Realistic gravity and elasticity
- Custom color palettes

### Infinite Circle Simulator
Advanced version with shrinking circles and escape mechanics.

**Features:**
- Progressive difficulty
- Victory conditions
- Particle effects
- Performance optimization

## 🤖 Social Media Integration

### TikTok Publishing
- Automated login and session management
- Video upload with captions and hashtags
- Publishing confirmation detection

### YouTube
- Cross-platform publishing support
- Platform-specific optimization
- Automated scheduling

### Instagram
> 🔨 **Under Construction**  
> This project is actively being developed. Some features may be incomplete.

## 🛠️ Development

### Adding New Simulators

1. Create a new class implementing `IVideoGenerator`
2. Place it in the `video_generators/` directory
3. Update your configuration to use the new generator

```python
from core.interfaces import IVideoGenerator

class MySimulator(IVideoGenerator):
    def generate(self, trend_data: TrendData) -> str:
        # Your implementation here
        pass
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📊 Performance

- **Generation Speed**: ~30 seconds for 60-second video
- **Resolution Support**: Up to 4K (optimized for mobile)
- **GPU Acceleration**: CUDA support for faster rendering
- **Memory Usage**: ~2GB RAM for typical videos

## 🔧 Troubleshooting

### Common Issues

**FFmpeg not found:**
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
choco install ffmpeg
```

**Browser automation fails:**
- Ensure Chrome/Chromium is installed
- Check if webdriver permissions are correct
- Try running in non-headless mode first

**Video generation slow:**
- Enable GPU acceleration in config
- Reduce video resolution for testing
- Close other resource-intensive applications

## 📈 Roadmap

- [ ] Instagram Reels optimization
- [ ] Advanced trend analysis with ML ans scraping
- [ ] Advanced physics engines

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/follox42/tiksimpro/issues)
- **Discussions**: [GitHub Discussions](https://github.com/follox42/tiksimpro/discussions)
- **Email**: your.email@example.com

## 📚 Acknowledgments

- Built with Python and love ❤️
- Physics simulation powered by Pygame
- Video processing with MoviePy
- Automation with Selenium

## ⚠️ Disclaimer
*Users are responsible for complying with social media platform 
terms of service. This software generates content only."*
---