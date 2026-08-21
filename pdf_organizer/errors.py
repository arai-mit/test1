class PdfOrganizerError(Exception):
    """画面にそのまま表示できる業務エラー。"""


class InvalidPageRange(PdfOrganizerError):
    pass


class InvalidFileName(PdfOrganizerError):
    pass

