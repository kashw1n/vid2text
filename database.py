from datetime import datetime
from sqlite_utils import Database
from sqlite_utils.db import NotFoundError
from model import VideoInfo, VIDEO_TABLE_SCHEMA

class VideoDatabase:
    def __init__(self, db_path: str = "knowledge.db") -> None:
        self.db = Database(db_path)
        self.initialize_db()

    def initialize_db(self) -> None:
        self.db['videos'].create(VIDEO_TABLE_SCHEMA, pk="id", if_not_exists=True)

    def is_video_present(self, video_id: str) -> bool:
        try:
            self.db["videos"].get(video_id)
            return True
        except NotFoundError:
            return False

    def insert_video(self, video_info: VideoInfo) -> None:
        self.db["videos"].insert({
            "run_date": datetime.now().isoformat(),
            "id": video_info.id,
            "title": video_info.title,
            "content": video_info.content,
            "creator": video_info.creator,
            "source": video_info.source,
            "upload_date": video_info.upload_date
        })
