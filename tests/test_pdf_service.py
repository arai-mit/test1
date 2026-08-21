from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter

from pdf_organizer.errors import InvalidFileName, InvalidPageRange
from pdf_organizer.pdf_service import load_pdf, merge, save_pdf, split_at, split_every, split_ranges
from pdf_organizer.utils import validate_pdf_name


@pytest.fixture
def sample(tmp_path: Path) -> Path:
    path = tmp_path / "請求書.pdf"
    writer = PdfWriter()
    for width in (100, 200, 300, 400, 500): writer.add_blank_page(width=width, height=600)
    with path.open("wb") as stream: writer.write(stream)
    return path


def test_load_split_and_save_without_changing_source(sample: Path, tmp_path: Path) -> None:
    before = sample.read_bytes()
    doc = load_pdf(sample)
    parts = split_at(doc, [2, 4])
    assert [len(x.pages) for x in parts] == [2, 2, 1]
    parts[0].pages[0].rotation = 90
    output = tmp_path / "結果.pdf"
    save_pdf(parts[0], output)
    reader = PdfReader(output)
    assert len(reader.pages) == 2
    assert reader.pages[0].rotation == 90
    assert sample.read_bytes() == before


def test_all_split_modes_and_merge(sample: Path) -> None:
    doc = load_pdf(sample)
    assert [len(x.pages) for x in split_ranges(doc, "1-2\n3-5")] == [2, 3]
    singles = split_every(doc, 1)
    assert len(singles) == 5
    assert len(merge(singles).pages) == 5


@pytest.mark.parametrize("text", ["", "3", "0-2", "3-2", "1-9", "1-3,3-4"])
def test_invalid_ranges(sample: Path, text: str) -> None:
    with pytest.raises(InvalidPageRange): split_ranges(load_pdf(sample), text)


def test_windows_filename_validation() -> None:
    assert validate_pdf_name("2026年8月_請求書") == "2026年8月_請求書.pdf"
    with pytest.raises(InvalidFileName): validate_pdf_name("請求書:東京.pdf")

