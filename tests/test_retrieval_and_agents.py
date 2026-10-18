from app.agents.contradiction import detect_contradictions
from app.agents.ingestion import ingest_path
from app.agents.orchestrator import classify_query
from app.agents.retrieval import MultimodalRetrievalAgent
from app.retrieval.index import HybridIndex
from app.services.store import EvidenceStore


def test_retrieval_prefers_matching_table(tmp_path):
    path = tmp_path / "table.csv"
    path.write_text("Region,Decline\nNorth,-12%\nSouth,-3%\n", encoding="utf-8")
    result = ingest_path(path)
    index = HybridIndex()
    index.add(result.evidence)
    hits = MultimodalRetrievalAgent(index).retrieve("North decline", {"table"}, 5)
    assert hits and hits[0].structured_content["row"]["Region"] == "North"


def test_query_planner_is_selective():
    text_plan = classify_query("Summarize the report")
    chart_plan = classify_query("Does the chart agree with the table?")
    assert text_plan.modes == {"text"}
    assert {"table", "chart", "image"}.issubset(chart_plan.modes)
    assert "comparison" in chart_plan.labels


def test_conflict_is_reported():
    store = EvidenceStore()
    store.ingest_files([("a.txt", b"North declined by 12%.") , ("b.txt", b"North declined by 3%.")])
    assert detect_contradictions(store.evidence())


def test_duplicate_filenames_are_isolated(tmp_path):
    store = EvidenceStore()
    result = store.ingest_files([("../report.txt", b"first"), ("report.txt", b"second")])
    assert result.files == ["report.txt", "report (2).txt"]
    assert {item.source_file for item in store.evidence()} == {"report.txt", "report (2).txt"}
