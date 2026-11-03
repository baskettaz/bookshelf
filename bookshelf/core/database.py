from __future__ import annotations

import sqlite3
from pathlib import Path

from bookshelf.config import get_database_path

SCHEMA_VERSION = 1

_CREATE_BOOKS_TABLE = """
CREATE TABLE books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    isbn TEXT,
    publisher TEXT,
    publication_year INTEGER CHECK (publication_year IS NULL OR publication_year > 0),
    genre TEXT,
    language TEXT,
    description TEXT,
    page_count INTEGER CHECK (page_count IS NULL OR page_count > 0),
    rating INTEGER CHECK (rating IS NULL OR rating BETWEEN 1 AND 5),
    status TEXT NOT NULL DEFAULT 'To Read'
        CHECK (status IN ('To Read', 'Reading', 'Completed', 'On Hold', 'Abandoned')),
    date_added TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_finished TEXT,
    notes TEXT
)
"""

_BOOK_INDEXES = (
    ("idx_books_title", "title"),
    ("idx_books_author", "author"),
    ("idx_books_status", "status"),
    ("idx_books_genre", "genre"),
    ("idx_books_isbn", "isbn"),
)


class Database:
    def __init__(self, path: str | Path | None = None) -> None:
        selected_path = get_database_path() if path is None else path
        self.path = None if str(selected_path) == ":memory:" else Path(selected_path)
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            connection_path = str(self.path)
        else:
            connection_path = ":memory:"

        self.connection = sqlite3.connect(connection_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        current_version = self.connection.execute("PRAGMA user_version").fetchone()[0]
        if current_version > SCHEMA_VERSION:
            raise RuntimeError(
                f"Database schema version {current_version} is newer than supported "
                f"version {SCHEMA_VERSION}"
            )
        if current_version == SCHEMA_VERSION:
            return

        with self.connection:
            self.connection.execute(_CREATE_BOOKS_TABLE)
            for index_name, column_name in _BOOK_INDEXES:
                self.connection.execute(
                    f"CREATE INDEX {index_name} ON books({column_name})"
                )
            self.connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> Database:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
