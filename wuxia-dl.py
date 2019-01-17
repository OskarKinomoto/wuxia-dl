import sys
import requests
import regex as re
from time import sleep
from collections import OrderedDict
import subprocess
import os
from os.path import expanduser

from lxml import etree
parser = etree.XMLParser(recover=True)

BASE_URL = "https://www.wuxiaworld.com"
headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/63.0'}

aberation = {
    "atg": "against-the-gods",
    "mga": "martial-god-asura",
    "ige": "imperial-god-emperor",
    "sotr": "sovereign-of-the-three-realms",
    "tdg": "tales-of-demons-and-gods",
    "te": "talisman-emperor",
    "womw": "warlock-of-the-magus-world",
}

def get_chapters(long_name: str) -> [(str, str)]:
    novel_page = download_html("/novel/{}".format(long_name))
    m = re.findall(r"<li class=\"chapter-item\">\n<a href=\"(.+)\">\n<span>(.+)</span>\n</a>\n</li>", novel_page)
    return m

def download_html(url: str) -> str:
    try:
        response = requests.get(BASE_URL + url, headers=headers)
        return response.content.decode("utf-8")
    except:
        raise

def download_chapter(url: str) -> str:
    print(url)
    html = download_html(url)
    dom = etree.fromstring(html, parser=parser)
    body = dom.find(".//body")
    divs = body.findall(".//div")

    divs = [etree.tostring(d).decode("utf-8") for d in divs if d.attrib.get("class") is not None and d.attrib.get("class") == "fr-view"]

    ch = max(divs, key=len)

    ch = re.sub("<(/)?(a|hr|div)[^>]*>", '', ch)
    ch = re.sub("Previous Chapter", '', ch)
    ch = re.sub("Next Chapter", '', ch)
    ch = re.sub("<p>(<br>)?</p>", '', ch)

    return ch

def download(short_name: str, long_name: str, first_chapter: int, chapter_count: int = 0):
    chapters = OrderedDict()
    for _ in range(0, 5):
        chs = get_chapters(long_name)
        for ch in chs:
            m = re.search(r"chapter-([0-9]+)-?([0-9]*)", ch[0])
            ch_num = m.group(1)
            try:
                ch_num += "." + str(int(m.group(2)))
            except:
                pass
            chapters[float(ch_num)] = ch

    if chapter_count == 0:
        chapter_count = len(chapters) - first_chapter

    chapters = OrderedDict(sorted(chapters.items()))

    chapters = list(chapters.items())[first_chapter:first_chapter+chapter_count]

    print(short_name, long_name, first_chapter, chapter_count, len(chapters))

    out = ""
    page_brk = ""

    for ch in chapters:
        chapter = page_brk + "<h3>" + ch[1][1] + "</h3>\n" + download_chapter(ch[1][0])
        page_brk = "\n\n<mbp:pagebreak>\n\n"
        out += chapter

    out = "<!DOCTYPE html>\n<head>\n\t<meta charset=\"UTF-8\">\n</head>\n\n<body>\n\n" + out + "\n\n</body>\n\n</html>"
    # print(out)
    path = short_name.upper() + " " + str(first_chapter) + "-" + str(first_chapter + chapter_count - 1) + ".html"
    file = open(path, "wb")
    file.write(out.encode("ascii", "xmlcharrefreplace"))
    file.flush()
    subprocess.call([expanduser("~") + "/kindlegen", path, "-c1"])
    os.unlink(path)

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def print_usage():
    eprint("Usage: ")
    eprint("    wuxia-dl <SHORT_NAME> [FIRST_CHAPTER] [CHAPTER_COUNT]")
    sys.exit(1)

if __name__ == "__main__":
    arg_len = len(sys.argv)
    if arg_len < 2:
        print_usage()
    short_name = sys.argv[1]
    long_name = aberation[short_name]

    if arg_len < 3:
        first_chapter = 0
    else:
        first_chapter = int(sys.argv[2])

    if arg_len < 4:
        ch_count = 0
    else:
        ch_count = int(sys.argv[3])

    download(short_name, long_name, first_chapter, ch_count)

