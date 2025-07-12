# Video Knowledge CLI

Process YouTube videos, local files, and M3U8 streams to extract searchable knowledge.

## Features
- **Multi-source**: YouTube, local videos, M3U8 streams
- **Auto-transcription**: MLX Whisper (macOS) or OpenAI Whisper (cross-platform)
- **SQLite storage**: Searchable database in `~/.video-knowledge/knowledge.db`
- **Datasette integration**: Browse data with web GUI

## Quick Start

```bash
# Install
pip install -e .

# Process single video
video-knowledge youtube "https://youtu.be/dQw4w9WgXcQ"

# Batch process from YAML
video-knowledge process videos.yaml

# View in browser (requires datasette)
video-knowledge view
```

## Installation

**Prerequisites:** Python 3.8+, FFmpeg

```bash
git clone https://github.com/yourusername/video-knowledge-project.git
cd video-knowledge-project
python -m venv venv && source venv/bin/activate
pip install -e .

# Install FFmpeg:
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
# Windows: Download from ffmpeg.org
```

## Usage

### Single Videos
```bash
video-knowledge youtube "https://youtu.be/VIDEO_ID"
video-knowledge local "/path/to/video.mp4"
video-knowledge m3u8 "https://example.com/stream.m3u8"
```

### Batch Processing
Create `videos.yaml`:
```yaml
videos:
  youtube:
    - url: "https://youtu.be/dQw4w9WgXcQ"
    - url: "https://youtu.be/jNQXAC9IVRw"
  local:
    - path: "/Users/me/Videos/"
  m3u8:
    - url: "https://example.com/live.m3u8"
      title: "Live Stream"
      order: 1
```

Process it:
```bash
video-knowledge process videos.yaml
video-knowledge --dry-run process videos.yaml  # Preview
```

### Database
```bash
video-knowledge stats                    # View database
video-knowledge --db-path custom.db ...  # Use custom DB
video-knowledge view                     # Datasette GUI (requires: pip install datasette)
```

## Configuration

### Environment Variables
| Variable | Default | Description |
|---|---|---|
| `VIDEO_DB_PATH` | `~/.video-knowledge/knowledge.db` | Database location |
| `LOG_LEVEL` | `INFO` | Logging level |
| `TRANSCRIPTION_ENGINE` | Auto-detected | `mlx-whisper` or `openai-whisper` |
| `WHISPER_MODEL` | Auto-selected | See models below |

### Transcription Models
**macOS (Apple Silicon):**
- Default: `mlx-community/whisper-medium.en-mlx`
- Any MLX-compatible model

**Cross-platform:**
- Default: `base.en`
- Options: `tiny.en`, `base.en`, `small.en`, `medium.en`, `large`

### Examples
```bash
# Custom settings
VIDEO_DB_PATH=my_videos.db LOG_LEVEL=DEBUG video-knowledge process videos.yaml
WHISPER_MODEL=small.en video-knowledge youtube "https://youtu.be/..."
```

### CLI Options
- `--db-path`: Custom database location
- `--model`: Override transcription model
- `--verbose/-v`: Increase logging
- `--dry-run`: Preview without processing

## Commands
- `video-knowledge youtube <url>` - Process YouTube video
- `video-knowledge local <path>` - Process local video
- `video-knowledge m3u8 <url>` - Process M3U8 stream
- `video-knowledge process <config.yaml>` - Batch process
- `video-knowledge stats` - Database summary
- `video-knowledge view` - Datasette GUI