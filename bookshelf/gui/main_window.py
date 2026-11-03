import sqlite3
from dataclasses import replace
from pathlib import Path

from PyQt6 import uic
from PyQt6.QtCore import QSignalBlocker, Qt
from PyQt6.QtGui import QBrush, QCloseEvent, QColor, QIntValidator
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
)

from bookshelf.core import (
    Book,
    BookFilters,
    BookRepository,
    BookService,
    BookStatus,
    Database,
    SortField,
)
from bookshelf.core.service import BookValidationError
from bookshelf.gui.book_dialogs import BookDetailsDialog, BookDialog

_UI_PATH = Path(__file__).with_name("main_window.ui")
_STATUS_NAV = (
    ("navAll", None, "All books"),
    ("navToRead", BookStatus.TO_READ, "To read"),
    ("navReading", BookStatus.READING, "Currently reading"),
    ("navCompleted", BookStatus.COMPLETED, "Finished"),
    ("navOnHold", BookStatus.ON_HOLD, "On hold"),
    ("navAbandoned", BookStatus.ABANDONED, "Abandoned"),
)


class MainWindow(QMainWindow):
    addBookButton: QPushButton
    booksTable: QTableWidget
    clearFiltersButton: QPushButton
    completedValue: QLabel
    deleteBookButton: QPushButton
    editBookButton: QPushButton
    emptyAddButton: QPushButton
    emptyState: QFrame
    emptySubtitle: QLabel
    emptyTitle: QLabel
    genreFilter: QComboBox
    navAbandoned: QPushButton
    navAll: QPushButton
    navCompleted: QPushButton
    navOnHold: QPushButton
    navReading: QPushButton
    navToRead: QPushButton
    ratingFilter: QComboBox
    readingValue: QLabel
    resultCount: QLabel
    searchInput: QLineEdit
    sectionTitle: QLabel
    sortFilter: QComboBox
    statusFilter: QComboBox
    statusbar: QStatusBar
    totalValue: QLabel
    yearFilter: QLineEdit
    collectionStack: QStackedWidget

    def __init__(self, service: BookService | None = None, parent=None) -> None:
        super().__init__(parent)
        uic.loadUi(str(_UI_PATH), self)
        self._database: Database | None = None
        if service is None:
            self._database = Database()
            service = BookService(BookRepository(self._database.connection))
        self._service = service
        self._status_filter: BookStatus | None = None

        self._configure_controls()
        self._connect_signals()
        self._refresh_books()

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        if self._database is not None:
            self._database.close()
            self._database = None
        super().closeEvent(a0)

    def _configure_controls(self) -> None:
        self.booksTable.setColumnCount(6)
        self.booksTable.setHorizontalHeaderLabels(
            ["TITLE", "AUTHOR", "GENRE", "YEAR", "STATUS", "RATING"]
        )
        vertical_header = self.booksTable.verticalHeader()
        if vertical_header is not None:
            vertical_header.setVisible(False)
            vertical_header.setDefaultSectionSize(46)
        horizontal_header = self.booksTable.horizontalHeader()
        if horizontal_header is not None:
            horizontal_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            horizontal_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            for column in (2, 4):
                horizontal_header.setSectionResizeMode(
                    column, QHeaderView.ResizeMode.ResizeToContents
                )
        self.booksTable.setColumnWidth(3, 70)
        self.booksTable.setColumnWidth(5, 80)
        self.booksTable.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.booksTable.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.yearFilter.setValidator(QIntValidator(1, 9999, self))

        for status in BookStatus:
            self.statusFilter.addItem(status.value, status)
        self.statusFilter.insertItem(0, "All statuses", None)
        self.statusFilter.setCurrentIndex(0)

        self.ratingFilter.addItem("All ratings", None)
        for rating in range(1, 6):
            self.ratingFilter.addItem(f"{rating} / 5", rating)

        sort_labels = {
            SortField.TITLE: "Title",
            SortField.AUTHOR: "Author",
            SortField.PUBLICATION_YEAR: "Publication year",
            SortField.RATING: "Rating",
            SortField.DATE_ADDED: "Date added",
        }
        for sort_field, label in sort_labels.items():
            self.sortFilter.addItem(label, sort_field)

    def _connect_signals(self) -> None:
        self.addBookButton.clicked.connect(self._add_book)
        self.emptyAddButton.clicked.connect(self._add_book)
        self.editBookButton.clicked.connect(self._edit_selected)
        self.deleteBookButton.clicked.connect(self._delete_selected)
        self.clearFiltersButton.clicked.connect(self._clear_filters)
        self.searchInput.textChanged.connect(self._refresh_books)
        self.genreFilter.currentIndexChanged.connect(self._refresh_books)
        self.statusFilter.currentIndexChanged.connect(self._on_status_filter_changed)
        self.ratingFilter.currentIndexChanged.connect(self._refresh_books)
        self.sortFilter.currentIndexChanged.connect(self._refresh_books)
        self.yearFilter.textChanged.connect(self._refresh_books)
        self.booksTable.itemSelectionChanged.connect(self._update_action_buttons)
        self.booksTable.cellDoubleClicked.connect(self._show_details)

        for button_name, status, _ in _STATUS_NAV:
            button = getattr(self, button_name)
            button.clicked.connect(
                lambda _checked=False, selected_status=status: self._select_status(
                    selected_status
                )
            )

    def _select_status(self, status: BookStatus | None) -> None:
        self._status_filter = status
        if status is None:
            self.navAll.setChecked(True)
        else:
            nav_button_name = next(
                name for name, value, _ in _STATUS_NAV if value is status
            )
            getattr(self, nav_button_name).setChecked(True)
        with QSignalBlocker(self.statusFilter):
            index = self.statusFilter.findData(status)
            self.statusFilter.setCurrentIndex(index)
        self._refresh_books()

    def _on_status_filter_changed(self, _index: int) -> None:
        self._status_filter = self.statusFilter.currentData()
        status = self._status_filter
        button_name = next(name for name, value, _ in _STATUS_NAV if value is status)
        getattr(self, button_name).setChecked(True)
        self._refresh_books()

    def _current_filters(self) -> BookFilters:
        year_text = self.yearFilter.text().strip()
        return BookFilters(
            search=self.searchInput.text(),
            genre=self.genreFilter.currentData(),
            status=self.statusFilter.currentData(),
            rating=self.ratingFilter.currentData(),
            publication_year=int(year_text) if year_text else None,
            sort_by=self.sortFilter.currentData() or SortField.TITLE,
        )

    def _refresh_books(self, *_args) -> None:
        try:
            books = self._service.list_books(self._current_filters())
            summary = self._service.collection_summary()
            all_books = self._service.list_books()
        except sqlite3.Error as error:
            self._show_database_error("load the collection", error)
            return

        self.totalValue.setText(str(summary.total))
        self.readingValue.setText(str(summary.reading))
        self.completedValue.setText(str(summary.completed))
        self._refresh_genres(all_books)

        self.booksTable.setRowCount(len(books))
        for row, book in enumerate(books):
            values = (
                book.title,
                book.author,
                book.genre or "-",
                str(book.publication_year) if book.publication_year else "-",
                book.status.value,
                f"{book.rating} / 5" if book.rating is not None else "-",
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, book.id)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if column == 4:
                    item.setForeground(QBrush(QColor(_status_color(book.status))))
                if column in (3, 5):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.booksTable.setItem(row, column, item)

        title = next(
            label for _, value, label in _STATUS_NAV if value is self._status_filter
        )
        self.sectionTitle.setText(title)
        self.resultCount.setText(
            f"{len(books)} book" + ("" if len(books) == 1 else "s")
        )
        if books:
            self.collectionStack.setCurrentWidget(self.booksTable)
        else:
            self.collectionStack.setCurrentWidget(self.emptyState)
            if summary.total:
                self.emptyTitle.setText("No books match these filters.")
                self.emptySubtitle.setText(
                    "Try a different search or clear the filters to see your collection."
                )
            else:
                self.emptyTitle.setText("Your next favorite is waiting.")
                self.emptySubtitle.setText(
                    "Add a book to start building your personal library."
                )
        self._update_action_buttons()

    def _refresh_genres(self, books: list[Book]) -> None:
        selected_genre = self.genreFilter.currentData()
        genres = sorted({book.genre for book in books if book.genre}, key=str.casefold)
        with QSignalBlocker(self.genreFilter):
            self.genreFilter.clear()
            self.genreFilter.addItem("All genres", None)
            for genre in genres:
                self.genreFilter.addItem(genre, genre)
            selected_index = self.genreFilter.findData(selected_genre)
            self.genreFilter.setCurrentIndex(max(selected_index, 0))

    def _clear_filters(self) -> None:
        self.searchInput.clear()
        self.yearFilter.clear()
        self._select_status(None)
        self.genreFilter.setCurrentIndex(0)
        self.ratingFilter.setCurrentIndex(0)
        self.sortFilter.setCurrentIndex(0)

    def _selected_book_id(self) -> int | None:
        selected_items = self.booksTable.selectedItems()
        if not selected_items:
            return None
        book_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        return int(book_id) if book_id is not None else None

    def _update_action_buttons(self) -> None:
        has_selection = self._selected_book_id() is not None
        self.editBookButton.setEnabled(has_selection)
        self.deleteBookButton.setEnabled(has_selection)

    def _add_book(self) -> None:
        self._show_book_dialog()

    def _edit_selected(self) -> None:
        book_id = self._selected_book_id()
        if book_id is not None:
            book = self._get_book(book_id)
            if book is not None:
                self._show_book_dialog(book)

    def _get_book(self, book_id: int) -> Book | None:
        try:
            return self._service.get_book(book_id)
        except sqlite3.Error as error:
            self._show_database_error("load this book", error)
            return None

    def _show_book_dialog(self, book: Book | None = None) -> None:
        dialog = BookDialog(book, self)

        def save_book(updated_book: Book) -> None:
            try:
                if book is None:
                    self._service.add_book(updated_book)
                elif book.id is None:
                    dialog.set_error("This book cannot be edited without a record ID.")
                    return
                else:
                    self._service.update_book(book.id, updated_book)
            except BookValidationError as error:
                dialog.set_error(str(error))
                return
            except sqlite3.Error as error:
                dialog.set_error(f"Could not save this book: {error}")
                return
            dialog.accept()

        dialog.saveRequested.connect(save_book)
        if dialog.exec():
            self.statusbar.showMessage("Book saved to your library.", 3000)
            self._refresh_books()

    def _delete_selected(self) -> None:
        book_id = self._selected_book_id()
        if book_id is None:
            return
        book = self._get_book(book_id)
        if book is None:
            return
        answer = QMessageBox.question(
            self,
            "Remove book",
            f'Remove "{book.title}" from your library?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self._service.delete_book(book_id)
        except sqlite3.Error as error:
            self._show_database_error("remove this book", error)
            return
        self.statusbar.showMessage("Book removed from your library.", 3000)
        self._refresh_books()

    def _show_details(self, row: int, _column: int) -> None:
        item = self.booksTable.item(row, 0)
        if item is None:
            return
        book_id = item.data(Qt.ItemDataRole.UserRole)
        book = self._get_book(book_id)
        if book is None:
            return
        dialog = BookDetailsDialog(book, self)
        dialog.statusChangeRequested.connect(
            lambda status: self._change_book_status(book_id, status, dialog)
        )
        dialog.exec()
        if dialog.edit_requested:
            latest_book = self._get_book(book_id)
            if latest_book is not None:
                self._show_book_dialog(latest_book)

    def _change_book_status(
        self, book_id: int, status: str, dialog: BookDetailsDialog
    ) -> None:
        book = self._get_book(book_id)
        if book is None:
            return
        try:
            updated_book = self._service.update_book(
                book_id,
                replace(book, status=BookStatus(status)),
            )
        except ValueError as error:
            QMessageBox.warning(self, "Invalid reading status", str(error))
            return
        except sqlite3.Error as error:
            self._show_database_error("update the reading status", error)
            return
        if updated_book is not None:
            dialog.set_book(updated_book)
            self.statusbar.showMessage("Reading status updated.", 3000)
            self._refresh_books()

    def _show_database_error(self, action: str, error: sqlite3.Error) -> None:
        QMessageBox.critical(
            self,
            "Library database error",
            f"Could not {action}.\n\n{error}",
        )


def _status_color(status: BookStatus) -> str:
    return {
        BookStatus.TO_READ: "#9b7653",
        BookStatus.READING: "#587d70",
        BookStatus.COMPLETED: "#50738b",
        BookStatus.ON_HOLD: "#9a7951",
        BookStatus.ABANDONED: "#8c7070",
    }[status]
