import json

from utils import eprint

aberations_file = "wuxia-novels.json"
chapters_file = "wuxia-last-chapter.json"

ABERATIONS = {}

with open(aberations_file) as novels:
    ABERATIONS = json.load(novels)

def get_fullname(shortname: str):
    if shortname in ABERATIONS:
        return ABERATIONS[shortname]
    eprint(f"Can't find full name for {shortname}. Please add it to {aberations_file} file.")
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
        json.dump(data, file)
