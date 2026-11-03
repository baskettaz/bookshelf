import sqlite3

from bookshelf.core.models import (
    Book,
    BookFilters,
    BookStatus,
    CollectionSummary,
    SortField,
)

_BOOK_COLUMNS = (
    "title",
    "author",
    "isbn",
    "publisher",
    "publication_year",
    "genre",
    "language",
    "description",
    "page_count",
    "rating",
    "status",
    "date_finished",
    "notes",
)


class BookRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def create(self, book: Book) -> Book:
        columns = ", ".join(_BOOK_COLUMNS)
        placeholders = ", ".join("?" for _ in _BOOK_COLUMNS)
        values = self._book_values(book)
        with self._connection:
            cursor = self._connection.execute(
                f"INSERT INTO books ({columns}) VALUES ({placeholders})",
                values,
            )
            book_id = cursor.lastrowid
            if book_id is None:
                raise RuntimeError("The database did not return an ID for the new book")
        created = self.get(book_id)
        if created is None:
            raise RuntimeError("The created book could not be loaded from the database")
        return created

    def get(self, book_id: int) -> Book | None:
        row = self._connection.execute(
            "SELECT * FROM books WHERE id = ?", (book_id,)
        ).fetchone()
        return self._book_from_row(row) if row is not None else None

    def list_books(self, filters: BookFilters = BookFilters()) -> list[Book]:
        conditions: list[str] = []
        parameters: list[object] = []

        if filters.search.strip():
            escaped_search = (
                filters.search.strip()
                .replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            search_pattern = f"%{escaped_search}%"
            conditions.append(
                "(title LIKE ? ESCAPE '\\' COLLATE NOCASE "
                "OR author LIKE ? ESCAPE '\\' COLLATE NOCASE "
                "OR isbn LIKE ? ESCAPE '\\' COLLATE NOCASE "
                "OR publisher LIKE ? ESCAPE '\\' COLLATE NOCASE)"
            )
            parameters.extend([search_pattern] * 4)

        if filters.genre is not None:
            conditions.append("genre = ? COLLATE NOCASE")
            parameters.append(filters.genre)
        if filters.status is not None:
            conditions.append("status = ?")
            parameters.append(filters.status.value)
        if filters.rating is not None:
            conditions.append("rating = ?")
            parameters.append(filters.rating)
        if filters.publication_year is not None:
            conditions.append("publication_year = ?")
            parameters.append(filters.publication_year)

        where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        direction = "DESC" if filters.descending else "ASC"
        sort_column = SortField(filters.sort_by).value
        rows = self._connection.execute(
            f"SELECT * FROM books{where_clause} "
            f"ORDER BY {sort_column} {direction}, id ASC",
            parameters,
        ).fetchall()
        return [self._book_from_row(row) for row in rows]

    def update(self, book_id: int, book: Book) -> Book | None:
        assignments = ", ".join(f"{column} = ?" for column in _BOOK_COLUMNS)
        with self._connection:
            cursor = self._connection.execute(
                f"UPDATE books SET {assignments} WHERE id = ?",
                (*self._book_values(book), book_id),
            )
            if cursor.rowcount == 0:
                return None
        return self.get(book_id)

    def delete(self, book_id: int) -> bool:
        with self._connection:
            cursor = self._connection.execute(
                "DELETE FROM books WHERE id = ?", (book_id,)
            )
        return cursor.rowcount > 0

    def summary(self) -> CollectionSummary:
        row = self._connection.execute(
            """
            SELECT
                COUNT(*) AS total,
                COALESCE(SUM(CASE WHEN status = 'Reading' THEN 1 ELSE 0 END), 0)
                    AS reading,
                COALESCE(SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END), 0)
                    AS completed
            FROM books
            """
        ).fetchone()
        return CollectionSummary(
            total=row["total"],
            reading=row["reading"],
            completed=row["completed"],
        )

    @staticmethod
    def _book_values(book: Book) -> tuple[object, ...]:
        return (
            book.title,
            book.author,
            book.isbn,
            book.publisher,
            book.publication_year,
            book.genre,
            book.language,
            book.description,
            book.page_count,
            book.rating,
            book.status.value,
            book.date_finished,
            book.notes,
        )

    @staticmethod
    def _book_from_row(row: sqlite3.Row) -> Book:
        return Book(
            id=row["id"],
            title=row["title"],
            author=row["author"],
            isbn=row["isbn"],
            publisher=row["publisher"],
            publication_year=row["publication_year"],
            genre=row["genre"],
            language=row["language"],
            description=row["description"],
            page_count=row["page_count"],
            rating=row["rating"],
            status=BookStatus(row["status"]),
            date_added=row["date_added"],
            date_finished=row["date_finished"],
            notes=row["notes"],
        )
