from typing import Optional
from pydantic import BaseModel

class VideoInfo(BaseModel):
    id: str
    title: str
    lesson: Optional[str] = ''
    content: Optional[str] = ''
    creator: Optional[str] = ''
    source: Optional[str] = ''
    upload_date: Optional[str] = ''

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
