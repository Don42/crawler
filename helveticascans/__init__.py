# coding: utf-8
import pathlib as pl

from bs4 import BeautifulSoup
import requests

from helveticascans.pages import Page, Cover
from helveticascans.uri import parse_page_links
from helveticascans.volume import group_volumes

kyuu_chan_base_url = "https://helveticascans.com/r/series/wonder-cat-kyuu-chan/"


def get_page_list(series_url):
    page = BeautifulSoup(requests.get(series_url).text, 'html.parser')
    comics = [
        div.find('a')
        for div in page.find("div", class_="group").find_all("div", class_="title")]
    comics = [
        x
        for x in comics
        if x is not None
    ]
    return comics


def main():
    pages = get_page_list(kyuu_chan_base_url)
    pages = sorted((Page.from_uri(x['href']) for x in pages))
    volumes = group_volumes(pages.__iter__())
    for i, x in enumerate(volumes):
        x.write_to_file(pl.Path("./") / f"kyuu_{i+1}.cbz")
    print(volumes)


if __name__ == '__main__':
    main()
