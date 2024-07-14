import requests
from bs4 import BeautifulSoup


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Scraper(metaclass=Singleton):
    def __init__(self):
        self.session = requests.Session()

    def fetch_page(self, url):
        response = self.session.get(url)
        return response

    def fetch_soup(self, response_content):
        soup = BeautifulSoup(response_content, "html.parser")
        return soup
