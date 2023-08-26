from typing import List
from mwparserfromhell.nodes import Template
from autosub.models.phrase_localisation import PhraseLocalisation
from autosub.wiki.context_transformer.wikipage_transformer import WikipageTransformer


class JPCreativeWorkWikipageTransformer(WikipageTransformer):
    def _extract_phrases_single_page(self, wikipage) -> List[PhraseLocalisation]:
        result = []
        for wikicode in wikipage.wikicodes:
            for node in wikicode.wiki_code_obj.nodes:
                if isinstance(node, Template) and node.name.lower().startswith('nihongo') and len(node.params) > 1:
                    foreign = self._extract_template_params_as_text_safe(node, 1)
                    local = self._extract_template_params_as_text_safe(node, 0)
                    if foreign is not None and local is not None:
                        localisation = PhraseLocalisation(
                            foreign=foreign,
                            local=local
                        )
                        if localisation.is_valid:
                            result.append(localisation)
        return result

    def prepare_phrases(self) -> List[PhraseLocalisation]:
        character_list_page = self._find_relevant_wikipage("character list")
        if character_list_page is not None:
            return self._extract_phrases_single_page(character_list_page)

        return self._extract_phrases_single_page(self._wikipage)
