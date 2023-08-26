import os
from typing import List, Optional, Tuple
from uuid import uuid4
import warnings
from google.cloud import speech
from google.cloud import storage  # type: ignore
from google.cloud import translate_v3

from autosub.models.language import Language
from autosub.models.transcription import Transcription
from autosub.models.translation_context import TranslationContext
from autosub.providers.base.transcriber import Transcriber
from autosub.providers.base.translator import Translator


class GoogleCloud(Transcriber, Translator):
    def __init__(
        self,
        *,
        service_account_file_path: str,
        project_id: str,
        location_id: str,
        glossary_bucket: str,
        audio_bucket: str,
    ):
        self._speech_client = speech.SpeechClient.from_service_account_file(service_account_file_path)
        self._storage_client = storage.Client.from_service_account_json(service_account_file_path)
        self._translation_client = translate_v3.TranslationServiceClient.from_service_account_file(service_account_file_path)
        self._project_id = project_id
        self._location_id = location_id
        self._glossary_bucket = glossary_bucket
        self._audio_bucket = audio_bucket

    def transcribe(self, target_language: Language, audio_file: str, context: Optional[TranslationContext] = None) -> Tuple[Transcription, ...]:
        recognition_config = speech.RecognitionConfig(
            enable_word_time_offsets=True,
            language_code=target_language.gcloud_code,
            model="latest_long",
            speech_contexts=[speech.SpeechContext(
                phrases=[phrase.foreign for phrase in context.phrases]
            )] if context is not None else None
        )
        audio_uploaded_name = str(uuid4()) + os.path.splitext(audio_file)[1]
        self._storage_client.bucket(self._audio_bucket).blob(audio_uploaded_name).upload_from_filename(audio_file)
        result = self._speech_client.long_running_recognize(
            config=recognition_config,
            audio=speech.RecognitionAudio(uri=f"gs://{self._audio_bucket}/{audio_uploaded_name}")
        ).result(timeout=90)

        sanitised: List[Transcription] = []
        for transcripted_sentence in result.results:
            alternative = transcripted_sentence.alternatives[0]
            if len(alternative.words) == 0:
                continue
            sanitised.append(Transcription(
                speaker=None,
                text=alternative.transcript,
                time_start=alternative.words[0].start_time,
                time_end=alternative.words[len(alternative.words) - 1].end_time,
            ))
        try:
            self._storage_client.bucket(self._audio_bucket).delete_blob(audio_uploaded_name)
        except Exception:
            warnings.warn(f"Failed to delete audio audio (file={audio_uploaded_name})")

        return tuple(sanitised)

    def translate(
        self,
        input: List[str],
        source_language: Language,
        target_language: Language,
        input_description: str | None = None,
        context: TranslationContext | None = None
    ) -> List[str]:
        parent = f"projects/{self._project_id}/locations/{self._location_id}"
        glossary_path: str | None = None

        if context is not None and len(context.phrases) > 0:
            glossary_id = 'g' + str(uuid4())
            glossary_path = f"{parent}/glossaries/{glossary_id}"
            glossary_ext = ".tsv"
            self._storage_client.bucket(self._glossary_bucket).blob(glossary_id + glossary_ext).upload_from_string(
                "\n".join([f"{phrase.foreign}\t{phrase.local}" for phrase in context.phrases])
            )
            glossary = translate_v3.Glossary(
                name=glossary_path,
                language_pair=translate_v3.Glossary.LanguageCodePair(source_language_code=source_language.code, target_language_code=target_language.code),
                input_config=translate_v3.GlossaryInputConfig(
                    gcs_source=translate_v3.GcsSource(input_uri=f"gs://{self._glossary_bucket}/{glossary_id}{glossary_ext}")
                ),
            )
            self._translation_client.create_glossary(parent=parent, glossary=glossary).result(timeout=90)

        translation_response = self._translation_client.translate_text(
            request={
                "contents": input,
                "source_language_code": source_language.code,
                "target_language_code": target_language.code,
                "mime_type": "text/plain",
                "parent": parent,
                **(
                    {"glossary_config": translate_v3.TranslateTextGlossaryConfig(glossary=glossary_path)}
                    if glossary_path is not None
                    else {}
                )
            }
        )

        if context is not None and len(context.phrases) > 0:
            try:
                self._translation_client.delete_glossary(name=glossary_path)
                self._storage_client.bucket(self._glossary_bucket).delete_blob(glossary_id + glossary_ext)
            except Exception:
                warnings.warn(f"Failed to delete glossary or its file (glossary={glossary_path}, file={glossary_id + glossary_ext})")
        return [translation.translated_text for translation in translation_response.translations]
