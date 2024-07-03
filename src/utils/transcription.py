import os
import random
import string
import mlx_whisper
import ffmpeg
import yt_dlp
from src.config import WHISPER_MODEL
import logging

class Transcriber:
    @staticmethod
    def generate_random_string(length: int) -> str:
        letters = string.ascii_lowercase + string.digits
        return ''.join(random.choice(letters) for _ in range(length))

    @staticmethod
    def load_audio(location: str) -> str:
        base_filename = Transcriber.generate_random_string(7)
        audio_file = f"{base_filename}.wav"
        
        if location.startswith("http://") or location.startswith("https://"):
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
                'outtmpl': base_filename,  # yt-dlp will add the extension
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
        if not os.path.exists(audio_file):
            logging.error(f"Audio file {audio_file} does not exist")
            raise FileNotFoundError(f"Audio file {audio_file} does not exist")

        try:
            logging.info(f"Starting transcription of {audio_file}")
            result = mlx_whisper.transcribe(audio_file, path_or_hf_repo=WHISPER_MODEL)
            transcription = result["text"]
            logging.info("Transcription completed successfully")
            return transcription
        except Exception as e:
            logging.error(f"Error during transcription: {e}")
            raise
        finally:
            if os.path.exists(audio_file):
                os.remove(audio_file)
                logging.info(f"Removed temporary audio file: {audio_file}")