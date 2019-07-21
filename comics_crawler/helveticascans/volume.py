import asyncio
import itertools
from typing import Iterator, List, Optional, Iterable

from .uri import get_image_uri, get_image, get_suffix
from comics_crawler.comics import Volume, Page
from comics_crawler.comics import cbz

# class Volume:
#     def __init__(self, number):
#         self.number = number
#         self.cover: Optional[Cover] = None
#         self.pages: List[Page] = list()
#
#     def add_cover(self, cover: Cover):
#         self.cover = cover
#
#     def add_page(self, page: Page):
#         self.pages.append(page)
#
#     @classmethod
#     def from_iterator(cls, number: int, it: Iterable[Page]):
#         self = cls(number)
#         for page in it:
#             if isinstance(page, Cover):
#                 self.add_cover(page)
#                 break
#             else:
#                 self.add_page(page)
#         else:
#             if len(self.pages) == 0:
#                 raise StopIteration
#         return self
#
#     async def write_to_file(self, file_path: pl.Path):
#         # TODO Must create folder here
#         with zipfile.ZipFile(
#                 file_path,
#                 mode='a',
#                 compression=zipfile.ZIP_DEFLATED
#         ) as zip_file:
#             if self.cover is not None:
#                 print(f"Writing Volume {self.number} Cover")
#                 await self.write_page_to_file(zip_file, self.cover)
#             for page in self.pages:
#                 print(f"Writing Volume {self.number} Page {page.number} of {self.pages[-1].number}")
#                 await self.write_page_to_file(zip_file, page)
#
#     @staticmethod
#     async def write_page_to_file(
#             zip_file: zipfile.ZipFile,
#             page: Page):
#         filename = await page.get_internal_filename()
#         if filename not in zip_file.namelist():
#             zip_file.writestr(
#                 zinfo_or_arcname=filename,
#                 data=await page.get_content())
#
#     def __repr__(self):
#         return f"<{self.__class__} {self.number}>"


def group_volumes(
        series_name: str,
        pages: Iterator[Page],
) -> List[Volume]:
    volume_number = 1
    volumes = []
    while True:
        try:
            volume = _from_iterator(
                series_name,
                f"{volume_number:0>3}",
                pages)
            volumes.append(volume)
            volume_number += 1
        except StopIteration:
            break

    return volumes


def _from_iterator(
         series_name: str,
         identifier: str,
         it: Iterator[Page]):
    pages = list()
    cover = None
    for x in it:
        if x.is_cover:
            cover = x
            break
        else:
            pages.append(x)

    if len(pages) == 0:
        raise StopIteration
    return Volume(
        series_name,
        identifier,
        cover,
        pages
    )


async def download_volume(volume: Volume):
    print(f"Downloading volume: {volume}")
    images = []
    if volume.cover is not None:
        images.append(await download_page(volume.cover))
    for pair in await asyncio.gather(*[
            download_page(page)
            for page in volume.pages]):
        images.append(pair)

    cbz.write_images_to_file(volume, images)


async def download_page(page: Page):
    image_url = await get_image_uri(page.url)
    image = await get_image(image_url)
    filename = (
        f"page_{page.identifier}.{get_suffix(image_url)}"
        if not page.is_cover
        else f"cover.{get_suffix(image_url)}"
    )
    print(filename)
    return filename, image
