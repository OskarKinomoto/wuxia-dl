#!/bin/env python

import sys
import requests
import regex as re
import subprocess
import os

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/57.0'}

#code = "atg"
code = "mga"
#code = "ige"
url_base = "http://www.wuxiaworld.com/{}-index/{}-chapter-{}"


def get_url(_code, n):
    return "http://www.wuxiaworld.com/{}-index/{}-chapter-{}".format(_code, _code, n)


out = ""
page_brk = ""

skip = False
first = 2275
last = 0

i = first
while True:
    response = requests.get(get_url(code, i), headers=headers)

    data = response.content.decode("utf-8")

    try:
        data = re.sub("<p>Previous Chapter <span style=\"float: right\">Next Chapter</span></p>", "", data)
        m = re.search(r"<div itemprop=\"articleBody\">(.*?)</div>", data, re.DOTALL)
        chapter_c = m.group(1)
        chapter_c = re.sub("<(/)?(a|hr)[^>]*>", '', chapter_c)
        if '<p><img src="http://moonbunnycafe.com/wp-content/uploads/2015/08/polebunny.gif" alt="" /><br />' in chapter_c:
            last = i - 1
            break
        chapter = page_brk + "<h3>Chapter " + str(i) + "</h3>\n" + chapter_c
        page_brk = "<mbp:pagebreak>"
        out += chapter
        eprint(i)
        skip = False
    except Exception as e:
        if skip:
            last = i - 2
            break
        skip = True

    i += 1

if last < first:
    print("No new chapters for {}! Sorry... ☹".format(code))
else:
    out = re.sub(r'<p>Previous Chapter <span style="float: right">Next Chapter</span></p>', '', out)
    out = "<!DOCTYPE html><head> <meta charset=\"UTF-8\"></head><body>" + out + "</body>"

    path = code.upper() + " " + str(first) + "-" + str(last) + ".html"
    file = open(path, "wb")
    file.write(out.encode("ascii", "xmlcharrefreplace"))

    subprocess.call(["kindlegen", path])

    os.unlink(path)
