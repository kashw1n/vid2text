from .base_processor import BaseProcessor
from src.database.database import VideoDatabase
from src.database.model import VideoInfo
from src.utils.transcription import Transcriber
from typing import List
import logging
import os
import hashlib

class LocalProcessor(BaseProcessor):
    def get_video_locations(self, input_file: str) -> List[str]:
        video_paths = []
        with open(input_file, 'r') as file:
            lines = file.read().splitlines()
        for line in lines:
            if os.path.isfile(line) and line.endswith(('.mp4', '.avi', '.mov', '.mkv')):
                video_paths.append(os.path.abspath(line))
            elif os.path.isdir(line):
                for root, _, files in os.walk(line):
                    for file in files:
                        if file.endswith(('.mp4', '.avi', '.mov', '.mkv')):
                            video_paths.append(os.path.join(root, file))
        return video_paths

    def process_video(self, location: str, db: VideoDatabase) -> None:
        logging.info(f'Starting to process video: {location}')
        with open(location, 'rb') as f:
            file_content = f.read()
        video_id = hashlib.sha256(file_content).hexdigest()[:11]

        if db.is_video_present(video_id):
            logging.info(f'Video with ID {video_id} already processed.')
            return

        print("LOCATION IS", location)
        audio_file = Transcriber.load_audio(location)
        print("AUDIO FILE IS ", audio_file)
        transcription = Transcriber.transcribe_audio(audio_file)

        video_info = VideoInfo(
            id=video_id,
            title=os.path.basename(location),
            content=transcription,
            creator=os.path.basename(os.path.dirname(location)),
            source='Local'
        )

        db.insert_video(video_info)
        logging.info(f'Video {video_id} processed and inserted into database.')