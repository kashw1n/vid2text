import os
import platform
from pathlib import Path

DEFAULT_DATA_DIR = Path.home() / '.vid2text'
DEFAULT_DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_PATH = os.environ.get('VIDEO_DB_PATH', str(DEFAULT_DATA_DIR / 'knowledge.db'))
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

TRANSCRIPTION_ENGINE = os.environ.get('TRANSCRIPTION_ENGINE', 
    'mlx-whisper' if platform.system() == 'Darwin' else 'openai-whisper')

WHISPER_MODEL = os.environ.get('WHISPER_MODEL', 
    'mlx-community/whisper-medium.en-mlx' if TRANSCRIPTION_ENGINE == 'mlx-whisper' else 'base.en')