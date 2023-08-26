from dataclasses import dataclass
from typing import List, Optional

import mwparserfromhell as mwparser
from mwparserfromhell.wikicode import Wikicode


@dataclass
class WikiCode:
    raw: str
    _wiki_code_obj: Optional[Wikicode] = None

    @property
    def wiki_code_obj(self):
        if self._wiki_code_obj is None:
            self._wiki_code_obj = mwparser.parse(self.raw)
        return self._wiki_code_obj


@dataclass
class WikiPage:
    title: str
    wikicodes: List[WikiCode]
