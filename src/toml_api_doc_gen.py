#!/usr/bin/env python3
import os.path
import pathlib
import sys
import tomllib
from collections.abc import Iterator

if not os.path.exists("api_paths"):
    print("`api_paths` does not exists", file=sys.stderr)
    exit(100)

api_real_path = os.path.realpath("api_paths")

api_paths = pathlib.Path(api_real_path)

docs = []
methods = ["get", "head", "options", "trace", "post", "put", "delete", "patch", "connect"]
for method in methods:
    docs += list(api_paths.glob(f"**/{method}.toml"))

docs.sort()


class TomlValidationError(Exception): pass


def open_and_add_path_detail() -> Iterator[dict]:
    for doc in docs:
        doc = str(doc)
        with open(doc, "rb") as docf:
            doc_data = tomllib.load(docf)
            match doc_data:
                case {"group": str()}:
                    pass
                case _:
                    raise TomlValidationError("Must have `group`")
            doc_data["endpoint"] = os.path.dirname(doc.removeprefix(api_real_path))
            doc_data["method"] = os.path.basename(doc).removesuffix(".toml").upper()
            yield doc_data


try:
    sorted_docs = list(open_and_add_path_detail())
except (OSError, tomllib.TOMLDecodeError, TomlValidationError) as e:
    print(e.__str__())
    exit(100)

group_docs = {}
for i in range(len(sorted_docs)):
    if sorted_docs[i]["group"].strip() not in group_docs:
        group_docs[sorted_docs[i]["group"].strip()] = []
    group_docs[sorted_docs[i]["group"].strip()].append(sorted_docs[i])


def create_doc() -> Iterator[str]:
    groups = list(group_docs.keys())
    groups.sort()
    for group in groups:
        docs = group_docs[group]
        yield f"## {group}"
        for doc in docs:
            yield f"### {doc['method'].strip()}: `{doc['endpoint'].strip()}` {doc.get('title', '').strip()}"
            yield doc.get("summary", "")
            for key, data in doc.get("data", {}).items():
                yield f"#### {key}"
                yield f"```{data.get('type', '').strip()}\n{data.get('content', '').strip()}\n```"
                if "note" in data:
                    yield data.get('note', '').strip()


with open(f"{api_real_path}/api_doc.md", "w", encoding='utf-8') as f:
    print("# API Doc", file=f)
    print("\n\n".join(create_doc()), file=f)
