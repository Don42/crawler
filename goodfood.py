#!/usr/bin/env python3
# ----------------------------------------------------------------------------
# "THE SCOTCH-WARE LICENSE" (Revision 42):
# <don@0xbeef.org> wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a scotch whisky in return
# Marco 'don' Kaulea
# ----------------------------------------------------------------------------
"""goodfood

Usage:
    goodfood recipe <url>
    goodfood recipes <url>
    goodfood categories <url>
    goodfood scrape
"""

import bs4
import docopt
import functools
import json
import multiprocessing as mp
import pathlib as pl
import re
import requests

BASE_URL = 'http://www.bbcgoodfood.com'
USER_AGENT = {'user-agent': 'spider'}

dump_json = functools.partial(json.dumps,
                              indent=4,
                              ensure_ascii=False,
                              sort_keys=True)


def make_absolute(url):
    return "{}{}".format(BASE_URL, url)


def parse_meta_tag(page, itemprop):
    content = page.find('meta', {'itemprop': itemprop})
    try:
        content = content['content']
    except TypeError:
        return None
    return content


def parse_meta_tags(page, itemprop):
    content = page.findAll('meta', {'itemprop': itemprop})
    try:
        content = [x['content'] for x in content]
    except TypeError:
        return None
    return content


def parse_recipe(page):
    soup = bs4.BeautifulSoup(page)
    main_content = soup.find('div', {'id': 'main-content',
                                     'class': 'row main node-type-recipe'})
    out = {}
    ingredients = main_content.findAll('li', {'itemprop': 'ingredients'})
    ingredients = [x.text for x in ingredients]
    name = main_content.find('h1', {'itemprop': 'name'})
    out['title'] = name.text
    content = main_content.find('p', {'itemprop': 'description'})
    out['description'] = content.text
    content = main_content.find('li', {'itemprop': 'recipeInstructions'})
    if content is not None:
        out['instructions'] = content.text
    content = main_content.find('section', {'itemprop': 'recipe-method'})
    if content is not None:
        out['method'] = content.find('div', {'class': 'field-item even'}).text

    out['ingredients'] = ingredients
    out['keywords'] = parse_meta_tags(main_content, 'keywords')
    out['recipe_categories'] = parse_meta_tags(main_content, 'recipeCategory')
    out['cook_time'] = parse_meta_tag(main_content, 'cookTime')
    out['prep_time'] = parse_meta_tag(main_content, 'prepTime')
    out['total_time'] = parse_meta_tag(main_content, 'totalTime')
    return out


def get_subcategories(url):
    r = requests.get(url, headers=USER_AGENT)
    if r.status_code != 200:
        raise requests.exceptions.RequestException(
            "Request error: get_subcategories('{}')".format(url))
    soup = bs4.BeautifulSoup(r.text)
    main_content = soup.find('div', {'id': 'main-content'})
    links = [x['href'] for x in main_content.findAll('a')]
    regex = re.compile('^/recipes/collection/[^/]*$')
    links = filter(regex.match, links)
    return links


def get_categories(url):
    r = requests.get(url, headers=USER_AGENT)
    if r.status_code != 200:
        raise requests.exceptions.RequestException(
            "Request error: get_categories('{}')".format(url))
    soup = bs4.BeautifulSoup(r.text)
    navigation = soup.find('div', {'id': 'nav-touch', 'class': 'nav-touch'})
    links = [x['href'] for x in navigation.findAll('a')]
    regex = re.compile('^/recipes/category/[^/]*$')
    links = filter(regex.match, links)
    for category in links:
        for subcategory in get_subcategories(make_absolute(category)):
            yield make_absolute(subcategory)


def get_recipes(category_url):
    r = requests.get(category_url, headers=USER_AGENT)
    if r.status_code != 200:
        raise requests.exceptions.RequestException(
            "Request error: get_recipes('{}')".format(category_url))
    soup = bs4.BeautifulSoup(r.text)
    main_content = soup.find('div', {'id': 'main-content'})
    articles = main_content.findAll('article',
                                    {'itemtype': 'http://schema.org/Recipe'})
    ret = list()
    for article in articles:
        link = article.find('div', {'class': 'node-image'}).a['href']
        ret.append(make_absolute(link))
    return ret


def scrape_recipe(url):
    file_name = url.split('/')[-1]
    file_path = pl.Path('goodfood') / file_name
    if file_path.is_file():
        return file_name
    try:
        r = requests.get(url, headers=USER_AGENT)
        if r.status_code == 200:
            recipe = parse_recipe(r.text)
            with file_path.open('w') as f:
                f.write(dump_json(recipe))
    except TypeError:
        print(url)
        raise
    except AttributeError:
        print(url)
        raise

    return file_name


def scrape(processes=4):
    with mp.Pool(processes=processes) as pool:
        for category in get_categories(BASE_URL):
            try:
                recipe_list = get_recipes(category)
            except requests.exceptions.RequestException:
                continue
            it = pool.imap_unordered(scrape_recipe, recipe_list)
            for recipe in it:
                print(recipe)


def main():
    arguments = docopt.docopt(__doc__)
    if arguments.get('recipe', False):
        r = requests.get(arguments['<url>'], headers=USER_AGENT)
        if r.status_code == 200:
            print(dump_json(parse_recipe(r.text)))
    elif arguments.get('recipes', False):
        for x in get_recipes(arguments['<url>']):
            print(x)
    elif arguments.get('categories', False):
        for x in get_categories(arguments['<url>']):
            print(x)
    elif arguments.get('scrape', False):
        scrape()


if __name__ == '__main__':
    main()
