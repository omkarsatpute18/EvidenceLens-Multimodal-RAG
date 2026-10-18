from app.agents.contradiction import detect_contradictions
from app.models import ContentType, EvidenceItem


def evidence(evidence_id: str, text: str, **metadata) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        source_file=f"{evidence_id}.txt",
        source_type="txt",
        content_type=ContentType.TEXT,
        text_content=text,
        metadata=metadata,
    )


def test_same_subject_category_unit_and_period_is_a_mismatch():
    items = [
        evidence("a", "North revenue was 10% in 2023."),
        evidence("b", "North revenue was 12 percent in 2023."),
    ]

    findings = detect_contradictions(items)

    assert len(findings) == 1
    assert "numeric value mismatch" in findings[0]
    assert "subject 'north'" in findings[0]
    assert "category 'revenue'" in findings[0]
    assert "unit 'percent'" in findings[0]
    assert "period '2023'" in findings[0]


def test_different_categories_are_not_contradictions():
    items = [
        evidence("a", "North revenue was 10% in 2023."),
        evidence("b", "North margin was 12% in 2023."),
    ]

    assert detect_contradictions(items) == []


def test_different_units_are_not_contradictions():
    items = [
        evidence("a", "North revenue was 10% in 2023."),
        evidence("b", "North revenue was 10 USD in 2023."),
    ]

    assert detect_contradictions(items) == []


def test_different_periods_are_not_contradictions():
    items = [
        evidence("a", "North revenue was 10% in 2023."),
        evidence("b", "North revenue was 12% in 2024."),
    ]

    assert detect_contradictions(items) == []


def test_incomplete_numeric_context_is_not_a_contradiction():
    items = [
        evidence("a", "North reported 10% in 2023."),
        evidence("b", "North revenue was 12% in 2023."),
    ]

    assert detect_contradictions(items) == []


def test_structured_subject_and_category_cues_are_normalized():
    items = [
        evidence(
            "a",
            "Region: North; Decline: 12%",
            subject="North Region",
            category="declines",
            period="FY 2023",
        ),
        evidence(
            "b",
            "Region: North; Decline: 15%",
            subject="North",
            category="decline",
            period="FY 2023",
        ),
    ]

    findings = detect_contradictions(items)

    assert len(findings) == 1
    assert "subject 'north'" in findings[0]
    assert "category 'decline'" in findings[0]
