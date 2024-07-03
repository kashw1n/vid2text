import os
from typing import List, Tuple
import hashlib
from .base_processor import BaseProcessor
from src.database.database import VideoDatabase
from src.database.model import VideoInfo
from src.utils.transcription import Transcriber
import logging

class M3U8Processor(BaseProcessor):
    def get_video_locations(self, input_file: str) -> List[Tuple[str, str, int]]:
        with open(input_file, 'r') as file:
            lines = file.read().splitlines()
        
        video_locations = []
        for index, line in enumerate(lines, start=1):
            if line.strip().endswith('.m3u8'):
                title = os.path.basename(input_file).replace('m3u8-', '').replace('.txt', '')
                video_locations.append((line.strip(), title, index))
        
        return video_locations

    def process_video(self, location_info: Tuple[str, str, int], db: VideoDatabase) -> None:
        location, title, order = location_info
        logging.info(f'Starting to process m3u8: {location}')
        video_id = hashlib.sha256(location.encode()).hexdigest()[:11]

        if db.is_video_present(video_id):
            logging.info(f'Video with ID {video_id} already processed.')
            return

        try:
            audio_file = Transcriber.load_audio(location)
            transcription = Transcriber.transcribe_audio(audio_file)

            video_info = VideoInfo(
                id=video_id,
                title=f"{title} - {order}",
                content=transcription,
                creator='Unknown',
                source=location
            )

            db.insert_video(video_info)
            logging.info(f'M3U8 stream {video_id} processed and inserted into database.')
        except Exception as e:
            logging.error(f"Error processing m3u8 stream {location}: {e}")
            raise