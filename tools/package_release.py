"""Create a portable source release without local caches or environments."""
from __future__ import annotations

import argparse
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
INCLUDE = ("run.py", "play.bat", "play.sh", "README.md", "README_VI.md", ".gitignore",
           "game", "web", "tests", "tools", "docs")
EXCLUDE = {"__pycache__", ".git", ".venv", ".env", ".DS_Store", "node_modules", "build", "dist"}


def package(output: Path) -> int:
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for entry in INCLUDE:
            base = ROOT / entry
            candidates = sorted(base.rglob("*")) if base.is_dir() else [base]
            for path in candidates:
                if not path.is_file() or path.resolve() == output:
                    continue
                relative = path.relative_to(ROOT)
                if any(part in EXCLUDE for part in relative.parts) or path.suffix in {".pyc", ".pyo"}:
                    continue
                archive.write(path, "VAN_DAO_Immortal_War/" + relative.as_posix())
                count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "VAN_DAO_Immortal_War.zip")
    args = parser.parse_args()
    count = package(args.output)
    print(f"Packed {count} files into {args.output.resolve()}")


if __name__ == "__main__":
    main()
