from abc import ABC, abstractmethod
from typing import Optional, Tuple
from autosub.models.language import Language

from autosub.models.transcription import Transcription
from autosub.models.translation_context import TranslationContext


class Transcriber(ABC):
    @abstractmethod
    def transcribe(self, target_language: Language, audio_file: str, context: Optional[TranslationContext] = None) -> Tuple[Transcription, ...]:
        """Transcribe audio file to text

        Args:
            target_language (Language): target language
            audio_file (str): path to the audio
            context (Optional[TranslationContext], optional): context. Defaults to None.

        Returns:
            Tuple[Transcription, ...]: a tuple of transcriptions
        """
        ...
