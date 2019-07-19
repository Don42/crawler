import pathlib as pl

from helveticascans.uri import get_page_list
from helveticascans.pages import uris_to_pages
from helveticascans.volume import group_volumes

kyuu_chan_base_url = "https://helveticascans.com/r/series/wonder-cat-kyuu-chan/"


def main():
    pages_list = get_page_list(kyuu_chan_base_url)
    pages_list = uris_to_pages(pages_list)
    volumes = group_volumes(pages_list.__iter__())
    for i, x in enumerate(volumes):
        x.write_to_file(pl.Path("./download") / f"kyuu_{i+1}.cbz")
    print(volumes)


if __name__ == '__main__':
    main()
