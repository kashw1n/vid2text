# vid2text

CLI tool for extracting searchable transcriptions from YouTube videos, local files, and M3U8 streams using local Whisper models.

## Features
- **Multi-source**: YouTube, local videos (.mp4, .avi, .mov, .mkv, .m4v), M3U8 streams
- **Local transcription**: MLX Whisper (macOS) or OpenAI Whisper (cross-platform)
- **SQLite storage**: Searchable database with Datasette web interface
- **Batch processing**: YAML configuration for multiple videos

## Quick Start

```bash
# Install
pip install -e .

# Process videos
vid2text youtube "https://youtu.be/dQw4w9WgXcQ"
vid2text local "/path/to/video.mp4"
vid2text process config.yaml

# View results
vid2text stats
vid2text view  # Web interface (requires: pip install datasette)
```

## Installation

**Prerequisites:** Python 3.9+, FFmpeg

### Install FFmpeg
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

### Install vid2text
```bash
pip install vid2text
```

## Usage

### Single Videos
```bash
vid2text youtube "https://youtu.be/VIDEO_ID"
vid2text local "/path/to/video.mp4"
vid2text m3u8 "https://example.com/stream.m3u8"

# With options
vid2text --model small.en --verbose youtube "https://youtu.be/..."
vid2text --dry-run local video.mp4  # Preview only
```

### Batch Processing
Create `config.yaml`:
```yaml
videos:
  youtube:
    - url: "https://youtu.be/dQw4w9WgXcQ"
    - url: "https://youtu.be/jNQXAC9IVRw"
      title: "Custom Title"  # Optional
  local:
    - path: "/path/to/video.mp4"
    - path: "/path/to/folder/"  # Process all videos in folder
      title: "Folder Videos"
  m3u8:
    - url: "https://example.com/video.m3u8"
      title: "Live Stream"
      order: 1

settings:  # Optional
  whisper_model: "small.en"  # Override default model
  log_level: "DEBUG"
```

Process:
```bash
vid2text process config.yaml
vid2text --dry-run process config.yaml  # Preview
```

### Database Operations
```bash
vid2text stats                           # Show video count
vid2text --db-path custom.db stats       # Custom database
vid2text view                            # Launch web interface
vid2text view --port 8080                # Custom port
```

## Configuration

### Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `VIDEO_DB_PATH` | `~/.vid2text/knowledge.db` | Database file location |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `TRANSCRIPTION_ENGINE` | Auto-detected | `mlx-whisper` or `openai-whisper` |
| `WHISPER_MODEL` | Auto-selected | Model name (see below) |

### Whisper Models

**macOS (Apple Silicon) - MLX Whisper:**
- `mlx-community/whisper-medium.en-mlx` (default) - Good balance
- `mlx-community/whisper-large-v3-mlx` - Best accuracy, slower
- `mlx-community/whisper-small.en-mlx` - Faster, less accurate

**Cross-platform - OpenAI Whisper:**
- `base.en` (default) - Good balance (~150MB)
- `tiny.en` - Fastest (~40MB)
- `small.en` - Better accuracy (~250MB) 
- `medium.en` - High accuracy (~800MB)
- `large` - Best accuracy (~3GB)

### CLI Options
- `--db-path PATH` - Custom database location
- `--model MODEL` - Override Whisper model
- `--verbose/-v` - Increase logging (use `-vv` for debug)
- `--dry-run` - Preview operations without processing

## Examples

```bash
# Custom model and database
WHISPER_MODEL=small.en vid2text --db-path ./videos.db youtube "https://youtu.be/..."

# Debug processing issues
vid2text -vv local problematic_video.mp4

# Batch process with custom settings
VIDEO_DB_PATH=./project.db LOG_LEVEL=DEBUG vid2text process videos.yaml

# Quick stats check
vid2text stats | grep "Total videos"
```

## Troubleshooting

**FFmpeg not found:**
```bash
# Verify installation
ffmpeg -version
# Add to PATH if needed
```

**Out of memory during transcription:**
- Try smaller Whisper model: `--model tiny.en`
- Close other applications
- Use MLX Whisper on Apple Silicon for better memory efficiency

**Database locked error:**
- Close any open Datasette instances
- Check if another vid2text process is running


## Commands Reference
- `vid2text youtube <url>` - Process YouTube video
- `vid2text local <path>` - Process local video/folder
- `vid2text m3u8 <url>` - Process M3U8 stream
- `vid2text process <config.yaml>` - Batch process from YAML
- `vid2text stats` - Show database statistics
- `vid2text view [--port PORT]` - Launch Datasette web interface

## Development

```bash
git clone https://github.com/yourusername/vid2text.git
cd vid2text
python -m venv venv && source venv/bin/activate
pip install -e ".[test]"

# Run CLI
vid2text --help

# Run tests
pytest
```