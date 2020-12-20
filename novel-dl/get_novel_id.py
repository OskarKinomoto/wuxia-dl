import json

import regex as re

from config import ABERATIONS, codes_file
from novelupdates import NuApi

ids = {}

for sname, name in ABERATIONS.items():
    id = NuApi.searchByName(name)
    try:
        ids[sname] = id[0]
    except Exception:
        ids[sname] = None

with open(codes_file, "w") as file:
    json.dump(ids, file, indent=4, sort_keys=True)
