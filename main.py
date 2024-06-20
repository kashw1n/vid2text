import sys
from database import VideoDatabase
from video_processing import YouTubeVideoProcessor, LocalVideoProcessor
from typing import Union

def process_videos(input_file: str, db: VideoDatabase) -> None:
    if input_file.startswith('youtube-'):
        processor = YouTubeVideoProcessor()
    elif input_file.startswith('local-'):
        processor = LocalVideoProcessor()
    else:
        raise ValueError("Unsupported video source")

    urls = processor.get_video_location(input_file)
    for url in urls:
        processor.process_video(url, db)

def main() -> None:
    input_file = sys.argv[1]
    db = VideoDatabase('databases/knowledge.db')
    if input_file.endswith('.txt'):
        process_videos(input_file, db)

if __name__ == "__main__":
    main()