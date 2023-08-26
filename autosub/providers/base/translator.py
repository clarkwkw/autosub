from abc import ABC, abstractmethod
from typing import List, Optional
from autosub.models.language import Language
from autosub.models.translation_context import TranslationContext


class Translator(ABC):
    @abstractmethod
    def translate(
        self,
        input: List[str],
        source_language: Language,
        target_language: Language,
        input_description: Optional[str] = None,
        context: Optional[TranslationContext] = None,
    ) -> List[str]:
        """Translate a list of texts.

        Args:
            input (List[str]): the list
            source_language (Language): language of the original text
            target_language (Language): target language
            input_description (Optional[str], optional): English description of the input, e.g. 'conversation'
            context (Optional[TranslationContext], optional): context for the translation

        Returns:
            List[str]: Translated text
        """
        ...
