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
    goodfood recipe <url>
    goodfood subcategory <url>
    goodfood category <url>
    goodfood categories <url>
    goodfood scrape
"""

import aiohttp
import asyncio
import bs4
import docopt
import functools
import json
import pathlib as pl
import re
import signal
import sys
import urllib.parse

HTML_PARSER = 'lxml'

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
    strainer = bs4.SoupStrainer('div', {'id': 'main-content', 'class': 'row main node-type-recipe'})
    soup = bs4.BeautifulSoup(page, HTML_PARSER, parse_only=strainer)
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


def parse_category(url, page):
    soup = bs4.BeautifulSoup(page, 'lxml')
    main_content = soup.find('div', {'id': 'main-content'})
    links = [x['href'] for x in main_content.findAll('a')]
    regex = re.compile('^/recipes/collection/[^/]*$')
    links = filter(regex.match, links)
    return [urllib.parse.urljoin(url, x) for x in links]


def parse_categories(url, page):
    soup = bs4.BeautifulSoup(page, 'lxml')
    navigation = soup.find('div', {'id': 'nav-touch', 'class': 'nav-touch'})
    links = [x['href'] for x in navigation.findAll('a')]
    regex = re.compile('^/recipes/category/[^/]*$')
    links = filter(regex.match, links)
    return [urllib.parse.urljoin(url, x) for x in links]


def parse_subcategory(url, page):
    soup = bs4.BeautifulSoup(page, 'lxml')
    main_content = soup.find('div', {'id': 'main-content'})
    articles = main_content.findAll('article',
                                    {'itemtype': 'http://schema.org/Recipe'})
    ret = list()
    for article in articles:
        link = article.find('div', {'class': 'node-image'}).a['href']
        ret.append(urllib.parse.urljoin(url, link))
    return ret


class Crawler:
    def __init__(self, root_url, root_type, loop, max_tasks=50):
        self.root_url = root_url
        self.root_type = root_type
        self.loop = loop
        self.todo = set()
        self.busy = set()
        self.done = {}
        self.tasks = set()
        self.sem = asyncio.Semaphore(max_tasks)
        self.type_handler = {'recipe': self.scrape_recipe,
                             'subcategory': self.scrape_subcategory,
                             'category': self.scrape_category,
                             'full': self.scrape_categories}

        # connector stores cookies between requests and uses connection pool
        self.connector = aiohttp.TCPConnector(share_cookies=True, loop=loop)

    async def run(self):
        asyncio.Task(self.add_urls([self.root_url], self.root_type))  # Set initial work.
        await asyncio.sleep(1)
        while self.busy:
            await asyncio.sleep(1)

        self.connector.close()
        self.loop.stop()

    async def add_urls(self, urls, url_type='recipe'):
        for url in urls:
            url, frag = urllib.parse.urldefrag(url)
            if (url not in self.busy and
                    url not in self.done and
                    url not in self.todo):
                self.todo.add(url)
                await self.sem.acquire()
                task = asyncio.Task(self.type_handler[url_type](url))
                task.add_done_callback(lambda t: self.sem.release())
                task.add_done_callback(self.tasks.remove)
                self.tasks.add(task)

    async def get_page(self, url):
        with await self.sem:
            r = await aiohttp.get(url, connector=self.connector)
            if r.status != 200:
                r.close()
                raise Exception("Request Error {}".format(url))
            page = await r.text(encoding='utf-8')
            r.close()
            return page

    async def get_recipe(self, url):
        page = await self.get_page(url)
        return parse_recipe(page)

    async def scrape_recipe(self, url):
        file_name = url.split('/')[-1]
        file_path = pl.Path('goodfood') / file_name
        if file_path.is_file():
            self.todo.remove(url)
            return
        self.todo.remove(url)
        self.busy.add(url)
        try:
            recipe = await self.get_recipe(url)
        except Exception as exc:
            print('...', url, 'has error', repr(str(exc)))
            self.done[url] = False
        else:
            with file_path.open('w') as f:
                f.write(dump_json(recipe))
            self.busy.remove(url)
            self.done[url] = True

    async def get_subcategory(self, url):
        page = await self.get_page(url)
        recipes = parse_subcategory(url, page)
        return recipes

    async def scrape_subcategory(self, url):
        self.todo.remove(url)
        self.busy.add(url)
        try:
            recipes = await self.get_subcategory(url)
        except Exception as exc:
            print('...', url, 'has error', repr(str(exc)))
            self.done[url] = False
        else:
            asyncio.Task(self.add_urls(recipes, 'recipe'))
            self.done[url] = True
        self.busy.remove(url)

    async def get_category(self, url):
        page = await self.get_page(url)
        return parse_category(url, page)

    async def scrape_category(self, url):
        self.todo.remove(url)
        self.busy.add(url)
        try:
            subcategories = await self.get_category(url)
        except Exception as exc:
            print('...', url, 'has error', repr(str(exc)))
            self.done[url] = False
        else:
            asyncio.Task(self.add_urls(subcategories, 'subcategory'))
            self.done[url] = True
        self.busy.remove(url)

    async def get_categories(self, url):
        page = await self.get_page(url)
        return parse_categories(url, page)

    async def scrape_categories(self, url):
        self.todo.remove(url)
        self.busy.add(url)
        try:
            categories = await self.get_categories(url)
        except Exception as exc:
            print('...', url, 'has error', repr(str(exc)))
            self.done[url] = False
        else:
            asyncio.Task(self.add_urls(categories, 'category'))
            self.done[url] = True
        self.busy.remove(url)


def main():
    arguments = docopt.docopt(__doc__)
    loop = asyncio.get_event_loop()
    if arguments.get('recipe', False):
        c = Crawler(arguments['<url>'], 'recipe', loop)
    elif arguments.get('subcategory'):
        c = Crawler(arguments['<url>'], 'subcategory', loop)
    elif arguments.get('category'):
        c = Crawler(arguments['<url>'], 'category', loop)
    elif arguments.get('scrape'):
        c = Crawler(BASE_URL, 'full', loop)
    else:
        loop.stop()
        sys.exit(1)

    asyncio.Task(c.run())

    try:
        loop.add_signal_handler(signal.SIGINT, loop.stop)
    except RuntimeError:
        pass
    loop.run_forever()
    print('todo:', len(c.todo))
    print('busy:', len(c.busy))
    print('done:', len(c.done), '; ok:', sum(c.done.values()))
    print('tasks:', len(c.tasks))


if __name__ == '__main__':
    main()
