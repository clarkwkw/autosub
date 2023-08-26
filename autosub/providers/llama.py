import re
from typing import List, cast
from llama_cpp import CreateCompletionResponse, Llama

from autosub.models.language import Language
from autosub.models.translation_context import TranslationContext
from autosub.providers.base.translator import Translator


MODEL_MAX_TOKEN = 4096
BUFFER_TOKEN = 20
MIN_INPUT_TOKEN_REQUIRED = 100
INDEX_PATTERN = re.compile(r'^\d+:\s*')


class LLAMA(Translator):
    def __init__(
        self,
        *,
        model: str,
    ):
        self._llm = Llama(model_path=model, n_ctx=MODEL_MAX_TOKEN)

    def _count_token(self, texts: List[str]) -> int:
        return sum((len(self._llm.tokenize(text.encode('utf-8'))) for text in texts))

    def _batch_by_token_count(self, max_tokens: int, texts: List[str], max_items_per_batch: int) -> List[List[str]]:
        batches: List[List[str]] = []
        current_batch: List[str] = []
        current_tokens: int = 0
        if max_items_per_batch < 1:
            raise Exception(f"max_items_per_batch must be at least 1, got {max_items_per_batch}")
        for text in texts:
            text_tokens = self._count_token([text])
            if text_tokens > max_tokens:
                raise RuntimeError(f"Input '{text}' ({text_tokens} tokens) longer than {max_tokens}")
            if text_tokens + current_tokens > max_tokens or len(current_batch) + 1 > max_items_per_batch:
                batches.append(current_batch)
                current_tokens = 0
                current_batch = []
            current_batch.append(text)
            current_tokens += text_tokens
        batches.append(current_batch)
        return batches

    def translate(
        self,
        input: List[str],
        source_language: Language,
        target_language: Language,
        input_description: str | None = None,
        context: TranslationContext | None = None
    ) -> List[str]:
        pretranslated_prompt = ""
        if context is not None:
            if len(context.phrases):
                pretranslated_prompt += (
                    "Below is a list of phrases with existing translation. Follow them if mentioned. "
                    f"If a phrase is not in the list, make up a suitable name in {target_language.name}.\n"
                )
                pretranslated_prompt += '\n'.join([f"{phrase.foreign}: {phrase.local}" for phrase in context.phrases])
        result: List[str] = []
        for line in input:
            full_context = (
                f"Repeat the {source_language.name} sentence in {target_language.name} and terminate immediately.\n"
                f"{pretranslated_prompt}\n\n"
                f"{source_language.name}: {line}\n"
                f"{target_language.name}: "
            )
            raw_response = cast(
                CreateCompletionResponse,
                self._llm(full_context, max_tokens=0, stop=[source_language.name + ":", target_language.name + ":", "\n"])
            )
            result.append(raw_response['choices'][0]['text'].strip())
        return result
