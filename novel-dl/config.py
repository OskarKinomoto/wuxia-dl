import json
import sys

from .utils import eprint

aberations_file = "wuxia-novels.json"
chapters_file = "wuxia-last-chapter.json"
codes_file = "novel-updates.json"

ABERATIONS = {}
CODES = {}

with open(aberations_file) as novels:
    ABERATIONS = json.load(novels)

with open(codes_file) as codes:
    CODES = json.load(codes)

def get_fullname(shortname: str):
    if shortname in ABERATIONS:
        return ABERATIONS[shortname]
    eprint(f"Can't find full name for {shortname}. Please add it to {aberations_file} file.")
    exit(1)

def get_code(shortname: str):
    if shortname in CODES:
        return CODES[shortname]
    eprint(f"Can't find code for {shortname}. Please add it to {codes_file} file.")
    exit(1)

def get_last_chapter(shortname: str):
    try:
        with open(chapters_file, 'r') as file:
            data = json.load(file)
            if shortname in data:
                return data[shortname]
            return 0
    except Exception:
        return 0

def set_last_chapter(shortname: str, chapter: int):
    data = {}
    try:
        with open(chapters_file, 'r') as file:
            data = json.load(file)
    except Exception:
        pass

    data[shortname] = chapter

    with open(chapters_file, 'w') as file:
        json.dump(data, file, indent=4, sort_keys=True)

def get_all_last_shortnames():
    try:
        with open(chapters_file, 'r') as file:
            data = json.load(file)
            return list(data.keys())
    except Exception:
        return []
