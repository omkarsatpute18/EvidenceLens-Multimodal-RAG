from pathlib import Path

from app.agents.ingestion import ingest_path
from app.parsers.table import parse_csv
from app.parsers.text import parse_text


def test_text_preserves_source_and_stable_ids(tmp_path: Path):
    path = tmp_path / "report.md"
    path.write_text("Revenue increased.\n\nNorth declined by 12%.", encoding="utf-8")
    first = parse_text(path)
    second = parse_text(path)
    assert len(first) == 2
    assert first[0].source_file == "report.md"
    assert [x.evidence_id for x in first] == [x.evidence_id for x in second]


def test_csv_has_row_and_column_provenance(tmp_path: Path):
    path = tmp_path / "table.csv"
    path.write_text("Region,Change\nNorth,-12%\nSouth,4%\n", encoding="utf-8")
    items = parse_csv(path)
    assert items[0].sheet_name == "CSV"
    assert items[0].row_start == 2
    assert items[0].structured_content["row"]["Change"] == "-12%"


def test_unsupported_and_empty_files_fail_gracefully(tmp_path: Path):
    empty = tmp_path / "empty.txt"
    empty.write_bytes(b"")
    assert ingest_path(empty).errors
    unsupported = tmp_path / "secret.exe"
    unsupported.write_bytes(b"data")
    assert "Unsupported" in ingest_path(unsupported).errors[0]
