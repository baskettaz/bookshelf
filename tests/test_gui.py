import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QMessageBox

from bookshelf.core import Book, BookRepository, BookService, BookStatus, Database
from bookshelf.gui.book_dialogs import BookDetailsDialog, BookDialog
from bookshelf.gui.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def library():
    with Database(":memory:") as database:
        yield BookService(BookRepository(database.connection))


def test_main_window_loads_ui_and_filters_books(qapp, library):
    library.add_book(
        Book(
            title="The Hobbit",
            author="J. R. R. Tolkien",
            genre="Fantasy",
            status=BookStatus.COMPLETED,
            rating=5,
        )
    )
    library.add_book(
        Book(
            title="Dune",
            author="Frank Herbert",
            genre="Science Fiction",
            status=BookStatus.READING,
        )
    )
    window = MainWindow(library)

    assert window.booksTable.rowCount() == 2
    assert window.statusFilter.currentData() is None
    assert window.totalValue.text() == "2"
    assert not window.editBookButton.isEnabled()

    window.navCompleted.click()
    assert window.booksTable.rowCount() == 1
    completed_title = window.booksTable.item(0, 0)
    assert completed_title is not None
    assert completed_title.text() == "The Hobbit"

    window.clearFiltersButton.click()
    window.searchInput.setText("dune")
    assert window.booksTable.rowCount() == 1
    searched_title = window.booksTable.item(0, 0)
    assert searched_title is not None
    assert searched_title.text() == "Dune"

    window.booksTable.selectRow(0)
    assert window.editBookButton.isEnabled()
    assert window.deleteBookButton.isEnabled()
    window.close()


def test_book_dialog_loads_ui_and_emits_book_data(qapp):
    dialog = BookDialog()
    dialog.titleInput.setText("A Wizard of Earthsea")
    dialog.authorInput.setText("Ursula K. Le Guin")
    dialog.yearInput.setText("1968")
    emitted_books = []
    dialog.saveRequested.connect(emitted_books.append)

    dialog.saveButton.click()

    assert len(emitted_books) == 1
    assert emitted_books[0].title == "A Wizard of Earthsea"
    assert emitted_books[0].publication_year == 1968
    dialog.close()


def test_book_dialog_keeps_open_for_invalid_numbers(qapp):
    dialog = BookDialog()
    dialog.titleInput.setText("A Book")
    dialog.authorInput.setText("An Author")
    dialog.pageCountInput.setText("many")

    dialog.saveButton.click()

    assert dialog.formError.text() == "Page count must be a whole number."
    dialog.close()


def test_add_edit_and_remove_books_through_the_gui(qapp, library):
    window = MainWindow(library)

    def submit_new_book():
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, BookDialog)
        dialog.titleInput.setText("The Dispossessed")
        dialog.authorInput.setText("Ursula K. Le Guin")
        dialog.saveButton.click()

    QTimer.singleShot(0, submit_new_book)
    window.addBookButton.click()

    added = library.list_books()[0]
    assert added.id is not None
    assert added.title == "The Dispossessed"
    assert window.totalValue.text() == "1"

    window.booksTable.selectRow(0)

    def submit_edit():
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, BookDialog)
        dialog.titleInput.setText("The Dispossessed (Revised)")
        dialog.saveButton.click()

    QTimer.singleShot(0, submit_edit)
    window.editBookButton.click()

    updated = library.list_books()[0]
    assert updated.id == added.id
    assert updated.title == "The Dispossessed (Revised)"

    window.booksTable.selectRow(0)

    def confirm_remove():
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, QMessageBox)
        yes_button = dialog.button(QMessageBox.StandardButton.Yes)
        assert yes_button is not None
        yes_button.click()

    QTimer.singleShot(0, confirm_remove)
    window.deleteBookButton.click()

    assert library.list_books() == []
    assert window.totalValue.text() == "0"
    window.close()


def test_book_details_change_status_from_the_gui(qapp, library):
    library.add_book(Book(title="A Book", author="An Author"))
    window = MainWindow(library)

    def update_status():
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, BookDetailsDialog)
        dialog.statusInput.setCurrentIndex(
            dialog.statusInput.findData(BookStatus.COMPLETED.value)
        )
        dialog.changeStatusButton.click()
        dialog.close()

    QTimer.singleShot(0, update_status)
    window._show_details(0, 0)

    assert library.list_books()[0].status is BookStatus.COMPLETED
    assert window.completedValue.text() == "1"
    window.close()


def test_book_details_render_user_text_as_plain_text(qapp):
    dialog = BookDetailsDialog(
        Book(
            title="The Book",
            author="An Author",
            description="<script>not markup</script>",
        )
    )

    assert dialog.detailsDescription.text() == "<script>not markup</script>"
    dialog.close()
