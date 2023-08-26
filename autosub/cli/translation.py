
from abc import ABC, abstractmethod, abstractproperty
from argparse import ArgumentParser, Namespace
import textwrap
from autosub.cli.gcloud import GCloudCommandMixin

from autosub.providers.base.translator import Translator
from autosub.providers.llama import LLAMA
from autosub.providers.openai import OpenAI
from autosub.utils import get_env_var


class TranslationCommand(ABC):
    @abstractproperty
    def provider(self) -> str:
        ...

    @abstractmethod
    def configure_subparser(self, subparser: ArgumentParser):
        ...

    @abstractmethod
    def create_translator(self, args: Namespace) -> Translator:
        ...


class OpenAITranslationCommand(TranslationCommand):
    ENV_VAR_API_KEY = 'AUTOSUB_OPENAI_API_KEY'

    @property
    def provider(self) -> str:
        return "openai"

    def configure_subparser(self, subparser: ArgumentParser):
        subparser.add_argument('openai_model', help='OpenAI LLM model (e.g. gpt-3.5-turbo)')
        subparser.epilog = textwrap.dedent(f"""\
            Following environment variables need to be set:
                {self.ENV_VAR_API_KEY} - API key for OpenAI
        """)

    def create_client(self, args: Namespace) -> OpenAI:
        return OpenAI(
            api_key=get_env_var(self.ENV_VAR_API_KEY),
            model=args.openai_model
        )

    def create_translator(self, args: Namespace) -> Translator:
        return self.create_client(args)


class GCloudTranslationCommand(GCloudCommandMixin, TranslationCommand):
    def create_translator(self, args: Namespace) -> Translator:
        return self.create_client()


class LLAMATranslationCommand(TranslationCommand):
    @property
    def provider(self) -> str:
        return "llama"

    def configure_subparser(self, subparser: ArgumentParser):
        subparser.add_argument('llama_model', help='Path to LLAMA model gguf file')

    def create_translator(self, args: Namespace) -> Translator:
        return LLAMA(model=args.llama_model)
