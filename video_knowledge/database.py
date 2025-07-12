"""Database module for video knowledge storage."""

from datetime import datetime
from sqlite_utils import Database
from sqlite_utils.db import NotFoundError
from pydantic import BaseModel
from typing import Optional


class VideoInfo(BaseModel):
    """Pydantic model for video information."""
    id: str
    title: str
    lesson: Optional[str] = ''
    content: Optional[str] = ''
    creator: Optional[str] = ''
    source: Optional[str] = ''
    upload_date: Optional[str] = ''


# Database schema for videos table
VIDEO_TABLE_SCHEMA = {
    "run_date": str,
    "id": str,
    "title": str,
    "lesson": str,
    "content": str,
    "creator": str,
    "source": str,
    "upload_date": str
}


class VideoDatabase:
    """Database interface for storing and retrieving video information."""

    def __init__(self, db_path: str) -> None:
        """Initialize the database connection and create tables if needed."""
        self.db = Database(db_path)
        self.initialize_db()

    def initialize_db(self) -> None:
        """Create the videos table if it doesn't exist."""
        self.db['videos'].create(VIDEO_TABLE_SCHEMA, pk="id", if_not_exists=True)

    def is_video_present(self, video_id: str) -> bool:
        """Check if a video already exists in the database."""
        try:
            self.db["videos"].get(video_id)
            return True
        except NotFoundError:
            return False

    def insert_video(self, video_info: VideoInfo) -> None:
        """Insert a new video record into the database."""
        self.db["videos"].insert({
            "run_date": datetime.now().isoformat(),
            "id": video_info.id,
            "title": video_info.title,
            "content": video_info.content,
            "creator": video_info.creator,
            "source": video_info.source,
            "upload_date": video_info.upload_date
        })
