# Video Knowledge Project

This project is designed to process videos from YouTube, local files, and .m3u8 streams, extract their content, and store the information in a database for easy access and analysis.

## Features

- Process YouTube videos, local video files, and .m3u8 streams
- Extract video metadata (title, upload date, creator)
- Transcribe video content using MLX Whisper
- Store video information in a SQLite database
- Configurable logging and transcription model
- Self-contained Python environment with no system dependencies

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/video-knowledge-project.git
   cd video-knowledge-project
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Prepare an input file:
   - For YouTube videos: Create a text file with YouTube URLs, one per line. Name it `youtube-urls.txt`.
   - For local videos: Create a text file with paths to video files or directories, one per line. Name it `local-videos.txt`.
   - For .m3u8 streams: Create a text file with .m3u8 URLs, one per line. Name it `m3u8-streams.txt`.

2. Run the script:
   ```
   python main.py youtube-urls.txt  # For YouTube videos
   python main.py local-videos.txt  # For local videos
   python main.py m3u8-streams.txt  # For .m3u8 streams
   ```

## Configuration

You can configure the application by setting environment variables or modifying the `src/config.py` file. Available options include:

- `VIDEO_DB_PATH`: Path to the SQLite database file (default: `knowledge.db`)
- `LOG_LEVEL`: Logging level (default: `INFO`)
- `LOG_FORMAT`: Format string for logging (default: `'%(asctime)s - %(name)s - %(levelname)s - %(message)s'`)
- `WHISPER_MODEL`: MLX Whisper model to use for transcription (default: `mlx-community/whisper-medium.en-mlx`)

All these configuration options are actively used in the project to control various aspects of the video processing pipeline.

## Project Structure

```
video_knowledge_project/
├── src/
│   ├── processors/
│   │   ├── base_processor.py
│   │   ├── youtube_processor.py
│   │   ├── local_processor.py
│   │   └── m3u8_processor.py
│   ├── utils/
│   │   └── transcription.py
│   ├── database/
│   │   ├── models.py
│   │   └── database.py
│   └── config.py
├── main.py
├── requirements.txt
└── README.md
```