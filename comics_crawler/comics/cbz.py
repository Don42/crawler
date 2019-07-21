import logging
from os import PathLike
import pathlib as pl
import zipfile

from .volume import Volume
from .pages import Page

logger = logging.getLogger(__name__)

ZIP_OPEN_MODE_APPEND = 'a'


async def write_cbz(
        file_path: PathLike,
        volume: Volume,
):
    with zipfile.ZipFile(
            file_path,
            mode=ZIP_OPEN_MODE_APPEND,
            compression=zipfile.ZIP_DEFLATED
    ) as zip_file:
        if volume.cover is not None:
            logger.info(
                "Writing Volume %s Cover",
                volume.identifier,
            )
            await _write_page_to_file(
                zip_file,
                f"cover.{await volume.cover.suffix}",
                volume.cover,
            )

        number_of_pages = volume.pages[-1].number()
        for page in volume.pages:
            logger.info(
                "Writing Volume %s Page of",
                volume.identifier,
                page.number(),
                number_of_pages,
            )
            await _write_page_to_file(
                zip_file,
                f"page_{page.number:0>5}.{await page.suffix}",
                page)


def open_zipfile(
        volume: Volume,
        mode='r',
) -> zipfile.ZipFile:
    return zipfile.ZipFile(
            volume.generate_file_name().with_suffix('.cbz'),
            mode=mode,
            compression=zipfile.ZIP_DEFLATED)


def filter_pages(
        volume: Volume,
):
    try:
        return _filter_pages(volume)
    except FileNotFoundError:
        return volume


def _filter_pages(
        volume: Volume
):
    with open_zipfile(volume) as zf:
        file_names = [_remove_suffix(x) for x in zf.filelist]
        cover = volume.cover if 'cover' not in file_names else None
        pages = [
            page
            for page in volume.pages
            if f"page_{page.identifier}" not in file_names
        ]

        return Volume(
            volume.series_name,
            volume.identifier,
            cover,
            pages,
        )


def _remove_suffix(file: zipfile.ZipInfo) -> str:
    return str(pl.Path(file.filename).with_suffix(""))


async def _write_page_to_file(
        zip_file: zipfile.ZipFile,
        file_name: str,
        page: Page):
    if file_name not in zip_file.namelist():
        zip_file.writestr(
            zinfo_or_arcname=file_name,
            data=await page.get_content())


def write_images_to_file(
        volume: Volume,
        images: list,
):
    with open_zipfile(
            volume,
            mode=ZIP_OPEN_MODE_APPEND
    ) as zf:
        for filename, image in images:
            _write_image_to_file(zf, filename, image)


def _write_image_to_file(zf, filename, image):
    if filename not in zf.namelist():
        zf.writestr(
            zinfo_or_arcname=filename,
            data=image)
