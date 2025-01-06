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

docs = list(api_paths.glob("**/get.toml"))
docs += list(api_paths.glob("**/head.toml"))
docs += list(api_paths.glob("**/options.toml"))
docs += list(api_paths.glob("**/trace.toml"))
docs += list(api_paths.glob("**/post.toml"))
docs += list(api_paths.glob("**/put.toml"))
docs += list(api_paths.glob("**/delete.toml"))
docs += list(api_paths.glob("**/patch.toml"))
docs += list(api_paths.glob("**/connect.toml"))
docs.sort()


def open_and_add_path_detail() -> Iterator[dict]:
    for doc in docs:
        doc = str(doc)
        with open(doc, "rb") as docf:
            doc_data = tomllib.load(docf)
            doc_data["endpoint"] = os.path.dirname(doc.removeprefix(api_real_path))
            doc_data["method"] = os.path.basename(doc).removesuffix(".toml").upper()
            yield doc_data


try:
    sorted_docs = list(open_and_add_path_detail())
except (OSError, tomllib.TOMLDecodeError) as e:
    print(e.__str__())
    exit(100)

group_docs = {}
for i in range(len(sorted_docs)):
    if sorted_docs[i]["group"] not in group_docs:
        group_docs[sorted_docs[i]["group"]] = []
    group_docs[sorted_docs[i]["group"]].append(sorted_docs[i])


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
                yield f"```{data.get('type', '').strip()}"
                yield data.get('content', '').strip()
                yield "```"
                if "note" in data:
                    yield data.get('note', '')


with open(f"{api_real_path}/api_doc.md", "w", encoding='utf-8') as f:
    print("# API Doc", file=f)
    print("\n".join(create_doc()), file=f)
