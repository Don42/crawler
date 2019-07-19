import re

import requests
from bs4 import BeautifulSoup

HTML_PARSER = 'html.parser'

pattern = re.compile(r"en/0/(\d+)/(\d+)?")

session = requests.Session()


def parse_page_link(link: str):
    return pattern.search(link)


def parse_page_links(links: list):
    return [(item['href'], parse_page_link(item['href']).groups()) for item in links]


def get_image_uri(page_uri):
    response = session.get(page_uri)
    bs = BeautifulSoup(response.text, 'html.parser')
    image = (bs
             .find("div", class_="inner")
             .find("a")
             .find("img"))
    return image['src']


def get_image(image_uri) -> bytes:
    response = session.get(image_uri)
    response.raise_for_status()
    return response.content


def get_page_list(series_url):
    response = session.get(series_url)
    page = BeautifulSoup(response.text, HTML_PARSER)
    comics = [
        div.find('a')
        for div in page.find("div", class_="group").find_all("div", class_="title")]
    comics = [
        x
        for x in comics
        if x is not None
    ]
    return comics
