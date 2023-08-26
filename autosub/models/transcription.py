from dataclasses import dataclass
from datetime import date, time, timedelta, datetime
from typing import Optional


@dataclass
class Transcription:
    speaker: Optional[str]
    text: str
    time_start: timedelta
    time_end: timedelta

    @classmethod
    def from_dict(cls, data: dict):
        return Transcription(
            speaker=data.get('speaker', None),
            text=data['text'],
            time_start=datetime.combine(date.min, time.fromisoformat(data['time_start'])) - datetime.min,
            time_end=datetime.combine(date.min, time.fromisoformat(data['time_end'])) - datetime.min,
        )
