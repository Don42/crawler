import pathlib as pl
import zipfile
from tempfile import NamedTemporaryFile
from typing import Iterator, List, Optional, Iterable

from helveticascans import Cover, Page


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

    def write_to_file(self, file_path: pl.Path):
        with zipfile.ZipFile(file_path, mode='w') as zip_file:
            if self.cover is not None:
                with NamedTemporaryFile() as tmp:
                    tmp.write(self.cover.get_content())
                    zip_file.write(
                        tmp.name,
                        arcname="cover.png")
            for f in self.pages:
                with NamedTemporaryFile() as tmp:
                    tmp.write(f.get_content())
                    zip_file.write(
                        tmp.name,
                        arcname=f"page_{f.page_number:0>5}.{f.suffix}")