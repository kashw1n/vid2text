"""Audio transcription utilities using MLX or OpenAI Whisper."""

import os
import random
import string
import ffmpeg
import yt_dlp
from .config import WHISPER_MODEL, TRANSCRIPTION_ENGINE
import logging

# Import transcription engines conditionally
try:
    import mlx_whisper
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False
    logging.warning("MLX Whisper not available - falling back to OpenAI Whisper")

try:
    import whisper
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI Whisper not available")

if TRANSCRIPTION_ENGINE == 'mlx-whisper' and not MLX_AVAILABLE:
    logging.warning("MLX Whisper requested but not available, falling back to OpenAI Whisper")
    TRANSCRIPTION_ENGINE = 'openai-whisper'

if TRANSCRIPTION_ENGINE == 'openai-whisper' and not OPENAI_AVAILABLE:
    raise ImportError("Neither MLX nor OpenAI Whisper is available. Please install appropriate dependencies.")


class Transcriber:
    """Audio transcription utilities for video processing."""
    
    @staticmethod
    def generate_random_string(length: int) -> str:
        """Generate a random string for temporary filenames."""
        letters = string.ascii_lowercase + string.digits
        return ''.join(random.choice(letters) for _ in range(length))

    @staticmethod
    def load_audio(location: str) -> str:
        """Load audio from location (URL or local file) and convert to WAV."""
        base_filename = Transcriber.generate_random_string(7)
        audio_file = f"{base_filename}.wav"
        
        if location.startswith("http://") or location.startswith("https://"):
            # Download audio from URL using yt-dlp
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
                'outtmpl': base_filename,
                'quiet': True,
                'no_warnings': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    ydl.download([location])
                    logging.info(f"Successfully downloaded audio to {audio_file}")
                except Exception as e:
                    logging.error(f"Error downloading audio: {e}")
                    raise
        else:
            # Convert local file using ffmpeg
            try:
                stream = ffmpeg.input(location)
                stream = ffmpeg.output(stream, audio_file, ar='16000', ac=1)
                ffmpeg.run(stream, quiet=True, overwrite_output=True, capture_stdout=True, capture_stderr=True)
                logging.info(f"Successfully converted local file to audio: {audio_file}")
            except ffmpeg.Error as e:
                logging.error(f"ffmpeg error: {e.stderr.decode()}")
                raise

        if not os.path.exists(audio_file):
            logging.error(f"Audio file {audio_file} was not created")
            raise FileNotFoundError(f"Audio file {audio_file} was not created")

        return audio_file

    @staticmethod
    def transcribe_audio(audio_file: str) -> str:
        """Transcribe audio file using the configured Whisper engine."""
        if not os.path.exists(audio_file):
            logging.error(f"Audio file {audio_file} does not exist")
            raise FileNotFoundError(f"Audio file {audio_file} does not exist")

        try:
            logging.info(f"Starting transcription of {audio_file} using {TRANSCRIPTION_ENGINE}")
            
            if TRANSCRIPTION_ENGINE == 'mlx-whisper':
                result = mlx_whisper.transcribe(audio_file, path_or_hf_repo=WHISPER_MODEL)
                transcription = result["text"]
                logging.info("MLX Whisper transcription completed successfully")
            else:  # openai-whisper
                model = whisper.load_model(WHISPER_MODEL)
                result = model.transcribe(audio_file)
                transcription = result["text"]
                logging.info("OpenAI Whisper transcription completed successfully")
            
            return transcription
        except Exception as e:
            logging.error(f"Error during transcription with {TRANSCRIPTION_ENGINE}: {e}")
            raise
        finally:
            if os.path.exists(audio_file):
                os.remove(audio_file)
                logging.info(f"Removed temporary audio file: {audio_file}")