from app.models import EvidenceItem


def verify_answer(answer: str, evidence: list[EvidenceItem], citations: list[str]) -> tuple[str, list[str]]:
    limitations: list[str] = []
    if not evidence:
        return "failed_no_evidence", ["No retrieved evidence supports an answer."]
    if not citations:
        return "failed_missing_citations", ["The answer has no source citations."]
    if any(item.extraction_confidence < 0.6 for item in evidence):
        limitations.append("At least one visual interpretation is uncertain; exact chart values were not asserted.")
    if len(answer.strip()) < 20:
        limitations.append("The answer is brief because the evidence set is limited.")
    return ("passed_with_warnings" if limitations else "passed"), limitations
