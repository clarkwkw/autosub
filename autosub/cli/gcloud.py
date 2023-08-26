from argparse import ArgumentParser
import textwrap

from autosub.providers.gcloud import GoogleCloud
from autosub.utils import get_env_var


class GCloudCommandMixin:
    ENV_VAR_SERVICE_ACCOUNT_FILE = 'AUTOSUB_GC_SERVICE_ACCOUNT_FILE'
    ENV_VAR_PROJECT_ID = 'AUTOSUB_GC_PROJECT_ID'
    ENV_VAR_LOCATION_ID = 'AUTOSUB_GC_LOCATION_ID'
    ENV_VAR_GLOSSARY_BUCKET = 'AUTOSUB_GC_GLOSSARY_BUCKET'
    ENV_VAR_AUDIO_BUCKET = 'AUTOSUB_GC_AUDIO_BUCKET'

    @property
    def provider(self) -> str:
        return 'gcloud'

    def configure_subparser(self, subparser: ArgumentParser):
        subparser.epilog = textwrap.dedent(f"""\
            Following environment variables need to be set:
                {self.ENV_VAR_SERVICE_ACCOUNT_FILE} - Google Cloud account file
                {self.ENV_VAR_PROJECT_ID} - Google Cloud project id
                {self.ENV_VAR_LOCATION_ID} - Google Cloud location id
                {self.ENV_VAR_GLOSSARY_BUCKET} - Bucket to store gloassary information for transcription
                {self.ENV_VAR_AUDIO_BUCKET} - Bucket to store audio file for transcription
        """)

    def create_client(self):
        return GoogleCloud(
            service_account_file_path=get_env_var(self.ENV_VAR_SERVICE_ACCOUNT_FILE),
            project_id=get_env_var(self.ENV_VAR_PROJECT_ID),
            location_id=get_env_var(self.ENV_VAR_LOCATION_ID),
            glossary_bucket=get_env_var(self.ENV_VAR_GLOSSARY_BUCKET),
            audio_bucket=get_env_var(self.ENV_VAR_AUDIO_BUCKET),
        )
