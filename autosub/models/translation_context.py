from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from autosub.models.phrase_localisation import PhraseLocalisation


@dataclass
class TranslationContext:
    synopsis: Optional[str]
    phrases: List[PhraseLocalisation]

    @classmethod
    def from_dict(cls, data: dict):
        return TranslationContext(
            synopsis=data['synopsis'],
            phrases=[PhraseLocalisation.from_dict(phrase_data) for phrase_data in data['phrases']]
        )


class AbstractTranslationContextTransformer(ABC):
    def prepare_context(self) -> TranslationContext:
        return TranslationContext(
            synopsis=self.prepare_synopsis(),
            phrases=self.prepare_phrases(),
        )

    @abstractmethod
    def prepare_synopsis(self) -> Optional[str]:
        ...

    @abstractmethod
    def prepare_phrases(self) -> List[PhraseLocalisation]:
        ...
