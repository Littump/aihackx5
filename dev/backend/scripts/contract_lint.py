import sys
from pathlib import Path
from typing import Any

import yaml


def collect_refs(node: Any, refs: list[str]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str):
                refs.append(value)
            else:
                collect_refs(value, refs)
    elif isinstance(node, list):
        for item in node:
            collect_refs(item, refs)


def resolve(spec: dict[str, Any], ref: str) -> bool:
    node: Any = spec
    for part in ref.removeprefix("#/").split("/"):
        if not isinstance(node, dict) or part not in node:
            return False
        node = node[part]
    return True


def main(path: str) -> int:
    spec = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    refs: list[str] = []
    collect_refs(spec, refs)
    broken = sorted({ref for ref in refs if not resolve(spec, ref)})
    for ref in broken:
        print(f"broken $ref: {ref}")
    paths = len(spec.get("paths", {}))
    schemas = len(spec.get("components", {}).get("schemas", {}))
    print(f"paths: {paths}, schemas: {schemas}, refs: {len(refs)}, broken: {len(broken)}")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
