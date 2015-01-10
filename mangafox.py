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

import docopt as dopt
import requests
import bs4


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
    print(image)
    filename = "downloads/{:03}_{:03}_{}".format(
        volume,
        chapter,
        image.split('/')[-1])
    r = requests.get(image, stream=True)
    with open(filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()
    return filename


def main():
    arguments = dopt.docopt(__doc__)
    data = requests.get(arguments['<manga_url>'])
    data.encoding = 'utf-8'
    data = bs4.BeautifulSoup(data.text)
    chapter_list = data.findAll('ul', 'chlist')
    chapter_list.reverse()
    links_list = list()
    for chapter in chapter_list:
        links = chapter.findAll('a', 'tips')
        links = [x['href'] for x in links]
        links.reverse()
        links_list.append(links)

    volume_num = 0
    for volume in links_list:
        chapter_num = 0
        volume_num += 1
        for link in volume:
            chapter_num += 1
            images_iter = crawl_chapter(link)
            for image in images_iter:
                print(download_image(image, volume_num, chapter_num))

if __name__ == '__main__':
    main()
