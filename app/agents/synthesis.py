from app.models import Citation, EvidenceItem


def synthesize(query: str, evidence: list[EvidenceItem]) -> tuple[str, list[str], list[Citation]]:
    if not evidence:
        return ("I could not find evidence that answers this question in the uploaded bundle.", [], [])
    citations = [Citation(evidence_id=item.evidence_id, label=item.citation, source_file=item.source_file,
                          location=item.metadata.get("location", "")) for item in evidence]
    findings = [item.text_content for item in evidence[:4]]
    answer = "Based on the retrieved evidence, " + " ".join(findings[:2])
    if len(evidence) > 2:
        answer += " The remaining retrieved sources provide additional context for this conclusion."
    return answer, findings, citations
