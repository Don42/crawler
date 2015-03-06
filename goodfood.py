#!/usr/bin/env python3
# ----------------------------------------------------------------------------
# "THE SCOTCH-WARE LICENSE" (Revision 42):
# <DonMarco42@gmail.com> wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a scotch whisky in return
# Marco 'don' Kaulea
# ----------------------------------------------------------------------------
"""goodfood

Usage:
    goodfood <url>
"""

import bs4
import docopt
import requests


def parse_meta_tag(page, itemprop):
    content = page.find('meta', {'itemprop': itemprop})
    content = content['content']
    return content


def parse_meta_tags(page, itemprop):
    content = page.findAll('meta', {'itemprop': itemprop})
    content = [x['content'] for x in content]
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
    out['instructions'] = content.text
    out['keywords'] = parse_meta_tags(main_content, 'keywords')
    out['recipe_categories'] = parse_meta_tags(main_content, 'recipeCategory')
    out['cook_time'] = parse_meta_tag(main_content, 'cookTime')
    out['prep_time'] = parse_meta_tag(main_content, 'prepTime')
    out['total_time'] = parse_meta_tag(main_content, 'totalTime')
    return out


def main():
    arguments = docopt.docopt(__doc__)
    r = requests.get(arguments['<url>'])
    if r.status_code == 200:
        print(parse_recipe(r.text))


if __name__ == '__main__':
    main()