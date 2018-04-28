#!/bin/env python

import sys
import requests
import regex as re
import subprocess
import os
from os.path import expanduser

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/57.0'}

code = "mga"
first = 2568

name_map = {
        "atg" : "against-the-gods",
        "mga" : "martial-god-asura",
        "ige" : "imperial-god-emperor",
        "sotr" : "sovereign-of-the-three-realms",
    }

def get_url(_code, n):
    name = name_map[_code]
    return "http://www.wuxiaworld.com/novel/{}/{}-chapter-{}".format(name, _code, n)


out = ""
page_brk = ""

skip = False
last = 0

next_url = None

i = first
while True:
    if next_url is None:
        url = get_url(code, i)
    else:
        url = next_url

    print(url)

    response = requests.get(url, headers=headers)

    data = response.content.decode("utf-8")

    m = re.search(r"<div class=\"fr-view\">(.*?)</div>", data, re.DOTALL)
    chapter_c = m.group(1)
    chapter_c = re.sub("<(/)?(a|hr)[^>]*>", '', chapter_c)

    if "Teaser" in data:
        last = i - 1
        break

    if '<p><img src="http://moonbunnycafe.com/wp-content/uploads/2015/08/polebunny.gif" alt="" /><br />' in chapter_c:
        last = i - 1
        break
    
    chapter = page_brk + "<h3>Chapter " + str(i) + "</h3>\n" + chapter_c
    page_brk = "<mbp:pagebreak>"
    out += chapter

    m = re.search(r"var NEXT_CHAPTER = '(.*?)'", data)
    if m is None:
        break

    next_url = "http://www.wuxiaworld.com" + m.group(1)

    mm = re.findall(r"\d+", m.group(1))
    last = int(mm[0])

    i += 1

if last < first:
    print("No new chapters for {}! Sorry... ☹".format(name_map[code]))
else:
    out = "<!DOCTYPE html><head> <meta charset=\"UTF-8\"></head><body>" + out + "</body>"

    path = code.upper() + " " + str(first) + "-" + str(last) + ".html"
    file = open(path, "wb")
    file.write(out.encode("ascii", "xmlcharrefreplace"))
    subprocess.call([expanduser("~") + "/kindlegen", path])
    os.unlink(path)
