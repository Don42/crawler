import re

import aiohttp
from aiohttp.client_exceptions import ClientConnectionError
from aiohttp.typedefs import StrOrURL
from bs4 import BeautifulSoup, element

HTML_PARSER = 'html.parser'

pattern = re.compile(r"en/0/(\d+)/(\d+)?")

session = aiohttp.ClientSession()


def parse_page_link(link: str):
    return pattern.search(link)


def parse_page_links(links: list):
    return [(item['href'], parse_page_link(item['href']).groups()) for item in links]


async def try_get(uri, retry_count=3):
    for _ in range(retry_count):
        try:
            return await session.get(uri)
        except ClientConnectionError:
            pass


async def get_image_uri(page_uri):
    response = await try_get(page_uri)
    bs = BeautifulSoup(await response.text(), 'html.parser')
    image: element.Tag = (
        bs
        .find("div", class_="inner")
        .find("a")
        .find("img"))
    return image['src']


async def get_image(image_uri: StrOrURL) -> bytes:
    response = await try_get(image_uri)
    response.raise_for_status()
    return await response.read()


async def get_page_list(series_url: StrOrURL):
    response = await try_get(series_url)
    page = BeautifulSoup(await response.text(), HTML_PARSER)
    comics = [
        div.find('a')
        for div in page.find("div", class_="group").find_all("div", class_="title")]
    comics = [
        x
        for x in comics
        if x is not None
    ]
    return comics
