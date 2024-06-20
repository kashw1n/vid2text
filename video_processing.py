from abc import ABC, abstractmethod
import os
import re
import hashlib
import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
from transcription import Transcriber
from database import VideoDatabase
from model import VideoInfo
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class VideoProcessor(ABC):
    @abstractmethod
    def get_video_location(self, input_file: str) -> List[str]:
        pass

    @abstractmethod
    def process_video(self, location: str, db: VideoDatabase) -> None:
        pass

class YouTubeVideoProcessor(VideoProcessor):
    def get_video_location(self, input_file: str) -> List[str]:
        logging.info(f'Reading video URLs from {input_file}')
        with open(input_file, 'r') as file:
            urls = file.read().splitlines()
        logging.info(f'Found {len(urls)} URLs')
        return urls

    def process_video(self, location: str, db: VideoDatabase) -> None:
        logging.info(f'Starting to process video: {location}')
        video_id = location.split('=')[1]
        if db.is_video_present(video_id):
            logging.info(f'Video {video_id} already present in database. Skipping.')
            return
        video_info = self.extract_video_details(location)
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
    def extract_video_details(url: str) -> VideoInfo:
        logging.info(f'Extracting video details from URL: {url}')
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
        logging.info(f'Fetching transcript for video {video_id}')
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            logging.info(f'Transcript fetched for video {video_id}')
            return ' '.join([entry['text'] for entry in transcript])
        except Exception as e:
            logging.error(f'Error fetching transcript for video {video_id}: {e}')
            return None

class LocalVideoProcessor(VideoProcessor):
    def get_video_location(self, input_file: str) -> List[str]:
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

        audio_file = Transcriber.load_audio(location)

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
