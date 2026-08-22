"""Track dataclass — represents a single audio track."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Track:
    title: str
    url: str  # direct audio/stream URL for PyTgCalls
    duration: int = 0  # seconds
    thumbnail: str = ""
    requester_id: int = 0
    requester_name: str = ""
    source: str = "youtube"  # youtube | manual | autoplay
    is_autoplay: bool = False
    added_at: datetime = field(default_factory=datetime.now)

    @property
    def duration_str(self) -> str:
        """Format duration as MM:SS or HH:MM:SS."""
        if self.duration <= 0:
            return "LIVE"
        m, s = divmod(self.duration, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"
