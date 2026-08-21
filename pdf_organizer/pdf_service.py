from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.errors import FileNotDecryptedError, PdfReadError

from .errors import PdfOrganizerError
from .models import PageRef, WorkingPdf
from .utils import parse_page_ranges


def load_pdf(path: str | Path) -> WorkingPdf:
    path = Path(path).resolve()
    if path.suffix.lower() != ".pdf":
        raise PdfOrganizerError("PDF以外のファイルは読み込めません。")
    try:
        reader = PdfReader(path)
        if reader.is_encrypted:
            raise PdfOrganizerError("パスワード保護されたPDFは読み込めません。保護を解除してからお試しください。")
        count = len(reader.pages)
    except PdfOrganizerError:
        raise
    except (PdfReadError, FileNotDecryptedError, OSError, ValueError) as exc:
        raise PdfOrganizerError(f"PDFを読み込めません。ファイルが破損していないか確認してください。\n{exc}") from exc
    if count == 0:
        raise PdfOrganizerError("ページがないPDFは読み込めません。")
    return WorkingPdf(path.name, [PageRef(path, i) for i in range(count)], path.parent)


def split_at(document: WorkingPdf, positions: list[int]) -> list[WorkingPdf]:
    cuts = sorted(set(p for p in positions if 0 < p < len(document.pages)))
    bounds = [0, *cuts, len(document.pages)]
    return _make_parts(document, [list(range(a, b)) for a, b in zip(bounds, bounds[1:])])


def split_ranges(document: WorkingPdf, ranges: str) -> list[WorkingPdf]:
    return _make_parts(document, parse_page_ranges(ranges, len(document.pages)))


def split_every(document: WorkingPdf, size: int) -> list[WorkingPdf]:
    if size < 1:
        raise PdfOrganizerError("分割するページ数は1以上を指定してください。")
    groups = [list(range(i, min(i + size, len(document.pages)))) for i in range(0, len(document.pages), size)]
    return _make_parts(document, groups)


def _make_parts(document: WorkingPdf, groups: list[list[int]]) -> list[WorkingPdf]:
    stem = Path(document.name).stem
    return [WorkingPdf(f"{stem}_{n:03d}.pdf", [document.pages[i] for i in indexes], document.source_dir)
            for n, indexes in enumerate(groups, 1)]


def merge(documents: list[WorkingPdf], name: str = "PDFまとめ.pdf") -> WorkingPdf:
    if len(documents) < 2:
        raise PdfOrganizerError("結合するPDFを2つ以上追加してください。")
    pages = [PageRef(p.source, p.index, p.rotation) for d in documents for p in d.pages]
    return WorkingPdf(name, pages, documents[0].source_dir)


def save_pdf(document: WorkingPdf, destination: str | Path) -> None:
    destination = Path(destination)
    writer = PdfWriter()
    readers: dict[Path, PdfReader] = {}
    try:
        for ref in document.pages:
            reader = readers.setdefault(ref.source, PdfReader(ref.source))
            page = reader.pages[ref.index]
            if ref.rotation:
                page.rotate(ref.rotation % 360)
            writer.add_page(page)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as output:
            writer.write(output)
    except (OSError, PdfReadError, FileNotDecryptedError, ValueError) as exc:
        if destination.exists() and destination.stat().st_size == 0:
            destination.unlink(missing_ok=True)
        raise PdfOrganizerError(f"PDFを保存できません。保存先への書き込み権限を確認してください。\n{exc}") from exc

