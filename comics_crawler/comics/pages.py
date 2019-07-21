import abc
from dataclasses import dataclass

from aiohttp.typedefs import StrOrURL
from yarl import URL


class IUPage(abc.ABC):
    def number(self):
        raise NotImplementedError()

    async def get_uri(self) -> URL:
        raise NotImplementedError()

    def __gt__(self, other: 'IUPage'):
        return self.cmp_number > other.cmp_number

    @property
    def cmp_number(self):
        raise NotImplementedError()


@dataclass(frozen=True)
class Page:
    url: StrOrURL
    identifier: str
    is_cover: bool


@dataclass(frozen=True)
class PageImage:
    url: StrOrURL
    identifier: str
    is_cover: bool
