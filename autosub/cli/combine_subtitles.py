
from argparse import ArgumentParser, Namespace
import json
import logging

from autosub.models.subtitle import SubtitleFile, SubtitleGroup
from autosub.models.transcription import Transcription


def create_combine_subtitles_parser(subparser: ArgumentParser):
    subparser.add_argument('config')
    subparser.add_argument('output')
    return subparser


def combine_subtitles(args: Namespace):
    logger = logging.getLogger(__name__)

    logger.info('Loading config')
    with open(args.config, 'r', encoding='utf8') as f:
        subtitle_groups_raw = json.load(f)

    logger.info('Constructing combined subtitle file')
    groups = [SubtitleGroup(**raw_dict) for raw_dict in subtitle_groups_raw]
    combined_subtitle_file = SubtitleFile(groups=groups, prefix_group_name=True)
    for group in groups:
        with open(group.json_path, 'r', encoding='utf8') as f:
            subtitle_dict = json.load(f)
            combined_subtitle_file.add_all(group.name, [Transcription.from_dict(transcription_dict) for transcription_dict in subtitle_dict['translated']])

    logger.info('Saving combined subtitle file')
    combined_subtitle_file.save(args.output)
