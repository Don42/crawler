import re

import requests
from bs4 import BeautifulSoup

pattern = re.compile(r"en/0/(\d+)/(\d+)?")


def parse_page_link(link: str):
    return pattern.search(link)


def parse_page_links(links: list):
    return [(item['href'], parse_page_link(item['href']).groups()) for item in links]


def get_image_uri(page_uri):
    response = requests.get(page_uri)
    bs = BeautifulSoup(response.text, 'html.parser')
    image = (bs
             .find("div", class_="inner")
             .find("a")
             .find("img"))
    return image['src']