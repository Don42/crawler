#!/usr/bin/env python3
# ----------------------------------------------------------------------------
# "THE SCOTCH-WARE LICENSE" (Revision 42):
# <DonMarco42@gmail.com> wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a scotch whisky in return
# Marco 'don' Kaulea
# ----------------------------------------------------------------------------
"""mangafox fetches images from mangafox.me

Usage:
    mangafox <manga_url>
    mangafox <manga_url> <number>

"""

import bs4
import docopt as dopt
import functools
import multiprocessing as mp
import os
import requests
import zipfile


def get_chapters_list(url):
    # Download content and parse as html
    main_page = requests.get(url)
    main_page.encoding = 'utf-8'
    main_page = bs4.BeautifulSoup(main_page.text)

    # Compile all available volumes into one list
    volume_list = main_page.findAll('ul', 'chlist')
    volume_list.reverse()  # Order from oldest to newest

    # Compile all chapters into one list
    print("Compiling chapters_list")
    chapters_list = list()
    for volume in volume_list:
        chapters = volume.findAll('a', 'tips')
        chapters_links = [x['href'] for x in chapters]
        chapters_links.reverse()
        chapters_list.append(chapters_links)
    return chapters_list


def crawl_chapter(chapter_url):
    """Crawl chapter and yield image links

    Args:
        chapter_url (string); Url to the first page of the chapter.

    Returns:
        Iterator: Over the image urls.

    """
    base_url = chapter_url.split('/')
    del base_url[len(base_url) - 1]
    data = requests.get(chapter_url)
    data.encoding = 'utf-8'
    data = bs4.BeautifulSoup(data.text)
    image_links = list()
    next_link = data.find('a', 'btn next_page')['href']
    while 'http' not in next_link:
        try:
            image_links.append([data.find('img')['src']])
        except TypeError:
            break
        data = requests.get('/'.join(base_url + [next_link]))
        data.encoding = 'utf-8'
        data = bs4.BeautifulSoup(data.text)
        next_link = data.find('a', 'btn next_page')['href']
        try:
            yield data.find('img')['src']
        except TypeError:
            break


def download_image(image, volume, chapter):
    """Download a image prepend the name with volume and chapter

    Args:
        image (string): Url to the image.
        volume (int): Number of the volume. Only used for file naming.
        chapter (int): Number of the chapter within the volume. Only used for
            file naming.

    Returns:
        string: Filename

    """
    filename = "downloads/{:03}_{:03}_{}".format(
        volume,
        chapter,
        image.split('/')[-1])
    if os.path.isfile(filename):
        return filename
    r = requests.get(image, stream=True)
    with open(filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()
    return filename


def download_images(images_iter, volume_idx, chapter_idx, threads=6):
    """Download images from one iterator

    Args:
        images_iter (iterator): Iterator over image urls
        volume (int): Number of the volume. Only used for file naming.
        chapter (int): Number of the chapter within the volume. Only used for
            file naming.
        threads (int): Number of threads used for downloading. Defaults to 6.


    """
    download = functools.partial(download_image,
                                 volume=volume_idx,
                                 chapter=chapter_idx)
    filenames = []
    with mp.Pool(processes=threads) as pool:
        for name in pool.imap(download,
                              images_iter):
            filenames.append(name)
    return filenames


def download_volume(url, number):
    """Process url and download specified volume

    Args:
        url (string): Url to the manga
        number (int): Zero-based index to the volume to download

    """
    chapters_links = get_chapters_list(url)[number]

    for chapter_idx, chapter in enumerate(chapters_links):
        print("Downloading chapter {:03} of {:03}".format(chapter_idx + 1,
                                                          len(chapters_links)))
        images_iter = crawl_chapter(chapter)
        filenames = download_images(images_iter, number, chapter_idx)
        create_zip_file(
            '{name}_{volume:03}_{chapter:03}.cbz'.format(
                name=url.split('/')[-2],
                volume=number + 1,
                chapter=chapter_idx + 1),
            filenames)


def download_complete_manga(url):
    """Process url and download all volumes/chapters

    Args:
        url (string): Url to the manga

    """
    chapters_list = get_chapters_list(url)
    print("Iterating over chapters_list")
    for volume_idx, volume in enumerate(chapters_list):
        print("Downloading volume {:03} of {:03}".format(volume_idx + 1,
                                                         len(chapters_list)))
        for chapter_idx, chapter in enumerate(volume):
            print("Downloading chapter {:03} of {:03}".format(chapter_idx + 1,
                                                              len(volume)))
            images_iter = crawl_chapter(chapter)
            filenames = download_images(images_iter, volume_idx, chapter_idx)
            create_zip_file(
                '{name}_{volume:03}_{chapter:03}.cbz'.format(
                    name=url.split('/')[-2],
                    volume=volume_idx + 1,
                    chapter=chapter_idx + 1),
                filenames)


def create_zip_file(zipname, filenames):
    with zipfile.ZipFile(zipname,
                         mode='w',
                         compression=zipfile.ZIP_DEFLATED) as cbz:

        for filename in filenames:
            cbz.write(filename)


def main():
    arguments = dopt.docopt(__doc__)
    if arguments.get('<number>', None) is not None:
        download_volume(arguments['<manga_url>'], int(arguments['<number>']))
    else:
        download_complete_manga(arguments['<manga_url>'])

if __name__ == '__main__':
    main()
