import argparse
import asyncio
import pathlib as pl

from helveticascans.uri import get_page_list
from helveticascans.pages import uris_to_pages
from helveticascans.volume import group_volumes

kyuu_chan_base_url = "https://helveticascans.com/r/series/wonder-cat-kyuu-chan/"


def parse_arguments():
    parser = argparse.ArgumentParser(description="Download volumes")
    parser.add_argument("volume_number", type=int, nargs='?')
    args = parser.parse_args()
    return args


async def main():
    args = parse_arguments()
    download_path = pl.Path("./download")
    pages_list = get_page_list(kyuu_chan_base_url)
    pages_list = await uris_to_pages(pages_list)
    volumes = group_volumes(pages_list.__iter__())
    if args.volume_number is not None:
        i = args.volume_number
        await volumes[i - 1].write_to_file(
            download_path / f"kyuu_{i}.cbz"
        )
    else:
        for i, x in enumerate(volumes):
            await x.write_to_file(
                download_path / f"kyuu_{i + 1}.cbz"
            )


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
