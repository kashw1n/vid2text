import os
import random
import string
import ffmpeg
import yt_dlp
from .config import WHISPER_MODEL, TRANSCRIPTION_ENGINE
import logging

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
    raise ImportError("No Whisper engine available. Please install mlx-whisper or openai-whisper")


class Transcriber:
    @staticmethod
    def load_audio(location: str) -> str:
        audio_file = f"{''.join(random.choices(string.ascii_lowercase + string.digits, k=7))}.wav"
        logging.info(f'Loading audio from: {location}')
        
        if location.startswith(("http://", "https://")):
            logging.info(f'Downloading audio from URL to {audio_file}')
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
                'outtmpl': audio_file[:-4],
                'quiet': True,
                'no_warnings': True,
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([location])
                logging.info(f'Successfully downloaded audio to {audio_file}')
            except Exception as e:
                logging.error(f'Error downloading audio from {location}: {e}')
                raise
        else:
            logging.info(f'Converting local file {location} to audio')
            try:
                stream = ffmpeg.input(location)
                stream = ffmpeg.output(stream, audio_file, ar='16000', ac=1)
                ffmpeg.run(stream, quiet=True, overwrite_output=True, capture_stdout=True, capture_stderr=True)
                logging.info(f'Successfully converted local file to audio: {audio_file}')
            except ffmpeg.Error as e:
                stderr_output = e.stderr.decode() if e.stderr else 'Unknown FFmpeg error'
                logging.error(f'FFmpeg error converting {location}: {stderr_output}')
                raise RuntimeError(f'Failed to convert video to audio: {stderr_output}')

        if not os.path.exists(audio_file):
            error_msg = f"Audio file {audio_file} was not created"
            logging.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        file_size = os.path.getsize(audio_file)
        logging.info(f'Audio file created: {audio_file} ({file_size} bytes)')
        return audio_file

    @staticmethod
    def transcribe_audio(audio_file: str) -> str:
        if not os.path.exists(audio_file):
            error_msg = f"Audio file {audio_file} does not exist"
            logging.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        
        logging.info(f'Starting transcription of {audio_file} using {TRANSCRIPTION_ENGINE} with model {WHISPER_MODEL}')
        
        try:
            if TRANSCRIPTION_ENGINE == 'mlx-whisper':
                result = mlx_whisper.transcribe(audio_file, path_or_hf_repo=WHISPER_MODEL)
                logging.info(f'MLX Whisper transcription completed successfully')
            else:
                model = whisper.load_model(WHISPER_MODEL)
                result = model.transcribe(audio_file)
                logging.info(f'OpenAI Whisper transcription completed successfully')
            
            transcription = result["text"]
            logging.info(f'Transcription result: {len(transcription)} characters')
            return transcription
        except Exception as e:
            logging.error(f'Error during transcription with {TRANSCRIPTION_ENGINE}: {e}')
            raise RuntimeError(f'Transcription failed: {e}')
        finally:
            if os.path.exists(audio_file):
                os.remove(audio_file)
                logging.info(f'Removed temporary audio file: {audio_file}')