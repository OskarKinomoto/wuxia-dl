#!/usr/bin/env python3

import sys
from typing import List, Tuple

import regex as re
import requests
from lxml import etree

from config import (
    get_fullname,
    get_last_chapter,
    set_last_chapter,
    get_all_last_shortnames,
    get_code,
)
from utils import eprint
from bs4 import BeautifulSoup

from novelupdates import NuApi
from kindle import KindleBook

parser = etree.XMLParser(recover=True, encoding="utf-8")

BASE_URL = "https://www.wuxiaworld.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/63.0"
}


def remove_attrs_from_children(bs):
    for tag in bs.find_all("a"):
        if "chapter" in tag.get_text().lower():
            tag.extract()


def get_chapters(long_name: str) -> List[Tuple[str, str]]:
    novel_page = download_html(f"/novel/{long_name}")[0]
    matches = re.findall(
        r"<li class=\"chapter-item\">\n<a href=\"(.+)\">\n(<span>)?(.+)(</span>)?\n</a>\n</li>",
        novel_page,
    )
    return [(url, title) for url, _, title, _ in matches]


def download_html(url: str, base=BASE_URL) -> str:
    response = requests.get(base + url, headers=HEADERS)
    return response.content.decode("utf-8"), response.url


def download_chapter(url: str) -> str:
    try:
        content, redirected_url = download_html("https:" + url, "")
        page = BeautifulSoup(content, "html.parser")

        if "wuxiaworld.com" not in redirected_url:
            return None

        try:
            title = page.find("title").get_text().split("-")[1].strip()
        except Exception:
            title = page.find("title").get_text().strip()

        cs = page.find(class_="fr-view")
        [x.extract() for x in cs.findAll("script")]
        remove_attrs_from_children(cs)
        content = cs.decode_contents()
        return title, etree.fromstring("<div>" + content + "</div>", parser=parser)
    except Exception:
        raise Exception(f"Problem with chapter - {url} - {redirected_url}")


def load_chapters(code: str, first_chapter: int):
    soup = NuApi._chapters(code)
    links = soup.find_all("a")
    links = [link["href"] for link in links if link.get_text()]
    links.reverse()
    return links[first_chapter:]


def download(short_name: str, long_name: str, code: str, first_chapter: int):
    fancy_name = long_name.replace("-", " ").capitalize()

    print(fancy_name)
    print("".join(["-" for _ in range(len(fancy_name))]))
    print()

    chapters_refs = load_chapters(code, first_chapter)

    if len(chapters_refs) < 1:
        print(f"No new chapters :(\n\n")
        return

    last_chapter = first_chapter + len(chapters_refs) - 1

    book_title = (
        f'{long_name.capitalize().replace("-", " ")} {first_chapter}-{last_chapter}'
    )

    book = KindleBook(book_title)

    for url in chapters_refs:
        chapter = download_chapter(url)
        if chapter is None:
            eprint("Chapter is not hosted on supported website :/ Skipping")
        else:
            book.add_chapter(chapter)

    book.create_ncx()
    book.create_opf()
    book.create_mobi()

    set_last_chapter(short_name, last_chapter)
    print()
    print(fancy_name, "-", len(chapters_refs), "new chapters!")
    print("\n")


def print_usage():
    eprint("Usage: ")
    eprint("    wuxia-dl <SHORT_NAME> [FIRST_CHAPTER]")
    exit(1)


def download_all_from_last():
    shornames = get_all_last_shortnames()

    for short_name in shornames:
        full_name = get_fullname(short_name)
        first_chapter = get_last_chapter(short_name) + 1
        code = get_code(short_name)
        download(short_name, full_name, code, first_chapter)


def main():
    arg_len = len(sys.argv)
    if arg_len < 2:
        download_all_from_last()
        exit(0)

    short_name = sys.argv[1]
    full_name = get_fullname(short_name)
    code = get_code(short_name)

    if arg_len < 3:
        first_chapter = get_last_chapter(short_name) + 1
    else:
        first_chapter = int(sys.argv[2])

    download(short_name, full_name, code, first_chapter)


if __name__ == "__main__":
    print()
    main()
