from dataclasses import replace, asdict, is_dataclass
import datetime
import json
import os
import subprocess
from typing import List, Optional, Tuple
from autosub.models.language import Language

from autosub.models.transcription import Transcription
from autosub.models.translation_context import TranslationContext
from autosub.providers.base.translator import Translator


def extract_audio_as_wav(
    path_input: str,
    path_output: str,
):
    subprocess.run(
        [
            'ffmpeg',
            '-i',
            path_input,
            '-ar',
            '16000',
            '-ac',
            '1',
            '-c:a',
            'pcm_s16le',
            '-y',
            path_output,
        ],
        capture_output=True,
        check=True
    )


def prefix_transcriptions(transcriptions: List[Transcription], prefix: str) -> List[Transcription]:
    return [
        replace(transcription, text=prefix + transcription.text)
        for transcription in transcriptions
    ]


def translate_transcriptions(
    *,
    transcriptions: Tuple[Transcription, ...],
    translator: Translator,
    source_language: Language,
    target_language: Language,
    input_description: str,
    context: Optional[TranslationContext]
) -> Tuple[Transcription, ...]:
    translation = translator.translate(
        input=[t.text for t in transcriptions],
        source_language=source_language,
        target_language=target_language,
        input_description=input_description,
        context=context
    )
    return tuple(
        replace(transcriptions[index], text=translated) for (index, translated) in enumerate(translation)
    )


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if is_dataclass(o):
            return asdict(o)
        if isinstance(o, datetime.timedelta):
            return (datetime.datetime.min + o).time().isoformat()
        return super().default(o)


def get_env_var(
    key: str,
    error_message_template: str = "Environment variable {key} is not defined"
) -> str:
    if key not in os.environ:
        raise RuntimeError(error_message_template.format(key=key))
    return os.environ[key]
