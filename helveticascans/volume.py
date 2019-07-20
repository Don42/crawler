import pathlib as pl
import zipfile
from typing import Iterator, List, Optional, Iterable

from helveticascans.pages import Cover, Page


class Volume:
    def __init__(self, number):
        self.number = number
        self.cover: Optional[Cover] = None
        self.pages: List[Page] = list()

    def add_cover(self, cover: Cover):
        self.cover = cover

    def add_page(self, page: Page):
        self.pages.append(page)

    @classmethod
    def from_iterator(cls, number: int, it: Iterable[Page]):
        self = cls(number)
        for page in it:
            if isinstance(page, Cover):
                self.add_cover(page)
                break
            else:
                self.add_page(page)
        else:
            if len(self.pages) == 0:
                raise StopIteration
        return self

    async def write_to_file(self, file_path: pl.Path):
        # TODO Must create folder here
        with zipfile.ZipFile(
                file_path,
                mode='a',
                compression=zipfile.ZIP_DEFLATED
        ) as zip_file:
            if self.cover is not None:
                print(f"Writing Volume {self.number} Cover")
                await self.write_page_to_file(zip_file, self.cover)
            for page in self.pages:
                print(f"Writing Volume {self.number} Page {page.number} of {self.pages[-1].number}")
                await self.write_page_to_file(zip_file, page)

    @staticmethod
    async def write_page_to_file(
            zip_file: zipfile.ZipFile,
            page: Page):
        filename = await page.get_internal_filename()
        if filename not in zip_file.namelist():
            zip_file.writestr(
                zinfo_or_arcname=filename,
                data=await page.get_content())

    def __repr__(self):
        return f"<{self.__class__} {self.number}>"


def group_volumes(pages: Iterator[Page]) -> List[Volume]:
    volume_number = 1
    volumes = []
    while True:
        try:
            volume = Volume.from_iterator(
                volume_number,
                pages)
            volumes.append(volume)
            volume_number += 1
        except StopIteration:
            break

    return volumes
