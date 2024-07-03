import sys
from src.processors.youtube_processor import YouTubeProcessor
from src.processors.local_processor import LocalProcessor
from src.processors.m3u8_processor import M3U8Processor
from src.database.database import VideoDatabase
from src.config import DATABASE_PATH, LOG_LEVEL, LOG_FORMAT
import logging

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)

def process_videos(input_file: str, db: VideoDatabase) -> None:
    if input_file.startswith('youtube-'):
        processor = YouTubeProcessor()
    elif input_file.startswith('local-'):
        processor = LocalProcessor()
    elif input_file.startswith('m3u8-'):
        processor = M3U8Processor()
    else:
        raise ValueError("Unsupported video source")

    locations = processor.get_video_locations(input_file)
    for location in locations:
        try:
            processor.process_video(location, db)
        except Exception as e:
            if isinstance(processor, M3U8Processor):
                logging.error(f"Error processing video {location[0]}: {e}")
            else:
                logging.error(f"Error processing video {location}: {e}")

def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python main.py <input_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    db = VideoDatabase(DATABASE_PATH)
    
    if input_file.endswith('.txt'):
        process_videos(input_file, db)
    else:
        print("Input file must be a .txt file")
        sys.exit(1)

if __name__ == "__main__":
    main()