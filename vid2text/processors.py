from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
import os
import hashlib
import logging
import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
import re

from .database import VideoDatabase
from .transcription import Transcriber


class BaseProcessor(ABC):
    @abstractmethod
    def get_video_locations(self, input_file: str) -> List[str]:
        pass

    @abstractmethod
    def process_video(self, location: str, db: VideoDatabase) -> None:
        pass


class YouTubeProcessor(BaseProcessor):
    def get_video_locations(self, input_file: str) -> List[str]:
        logging.info(f'Reading URLs from {input_file}')
        with open(input_file, 'r') as file:
            urls = file.read().splitlines()
        logging.info(f'Found {len(urls)} URLs')
        return urls

    def process_video(self, location: str, db: VideoDatabase) -> None:
        self.process_video_with_title(location, db)

    def process_video_with_title(self, location: str, db: VideoDatabase, custom_title: str = None) -> None:
        logging.info(f'Processing YouTube video: {location}')
        
        if not location or not location.strip():
            raise ValueError("Empty YouTube URL provided")
        
        if not ('youtube.com' in location or 'youtu.be' in location):
            raise ValueError(f"Invalid YouTube URL: {location}")
        
        try:
            video_id = location.split('=')[1] if '=' in location else location.split('/')[-1]
        except (IndexError, AttributeError):
            raise ValueError(f"Could not extract video ID from URL: {location}")
        
        if not video_id:
            raise ValueError(f"Empty video ID extracted from URL: {location}")
        
        if db.is_video_present(video_id):
            logging.info(f'Video {video_id} already exists, skipping')
            return

        video_data = self._extract_video_details(location, custom_title)
        
        transcription = self._get_transcript(video_id)
        if not transcription:
            logging.info(f'No transcript found for {video_id}, downloading audio for transcription')
            audio_file = Transcriber.load_audio(location)
            transcription = Transcriber.transcribe_audio(audio_file)

        video_data.update({
            'content': transcription,
            'source': 'YouTube'
        })
        db.insert_video(video_data)
        logging.info(f'Successfully processed video {video_id}: {video_data["title"]}')

    def _extract_video_details(self, url: str, custom_title: str = None) -> dict:
        video_id = re.search(r'v=([^&]+)', url).group(1)
        logging.info(f'Extracting details for video {video_id}')
        
        if custom_title:
            logging.info(f'Using custom title: {custom_title}')
            return {
                'id': video_id,
                'title': custom_title,
                'upload_date': '',
                'creator': ''
            }
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            title_elem = soup.select_one('meta[itemprop="name"][content]')
            date_elem = soup.select_one('meta[itemprop="datePublished"][content]')
            creator_elem = soup.find('link', {'itemprop': 'name'})
            
            if not title_elem:
                raise ValueError("Could not extract video title from page")
            
            return {
                'id': video_id,
                'title': title_elem['content'],
                'upload_date': date_elem['content'] if date_elem else '',
                'creator': creator_elem['content'] if creator_elem else ''
            }
        except Exception as e:
            logging.error(f'Error extracting video details: {e}')
            raise

    def _get_transcript(self, video_id: str) -> Optional[str]:
        logging.info(f'Fetching transcript for video {video_id}')
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            logging.info(f'Successfully fetched transcript for {video_id}')
            return ' '.join([entry['text'] for entry in transcript])
        except Exception as e:
            logging.warning(f'No transcript available for {video_id}: {e}')
            return None


class LocalProcessor(BaseProcessor):
    VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv', '.m4v')

    def get_video_locations(self, input_file: str) -> List[str]:
        video_paths = []
        with open(input_file, 'r') as file:
            lines = file.read().splitlines()

        for line in lines:
            if os.path.isfile(line) and line.endswith(self.VIDEO_EXTENSIONS):
                video_paths.append(os.path.abspath(line))
            elif os.path.isdir(line):
                for root, _, files in os.walk(line):
                    for file in files:
                        if file.endswith(self.VIDEO_EXTENSIONS):
                            video_paths.append(os.path.join(root, file))
        
        logging.info(f'Found {len(video_paths)} video files')
        return video_paths

    def process_video(self, location: str, db: VideoDatabase) -> None:
        self.process_video_with_title(location, db)

    def process_video_with_title(self, location: str, db: VideoDatabase, custom_title: str = None) -> None:
        logging.info(f'Processing local video: {location}')
        
        if not location or not location.strip():
            raise ValueError("Empty file path provided")
        
        if not os.path.exists(location):
            raise FileNotFoundError(f"Video file not found: {location}")
        
        if not os.path.isfile(location):
            raise ValueError(f"Path is not a file: {location}")
        
        if not location.lower().endswith(self.VIDEO_EXTENSIONS):
            raise ValueError(f"Unsupported video format: {location}")
        
        file_size = os.path.getsize(location)
        if file_size == 0:
            raise ValueError(f"Video file is empty: {location}")
        
        logging.info(f'Processing video file: {location} ({file_size} bytes)')
        
        try:
            with open(location, 'rb') as f:
                video_id = hashlib.sha256(f.read()).hexdigest()[:11]
        except Exception as e:
            raise RuntimeError(f"Failed to read video file {location}: {e}")

        if db.is_video_present(video_id):
            logging.info(f'Video {video_id} already exists, skipping')
            return

        audio_file = Transcriber.load_audio(location)
        transcription = Transcriber.transcribe_audio(audio_file)

        title = custom_title or os.path.basename(location)
        video_data = {
            'id': video_id,
            'title': title,
            'content': transcription,
            'creator': os.path.basename(os.path.dirname(location)),
            'source': 'Local',
            'upload_date': ''
        }
        db.insert_video(video_data)
        logging.info(f'Successfully processed local video {video_id}: {title}')


class M3U8Processor(BaseProcessor):
    def get_video_locations(self, input_file: str) -> List[Tuple[str, str, int]]:
        with open(input_file, 'r') as file:
            lines = file.read().splitlines()

        video_locations = []
        for index, line in enumerate(lines, start=1):
            if line.strip().endswith('.m3u8'):
                title = os.path.basename(input_file).replace('m3u8-', '').replace('.txt', '')
                video_locations.append((line.strip(), title, index))
        
        logging.info(f'Found {len(video_locations)} M3U8 streams')
        return video_locations

    def process_video(self, location_info: Tuple[str, str, int], db: VideoDatabase) -> None:
        location, title, order = location_info
        self.process_video_with_title(location, db, title, order)

    def process_video_with_title(self, location: str, db: VideoDatabase, title: str = None, order: int = 1) -> None:
        logging.info(f'Processing M3U8 stream: {location}')
        video_id = hashlib.sha256(location.encode()).hexdigest()[:11]

        if db.is_video_present(video_id):
            logging.info(f'Stream {video_id} already exists, skipping')
            return

        try:
            audio_file = Transcriber.load_audio(location)
            transcription = Transcriber.transcribe_audio(audio_file)

            final_title = title or f"Stream {order}"
            video_data = {
                'id': video_id,
                'title': final_title,
                'content': transcription,
                'creator': 'Unknown',
                'source': location,
                'upload_date': ''
            }
            db.insert_video(video_data)
            logging.info(f'Successfully processed M3U8 stream {video_id}: {final_title}')
        except Exception as e:
            logging.error(f'Error processing M3U8 stream {location}: {e}')
            raise