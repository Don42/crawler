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

"""

import bs4
import docopt as dopt
import functools
import multiprocessing as mp
import os
import requests


def crawl_chapter(chapter_url):
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
    download = functools.partial(download_image,
                                 volume=volume_idx,
                                 chapter=chapter_idx)
    with mp.Pool(processes=threads) as pool:
        for name in pool.imap(download,
                              images_iter):
            print(name)


def download_complete_manga(url):
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

    print("Iterating over chapters_list")
    for volume_idx, volume in enumerate(chapters_list):
        print("Downloading volume {:03} of {:03}".format(volume_idx,
                                                         len(chapters_list)))
        for chapter_idx, chapter in enumerate(volume):
            print("Downloading chapter {:03} of {:03}".format(chapter_idx,
                                                              len(volume)))
            images_iter = crawl_chapter(chapter)
            download_images(images_iter, volume_idx, chapter_idx)


def main():
    arguments = dopt.docopt(__doc__)
    download_complete_manga(arguments['<manga_url>'])

if __name__ == '__main__':
    main()
