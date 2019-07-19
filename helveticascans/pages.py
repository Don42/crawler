import requests

from helveticascans.uri import pattern, get_image_uri


class Page:
    def __init__(self, number, uri):
        self.page_number = int(number)
        self.page_uri = uri
        self._image_uri = None

    @property
    def uri(self) -> str:
        if self._image_uri is None:
            self._image_uri = get_image_uri(self.page_uri)
        return self._image_uri

    @classmethod
    def from_uri(cls, uri):
        match = pattern.search(uri)
        if not match:
            return
        elif match.group(2) is not None:
            assert match.group(2) == "5"
            return Cover(match.group(1), uri)
        else:
            return cls(match.group(1), uri)

    def __gt__(self, other):
        if isinstance(other, Cover):
            return self.page_number > other.page_number + 0.5
        else:
            return self.page_number > other.page_number

    def __str__(self):
        return f"Page {self.page_number}"

    def get_content(self):
        return requests.get(self.uri).content

    @property
    def suffix(self):
        return self.uri.split('.')[-1]


class Cover(Page):
    def __init__(self, number, uri):
        super().__init__(number, uri)

    def __gt__(self, other):
        if isinstance(other, Cover):
            return self.page_number + 0.5 > other.page_number + 0.5
        else:
            return self.page_number + 0.5 > other.page_number

    def __str__(self):
        return f"Cover {self.page_number}"