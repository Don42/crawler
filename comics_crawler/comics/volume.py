from dataclasses import dataclass
from typing import List, Optional
from os import PathLike
import pathlib as pl

from .pages import Page


@dataclass(frozen=True)
class Volume:
    series_name: str
    identifier: str
    cover: Optional[Page]
    pages: List[Page]

    def generate_file_name(
            self,
            base_path: PathLike = None,
    ) -> pl.Path:
        if base_path is None:
            base_path = pl.Path("./download")
        return base_path / f"{self.series_name}_{self.identifier}"
