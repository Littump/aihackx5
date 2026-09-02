import ast
import io
import re
import sys
import tokenize
from pathlib import Path

SKIP_DIRS = {"node_modules", "dist", ".venv", ".git", "__pycache__"}
SKIP_NAMES = {"schema.d.ts"}
TS_BLOCK_OPEN = re.compile(r"/\*")
TS_BLOCK_CLOSE = re.compile(r"\*/")


def iter_files(paths: list[str]) -> list[Path]:
    result: list[Path] = []
    for raw in paths:
        path = Path(raw)
        candidates = [path] if path.is_file() else path.rglob("*")
        for file in candidates:
            if file.suffix not in {".py", ".ts", ".tsx"} or file.name in SKIP_NAMES:
                continue
            if any(part in SKIP_DIRS for part in file.parts):
                continue
            result.append(file)
    return result


def check_python(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    tree = ast.parse(text, filename=str(path))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        doc = ast.get_docstring(node, clean=False)
        if doc is not None and "\n" in doc.strip():
            line = node.body[0].lineno
            errors.append(f"{path}:{line}: многострочный докстринг")
    errors.extend(check_python_comments(path, text))
    return errors


def check_python_comments(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    previous_line = -2
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type != tokenize.COMMENT:
            continue
        line_no, col = token.start
        is_full_line = token.line[:col].strip() == ""
        if not is_full_line or line_no <= 2 and token.string.startswith(("#!", "# -*-")):
            continue
        if line_no == previous_line + 1:
            errors.append(f"{path}:{line_no}: два комментария подряд")
        previous_line = line_no
    return errors


def check_typescript(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    previous_line = -2
    block_start: int | None = None
    for index, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if block_start is not None:
            if TS_BLOCK_CLOSE.search(line):
                if index > block_start:
                    errors.append(f"{path}:{block_start}: многострочный блочный комментарий")
                block_start = None
            continue
        if stripped.startswith("//") and not stripped.startswith("///"):
            if index == previous_line + 1:
                errors.append(f"{path}:{index}: два комментария подряд")
            previous_line = index
            continue
        if stripped.startswith("/*"):
            block_start = index
            if TS_BLOCK_CLOSE.search(line[2:]):
                block_start = None
    return errors


def main(argv: list[str]) -> int:
    errors: list[str] = []
    for file in iter_files(argv):
        text = file.read_text(encoding="utf-8")
        checker = check_python if file.suffix == ".py" else check_typescript
        errors.extend(checker(file, text))
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
