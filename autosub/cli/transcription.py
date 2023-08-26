from abc import ABC, abstractmethod, abstractproperty
from argparse import ArgumentParser, Namespace

from autosub.cli.gcloud import GCloudCommandMixin
from autosub.providers.base.transcriber import Transcriber
from autosub.providers.whisper import Whisper


class TranscriptionCommand(ABC):
    @abstractproperty
    def provider(self) -> str:
        ...

    @abstractmethod
    def configure_subparser(self, subparser: ArgumentParser):
        ...

    @abstractmethod
    def create_transcriber(self, args: Namespace) -> Transcriber:
        ...


class WhisperTranscriptionCommand(TranscriptionCommand):
    @property
    def provider(self) -> str:
        return 'whisper'

    def configure_subparser(self, subparser: ArgumentParser):
        subparser.add_argument('whisper_model', type=str)

    def create_transcriber(self, args: Namespace) -> Transcriber:
        return Whisper(args.whisper_model)


class GCloudTranscriptionCommand(GCloudCommandMixin, TranscriptionCommand):
    def create_transcriber(self, args: Namespace) -> Transcriber:
        return self.create_client()
