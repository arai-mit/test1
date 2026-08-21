import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QListView

from pdf_organizer.models import PageRef, WorkingPdf
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
        assert window.pages.iconSize() == QSize(130, 184)
    finally:
        window.close()


def test_thumbnail_size_controls_pixmap_and_icon_size(application: QApplication, monkeypatch) -> None:
    requested_widths = []

    def fake_page_pixmap(page: PageRef, width: int) -> QPixmap:
        requested_widths.append(width)
        return QPixmap(width, round(width * 2**0.5))

    monkeypatch.setattr("pdf_organizer.main_window.page_pixmap", fake_page_pixmap)
    window = MainWindow()
    try:
        page = PageRef(source=Path("sample.pdf"), index=0)
        window.documents = [WorkingPdf(name="sample.pdf", pages=[page], source_dir=Path.cwd())]
        window.current_index = 0

        for index, width in enumerate((90, 130, 180)):
            window.change_thumbnail_size(index)
            pixmap = window.pages.item(0).icon().pixmap(window.pages.iconSize())
            assert requested_widths[-1] == width
            assert window.pages.iconSize() == QSize(width, round(width * 2**0.5))
            assert pixmap.size() == window.pages.iconSize()
            assert window.pages.item(0).sizeHint() == QSize(width + 24, round(width * 2**0.5) + 40)
    finally:
        window.close()
