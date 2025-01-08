#!/usr/bin/env python3
import json
import os.path
import pathlib
import sys
import tomllib
from collections.abc import Iterator

if not os.path.exists("api_paths/openapi.toml"):
    print("`api_paths/openapi.toml` does not exists", file=sys.stderr)
    exit(100)

api_real_path = os.path.realpath("api_paths")

api_paths = pathlib.Path(api_real_path)

paths_data = []
methods = ["get", "head", "options", "trace", "post", "put", "delete", "patch", "connect"]
for method in methods:
    paths_data += list(api_paths.glob(f"**/{method}.toml"))

paths_data.sort()

components_data = list(api_paths.glob(f"**/components.toml"))

open_api_data = {}
try:
    with open("api_paths/openapi.toml", "rb") as f:
        open_api_data = tomllib.load(f)
except (OSError, tomllib.TOMLDecodeError) as e:
    print(e.__str__(), file=sys.stderr)
    exit(100)

class TomlValidationError(Exception): pass


def open_and_yield_path_detail() -> Iterator[dict]:
    for path_data in paths_data:
        path_data = str(path_data)
        with open(path_data, "rb") as docf:
            doc_data = tomllib.load(docf)
            has_paths = False
            has_webhooks = False
            match doc_data:
                case {"openapi_paths": dict(), "openapi_webhooks": dict()}:
                    has_paths = True
                    has_webhooks = True
                case {"openapi_paths": dict()}:
                    has_paths = True
                case {"openapi_webhooks": dict()}:
                    has_webhooks = True
                case _:
                    raise TomlValidationError("Must have `openapi_paths`(dict) or `openapi_webhooks`(dict)")
            if has_paths:
                yield {
                    "paths": {
                        os.path.dirname(path_data.removeprefix(api_real_path)): {
                            os.path.basename(path_data).removesuffix(".toml").lower(): doc_data["openapi_paths"]
                        }
                    }
                }
            if has_webhooks:
                yield {
                    "webhooks": {
                        os.path.dirname(path_data.removeprefix(api_real_path)): {
                            os.path.basename(path_data).removesuffix(".toml").lower(): doc_data["openapi_webhooks"]
                        }
                    }
                }


def open_and_yield_components_detail() -> Iterator[dict]:
    for component_data in components_data:
        component_data = str(component_data)
        with open(component_data, "rb") as docf:
            doc_data = tomllib.load(docf)
            match doc_data:
                case {"openapi_components": dict()}:
                    pass
                case _:
                    raise TomlValidationError("Must have `openapi_path`")
            yield {
                "components": doc_data["openapi_components"]
            }


def update_dicts(dict1: dict, dict2: dict):
    for key, value in dict2.items():
        if type(value) is dict and key in dict1:
            update_dicts(dict1[key], value)
        else:
            dict1[key] = value
    return dict1


try:
    for path in open_and_yield_path_detail():
        open_api_data = update_dicts(open_api_data, path)
    for component in open_and_yield_components_detail():
        open_api_data = update_dicts(open_api_data, component)
except (OSError, tomllib.TOMLDecodeError) as e:
    print(e.__str__(), file=sys.stderr)
    exit(100)


with open(f"{api_real_path}/openapi.json", "w", encoding='utf-8') as f:
    json.dump(open_api_data, f, indent="  ")