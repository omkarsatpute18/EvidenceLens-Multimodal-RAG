from app.agents.contradiction import detect_contradictions
from app.agents.synthesis import synthesize
from app.agents.verification import verify_answer
from app.models import FinalAnswer, EvidenceItem, WorkflowEvent


def format_answer(query: str, evidence: list[EvidenceItem], events: list[WorkflowEvent]) -> FinalAnswer:
    answer, findings, citations = synthesize(query, evidence)
    contradictions = detect_contradictions(evidence)
    status, limitations = verify_answer(answer, evidence, [citation.evidence_id for citation in citations])
    if contradictions:
        events.append(WorkflowEvent(label="Consistency check completed", detail="Potential mismatch detected", status="warning"))
    else:
        events.append(WorkflowEvent(label="Consistency check completed", detail="No direct mismatch detected"))
    events.append(WorkflowEvent(label="Verification completed", detail=status, status="warning" if status != "passed" else "completed"))
    confidence = 0.0 if not evidence else max(0.25, min(0.98, sum(item.extraction_confidence for item in evidence) / len(evidence)))
    if contradictions:
        confidence = min(confidence, 0.65)
    return FinalAnswer(
        answer=answer,
        key_findings=findings,
        citations=citations,
        evidence_items=evidence,
        confidence=round(confidence, 2),
        contradictions=contradictions,
        limitations=limitations,
        verification_status=status,
        suggested_followups=["Which source should be treated as authoritative?", "Would you like the evidence filtered to one file or date?"],
        workflow_events=events,
    )
