# /// script
# requires-python = ">=3.10"
# ///
"""Tag the current version and create a GitHub release."""

import subprocess
import tomllib
from pathlib import Path


def execute(*cmd: str) -> None:
    print(f"$ {' '.join(cmd)}")  # noqa: T201
    subprocess.run(cmd, check=True)


def main() -> None:
    # fmt: off
    pyproject  = tomllib.loads(Path("pyproject.toml").read_text())
    name       = pyproject["project"]["name"]
    version    = pyproject["project"]["version"]
    tag        = f"v{version}"
    notes_path = Path(f"CHANGELOG/{version}.md")
    lines      = notes_path.read_text().splitlines(keepends = True)
    title      = f"{name} {version}"
    # fmt: on

    if lines and lines[0].startswith("# "):
        title = lines[0].lstrip("# ").strip()
        lines = lines[1:]
        if lines and not lines[0].strip():
            lines = lines[1:]
    notes = "".join(lines).rstrip()

    # fmt: off
    # CMD 1: Create an unsigned
    execute(
    "git",
        "tag",
        "-a",
        tag,
        "-m",
        f"Release {tag}"
    )

    # CMD 2: Push tag to remote server
    execute(
        "git",
        "push",
        "origin",
        tag
    )

    execute(
        "gh",
        "release",
        "create",
        tag,
        "--verify-tag",
        "--title",
        title,
        "--notes",
        notes,
    )
    # fmt: on


if __name__ == "__main__":
    main()
