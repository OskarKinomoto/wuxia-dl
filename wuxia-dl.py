#!/usr/bin/env python3

import json
import os
import shutil
import subprocess
import sys
from collections import OrderedDict
from os.path import expanduser
from time import sleep
from typing import List, Tuple

import regex as re
import requests
from lxml import etree
from lxml.builder import E
from lxml.html import fragments_fromstring

from config import get_fullname, get_last_chapter, set_last_chapter, get_all_last_shortnames, get_code
from utils import eprint, extension_to_media_type
from bs4 import BeautifulSoup, element

from novelupdates import NuApi


parser = etree.XMLParser(recover=True, encoding='utf-8')

BASE_URL = "https://www.wuxiaworld.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/63.0"}

dc_namespace = "http://purl.org/dc/elements/1.1/"
dc_metadata_nsmap = {"dc": dc_namespace}
dc = "{{{0}}}".format(dc_namespace)

opf_namespace = "http://www.idpf.org/2007/opf"


def remove_attrs_from_children(bs):
    for tag in bs.find_all('a'):
        if 'chapter' in tag.get_text().lower():
            tag.extract()

def get_chapters(long_name: str) -> List[Tuple[str, str]]:
    novel_page = download_html(f"/novel/{long_name}")[0]
    matches = re.findall(
        r"<li class=\"chapter-item\">\n<a href=\"(.+)\">\n(<span>)?(.+)(</span>)?\n</a>\n</li>", novel_page
    )
    return [(url, title) for url, _, title, _ in matches]


def download_html(url: str, base = BASE_URL) -> str:
    response = requests.get(base + url, headers=HEADERS)
    return response.content.decode("utf-8"), response.url


def download_chapter(url: str) -> str:
    try:
        content, redirected_url = download_html('https:' + url, '')
        page = BeautifulSoup(content, 'html.parser')

        if 'wuxiaworld.com' not in redirected_url:
            return None

        try:
            title = page.find('title').get_text().split('-')[1].strip()
        except:
            title = page.find('title').get_text().strip()

        cs = page.find(class_='fr-view')
        [x.extract() for x in cs.findAll('script')]
        remove_attrs_from_children(cs)
        content = cs.decode_contents()
        return title, etree.fromstring('<div>' + content + '</div>', parser=parser)
    except:
        raise Exception(f'Problem with chapter - {url} - {redirected_url}')


def load_chapters(code: str, first_chapter: int):
    soup = NuApi._chapters(code)
    links = soup.find_all('a')
    links = [link['href'] for link in links if link.get_text()]
    links.reverse()
    return links[first_chapter:]


def create_opf(title: str, files: List[str]):
    package = etree.Element(
        "{{{0}}}package".format(opf_namespace),
        nsmap={None: opf_namespace},
        attrib={"version": "2.0", "unique-identifier": "uid"},
    )

    metadata = etree.SubElement(package, 'metadata')

    dc_metadata = etree.Element("dc-metadata", nsmap=dc_metadata_nsmap)
    metadata.append(dc_metadata)
    etree.SubElement(dc_metadata, f"{dc}title").text = title
    etree.SubElement(dc_metadata, f"{dc}language").text = 'en-US'
    etree.SubElement(dc_metadata, f"{dc}creator").text = 'wuxia'
    etree.SubElement(dc_metadata, f"{dc}publisher").text = 'wuxia'

    manifest = etree.SubElement(package, "manifest")

    for i, f in enumerate(files):
        item_id = re.sub('\..*$', '', f)
        extension = re.sub('^.*\.', '', f)
        etree.SubElement(
            manifest,
            "item",
            attrib={"id": f'{item_id}_{i}', "media-type": extension_to_media_type(extension), "href": f},
        )

    spine = etree.SubElement(package, "spine", attrib={"toc": "nav-contents"})

    for i, f in enumerate(files):
        if re.search('\.html$', f):
            item_id = re.sub('\..*$', '', f)
            etree.SubElement(spine, "itemref", attrib={"idref": f'{item_id}_{i}'})

    with open(f'{title}/{title}.opf', "wb") as fp:
        opf_element_tree = etree.ElementTree(package)
        opf_element_tree.write(fp, pretty_print=True, encoding="utf-8", xml_declaration=True)
        fp.flush()

    with open(f'{title}/{title}.opf', 'r') as fp:
        data = fp.read()

    data = data.replace('&amp;', '&')

    with open(f'{title}/{title}.opf', "w") as fp:
        fp.write(data)


styles = {}


