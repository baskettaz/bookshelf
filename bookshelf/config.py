import os
import sys
from pathlib import Path

APP_DIRECTORY_NAME = "MyBookShelf"
DATABASE_FILENAME = "bookshelf.db"


def get_data_directory() -> Path:
    if sys.platform == "win32":
        base_directory = os.environ.get("LOCALAPPDATA")
        base_path = (
            Path(base_directory)
            if base_directory
            else Path.home() / "AppData" / "Local"
        )
    elif sys.platform == "darwin":
        base_path = Path.home() / "Library" / "Application Support"
    else:
        base_directory = os.environ.get("XDG_DATA_HOME")
        base_path = (
            Path(base_directory) if base_directory else Path.home() / ".local" / "share"
        )

    return base_path / APP_DIRECTORY_NAME


def get_database_path() -> Path:
    return get_data_directory() / DATABASE_FILENAME
