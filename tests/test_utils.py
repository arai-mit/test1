import pytest

from pdf_organizer.errors import InvalidFileName
from pdf_organizer.utils import validate_folder_name


@pytest.mark.parametrize("name", ['請求書:8月', "資料?", "CON", "NUL.txt", "末尾."])
def test_validate_folder_name_rejects_windows_invalid_names(name: str) -> None:
    with pytest.raises(InvalidFileName, match="Windows"):
        validate_folder_name(name)


def test_validate_folder_name_accepts_japanese_name() -> None:
    assert validate_folder_name(" 2026年8月_請求書 ") == "2026年8月_請求書"
