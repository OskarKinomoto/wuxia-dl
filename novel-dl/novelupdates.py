import regex as re
import requests
from bs4 import BeautifulSoup, element


class NuApi:
    @staticmethod
    def request(data):
        # print('NuApi request data - ', data)
        response = requests.post(
            'https://www.novelupdates.com/wp-admin/admin-ajax.php',
            data=data,
            headers={
                'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:80.0) Gecko/20100101 Firefox/80.0',
            }
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup

    @classmethod
    def _searchByName(cls, name):
        return cls.request({
            'action': 'nd_ajaxsearchmain',
            'strType': 'desktop',
            'strOne': name.replace('-', ' '),
            'strSearchType': 'series',
        })

    @classmethod
    def searchByName(cls, name):
        soup = cls._searchByName(name)
        imgs = soup.findAll('img')
        return [re.findall(r'/series_([0-9]+)\.[a-zA-Z0-9]+', img['src'])[0] for img in imgs]

    @classmethod
    def _chapters(cls, code: str):
        return cls.request({
            'action': 'nd_getchapters',
            'mypostid': code,
        })
