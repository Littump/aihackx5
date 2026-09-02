import sys
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import create_app

METHODS = {"get", "post", "put", "patch", "delete"}


def deref(spec: dict[str, Any], node: Any) -> Any:
    while isinstance(node, dict) and "$ref" in node:
        target: Any = spec
        for part in node["$ref"].removeprefix("#/").split("/"):
            target = target[part]
        node = target
    return node


def property_names(spec: dict[str, Any], schema: Any) -> set[str]:
    schema = deref(spec, schema)
    if not isinstance(schema, dict):
        return set()
    names = set(schema.get("properties", {}).keys())
    for part in schema.get("allOf", []):
        names |= property_names(spec, part)
    variants = [v for v in schema.get("oneOf", []) + schema.get("anyOf", [])]
    for variant in variants:
        resolved = deref(spec, variant)
        if isinstance(resolved, dict) and resolved.get("type") != "null":
            names |= property_names(spec, resolved)
    return names


def success_schema(spec: dict[str, Any], operation: dict[str, Any]) -> Any:
    for status in ("200", "201"):
        response = deref(spec, operation.get("responses", {}).get(status))
        if response:
            return response.get("content", {}).get("application/json", {}).get("schema")
    return None


def operations(spec: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for path, item in spec.get("paths", {}).items():
        for method, operation in item.items():
            if method in METHODS:
                result[(method.upper(), path)] = operation
    return result


def main(contract_path: str, strict: bool) -> int:
    contract = yaml.safe_load(Path(contract_path).read_text(encoding="utf-8"))
    actual = create_app().openapi()
    expected_ops = operations(contract)
    actual_ops = operations(actual)
    problems: list[str] = []
    for key in sorted(actual_ops.keys() - expected_ops.keys()):
        problems.append(f"в приложении есть ручка, которой нет в контракте: {key[0]} {key[1]}")
    missing = sorted(expected_ops.keys() - actual_ops.keys())
    for key in sorted(expected_ops.keys() & actual_ops.keys()):
        expected = property_names(contract, success_schema(contract, expected_ops[key]))
        got = property_names(actual, success_schema(actual, actual_ops[key]))
        if expected != got:
            problems.append(
                f"{key[0]} {key[1]}: поля ответа отличаются; "
                f"нет в приложении {sorted(expected - got)}, лишние {sorted(got - expected)}"
            )
    for key in missing:
        print(f"ещё не реализовано: {key[0]} {key[1]}")
    for problem in problems:
        print(f"ОШИБКА: {problem}")
    done = len(expected_ops) - len(missing)
    print(f"реализовано {done}/{len(expected_ops)}, ошибок {len(problems)}")
    return 1 if problems or (strict and missing) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], "--strict" in sys.argv))
