from app.models import ContentType, EvidenceItem
from app.retrieval.index import HybridIndex


def _item(
    evidence_id: str,
    text: str,
    *,
    content_type: ContentType = ContentType.TEXT,
    metadata: dict[str, object] | None = None,
    page_number: int | None = None,
) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        source_file=f"{evidence_id}.txt",
        source_type="txt",
        content_type=content_type,
        text_content=text,
        metadata=metadata or {},
        page_number=page_number,
    )


def test_hybrid_scores_are_deterministic_and_traceable():
    index = HybridIndex(lexical_weight=0.7, vector_weight=0.3)
    index.add(
        [
            _item("b", "alpha beta"),
            _item("a", "alpha unrelated"),
        ]
    )

    results, trace = index.search_with_trace("alpha beta", top_k=2)

    assert [item.evidence_id for item in results] == ["b", "a"]
    assert trace == index.last_trace
    assert trace[0]["evidence_id"] == results[0].evidence_id
    assert trace[0]["lexical_score"] == 1.0
    assert trace[0]["vector_score"] > 0.0
    assert trace[0]["components"] == {
        "lexical": trace[0]["lexical_score"],
        "vector": trace[0]["vector_score"],
    }
    assert trace[0]["fused_score"] == results[0].retrieval_score
    assert results[0].metadata["retrieval_trace"] == trace[0]


def test_content_type_and_metadata_filters_are_applied_before_ranking():
    index = HybridIndex()
    index.add(
        [
            _item(
                "table-finance",
                "revenue increased",
                content_type=ContentType.TABLE,
                metadata={"topic": "finance"},
                page_number=2,
            ),
            _item(
                "text-finance",
                "revenue increased",
                metadata={"topic": "finance"},
                page_number=2,
            ),
            _item(
                "table-sales",
                "revenue increased",
                content_type=ContentType.TABLE,
                metadata={"topic": "sales"},
                page_number=3,
            ),
        ]
    )

    results = index.search(
        "revenue",
        content_types={ContentType.TABLE},
        metadata_filters={"topic": "finance", "page_number": 2},
        top_k=5,
    )

    assert [item.evidence_id for item in results] == ["table-finance"]


def test_equal_fused_scores_use_a_stable_evidence_id_tiebreaker():
    index = HybridIndex(vector_weight=0.0)
    index.add([_item("z", "same signal"), _item("a", "same signal")])

    results = index.search("same signal", top_k=2)

    assert [item.evidence_id for item in results] == ["a", "z"]
