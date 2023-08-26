from datetime import timedelta
from typing import Optional, Tuple
import whisper
from autosub.models.language import Language
from autosub.models.transcription import Transcription
from autosub.models.translation_context import TranslationContext
from autosub.providers.base.transcriber import Transcriber


class Whisper(Transcriber):
    def __init__(self, model: str):
        self._model = whisper.load_model(model, in_memory=True)

    def transcribe(self, target_language: Language, audio_file: str, context: Optional[TranslationContext] = None) -> Tuple[Transcription, ...]:
        phrases: str = ', '.join([phrase.foreign for phrase in context.phrases] if context is not None else [])

        raw_result = self._model.transcribe(
            audio_file,
            fp16=False,
            prompt=phrases if len(phrases) > 0 else None
        )
        return tuple(
            Transcription(
                speaker=None,
                text=segment['text'],
                time_start=timedelta(seconds=segment['start']),
                time_end=timedelta(seconds=segment['end']),
            )
            for segment in raw_result['segments']
        )
