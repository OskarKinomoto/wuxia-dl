#!/bin/env python

#from __future__ import print_function
import sys
import requests
import regex as re

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/55.0'}

#code = "mga"
code = "ige"
url_base = "http://www.wuxiaworld.com/" + code + "-index/" + code + "-chapter-"

def get_url(url_base, n):
    return url_base + str(n) + "/"

out = ""
page_brk = ""
for i in range(0,131):
    response = requests.get(get_url(url_base, i), headers=headers)

    data = response.content.decode("utf-8")
    
    if code == "ige":
        data = re.sub("<p>Previous Chapter <span style=\"float: right\">Next Chapter</span></p>", "", data)
        m = re.search(r"<div itemprop=\"articleBody\">(.*?)</div>", data, re.DOTALL)
        chapter_c = m.group(1)
        chapter_c = re.sub("<(/)?(a|hr)[^>]*>", '', chapter_c)
        chapter = page_brk + "<h3>Chapter " + str(i) + "</h3>\n" + chapter_c
        page_brk = "<mbp:pagebreak>"
        out += chapter
        eprint(i)
        continue

    data = re.sub("<strong>Please support the translation through my <a href=\"https://www\.patreon\.com/YangWenLi\">patreon</a> if you are able to\.<br />", "", data)
    data = re.sub("There will be early access to future chapters :\)\.</strong></p>", "", data)
    m = re.search(r"<div itemprop=\"articleBody\">(.*)<(strong|b)>(.*)</(b|strong)>(.*)(<a [^>]*>)?Previous Chapter(</a>)?(.*)?(<a [^>]*>)?Next Chapter(</a>)?", data, re.DOTALL)

    title = m.group(3)
    chapter_c = m.group(5)
    
    if chapter_c.startswith('</p>'):
        chapter_c = chapter_c[4:]
    
    if chapter_c.endswith('<p>'):
        chapter_c = chapter_c[:-3]
        
    chapter_c = re.sub("<(/)?(a|hr)[^>]*>", '', chapter_c)
    chapter = page_brk + "<h3>" + title + "</h3>\n" + chapter_c
    page_brk = "<mbp:pagebreak>"
    out += chapter
    eprint(i)

outt = "<!DOCTYPE html><head> <meta charset=\"UTF-8\"></head><body>" + out + "</body>"

sys.stdout.buffer.write(outt.encode("ascii","xmlcharrefreplace"))
