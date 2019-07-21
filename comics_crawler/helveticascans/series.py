import asyncio

from .uri import retrieve_series_page
from .pages import parse_series_page
from .volume import group_volumes, download_volume
from comics_crawler.comics.cbz import filter_pages
from comics_crawler.comics.pages import Page


async def download_series(series_name: str):
    # Download series page
    series_page = await retrieve_series_page(series_name)
    ungrouped_pages = sorted(
        parse_series_page(await series_page.text()),
        key=to_sortable,
    )
    volumes = group_volumes(
        series_name,
        ungrouped_pages.__iter__())
    filtered_volumes = [
        filter_pages(volume)
        for volume in volumes
    ]

    await asyncio.gather(*[
        download_volume(x)
        for x in filtered_volumes])


def to_sortable(page: Page):
    number = int(page.identifier)
    if page.is_cover:
        # Covers are at the end of the numbering
        # Don't ask why, they just seem to be released last
        return number + 0.5
    else:
        return number
