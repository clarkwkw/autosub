from argparse import ArgumentParser, Namespace
from dataclasses import asdict, replace
import json
import logging
import os
from typing import Mapping, Optional, Tuple

from autosub.cli.transcription import (
    GCloudTranscriptionCommand,
    TranscriptionCommand,
    WhisperTranscriptionCommand,
)
from autosub.cli.translation import GCloudTranslationCommand, LLAMATranslationCommand, OpenAITranslationCommand, TranslationCommand
from autosub.models.language import Languages
from autosub.models.translation_context import TranslationContext
from autosub.utils import EnhancedJSONEncoder, extract_audio_as_wav, translate_transcriptions


__TRANSCRIPTION_COMMANDS: Tuple[TranscriptionCommand, ...] = (
    WhisperTranscriptionCommand(),
    GCloudTranscriptionCommand(),
)
TRANSCRIPTION_COMMANDS: Mapping[str, TranscriptionCommand] = {
    command.provider: command for command in __TRANSCRIPTION_COMMANDS
}

__TRANSLATION_COMMANDS: Tuple[TranslationCommand, ...] = (
    OpenAITranslationCommand(),
    GCloudTranslationCommand(),
    LLAMATranslationCommand(),
)
TRANSLATION_COMMANDS: Mapping[str, TranslationCommand] = {
    command.provider: command for command in __TRANSLATION_COMMANDS
}


def create_subtitle_parser(subparser: ArgumentParser):
    subparser.add_argument('video', help='path to video file')
    subparser.add_argument('from_language', type=str, choices=[language.name for language in Languages])
    subparser.add_argument('to_language', type=str, choices=[language.name for language in Languages])
    subparser.add_argument('output_file', help='path to json output')
    subparser.add_argument('--context', dest='context', default=None)

    transcription_subparsers = subparser.add_subparsers(dest='transcription_provider', help='Provider for transcription')
    for transcription_provider, transcrption_command in TRANSCRIPTION_COMMANDS.items():
        transcription_subparser = transcription_subparsers.add_parser(transcription_provider)
        transcrption_command.configure_subparser(transcription_subparser)
        translation_subparsers = transcription_subparser.add_subparsers(dest='translation_provider', help='Provider for translation')
        for translation_provider, translation_command in TRANSLATION_COMMANDS.items():
            translation_subparser = translation_subparsers.add_parser(translation_provider)
            translation_command.configure_subparser(translation_subparser)


def load_context(args: Namespace) -> Optional[TranslationContext]:
    if args.context is None:
        return None

    with open(args.context, 'r', encoding='utf8') as f:
        context = TranslationContext.from_dict(json.load(f))
        context = replace(context, phrases=context.phrases[:30])
        return context


def generate_subtitle(args: Namespace):
    logger = logging.getLogger(__name__)
    from_language = Languages[args.from_language]
    to_language = Languages[args.to_language]

    transcription_cmd = TRANSCRIPTION_COMMANDS[args.transcription_provider]
    transcriber = transcription_cmd.create_transcriber(args)
    translation_cmd = TRANSLATION_COMMANDS[args.translation_provider]
    translator = translation_cmd.create_translator(args)
    context = load_context(args)

    logger.info("Extracting audio from the video file")
    audio_path = os.path.splitext(args.video)[0] + '.wav'
    extract_audio_as_wav(args.video, audio_path)

    logger.info("Transcribing audio")
    transcriptions = transcriber.transcribe(from_language.value, audio_path, context=context)

    logger.info("Translating audio")
    translation = translate_transcriptions(
        transcriptions=transcriptions,
        translator=translator,
        source_language=from_language.value,
        target_language=to_language.value,
        input_description='dialogue from a video',
        context=context,
    )

    logger.info(f"Writing to file {args.output_file}")
    with open(args.output_file, 'w', encoding='utf8') as f:
        json.dump(
            {
                'transcriptions': [asdict(t) for t in transcriptions],
                'translated': [asdict(t) for t in translation]
            },
            f,
            cls=EnhancedJSONEncoder,
            indent=4,
            ensure_ascii=False,
        )
