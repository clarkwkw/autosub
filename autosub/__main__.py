from argparse import ArgumentParser
import logging
import warnings

from numba.core.errors import NumbaDeprecationWarning
from autosub.cli.combine_subtitles import combine_subtitles, create_combine_subtitles_parser
from autosub.cli.context import create_context_parser, generate_context

warnings.simplefilter('ignore', category=NumbaDeprecationWarning)
logging.basicConfig(level=logging.INFO)

from autosub.cli.subtitle import create_subtitle_parser, generate_subtitle  # noqa: E402  # deliberately put import after warnings are suppressed


def _create_parser() -> ArgumentParser:
    parser = ArgumentParser()
    action_subparsers = parser.add_subparsers(dest='action')
    subtitle_subparser = action_subparsers.add_parser('subtitle')
    create_subtitle_parser(subtitle_subparser)

    context_subparser = action_subparsers.add_parser('context')
    create_context_parser(context_subparser)

    combine_subparser = action_subparsers.add_parser('combine')
    create_combine_subtitles_parser(combine_subparser)

    return parser


if __name__ == '__main__':
    parser = _create_parser()
    args = parser.parse_args()
    if args.action == 'subtitle':
        generate_subtitle(args)
    elif args.action == 'context':
        generate_context(args)
    elif args.action == 'combine':
        combine_subtitles(args)
