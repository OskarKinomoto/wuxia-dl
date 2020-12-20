import os
from lxml import etree
import regex as re
from utils import extension_to_media_type
from lxml.builder import E
import shutil
import subprocess
from os.path import expanduser

from typing import Tuple

opf_namespace = "http://www.idpf.org/2007/opf"

dc_namespace = "http://purl.org/dc/elements/1.1/"
dc_metadata_nsmap = {"dc": dc_namespace}
dc = "{{{0}}}".format(dc_namespace)


class KindleBook:
    def __init__(self, book_title: str):
        self.book_title = book_title
        self.files = []
        self.author = "Wuxia"
        self.styles = {}

        try:
            os.mkdir(book_title)
        except FileExistsError:
            pass

    def create_mobi(self):
        subprocess.run(
            [
                expanduser("~") + "/kindlegen",
                f"{self.book_title}/{self.book_title}.opf",
                "-c1",
            ],
            capture_output=True,
        )

        try:
            os.unlink(f"{self.book_title}.mobi")
        except Exception:
            pass

        shutil.move(f"{self.book_title}/{self.book_title}.mobi", ".")
        shutil.rmtree(self.book_title)

    def add_chapter(self, chapter: Tuple[str, etree.Element]):
        title = chapter[0]

        body = E.body()

        etree.SubElement(body, "h3").text = title

        for child in chapter[1]:
            if child.tag == "p":
                body.append(self._cssize(child))

        html = E.html(
            {
                "xmlns": "http://www.w3.org/1999/xhtml",
                "{http://www.w3.org/XML/1998/namespace}lang": "en",
                "lang": "en",
            },
            E.head(
                E.meta(
                    {
                        "http-equiv": "Content-Type",
                        "content": "http://www.w3.org/1999/xhtml; charset=utf-8",
                    }
                ),
                E.title(title),
            ),
            body,
        )

        print(title)

        file_name = f"{title}.html"
        chapter_path = f"{self.book_title}/{title}.html"

        with open(chapter_path, "wb") as file:
            file.write(etree.tostring(html, method="html", pretty_print=True))

        self.files.append(file_name)

    def create_ncx(self):
        mbp_namespace = "http://mobipocket.com/ns/mbp"
        ncx_namespace = "http://www.daisy.org/z3986/2005/ncx/"
        ncx_nsmap = {None: ncx_namespace, "mbp": mbp_namespace}

        ncx = etree.Element(
            "ncx",
            nsmap=ncx_nsmap,
            attrib={
                "version": "2005-1",
                "{http://www.w3.org/XML/1998/namespace}lang": "en-GB",
            },
        )

        head = etree.SubElement(ncx, "head")
        etree.SubElement(
            head, "meta", attrib={"name": "dtb:uid", "content": self.book_title}
        )
        etree.SubElement(head, "meta", attrib={"name": "dtb:depth", "content": "2"})
        etree.SubElement(
            head, "meta", attrib={"name": "dtb:totalPageCount", "content": "0"}
        )
        etree.SubElement(
            head, "meta", attrib={"name": "dtb:maxPageNumber", "content": "0"}
        )

        title_text_element = etree.Element("text")
        title_text_element.text = self.book_title
        author_text_element = etree.Element("text")
        author_text_element.text = self.author

        etree.SubElement(ncx, "docTitle").append(title_text_element)
        etree.SubElement(ncx, "docAuthor").append(author_text_element)

        nav_map = etree.SubElement(ncx, "navMap")

        nav_contents_files = [fn for fn in self.files if re.search(r"\.html$", fn)]

        i = 1
        for f in nav_contents_files:
            nav_point_section = etree.SubElement(
                nav_map,
                "navPoint",
                attrib={"class": "chapter", "id": f"chapter_{i}", "playOrder": str(i)},
            )
            content = etree.Element("content", attrib={"src": f})
            title_text_element = etree.Element("text")
            title_text_element.text = f.replace(".html", "")
            nav_label = etree.SubElement(nav_point_section, "navLabel")
            nav_label.append(title_text_element)
            nav_point_section.append(content)
            i += 1

        ncx_file_name = f"{self.book_title}.ncx"

        with open(f"{self.book_title}/{ncx_file_name}", "wb") as fp:
            fp.write(b"<?xml version='1.0' encoding='utf-8'?>\n")
            fp.write(
                b'<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">\n'
            )
            fp.write(
                etree.tostring(
                    ncx, pretty_print=True, encoding="utf-8", xml_declaration=False
                )
            )

        self.files.append(ncx_file_name)

    def create_opf(self):
        package = etree.Element(
            "{{{0}}}package".format(opf_namespace),
            nsmap={None: opf_namespace},
            attrib={"version": "2.0", "unique-identifier": "uid"},
        )

        metadata = etree.SubElement(package, "metadata")

        dc_metadata = etree.Element("dc-metadata", nsmap=dc_metadata_nsmap)
        metadata.append(dc_metadata)
        etree.SubElement(dc_metadata, f"{dc}title").text = self.book_title
        etree.SubElement(dc_metadata, f"{dc}language").text = "en-US"
        etree.SubElement(dc_metadata, f"{dc}creator").text = "wuxia"
        etree.SubElement(dc_metadata, f"{dc}publisher").text = "wuxia"

        manifest = etree.SubElement(package, "manifest")

        for i, f in enumerate(self.files):
            item_id = re.sub(r"\..*$", "", f)
            extension = re.sub(r"^.*\.", "", f)
            etree.SubElement(
                manifest,
                "item",
                attrib={
                    "id": f"{item_id}_{i}",
                    "media-type": extension_to_media_type(extension),
                    "href": f,
                },
            )

        spine = etree.SubElement(package, "spine", attrib={"toc": "nav-contents"})

        for i, f in enumerate(self.files):
            if re.search(r"\.html$", f):
                item_id = re.sub(r"\..*$", "", f)
                etree.SubElement(spine, "itemref", attrib={"idref": f"{item_id}_{i}"})

        path = f"{self.book_title}/{self.book_title}.opf"

        with open(path, "wb") as fp:
            opf_element_tree = etree.ElementTree(package)
            opf_element_tree.write(
                fp, pretty_print=True, encoding="utf-8", xml_declaration=True
            )
            fp.flush()

        with open(path, "r") as fp:
            data = fp.read()

        data = data.replace("&amp;", "&")

        with open(path, "w") as fp:
            fp.write(data)

    def _cssize(self, element: etree.Element):
        attribs = element.attrib
        if "dir" in attribs:
            del attribs["dir"]

        spans = element.findall(".//span")

        for span in spans:
            span_attrs = span.attrib
            if "style" in span_attrs:
                if span_attrs["style"] not in self.styles:
                    self.styles[span_attrs["style"]] = f"span-style-{len(self.styles)}"

                span_attrs["class"] = self.styles[span_attrs["style"]]

                del span_attrs["style"]

        return element