def cssize(element: etree.Element):
    attribs = element.attrib
    if 'dir' in attribs:
        del attribs['dir']

    spans = element.findall(".//span")

    for span in spans:
        span_attrs = span.attrib
        if 'style' in span_attrs:
            if span_attrs['style'] not in styles:
                styles[span_attrs['style']] = f'span-style-{len(styles)}'

            span_attrs['class'] = styles[span_attrs['style']]

            del span_attrs['style']

    return element


def create_chapter(book_title: str, payload: Tuple[str, etree.Element]):
    title = payload[0]

    body = E.body()

    etree.SubElement(body, 'h3').text = title

    for child in payload[1]:
        if child.tag == 'p':
            body.append(cssize(child))

    html = E.html(
        {"xmlns": 'http://www.w3.org/1999/xhtml', "{http://www.w3.org/XML/1998/namespace}lang": 'en', "lang": 'en'},
        E.head(
            E.meta({'http-equiv': 'Content-Type', 'content': 'http://www.w3.org/1999/xhtml; charset=utf-8'}),
            E.title(title),
        ),
        body,
    )

    print(title, '-------', len(body))

    chapter_path = f'{book_title}/{title}.html'

    with open(chapter_path, 'wb') as file:
        file.write(etree.tostring(html, method='html', pretty_print=True))

    return f'{title}.html'


def create_ncx(book_title: str, files: List[str]):
    mbp_namespace = "http://mobipocket.com/ns/mbp"
    ncx_namespace = "http://www.daisy.org/z3986/2005/ncx/"
    ncx_nsmap = {None: ncx_namespace, "mbp": mbp_namespace}

    ncx = etree.Element(
        "ncx", nsmap=ncx_nsmap, attrib={"version": "2005-1", "{http://www.w3.org/XML/1998/namespace}lang": "en-GB"}
    )

    head = etree.SubElement(ncx, "head")
    etree.SubElement(head, "meta", attrib={"name": "dtb:uid", "content": book_title})
    etree.SubElement(head, "meta", attrib={"name": "dtb:depth", "content": "2"})
    etree.SubElement(head, "meta", attrib={"name": "dtb:totalPageCount", "content": "0"})
    etree.SubElement(head, "meta", attrib={"name": "dtb:maxPageNumber", "content": "0"})

    title_text_element = etree.Element("text")
    title_text_element.text = book_title
    author_text_element = etree.Element("text")
    author_text_element.text = 'wuxia'

    etree.SubElement(ncx, "docTitle").append(title_text_element)
    etree.SubElement(ncx, "docAuthor").append(author_text_element)

    nav_map = etree.SubElement(ncx, "navMap")

    nav_contents_files = [fn for fn in files if re.search('\.html$', fn)]

    i = 1
    for f in nav_contents_files:
        nav_point_section = etree.SubElement(
            nav_map, "navPoint", attrib={"class": "chapter", "id": f'chapter_{i}', "playOrder": str(i)}
        )
        content = etree.Element("content", attrib={"src": f})
        title_text_element = etree.Element("text")
        title_text_element.text = f.replace('.html', '')
        nav_label = etree.SubElement(nav_point_section, "navLabel")
        nav_label.append(title_text_element)
        nav_point_section.append(content)
        i += 1

    with open(f'{book_title}/{book_title}.ncx', "wb") as fp:
        fp.write(b"<?xml version='1.0' encoding='utf-8'?>\n")
        fp.write(
            b'<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">\n'
        )
        fp.write(etree.tostring(ncx, pretty_print=True, encoding="utf-8", xml_declaration=False))

    return f'{book_title}.ncx'


def download(short_name: str, long_name: str, code: str, first_chapter: int):
    print(short_name, long_name, first_chapter)

    chapters_refs = load_chapters(code, first_chapter)

    last_chapter = first_chapter + len(chapters_refs) - 1

    book_title = f'{long_name.capitalize().replace("-", " ")} {first_chapter}-{last_chapter}'

    try:
        os.mkdir(book_title)
    except FileExistsError:
        pass

    files = []

    for url in chapters_refs:
        chapter = download_chapter(url)
        if chapter is None:
            eprint('Chapter is not hosted on supported website :/ Skipping')
        else:
            file_path = create_chapter(book_title, chapter)
            files.append(file_path)

    files.append(create_ncx(book_title, files))
    create_opf(book_title, files)

    subprocess.run([expanduser("~") + "/kindlegen", f'{book_title}/{book_title}.opf', "-c1"], capture_output=True)

    try:
        os.unlink(f'{book_title}.mobi')
    except:
        pass

    shutil.move(f'{book_title}/{book_title}.mobi', '.')
    shutil.rmtree(book_title)

    set_last_chapter(short_name, last_chapter)
    print(short_name, long_name, first_chapter, last_chapter, len(chapters_refs))


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
    main()
