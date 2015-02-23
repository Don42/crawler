#!/usr/bin/env python3
# ----------------------------------------------------------------------------
# "THE SCOTCH-WARE LICENSE" (Revision 42):
# <DonMarco42@gmail.com> wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a scotch whisky in return
# Marco 'don' Kaulea
# ----------------------------------------------------------------------------

'''Download recipes

Usage:
    jamieoliver recipes <url>
    jamieoliver recipe <url>
    jamieoliver cat <url>
    jamieoliver categories
    jamieoliver crawl
    jamieoliver process <url>
'''

import bs4
import docopt
import functools
import itertools
import json
import pathlib as pl
import requests
import urllib.parse

BASE_URL = 'http://www.jamieoliver.com'

dump_json = functools.partial(json.dumps,
                              indent=4,
                              ensure_ascii=False,
                              sort_keys=True)


def download_page(url, base=""):
    url = base + url
    r = requests.get(url)
    r.encoding = 'utf-8'
    return r.text


def parse_recipe(page):
    soup = bs4.BeautifulSoup(page)
    content = soup.find('div', {'class': 'tab-content'})
    try:
        desc_yield = content.find('span', {'class': 'description yield'}).text
    except AttributeError:
        desc_yield = ''

    ingredients_list = [x.text for x in content.find_all(
        'span', {'class': ''})]
    instructions = content.find('p', {'class', 'instructions'}).text
    return {'instructions': instructions, 'desc_yield': desc_yield,
            'ingredients': ingredients_list}


def parse_recipe_list(page):
    soup = bs4.BeautifulSoup(page)
    section = soup.find('section', {'id': 'recipe_filtered'})
    if section is None:
        return []
    a_list = [x.a['href'] for x in section.find_all('h3')]
    link_list = map(functools.partial(prepend_base_url, BASE_URL),
                    a_list)
    return link_list


def process_recipe(url):
    parsed_url = urllib.parse.urlparse(url)
    path = parsed_url.path.split('/')
    name = path[-1]
    recipe_type = path[-2]
    filepath = pl.Path('dump/{}/{}.json'.format(recipe_type, name))
    print(name)
    if filepath.is_file():
        print("File already exists\n")
        return

    try:
        filepath.parent.mkdir(parents=True)
    except FileExistsError:
        if not filepath.parent.is_dir():
            filepath.parent.unlink()
            filepath.parent.mkdir(parents=True)

    page = download_page(url)
    try:
        recipe = parse_recipe(page)
    except Exception as e:
        print(e)
        print(url)
        raise

    with filepath.open('w') as f:
        f.write(dump_json(recipe))

    return filepath


def download_main_categories(url):
    r = requests.get(url)
    r.encoding = 'utf-8'
    soup = bs4.BeautifulSoup(r.text)
    categories_div = soup.find('div', {'class': 'cat_secondary'})
    categories_a = categories_div.find_all('a')
    link_list = [x['href'] if x is not None else [] for x in categories_a]
    return link_list


def download_categories(url):
    categories = download_main_categories(url)
    for x in categories:
        page = download_page(x)
        subcategories = detect_subcategories(page)
        if subcategories is not None:
            subcategories = parse_subcategories(subcategories)
            subcategories = map(
                functools.partial(prepend_base_url, BASE_URL),
                subcategories)
            categories.extend(subcategories)
    return set(categories)


def detect_subcategories(page):
    soup = bs4.BeautifulSoup(page)
    section = soup.find('section', {'id': 'category_top'})
    if section is not None:
        section = soup.find('section', {'id': 'recipe_collections'})
    return section


def parse_subcategories(section):
    categories_articles = section.find_all('article')
    link_list = [x.a['href'] for x in categories_articles]
    return link_list


def retrieve_recipe_list(url):
    page = download_page(url)
    recipes = parse_recipe_list(page)
    return recipes


def crawl_recipes():
    categories = download_categories(BASE_URL)
    recipes = itertools.chain.from_iterable(
        map(retrieve_recipe_list, categories))
    for url in recipes:
        process_recipe(url)


def prepend_base_url(base, url):
    if 'http' in url:
        return url
    else:
        return base + url


def main():
    arguments = docopt.docopt(__doc__)
    if arguments.get('recipe', False):
        page = download_page(arguments['<url>'])
        recipe = parse_recipe(page)
        print(recipe)
    elif arguments.get('cat', False):
        page = download_page(arguments['<url>'])
        print(parse_subcategories(detect_subcategories(page)))
    elif arguments.get('recipes', False):
        page = download_page(arguments['<url>'])
        recipes = parse_recipe_list(page)
        for x in recipes:
            print(x)
    elif arguments.get('crawl', False):
        crawl_recipes()
    elif arguments.get('process', False):
        page = process_recipe(arguments['<url>'])
        print(page)
    else:
        categories = download_categories(BASE_URL)
        for x in categories:
            print(x)


if __name__ == '__main__':
    main()
