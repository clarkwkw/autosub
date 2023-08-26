from dataclasses import dataclass
from enum import Enum


@dataclass
class Language:
    code: str
    gcloud_code: str
    name: str


class Languages(Enum):
    ZH_TW = Language(code='zh-TW', gcloud_code='zh-TW', name='Traditional Chinese')
    EN = Language(code='en', gcloud_code='en', name='English')
    JA = Language(code='ja', gcloud_code='ja-JP', name='Japanese')
