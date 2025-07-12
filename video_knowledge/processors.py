"""Video processors for different source types."""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
import os
import hashlib
import logging
import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
import re

from .database import VideoDatabase, VideoInfo
from .transcription import Transcriber


class BaseProcessor(ABC):
    """Abstract base class for all video processors."""

    @abstractmethod
    def get_video_locations(self, input_file: str) -> List[str]:
        """Get list of video locations from input file."""
        pass

    @abstractmethod
    def process_video(self, location: str, db: VideoDatabase) -> None:
        """Process a single video."""
        pass


class YouTubeProcessor(BaseProcessor):
    """Processor for YouTube videos."""

    def get_video_locations(self, input_file: str) -> List[str]:
        """Read YouTube URLs from input file."""
        logging.info(f'Reading video URLs from {input_file}')
        with open(input_file, 'r') as file:
            urls = file.read().splitlines()
        logging.info(f'Found {len(urls)} URLs')
        return urls

    def process_video(self, location: str, db: VideoDatabase) -> None:
        """Process a YouTube video."""
        self.process_video_with_title(location, db)

    def process_video_with_title(self, location: str, db: VideoDatabase, custom_title: str = None) -> None:
        """Process YouTube video with optional custom title."""
        logging.info(f'Starting to process video: {location}')
        video_id = location.split('=')[1]
        if db.is_video_present(video_id):
            logging.info(f'Video {video_id} already present in database. Skipping.')
            return

        video_info = self.extract_video_details(location, custom_title)
        assert video_id == video_info.id

        transcription = self.get_transcript(video_info.id)
        if not transcription:
            logging.info(f'No transcript found for video {video_info.id}. Downloading audio for transcription.')
            audio_file = Transcriber.load_audio(location)
            transcription = Transcriber.transcribe_audio(audio_file)

        video_info.content = transcription
        video_info.source = 'YouTube'
        db.insert_video(video_info)
        logging.info(f'Video {video_info.id} processed and inserted into database.')

    @staticmethod
    def extract_video_details(url: str, custom_title: str = None) -> VideoInfo:
        """Extract video details from YouTube URL."""
        logging.info(f'Extracting video details from URL: {url}')
        if custom_title:
            title = custom_title
            upload_date = ''
            channel_name = ''
        else:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.select_one('meta[itemprop="name"][content]')['content']
            upload_date = soup.select_one('meta[itemprop="datePublished"][content]')['content']
            channel_name = soup.find('link', {'itemprop': 'name'})['content']

        video_id = re.search(r'v=([^&]+)', url).group(1)
        logging.info(f'Extracted details for video {video_id}: title={title}, uploaded_date={upload_date}, channel_name={channel_name}')
        return VideoInfo(id=video_id, title=title, upload_date=upload_date, creator=channel_name)

    @staticmethod
    def get_transcript(video_id: str) -> Optional[str]:
        """Fetch transcript for YouTube video."""
        logging.info(f'Fetching transcript for video {video_id}')
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            logging.info(f'Transcript fetched for video {video_id}')
            return ' '.join([entry['text'] for entry in transcript])
        except Exception as e:
            logging.error(f'Error fetching transcript for video {video_id}: {e}')
            return None


class LocalProcessor(BaseProcessor):
    """Processor for local video files."""

    def get_video_locations(self, input_file: str) -> List[str]:
        """Get local video file paths from input file."""
        video_paths = []
        with open(input_file, 'r') as file:
            lines = file.read().splitlines()

        for line in lines:
            if os.path.isfile(line) and line.endswith(('.mp4', '.avi', '.mov', '.mkv', '.m4v')):
                video_paths.append(os.path.abspath(line))
            elif os.path.isdir(line):
                for root, _, files in os.walk(line):
                    for file in files:
                        if file.endswith(('.mp4', '.avi', '.mov', '.mkv', '.m4v')):
                            video_paths.append(os.path.join(root, file))
        return video_paths

    def process_video(self, location: str, db: VideoDatabase) -> None:
        """Process a local video file."""
        self.process_video_with_title(location, db)

    def process_video_with_title(self, location: str, db: VideoDatabase, custom_title: str = None) -> None:
        """Process local video file with optional custom title."""
        logging.info(f'Starting to process video: {location}')

        with open(location, 'rb') as f:
            file_content = f.read()
        video_id = hashlib.sha256(file_content).hexdigest()[:11]

        if db.is_video_present(video_id):
            logging.info(f'Video with ID {video_id} already processed.')
            return

        audio_file = Transcriber.load_audio(location)
        transcription = Transcriber.transcribe_audio(audio_file)

        title = custom_title if custom_title else os.path.basename(location)
        video_info = VideoInfo(
            id=video_id,
            title=title,
            content=transcription,
            creator=os.path.basename(os.path.dirname(location)),
            source='Local'
        )

        db.insert_video(video_info)
        logging.info(f'Video {video_id} processed and inserted into database.')


class M3U8Processor(BaseProcessor):
    """Processor for M3U8 stream URLs."""

    def get_video_locations(self, input_file: str) -> List[Tuple[str, str, int]]:
        """Get M3U8 URLs from input file with order information."""
        with open(input_file, 'r') as file:
            lines = file.read().splitlines()

        video_locations = []
        for index, line in enumerate(lines, start=1):
            if line.strip().endswith('.m3u8'):
                title = os.path.basename(input_file).replace('m3u8-', '').replace('.txt', '')
                video_locations.append((line.strip(), title, index))

        return video_locations

    def process_video(self, location_info: Tuple[str, str, int], db: VideoDatabase) -> None:
        """Process M3U8 stream information."""
        location, title, order = location_info
        self.process_video_with_title(location, db, title, order)

    def process_video_with_title(self, location: str, db: VideoDatabase, title: str = None, order: int = 1) -> None:
        """Process M3U8 stream with optional custom title and order."""
        logging.info(f'Starting to process m3u8: {location}')
        video_id = hashlib.sha256(location.encode()).hexdigest()[:11]

        if db.is_video_present(video_id):
            logging.info(f'Video with ID {video_id} already processed.')
            return

        try:
            audio_file = Transcriber.load_audio(location)
            transcription = Transcriber.transcribe_audio(audio_file)

            final_title = title if title else f"Stream {order}"

            video_info = VideoInfo(
                id=video_id,
                title=final_title,
                content=transcription,
                creator='Unknown',
                source=location
            )

            db.insert_video(video_info)
            logging.info(f'M3U8 stream {video_id} processed and inserted into database.')
        except Exception as e:
            logging.error(f"Error processing m3u8 stream {location}: {e}")
            raise
