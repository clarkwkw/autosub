from dataclasses import dataclass


@dataclass
class PhraseLocalisation:
    foreign: str
    local: str

    @classmethod
    def from_dict(cls, data: dict):
        return PhraseLocalisation(foreign=data['foreign'], local=data['local'])

    @property
    def is_valid(self):
        return len(self.foreign) > 0 and len(self.local) > 0
