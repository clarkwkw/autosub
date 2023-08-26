from dataclasses import dataclass
import string
from typing import Iterable, List
from pysubs2 import SSAFile, SSAEvent
from pysubs2.common import Color as PS2Color

from autosub.models.transcription import Transcription


class Color(PS2Color):
    ...


@dataclass
class SubtitleGroup:
    name: str
    color_hex: str
    margin_bottom: int
    json_path: str

    @property
    def color_rgb(self) -> Color:
        value = self.color_hex.lstrip('#')
        if len(value) != 6 or not all(c in string.hexdigits for c in value):
            raise ValueError(f"color_hex must be a hex string starting with '#', got '{self.color_hex}'")
        return Color(*[int(value[i:i + 2], 16) for i in range(3)])


class SubtitleFile:
    def __init__(self, *, groups: List[SubtitleGroup], prefix_group_name: bool = False):
        self._file = SSAFile()
        self._prefix_group_name = prefix_group_name
        for group in groups:
            style = self._file.styles['Default'].copy()
            style.marginv += group.margin_bottom
            style.primarycolor = group.color_rgb
            style.fontsize = 10
            self._file.styles[group.name] = style

    def add(self, group_name: str, transcription: Transcription):
        self._file.insert(
            len(self._file.events),
            SSAEvent(
                start=int(transcription.time_start.total_seconds() * 1000),
                end=int(transcription.time_end.total_seconds() * 1000),
                text=f"{group_name + ': ' if self._prefix_group_name else ''}{transcription.text}",
                style=group_name
            )
        )

    def add_all(self, group_name: str, transcriptions: Iterable[Transcription]):
        for transcription in transcriptions:
            self.add(group_name, transcription)

    def save(self, file_name: str):
        self._file.save(file_name)
