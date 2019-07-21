from typing import Optional

from bs4 import BeautifulSoup
from .uri import pattern, get_image_uri, get_image, HTML_PARSER, retrieve_series_page

from comics_crawler.comics.pages import Page as GeneralPage


class Page:
    def __init__(self, number, uri):
        self.number = int(number)
        self.page_uri = uri
        self._image_uri = None

    @property
    async def uri(self) -> str:
        if self._image_uri is None:
            self._image_uri = await get_image_uri(self.page_uri)
        return self._image_uri

    @classmethod
    def from_uri(cls, uri):
        match = pattern.search(uri)
        if not match:
            return
        elif match.group(2) is not None:
            assert match.group(2) == "5"
            return Cover(match.group(1), uri)
        else:
            return cls(match.group(1), uri)

    def __gt__(self, other: 'Page'):
        if isinstance(other, Cover):
            return self.number > other.number + 0.5
        else:
            return self.number > other.number

    def __str__(self):
        return f"Page {self.number}"

    async def get_content(self) -> bytes:
        return await get_image(await self.uri)

    @property
    async def suffix(self):
        return (await self.uri).split('.')[-1]

    async def get_internal_filename(self) -> str:
        return f"page_{self.number:0>5}.{await self.suffix}"


class Cover(Page):
    def __init__(self, number, uri):
        super().__init__(number, uri)

    def __gt__(self, other: Page):
        if isinstance(other, Cover):
            return self.number + 0.5 > other.number + 0.5
        else:
            return self.number + 0.5 > other.number

    def __str__(self):
        return f"Cover {self.number}"

    async def get_internal_filename(self) -> str:
        return f"cover.{await self.suffix}"


async def uris_to_pages(pages_list):
    pages_list = sorted((Page.from_uri(x['href']) for x in await pages_list))
    return pages_list


async def retrieve_pages_of_series(series_name: str):
    page = await retrieve_series_page(series_name)
    return parse_series_page(await page.text())


def parse_series_page(page: str):
    page = BeautifulSoup(page, HTML_PARSER)
    page_group = page.find("div", class_="group")
    comics = [
        div.find('a')
        for div in page_group.find_all("div", class_="title")]
    comics = [
        make_page(x['href'])
        for x in comics
        if x is not None
    ]
    return comics


def make_page(page_url: str) -> GeneralPage:
    match = pattern.search(page_url)
    if not match:
        raise Exception("no pattern match on page url")
    elif match.group(2) is not None:
        assert match.group(2) == "5"
        return GeneralPage(
            url=page_url,
            identifier=f"{match.group(1):0>5}",
            is_cover=True,
        )
    else:
        return GeneralPage(
            url=page_url,
            identifier=f"{match.group(1):0>5}",
            is_cover=False,
        )
