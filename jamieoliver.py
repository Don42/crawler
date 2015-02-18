#!/usr/bin/env python3
# ----------------------------------------------------------------------------
# "THE SCOTCH-WARE LICENSE" (Revision 42):
# <DonMarco42@gmail.com> wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a scotch whisky in return
# Marco 'don' Kaulea
# ----------------------------------------------------------------------------

'''Download recipies

Usage:
    jamieoliver recipes <url>
    jamieoliver categories
'''

import bs4
import docopt
import requests


def download_recipe(url):
    r = requests.get(url)
    r.encoding = 'utf-8'
    return r.text


def parse_recipe(page):
    soup = bs4.BeautifulSoup(page)
    content = soup.find('div', {'class': 'tab-content'})
    desc_yield = content.find('span', {'class': 'description yield'}).text
    ingredients_list = [x.text for x in content.find_all(
        'span', {'class': ''})]
    instructions = content.find('p', {'class', 'instructions'}).text
    return {'instructions': instructions, 'desc_yield': desc_yield,
            'ingredients': ingredients_list}


def download_categories():
    url = 'http://www.jamieoliver.com/'
    r = requests.get(url)
    r.encoding = 'utf-8'
    soup = bs4.BeautifulSoup(r.text)
    categories_div = soup.find('div', {'class': 'cat_secondary'})
    categories_a = categories_div.find_all('a')
    link_list = [x['href'] for x in categories_a]
    return link_list


def main():
    arguments = docopt.docopt(__doc__)
    if arguments.get('recipies', False):
        page = download_recipe(arguments['<url>'])
        recipe = parse_recipe(page)
        print(recipe)
    else:
        for x in download_categories():
            print(x)


if __name__ == '__main__':
    main()
