from abc import ABC
from typing import Dict, Optional, MutableSet
from mwparserfromhell.nodes import Template, Heading
from mwparserfromhell.wikicode import Wikicode as WikicodeRaw
from autosub.models.translation_context import AbstractTranslationContextTransformer
from autosub.models.wiki import WikiPage
from autosub.wiki.transport import WikiTransport
from autosub.providers.base.llm import LLM


class WikipageTransformer(AbstractTranslationContextTransformer, ABC):
    def __init__(
        self,
        *,
        wiki_transport: WikiTransport,
        llm_transport: LLM,
        wikipage: WikiPage,
    ):
        self._llm_transport = llm_transport
        self._wikipage = wikipage
        self._wiki_transport = wiki_transport

    def _extract_template_params_as_text_safe(self, node: Template, index: int) -> Optional[str]:
        if index >= len(node.params):
            return None
        param = node.params[index].value
        parsed = param.strip_code().strip()
        if len(parsed) == 0 and len(param.nodes) > 0 and param.nodes[0].name == 'vanchor':
            parsed = self._extract_template_params_as_text_safe(param.nodes[0], 0)
        return parsed

    def _extract_title_from_template(self, wikicode: Template) -> Optional[str]:
        if wikicode.name.lower() not in ('main', 'see', 'further') or len(wikicode.params) == 0:
            return None
        raw = str(wikicode.params[0].value)
        if '{{' in raw:
            raw = raw[0:raw.index('{{')]
        return raw

    def _find_relevant_wikipage(
        self,
        page_criteria_description: str
    ) -> Optional[WikiPage]:
        related_titles: MutableSet[str] = set()
        for wikicode in self._wikipage.wikicodes:
            for wikicode in wikicode.wiki_code_obj.nodes:
                if isinstance(wikicode, Template):
                    parsed_title = self._extract_title_from_template(wikicode)
                    if parsed_title is not None:
                        related_titles.add(parsed_title)

        if len(related_titles) == 0:
            return None

        selected_title = self._llm_transport.select_one_from_list(
            list(related_titles),
            "entries",
            page_criteria_description,
            allow_none=True,
        )
        if selected_title is None:
            return None

        return self._wiki_transport.retrieve_wikipage(selected_title)

    def prepare_synopsis(self) -> Optional[str]:
        heading_to_section: Dict[str, WikicodeRaw] = {}
        for wiki_code in self._wikipage.wikicodes:
            sections = wiki_code.wiki_code_obj.get_sections()
            for section in sections:
                headings = [node for node in section.nodes if isinstance(node, Heading)]
                for heading in headings:
                    heading_to_section[heading.title.strip_code().strip()] = section
        section_heading_overview = self._llm_transport.select_one_from_list(
            list(heading_to_section.keys()),
            "section headings of an encyclopedia entry",
            "synopsis/overview",
            allow_none=False,
        )
        if section_heading_overview is None:
            return None
        return heading_to_section[section_heading_overview].strip_code()
