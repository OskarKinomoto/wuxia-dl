#!/usr/bin/env python3

import json
import os
import subprocess
import sys
from collections import OrderedDict
from os.path import expanduser
from time import sleep

import regex as re
import requests
from lxml import etree
from typing import List, Tuple

parser = etree.XMLParser(recover=True)

BASE_URL = "https://www.wuxiaworld.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/63.0"}

CHAPTER_BREAK = """

<mbp:pagebreak>

"""

with open("wuxia-novels.json") as novels:
    aberation = json.load(novels)


def get_chapters(long_name: str) -> List[Tuple[str, str]]:
    novel_page = download_html(f"/novel/{long_name}")
    matches = re.findall(
        r"<li class=\"chapter-item\">\n<a href=\"(.+)\">\n(<span>)?(.+)(</span>)?\n</a>\n</li>", novel_page
    )
    return [(url, title) for url, _, title, _ in matches]


def download_html(url: str) -> str:
    response = requests.get(BASE_URL + url, headers=HEADERS)
    return response.content.decode("utf-8")


def download_chapter(url: str) -> str:
    html = download_html(url)
    dom = etree.fromstring(html, parser=parser)
    body = dom.find(".//body")
    divs = body.findall(".//div")

    divs = [etree.tostring(d).decode("utf-8") for d in divs if d.attrib.get("class") == "fr-view"]

    ch = max(divs, key=len)

    ch = re.sub("<(/)?(a|hr|div)[^>]*>", "", ch)
    ch = re.sub("Previous Chapter", "", ch)
    ch = re.sub("Next Chapter", "", ch)
    ch = re.sub("<p>(<br>)?</p>", "", ch)

    return ch


def load_chapters(long_name: str, first_chapter: int, chapter_count: int):
    chapters = OrderedDict()

    for _ in range(0, 20):
        chs = get_chapters(long_name)
        for ch in chs:
            m = re.search(r'chapter-([0-9]+)-?([0-9]*)', ch[0])
            ch_num = m.group(1)
            try:
                ch_num += "." + str(int(m.group(2)))
            except:
                pass
            chapters[float(ch_num)] = ch

    if chapter_count == 0:
        chapter_count = len(chapters) - first_chapter

    chapters = OrderedDict(sorted(chapters.items()))

    return list(chapters.items())[first_chapter : first_chapter + chapter_count]


def download(short_name: str, long_name: str, first_chapter: int, chapter_count: int = 0):
    chapters_refs = load_chapters(long_name, first_chapter, chapter_count)



    chapters = [f'<h3>{name}</h3>\n{download_chapter(url)}' for _, (url, name) in chapters_refs]
    out = f'''
        <!DOCTYPE html>
            <head>
                <meta charset="UTF-8">
            </head>

            <body>
                {CHAPTER_BREAK.join(chapters)}
            </body>
        </html>
    '''

    path = f'{short_name.upper()} {first_chapter}-{first_chapter + chapter_count - 1}.html'

    with open(path, "wb") as file:
        file.write(out.encode("ascii", "xmlcharrefreplace"))
        file.flush()

    subprocess.call([expanduser("~") + "/kindlegen", path, "-c1"])
    os.unlink(path)

    print(short_name, long_name, first_chapter, chapter_count, len(chapters_refs))


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def print_usage():
    eprint("Usage: ")
    eprint("    wuxia-dl <SHORT_NAME> [FIRST_CHAPTER] [CHAPTER_COUNT]")
    sys.exit(1)


def main():
    arg_len = len(sys.argv)
    if arg_len < 2:
        print_usage()
    short_name = sys.argv[1]

    try:
        long_name = aberation[short_name.lower()]
    except KeyError:
        print(f'Aberation "{short_name}" not found :(')
        exit(1)

    if arg_len < 3:
        first_chapter = 0
    else:
        first_chapter = int(sys.argv[2])

    if arg_len < 4:
        ch_count = 0
    else:
        ch_count = int(sys.argv[3])

    download(short_name, long_name, first_chapter, ch_count)


if __name__ == "__main__":
    main()
