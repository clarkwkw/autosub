from abc import ABC, abstractmethod
from typing import List, Optional


class LLM(ABC):
    @abstractmethod
    def select_one_from_list(
        self,
        input: List[str],
        item_description: str,
        criteria_description: str,
        allow_none: bool
    ) -> Optional[str]:
        """Ask LLM to analyse a list and select the most suitable item

        Args:
            input (List[str]): the list
            item_description (str): short description of the list
            criteria_description (str): short description of what would be the best item
            allow_none (bool): whether the LLM can choose to not return an item

        Returns:
            Optional[str]: the most suitable item
        """
        ...
