import re

from app.models import EvidenceItem


NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?%?")


def detect_contradictions(items: list[EvidenceItem]) -> list[str]:
    findings: list[str] = []
    numeric_claims: dict[str, list[tuple[str, str]]] = {}
    for item in items:
        for number in NUMBER_RE.findall(item.text_content):
            context = re.sub(r"\s+", " ", item.text_content).strip()[:120]
            numeric_claims.setdefault(number, []).append((item.evidence_id, context))
    # Surface a meaningful cross-source warning when comparable evidence has different values.
    if len(items) >= 2:
        values = [(item.evidence_id, NUMBER_RE.findall(item.text_content)) for item in items]
        nonempty = [(identifier, nums) for identifier, nums in values if nums]
        if len(nonempty) >= 2 and len({tuple(nums) for _, nums in nonempty}) > 1:
            findings.append("Retrieved sources contain different numeric claims; verify units, dates, and category labels.")
    return findings
