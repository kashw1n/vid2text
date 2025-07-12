import os
import platform
from pathlib import Path

# Database
DEFAULT_DATA_DIR = Path.home() / '.video-knowledge'
DEFAULT_DATA_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_DB_PATH = DEFAULT_DATA_DIR / 'knowledge.db'
DATABASE_PATH = os.environ.get('VIDEO_DB_PATH', str(DEFAULT_DB_PATH))

# Logging
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Transcription Engine Selection
# Options: 'mlx-whisper' (macOS Apple Silicon), 'openai-whisper' (cross-platform)
TRANSCRIPTION_ENGINE = os.environ.get('TRANSCRIPTION_ENGINE', 'mlx-whisper' if platform.system() == 'Darwin' else 'openai-whisper')

# Model configuration
if TRANSCRIPTION_ENGINE == 'openai-whisper':
    # OpenAI Whisper models (English-only models for better performance)
    WHISPER_MODEL = os.environ.get('WHISPER_MODEL', 'base.en')
    # Available: 'tiny.en', 'base.en', 'small.en', 'medium.en', 'large'
else:
    # MLX Whisper models (macOS Apple Silicon optimized)
    WHISPER_MODEL = os.environ.get('WHISPER_MODEL', 'mlx-community/whisper-medium.en-mlx')