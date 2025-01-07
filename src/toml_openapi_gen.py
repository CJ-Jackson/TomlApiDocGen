#!/usr/bin/env python3
import json
import os.path
import pathlib
import sys
import tomllib
from collections.abc import Iterator
from functools import reduce

if not os.path.exists("api_paths/openapi.toml"):
    print("`api_paths/openapi.toml` does not exists", file=sys.stderr)
    exit(100)

api_real_path = os.path.realpath("api_paths")

api_paths = pathlib.Path(api_real_path)

docs = []
methods = ["get", "head", "options", "trace", "post", "put", "delete", "patch", "connect"]
for method in methods:
    docs += list(api_paths.glob(f"**/{method}.toml"))

docs.sort()


open_api_data = {}
try:
    with open("api_paths/openapi.toml", "rb") as f:
        open_api_data = tomllib.load(f)
except (OSError, tomllib.TOMLDecodeError) as e:
    print(e.__str__(), file=sys.stderr)
    exit(100)

open_api_data["paths"] = {}

class TomlValidationError(Exception): pass


def open_and_yield_path_detail() -> Iterator[dict]:
    for doc in docs:
        doc = str(doc)
        with open(doc, "rb") as docf:
            doc_data = tomllib.load(docf)
            match doc_data:
                case {"openapi": dict()}:
                    pass
                case _:
                    raise TomlValidationError("Must have `openapi.summary`")
            yield {
                "paths": {
                    os.path.dirname(doc.removeprefix(api_real_path)): {
                        os.path.basename(doc).removesuffix(".toml").lower(): doc_data["openapi"]
                    }
                }
            }

def update_dicts(dict1: dict, dict2: dict):
    for key, value in dict2.items():
        if type(value) is dict and key in dict1:
            update_dicts(dict1[key], value)
        else:
            dict1[key] = value
    return dict1


for path in open_and_yield_path_detail():
    open_api_data = update_dicts(open_api_data, path)

with open(f"{api_real_path}/openapi.json", "w", encoding='utf-8') as f:
    json.dump(open_api_data, f, indent="  ")