import csv
from pathlib import Path

from app.models import ContentType, EvidenceItem
from .text import stable_id


def _row_item(path: Path, sheet: str, row_number: int, headers: list[str], values: list[str]) -> EvidenceItem:
    pairs = {header or f"column_{i + 1}": value for i, (header, value) in enumerate(zip(headers, values))}
    text = "; ".join(f"{key}: {value}" for key, value in pairs.items() if value != "")
    return EvidenceItem(
        evidence_id=stable_id(path.name, f"{sheet}-{row_number}", text),
        source_file=path.name,
        source_type=path.suffix.lower().lstrip("."),
        content_type=ContentType.TABLE,
        text_content=text,
        structured_content={"headers": headers, "row": pairs},
        sheet_name=sheet,
        row_start=row_number,
        row_end=row_number,
        column_start="A",
        column_end=chr(64 + min(len(headers), 26)) if headers else None,
        metadata={"units": "not specified", "location": f"{sheet} row {row_number}"},
    )


def parse_csv(path: Path) -> list[EvidenceItem]:
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        rows = list(csv.reader(handle))
    if len(rows) < 2:
        return []
    headers = rows[0]
    return [_row_item(path, "CSV", number, headers, row) for number, row in enumerate(rows[1:], start=2) if any(row)]


def parse_xlsx(path: Path) -> list[EvidenceItem]:
    try:
        import openpyxl
    except ImportError as exc:
        raise RuntimeError("XLSX support requires openpyxl") from exc
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    items: list[EvidenceItem] = []
    for sheet in workbook.worksheets:
        rows = list(sheet.iter_rows(values_only=True))
        if len(rows) < 2:
            continue
        headers = [str(value or "") for value in rows[0]]
        for number, row in enumerate(rows[1:], start=2):
            values = ["" if value is None else str(value) for value in row]
            if any(values):
                items.append(_row_item(path, sheet.title, number, headers, values))
    return items
