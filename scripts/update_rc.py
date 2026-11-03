from collections.abc import Generator
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

# Note:
# Intentionally all relevant variables are set as global variables

# fmt: off
TEMPLATE_DIR  = Path(__file__).parent.parent / "bookshelf" / "templates"
TEMPLATE_NAME = "resources.qrc"
ICONS_DIR     = TEMPLATE_DIR.parent / "gui" / "icons"
RC_FILE       = ICONS_DIR.parent / TEMPLATE_NAME
# fmt: on


def list_all_icons() -> Generator[Path]:
    yield from (file for file in ICONS_DIR.iterdir() if file.is_file())


def write_resource_file() -> None:
    # fmt: off
    env = Environment(
        loader        = FileSystemLoader(TEMPLATE_DIR),
        lstrip_blocks = True, # removes the spaces left from the comments at the start
    )
    template = env.get_template(TEMPLATE_NAME)
    # fmt: on

    with open(RC_FILE, "w") as f:
        icons = list_all_icons()
        ready = template.render(icons=icons)
        f.write(ready.strip())


if __name__ == "__main__":
    write_resource_file()
