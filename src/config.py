import os

# Database
DATABASE_PATH = os.environ.get('VIDEO_DB_PATH', 'knowledge.db')

# Logging
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Transcription
WHISPER_MODEL = os.environ.get('WHISPER_MODEL', 'mlx-community/whisper-medium.en-mlx')