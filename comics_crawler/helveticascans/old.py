from .uri import parse_page_links


def compare(x):
    _, (i, j) = x
    return int(i) * 10 + int(j or 0)


def get_volume(number: int, page_list):
    page_links = list(sorted(parse_page_links(page_list), key=compare))
    cover_indices = [0] + get_cover_page_indices(page_links) + [len(page_links) - 1]
    cover = page_links[cover_indices[number]]
    pages = page_links[cover_indices[number-1]:cover_indices[number]]
    return [cover] + pages


def get_cover_page_indices(page_links):
    return [i
            for i, (url, (x, y)) in enumerate(page_links)
            if y is not None]