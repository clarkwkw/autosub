import re
from typing import List, Optional
import openai
import tiktoken

from autosub.models.exceptions import UnexpectedResponseException
from autosub.models.language import Language
from autosub.models.translation_context import TranslationContext
from autosub.providers.base.translator import Translator
from autosub.providers.base.llm import LLM


MODEL_MAX_TOKEN = 4096
BUFFER_TOKEN = 20
MIN_INPUT_TOKEN_REQUIRED = 100
INDEX_PATTERN = re.compile(r'^\d+:\s*')


class OpenAI(LLM, Translator):
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
    ):
        self._api_key = api_key
        self._model = model

    def _create_unexpected_response_exception(
        self,
        response: str
    ) -> Exception:
        return UnexpectedResponseException(f"Unexpected response from LLM API '{response}'")

    def _count_token(self, texts: List[str]) -> int:
        encoding = tiktoken.encoding_for_model(self._model)
        return sum((len(encoding.encode(text)) for text in texts))

    def _count_token_in_transcriptions(self, texts: List[str]) -> int:
        encoding = tiktoken.encoding_for_model(self._model)
        return sum((len(encoding.encode(text)) for text in texts))

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

    def select_one_from_list(
        self,
        input: List[str],
        item_description: str,
        criteria_description: str,
        allow_none: bool
    ) -> Optional[str]:
        prompt_context = (
            f"The user is going to provide a list of {item_description}. One item per line. "
            f"Does any of them correspond to {criteria_description}? "
            "Please provide just the index of the most likely item. "
        )

        if allow_none:
            prompt_context += "If none of them looks likely, you can reply 'null'"

        response = openai.ChatCompletion.create(
            api_key=self._api_key,
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": prompt_context,
                },
                {"role": "user", "content": "\n".join([f"{index}. {item}" for (index, item) in enumerate(input)])},
            ]
        )

        raw_response = response['choices'][0]['message']['content']
        match = re.search(r'(\d+)', raw_response)
        if not match:
            raise UnexpectedResponseException(f"LLM gave an unexpected response '{raw_response}'")
        index = int(match.group(1))
        if index < 0 or index >= len(input) or (index is None and not allow_none):
            raise UnexpectedResponseException(f"LLM picked an unexpected index '{index}'")
        return input[index]

    def translate(
        self,
        input: List[str],
        source_language: Language,
        target_language: Language,
        input_description: str | None = None,
        context: TranslationContext | None = None
    ) -> List[str]:
        prompt_context = (
            f"The user is going to provide {input_description}. "
            f"Translate each line to {target_language.name}. "
            "Provide all translations in 1 reply, 1 line per translation. You must translate each line seperately.\n"
        )
        if context is not None:
            if len(context.phrases):
                prompt_context += "Below are some phrases with preexisting translation. Please follow the given translation whenever they show up.\n"
                prompt_context += '\n'.join([f"{phrase.foreign}: {phrase.local}" for phrase in context.phrases])

        result = []
        context_tokens = self._count_token([prompt_context])
        remaining_tokens = MODEL_MAX_TOKEN - BUFFER_TOKEN - context_tokens
        if remaining_tokens <= MIN_INPUT_TOKEN_REQUIRED:
            raise RuntimeError(f"Only {remaining_tokens} remained, not enough for input")
        for batch in self._batch_by_token_count(remaining_tokens, input, 15):
            result.extend(self._translate_one_batch(prompt_context, batch))
        return result

    def _translate_one_batch(self, prompt_context: str, input_batch: List[str]) -> List[str]:
        response = openai.ChatCompletion.create(
            api_key=self._api_key,
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": prompt_context,
                }
            ] + [
                {"role": "user", "content": '\n'.join([f"{index}: {text}" for (index, text) in enumerate(input_batch)])}
            ]
        )
        response_deserialised = [line.strip() for line in response['choices'][0]['message']['content'].split('\n')]
        response_deserialised = [line for line in response_deserialised if len(line) > 0]
        response_deserialised = [re.sub(INDEX_PATTERN, '', line).strip() for line in response_deserialised]
        if len(response_deserialised) != len(input_batch):
            if len(input_batch) > 1:
                return self._translate_one_batch(
                    prompt_context,
                    input_batch[0:len(input_batch)//2]
                ) + self._translate_one_batch(
                    prompt_context,
                    input_batch[len(input_batch)//2:]
                )
            raise UnexpectedResponseException("LLM's did not produce exactly the same number of translation as given input")
        return response_deserialised
