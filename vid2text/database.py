from datetime import datetime
from sqlite_utils import Database
from sqlite_utils.db import NotFoundError
import logging


class VideoDatabase:
    def __init__(self, db_path: str):
        try:
            self.db = Database(db_path)
            self._initialize_schema()
            logging.info(f'Database initialized at: {db_path}')
        except Exception as e:
            logging.error(f'Failed to initialize database at {db_path}: {e}')
            raise

    def _initialize_schema(self):
        try:
            self.db['videos'].create({
                "run_date": str,
                "id": str,
                "title": str,
                "lesson": str,
                "content": str,
                "creator": str,
                "source": str,
                "upload_date": str
            }, pk="id", if_not_exists=True)
            logging.debug('Database schema initialized')
        except Exception as e:
            logging.error(f'Failed to create database schema: {e}')
            raise

    def is_video_present(self, video_id: str) -> bool:
        if not video_id or not video_id.strip():
            logging.warning('Empty video_id provided to is_video_present')
            return False
        
        try:
            self.db["videos"].get(video_id)
            return True
        except NotFoundError:
            return False
        except Exception as e:
            logging.error(f'Error checking if video {video_id} exists: {e}')
            raise

    def insert_video(self, video_data: dict):
        required_fields = ['id', 'title', 'content']
        missing_fields = [field for field in required_fields if not video_data.get(field)]
        
        if missing_fields:
            error_msg = f'Missing required fields: {missing_fields}'
            logging.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            record = {
                "run_date": datetime.now().isoformat(),
                "id": video_data['id'],
                "title": video_data['title'],
                "lesson": video_data.get('lesson', ''),
                "content": video_data['content'],
                "creator": video_data.get('creator', ''),
                "source": video_data.get('source', ''),
                "upload_date": video_data.get('upload_date', '')
            }
            self.db["videos"].insert(record)
            logging.info(f'Successfully inserted video {video_data["id"]}: {video_data["title"]}')
        except Exception as e:
            logging.error(f'Failed to insert video {video_data.get("id", "unknown")}: {e}')
            raise