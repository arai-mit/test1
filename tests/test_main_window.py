import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QListView

from pdf_organizer.main_window import MainWindow


@pytest.fixture(scope="module")
def application() -> QApplication:
    app = QApplication.instance() or QApplication([])
    yield app


def test_main_window_starts_without_error(application: QApplication) -> None:
    window = MainWindow()
    try:
        window.show()
        application.processEvents()

        assert window.isVisible()
        assert window.pages.viewMode() == QListView.ViewMode.IconMode
        assert window.pages.resizeMode() == QListView.ResizeMode.Adjust
        assert window.size_combo.currentIndex() == 1
        assert window.thumb_width == 520
        assert window.pages.horizontalScrollBarPolicy() == Qt.ScrollBarAsNeeded
        assert window.pages.verticalScrollBarPolicy() == Qt.ScrollBarAsNeeded
    finally:
        window.close()


@pytest.mark.parametrize(("index", "expected_width"), [(0, 360), (1, 520), (2, 720)])
def test_thumbnail_size_options(application: QApplication, index: int, expected_width: int) -> None:
    window = MainWindow()
    try:
        window.size_combo.setCurrentIndex(index)
        assert window.thumb_width == expected_width
    finally:
        window.close()
