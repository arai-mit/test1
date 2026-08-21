from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QFileDialog,
    QFormLayout, QHBoxLayout, QInputDialog, QLabel, QListView, QListWidgetItem, QMainWindow,
    QMessageBox, QPushButton, QSpinBox, QSplitter, QVBoxLayout, QWidget)

from .errors import PdfOrganizerError
from .history import History
from .models import WorkingPdf
from .pdf_service import load_pdf, merge, save_pdf, split_at, split_every, split_ranges
from .utils import validate_pdf_name
from .widgets import FileDropList, page_pixmap


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("経理実務向け PDF整理ツール")
        self.resize(1280, 760)
        self.documents: list[WorkingPdf] = []
        self.current_index = -1
        self.history = History()
        self.thumb_width = 520
        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget(); outer = QVBoxLayout(root)
        toolbar = QHBoxLayout()
        for text, slot in (("PDFを追加", self.choose_files), ("PDFを結合", self.combine),
                           ("元に戻す", self.undo), ("すべてクリア", self.clear_all)):
            button = QPushButton(text); button.clicked.connect(slot); toolbar.addWidget(button)
        toolbar.addStretch(); toolbar.addWidget(QLabel("サムネイル:"))
        self.size_combo = QComboBox(); self.size_combo.addItems(["小", "中", "大"]); self.size_combo.setCurrentIndex(1)
        self.size_combo.currentIndexChanged.connect(self.change_thumbnail_size); toolbar.addWidget(self.size_combo)
        outer.addLayout(toolbar)
        hint = QLabel("PDFをこの画面へドラッグ＆ドロップできます（処理はすべてPC内で完結します）")
        hint.setObjectName("dropHint"); hint.setAlignment(Qt.AlignCenter); outer.addWidget(hint)

        splitter = QSplitter(); outer.addWidget(splitter, 1)
        left = QWidget(); lv = QVBoxLayout(left); lv.addWidget(QLabel("ファイル／作業中PDF（ドラッグで順番変更）"))
        self.file_list = FileDropList(); self.file_list.filesDropped.connect(self.add_files)
        self.file_list.orderChanged.connect(self.sync_document_order); self.file_list.currentRowChanged.connect(self.select_document)
        lv.addWidget(self.file_list); splitter.addWidget(left)
        center = QWidget(); cv = QVBoxLayout(center); cv.addWidget(QLabel("ページ（Ctrl/Shiftで複数選択、ドラッグで並び替え）"))
        self.pages = FileDropList(); self.pages.setViewMode(QListView.ViewMode.IconMode); self.pages.setResizeMode(QListView.ResizeMode.Adjust)
        self.pages.setSelectionMode(QAbstractItemView.ExtendedSelection); self.pages.setWrapping(True)
        self.pages.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded); self.pages.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.pages.orderChanged.connect(self.sync_page_order); cv.addWidget(self.pages); splitter.addWidget(center)
        right = QWidget(); rv = QVBoxLayout(right); rv.addWidget(QLabel("選択PDF／ページの操作"))
        for text, slot in (("名前変更", self.rename), ("左へ90度回転", lambda: self.rotate(-90)),
                           ("右へ90度回転", lambda: self.rotate(90)), ("180度回転", lambda: self.rotate(180)),
                           ("ページ削除", self.delete_pages), ("選択ページの前で分割", lambda: self.split_selected(False)),
                           ("選択ページの後で分割", lambda: self.split_selected(True)), ("ページ範囲で分割", self.split_by_ranges)):
            button = QPushButton(text); button.clicked.connect(slot); rv.addWidget(button)
        form = QFormLayout(); self.every = QSpinBox(); self.every.setRange(1, 9999); self.every.setValue(5)
        form.addRow("ページごと:", self.every); rv.addLayout(form)
        b = QPushButton("指定ページ数ごとに分割"); b.clicked.connect(lambda: self.split_fixed(self.every.value())); rv.addWidget(b)
        b = QPushButton("1ページずつ分割"); b.clicked.connect(lambda: self.split_fixed(1)); rv.addWidget(b)
        rv.addStretch(); b = QPushButton("選択PDFを保存"); b.clicked.connect(self.save_current); rv.addWidget(b)
        b = QPushButton("すべて保存"); b.clicked.connect(self.save_all); rv.addWidget(b); splitter.addWidget(right)
        splitter.setSizes([260, 760, 260]); self.setCentralWidget(root)
        self.setStyleSheet("#dropHint{background:#eef3f7;border:1px dashed #6d8294;padding:12px} QPushButton{padding:6px}")
        undo = QAction(self); undo.setShortcut(QKeySequence.Undo); undo.triggered.connect(self.undo); self.addAction(undo)

    def choose_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "PDFを追加", "", "PDFファイル (*.pdf)")
        self.add_files(paths)

    def add_files(self, paths: list[str]) -> None:
        for path in paths:
            try:
                self.documents.append(load_pdf(path))
            except PdfOrganizerError as exc: self.error(str(exc))
        self.refresh_files(select=len(self.documents) - 1)

    def refresh_files(self, select: int | None = None) -> None:
        self.file_list.blockSignals(True); self.file_list.clear()
        for doc in self.documents:
            item = QListWidgetItem(f"{doc.name}\n{len(doc.pages)}ページ")
            item.setData(Qt.UserRole, doc.id); self.file_list.addItem(item)
        self.file_list.blockSignals(False)
        if self.documents:
            self.file_list.setCurrentRow(max(0, min(select if select is not None else self.current_index, len(self.documents)-1)))
        else: self.current_index = -1; self.pages.clear()

    def select_document(self, row: int) -> None:
        self.current_index = row; self.refresh_pages()

    def refresh_pages(self) -> None:
        self.pages.clear()
        if not (0 <= self.current_index < len(self.documents)): return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            for n, page in enumerate(self.documents[self.current_index].pages, 1):
                item = QListWidgetItem(page_pixmap(page, self.thumb_width), f"{n}ページ")
                item.setData(Qt.UserRole, id(page)); item.setSizeHint(QSize(self.thumb_width + 96, self.thumb_width + 300)); self.pages.addItem(item)
        except Exception as exc: self.error(f"サムネイルを表示できません。\n{exc}")
        finally: QApplication.restoreOverrideCursor()

    def snapshot(self) -> None: self.history.push(self.documents)
    def current(self) -> WorkingPdf | None: return self.documents[self.current_index] if 0 <= self.current_index < len(self.documents) else None
    def selected_rows(self) -> list[int]: return sorted(self.pages.row(x) for x in self.pages.selectedItems())

    def rotate(self, degrees: int) -> None:
        doc, rows = self.current(), self.selected_rows()
        if not doc or not rows: return self.error("回転するページを選択してください。")
        self.snapshot()
        for row in rows: doc.pages[row].rotation = (doc.pages[row].rotation + degrees) % 360
        self.refresh_pages()

    def delete_pages(self) -> None:
        doc, rows = self.current(), self.selected_rows()
        if not doc or not rows: return self.error("削除するページを選択してください。")
        if len(rows) == len(doc.pages): return self.error("すべてのページを削除することはできません。")
        if QMessageBox.question(self, "ページ削除", f"選択した{len(rows)}ページを削除しますか？") != QMessageBox.Yes: return
        self.snapshot()
        for row in reversed(rows): del doc.pages[row]
        self.refresh_files(select=self.current_index); self.refresh_pages()

    def rename(self) -> None:
        doc = self.current()
        if not doc: return self.error("名前を変更するPDFを選択してください。")
        value, ok = QInputDialog.getText(self, "名前変更", "新しいファイル名:", text=doc.name)
        if ok:
            try: doc.name = validate_pdf_name(value); self.refresh_files(select=self.current_index)
            except PdfOrganizerError as exc: self.error(str(exc))

    def split_selected(self, after: bool) -> None:
        rows = self.selected_rows()
        if not rows: return self.error("分割位置にするページを選択してください。")
        self.apply_split(split_at(self.current(), [r + (1 if after else 0) for r in rows]))

    def split_by_ranges(self) -> None:
        doc = self.current()
        if not doc: return self.error("分割するPDFを選択してください。")
        value, ok = QInputDialog.getMultiLineText(self, "ページ範囲で分割", "範囲（改行またはカンマ区切り）:", "1-3\n4-7")
        if ok:
            try: self.apply_split(split_ranges(doc, value))
            except PdfOrganizerError as exc: self.error(str(exc))

    def split_fixed(self, size: int) -> None:
        doc = self.current()
        if not doc: return self.error("分割するPDFを選択してください。")
        self.apply_split(split_every(doc, size))

    def apply_split(self, parts: list[WorkingPdf]) -> None:
        if len(parts) < 2: return self.error("指定した位置ではPDFを分割できません。")
        self.snapshot(); self.documents[self.current_index:self.current_index + 1] = parts; self.refresh_files(select=self.current_index)

    def combine(self) -> None:
        if len(self.documents) < 2: return self.error("結合するPDFを2つ以上追加してください。")
        self.snapshot()
        try: self.documents = [merge(self.documents)]; self.refresh_files(select=0)
        except PdfOrganizerError as exc: self.error(str(exc))

    def sync_document_order(self) -> None:
        by_id = {d.id: d for d in self.documents}
        self.snapshot(); self.documents = [by_id[self.file_list.item(i).data(Qt.UserRole)] for i in range(self.file_list.count())]; self.current_index = self.file_list.currentRow()

    def sync_page_order(self) -> None:
        doc = self.current()
        if not doc: return
        by_id = {id(p): p for p in doc.pages}; self.snapshot()
        doc.pages = [by_id[self.pages.item(i).data(Qt.UserRole)] for i in range(self.pages.count())]; self.refresh_pages()

    def change_thumbnail_size(self, index: int) -> None:
        self.thumb_width = [360, 520, 720][index]; self.refresh_pages()

    def undo(self) -> None:
        state = self.history.undo()
        if state is None: return self.statusBar().showMessage("元に戻せる操作はありません。", 3000)
        self.documents = state; self.refresh_files(select=min(self.current_index, len(state)-1))

    def clear_all(self) -> None:
        if self.documents and QMessageBox.question(self, "すべてクリア", "作業中のPDFをすべて一覧から外しますか？") != QMessageBox.Yes: return
        self.snapshot(); self.documents = []; self.refresh_files()

    def save_current(self) -> None:
        doc = self.current()
        if not doc: return self.error("保存するPDFを選択してください。")
        path, _ = QFileDialog.getSaveFileName(self, "PDFを保存", str(doc.source_dir / doc.name), "PDFファイル (*.pdf)")
        if path: self._save_one(doc, Path(path))

    def save_all(self) -> None:
        if not self.documents: return self.error("保存するPDFがありません。")
        folder = QFileDialog.getExistingDirectory(self, "保存先フォルダ", str(self.documents[0].source_dir))
        if not folder: return
        saved = 0
        for doc in self.documents:
            if self._save_one(doc, Path(folder) / doc.name): saved += 1
        self.statusBar().showMessage(f"{saved}件のPDFを保存しました。", 5000)

    def _save_one(self, doc: WorkingPdf, path: Path) -> bool:
        if path.exists():
            box = QMessageBox(QMessageBox.Warning, "同名ファイル", "同じ名前のファイルが存在します。", parent=self)
            overwrite = box.addButton("上書き", QMessageBox.AcceptRole); rename = box.addButton("名前を変更", QMessageBox.ActionRole); box.addButton("キャンセル", QMessageBox.RejectRole); box.exec()
            if box.clickedButton() == rename:
                new_path, _ = QFileDialog.getSaveFileName(self, "別名で保存", str(path), "PDFファイル (*.pdf)")
                if not new_path: return False
                path = Path(new_path)
                if path.exists(): return self.error("指定した名前のファイルも既に存在します。") or False
            elif box.clickedButton() != overwrite: return False
        try: save_pdf(doc, path); return True
        except PdfOrganizerError as exc: self.error(str(exc)); return False

    def error(self, message: str) -> None: QMessageBox.warning(self, "確認", message)
