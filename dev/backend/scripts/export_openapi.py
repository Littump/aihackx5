import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import create_app


def main() -> None:
    print(json.dumps(create_app().openapi(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
