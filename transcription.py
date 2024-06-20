import os
import subprocess
import random
import string
import mlx_whisper

class Transcriber:
    @staticmethod
    def generate_random_string(length: int) -> str:
        letters = string.ascii_lowercase + string.digits
        return ''.join(random.choice(letters) for _ in range(length))

    @staticmethod
    def load_audio(location: str) -> str:
        audio_file = f"{Transcriber.generate_random_string(7)}.wav"
        if location.startswith("http://") or location.startswith("https://"):
            command = [
                "yt-dlp",
                "-x",
                "--audio-format", "wav",
                "--postprocessor-args", "-ar 16000",
                location,
                "-o", audio_file
            ]
        else:
            command = [
                "ffmpeg",
                "-i", location,
                "-ar", "16000",
                "-ac", "1",
                "-f", "wav",
                audio_file
            ]
        subprocess.run(command, capture_output=True, text=True)
        return audio_file

    @staticmethod
    def transcribe_audio(audio_file: str) -> str:
        result = mlx_whisper.transcribe(audio_file, path_or_hf_repo='mlx-community/whisper-medium.en-mlx')
        transcription = result["text"]
        os.remove(audio_file)
        return transcription
