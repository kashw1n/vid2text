from abc import ABC, abstractmethod
from typing import List
from src.database.database import VideoDatabase

class BaseProcessor(ABC):
    @abstractmethod
    def get_video_locations(self, input_file: str) -> List[str]:
        pass

    @abstractmethod
    def process_video(self, location: str, db: VideoDatabase) -> None:
        pass