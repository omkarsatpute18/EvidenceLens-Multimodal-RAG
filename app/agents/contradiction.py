from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re
from typing import Any, Iterable, Mapping

from app.models import EvidenceItem


# Keep the public module-level name used by the original implementation while
# allowing currency symbols, commas, and numbers next to a unit suffix.
NUMBER_RE = re.compile(
    r"(?<![\w.])(?P<prefix>[$€£¥])?\s*"
    r"(?P<number>[+-]?(?:\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?|\.\d+))(?!\d)",
    re.IGNORECASE,
)

_CLAUSE_RE = re.compile(r"(?<=[.!?])\s+|[\n;|]+")
_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_&'/-]*")
_LABEL_RE = re.compile(
    r"\b(?P<label>subject|entity|region|area|segment|group|category|metric|measure|"
    r"period|date|year|quarter|unit|units)\s*[:=]\s*"
    r"(?P<value>[^;|,\n]+)",
    re.IGNORECASE,
)

_DATE_RE = re.compile(
    r"\b(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4}|"
    r"\d{1,2}/\d{4})\b"
)
_MONTH_DATE_RE = re.compile(
    r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|"
    r"dec(?:ember)?)\s+\d{1,2}(?:,\s*|\s+)\d{4}\b",
    re.IGNORECASE,
)
_MONTH_YEAR_RE = re.compile(
    r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|"
    r"dec(?:ember)?)\s+\d{4}\b",
    re.IGNORECASE,
)
_QUARTER_RE = re.compile(
    r"\b(?:fy\s*)?(?:q(?:uarter)?\s*[1-4])\s*[-/]?\s*(?:fy\s*)?\d{4}\b|"
    r"\b(?:fy\s*)?\d{4}\s*[-/]?\s*(?:q(?:uarter)?\s*[1-4])\b",
    re.IGNORECASE,
)
_FISCAL_YEAR_RE = re.compile(r"\bfy\s*\d{4}\b", re.IGNORECASE)
_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")

_FIELD_ALIASES = {
    "subject": {"subject", "entity", "region", "area", "segment", "group", "name"},
    "category": {"category", "metric", "measure", "indicator"},
    "period": {"period", "date", "year", "quarter", "time", "asof", "reportingperiod"},
    "unit": {"unit", "units", "uom", "currency"},
}
_SUBJECT_LABELS = _FIELD_ALIASES["subject"]
_PERIOD_LABELS = _FIELD_ALIASES["period"]

_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "by",
    "came",
    "equals",
    "equal",
    "for",
    "from",
    "had",
    "has",
    "in",
    "is",
    "of",
    "on",
    "reported",
    "reports",
    "stood",
    "stands",
    "the",
    "to",
    "was",
    "were",
    "with",
}
_CATEGORY_WORDS = {
    "amount",
    "change",
    "churn",
    "cost",
    "costs",
    "count",
    "decline",
    "declined",
    "decrease",
    "decreased",
    "employees",
    "expenses",
    "growth",
    "headcount",
    "margin",
    "price",
    "profit",
    "rate",
    "revenue",
    "sales",
    "total",
    "users",
    "volume",
}
_CATEGORY_ALIASES = {
    "declined": "decline",
    "decreased": "decline",
    "decreasing": "decline",
    "decrease": "decline",
    "fall": "decline",
    "fallen": "decline",
    "fell": "decline",
    "falling": "decline",
    "down": "decline",
    "increased": "increase",
    "increasing": "increase",
    "increase": "increase",
    "grew": "increase",
    "growing": "increase",
    "growth": "increase",
    "up": "increase",
}
_UNIT_ALIASES = {
    "%": "percent",
    "percent": "percent",
    "percentage": "percent",
    "percentages": "percent",
    "pp": "percentage_points",
    "point": "percentage_points",
    "points": "percentage_points",
    "percentagepoint": "percentage_points",
    "percentagepoints": "percentage_points",
    "bps": "basis_points",
    "basispoint": "basis_points",
    "basispoints": "basis_points",
    "$": "usd",
    "usd": "usd",
    "us dollar": "usd",
    "us dollars": "usd",
    "dollar": "usd",
    "dollars": "usd",
    "€": "eur",
    "eur": "eur",
    "euro": "eur",
    "euros": "eur",
    "£": "gbp",
    "gbp": "gbp",
    "pound": "gbp",
    "pounds": "gbp",
    "¥": "jpy",
    "jpy": "jpy",
    "yen": "jpy",
    "unit": "unit",
    "units": "unit",
    "count": "count",
    "counts": "count",
    "people": "people",
    "person": "people",
    "employee": "employee",
    "employees": "employee",
    "users": "user",
    "user": "user",
    "kg": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "g": "g",
    "gram": "g",
    "grams": "g",
    "km": "km",
    "kilometer": "km",
    "kilometers": "km",
}
_SCALE_ALIASES = {
    "k": ("thousand", Decimal("1000")),
    "thousand": ("thousand", Decimal("1000")),
    "thousands": ("thousand", Decimal("1000")),
    "m": ("million", Decimal("1000000")),
    "mn": ("million", Decimal("1000000")),
    "million": ("million", Decimal("1000000")),
    "millions": ("million", Decimal("1000000")),
    "b": ("billion", Decimal("1000000000")),
    "bn": ("billion", Decimal("1000000000")),
    "billion": ("billion", Decimal("1000000000")),
    "billions": ("billion", Decimal("1000000000")),
    "t": ("trillion", Decimal("1000000000000")),
    "tn": ("trillion", Decimal("1000000000000")),
    "trillion": ("trillion", Decimal("1000000000000")),
    "trillions": ("trillion", Decimal("1000000000000")),
}
_CURRENCY_SYMBOLS = {"$": "usd", "€": "eur", "£": "gbp", "¥": "jpy"}
_MISSING_CONTEXT = {"", "n/a", "na", "none", "not specified", "unknown", "unspecified"}


@dataclass(frozen=True)
class _Context:
    subject: str | None = None
    category: str | None = None
    unit: str | None = None
    period: str | None = None


@dataclass(frozen=True)
class _NumericClaim:
    evidence_id: str
    value: Decimal
    display_value: str
    subject: str | None
    category: str | None
    unit: str | None
    period: str | None


def _key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).strip().casefold())


def _clean_value(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if text.casefold() in _MISSING_CONTEXT:
        return None
    return text or None


def _mapping_value(mapping: Mapping[str, Any] | None, names: Iterable[str]) -> object | None:
    if not mapping:
        return None
    wanted = {_key(name) for name in names}
    for name, value in mapping.items():
        if _key(name) in wanted:
            cleaned = _clean_value(value)
            if cleaned is not None:
                return cleaned
    return None


def _normalize_subject(value: object | None) -> str | None:
    text = _clean_value(value)
    if text is None:
        return None
    words = [word.casefold() for word in _TOKEN_RE.findall(text)]
    words = [
        word
        for word in words
        if word not in {"the", "subject", "entity", "region", "area", "segment", "group"}
    ]
    return " ".join(words) or None


def _normalize_category(value: object | None) -> str | None:
    text = _clean_value(value)
    if text is None:
        return None
    # Units in a header such as "Revenue (%)" identify the value's unit, not
    # a second category.
    text = re.sub(
        r"\((?:%|percent(?:age)?|pp|bps|usd|eur|gbp|jpy|dollars?|euros?)\)",
        " ",
        text,
        flags=re.IGNORECASE,
    )
    words = [word.casefold() for word in _TOKEN_RE.findall(text)]
    words = [word for word in words if word not in {"the", "category", "metric", "measure", "indicator", "value"}]
    normalized: list[str] = []
    for word in words:
        if word in _CATEGORY_ALIASES:
            word = _CATEGORY_ALIASES[word]
        elif len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
            word = word[:-1]
        normalized.append(word)
    return " ".join(normalized) or None


def _normalize_unit(value: object | None) -> str | None:
    text = _clean_value(value)
    if text is None:
        return None
    lowered = text.casefold().strip()
    if lowered in _MISSING_CONTEXT:
        return None
    for alias, canonical in sorted(_UNIT_ALIASES.items(), key=lambda pair: len(pair[0]), reverse=True):
        if re.fullmatch(re.escape(alias), lowered):
            return canonical
    if re.search(r"(?:%|percent(?:age)?)", lowered):
        return "percent"
    if re.search(r"percentage\s*points?|\bpp\b", lowered):
        return "percentage_points"
    for alias, canonical in _UNIT_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", lowered):
            return canonical
    return None


def _normalize_period(value: object | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    text = _clean_value(value)
    if text is None:
        return None
    periods = _extract_periods(text)
    if periods:
        return "|".join(periods)
    return re.sub(r"[^a-z0-9]+", "", text.casefold()) or None


def _period_spans(text: str) -> list[tuple[int, int, str]]:
    spans: list[tuple[int, int, str]] = []

    def add_matches(pattern: re.Pattern[str], normalizer) -> None:
        for match in pattern.finditer(text):
            if any(match.start() < end and start < match.end() for start, end, _ in spans):
                continue
            spans.append((match.start(), match.end(), normalizer(match.group(0))))

    add_matches(_DATE_RE, _normalize_period_token)
    add_matches(_MONTH_DATE_RE, _normalize_period_token)
    add_matches(_QUARTER_RE, _normalize_period_token)
    add_matches(_FISCAL_YEAR_RE, _normalize_period_token)
    add_matches(_MONTH_YEAR_RE, _normalize_period_token)
    add_matches(_YEAR_RE, _normalize_period_token)
    return spans


def _normalize_period_token(value: str) -> str:
    text = value.casefold().strip()
    text = re.sub(r"\s+", " ", text)
    fiscal = bool(re.search(r"\bfy\s*\d{4}\b", text))
    quarter = re.search(r"q(?:uarter)?\s*([1-4])", text)
    year = re.search(r"(?:19|20)\d{2}", text)
    if quarter and year:
        return f"{'fy-' if fiscal else ''}q{quarter.group(1)}-{year.group(0)}"
    if fiscal and year:
        return f"fy-{year.group(0)}"
    if year and re.search(r"[-/]", text):
        parts = re.findall(r"\d+", text)
        if len(parts) == 3:
            if len(parts[0]) == 4:
                return f"{parts[0]}-{int(parts[1]):02d}-{int(parts[2]):02d}"
            return f"{parts[2]}-{int(parts[1]):02d}-{int(parts[0]):02d}"
        if len(parts) == 2 and len(parts[0]) <= 2:
            return f"{parts[1]}-{int(parts[0]):02d}"
    month = re.search(
        r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|"
        r"dec(?:ember)?)\b",
        text,
    )
    if month and year:
        month_names = {
            "jan": 1,
            "january": 1,
            "feb": 2,
            "february": 2,
            "mar": 3,
            "march": 3,
            "apr": 4,
            "april": 4,
            "may": 5,
            "jun": 6,
            "june": 6,
            "jul": 7,
            "july": 7,
            "aug": 8,
            "august": 8,
            "sep": 9,
            "september": 9,
            "oct": 10,
            "october": 10,
            "nov": 11,
            "november": 11,
            "dec": 12,
            "december": 12,
        }
        month_number = month_names[month.group(1)]
        day = re.search(r"\b\d{1,2}\b", text.replace(year.group(0), ""))
        return f"{year.group(0)}-{month_number:02d}-{int(day.group(0)):02d}" if day else f"{year.group(0)}-{month_number:02d}"
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def _extract_periods(text: str) -> tuple[str, ...]:
    values = [normalized for _, _, normalized in _period_spans(text) if normalized]
    # Preserve the order in the source while removing repeated cues such as a
    # year appearing both in a date and in a surrounding phrase.
    return tuple(dict.fromkeys(values))


def _is_period_number(match: re.Match[str], spans: list[tuple[int, int, str]]) -> bool:
    return any(match.start() < end and start < match.end() for start, end, _ in spans)


def _scale_after(text: str, end: int) -> tuple[str | None, Decimal]:
    tail = text[end : end + 24]
    match = re.match(r"\s*(k|m|b|t|mn|bn|tn|thousand|thousands|million|millions|"
                     r"billion|billions|trillion|trillions)\b", tail, re.IGNORECASE)
    if not match:
        return None, Decimal("1")
    return _SCALE_ALIASES[match.group(1).casefold()]


def _unit_near_number(text: str, match: re.Match[str]) -> tuple[str | None, Decimal]:
    before = text[max(0, match.start() - 18) : match.start()]
    after = text[match.end() : match.end() + 30]
    prefix = match.group("prefix") or ""
    currency = _CURRENCY_SYMBOLS.get(prefix)
    if currency is None:
        currency_match = re.search(r"(?:^|\s)(usd|eur|gbp|jpy)\s*$", before, re.IGNORECASE)
        if currency_match:
            currency = currency_match.group(1).casefold()

    scale, multiplier = _scale_after(text, match.end())
    if scale is None:
        scale_match = re.search(r"\b(k|m|b|t|mn|bn|tn|thousand|thousands|million|millions|"
                                r"billion|billions|trillion|trillions)\b", after, re.IGNORECASE)
        if scale_match and scale_match.start() <= 8:
            scale, multiplier = _SCALE_ALIASES[scale_match.group(1).casefold()]

    unit_match = re.match(
        r"\s*(%|percent(?:age)?|percentage\s+points?|pp|bps|usd|eur|gbp|jpy|"
        r"dollars?|euros?|pounds?|yen|units?|count|people|persons?|employees?|"
        r"users?|kg|kilograms?|g|grams?|km|kilometers?)(?![A-Za-z])",
        after,
        re.IGNORECASE,
    )
    unit = _normalize_unit(unit_match.group(1)) if unit_match else currency
    if unit is None:
        # A currency code can follow a scale, for example "10 million USD".
        code_match = re.search(r"\b(usd|eur|gbp|jpy|dollars?|euros?|pounds?|yen)\b", after, re.IGNORECASE)
        if code_match and code_match.start() <= 18:
            unit = _normalize_unit(code_match.group(1))
    if scale is not None:
        unit = f"{unit or 'number'}:{scale}"
    return unit, multiplier


def _item_context(item: EvidenceItem) -> _Context:
    mappings: list[Mapping[str, Any]] = []
    if item.metadata:
        mappings.append(item.metadata)
    if item.structured_content:
        mappings.append(item.structured_content)

    subject = category = unit = period = None
    for mapping in mappings:
        subject = subject or _normalize_subject(_mapping_value(mapping, _SUBJECT_LABELS))
        category = category or _normalize_category(_mapping_value(mapping, _FIELD_ALIASES["category"]))
        unit = unit or _normalize_unit(_mapping_value(mapping, _FIELD_ALIASES["unit"]))
        period = period or _normalize_period(_mapping_value(mapping, _PERIOD_LABELS))

    row = item.structured_content.get("row") if isinstance(item.structured_content, Mapping) else None
    if isinstance(row, Mapping):
        subject = subject or _normalize_subject(_mapping_value(row, _SUBJECT_LABELS))
        period = period or _normalize_period(_mapping_value(row, _PERIOD_LABELS))
    return _Context(subject=subject, category=category, unit=unit, period=period)


def _label_context(text: str) -> _Context:
    subject = category = unit = period = None
    for match in _LABEL_RE.finditer(text):
        label = _key(match.group("label"))
        value = match.group("value").strip()
        if label in {_key(name) for name in _SUBJECT_LABELS}:
            subject = subject or _normalize_subject(value)
        elif label in {_key(name) for name in _FIELD_ALIASES["category"]}:
            category = category or _normalize_category(value)
        elif label in {_key(name) for name in _PERIOD_LABELS}:
            period = period or _normalize_period(value)
        elif label in {_key(name) for name in _FIELD_ALIASES["unit"]}:
            unit = unit or _normalize_unit(value)
    return _Context(subject=subject, category=category, unit=unit, period=period)


def _row_category(item: EvidenceItem, match: re.Match[str]) -> str | None:
    structured = item.structured_content
    row = structured.get("row") if isinstance(structured, Mapping) else None
    if not isinstance(row, Mapping):
        return None
    try:
        target = Decimal(match.group("number").replace(",", ""))
    except InvalidOperation:
        return None
    for name, value in row.items():
        if _key(name) in {_key(alias) for alias in _SUBJECT_LABELS | _PERIOD_LABELS}:
            continue
        value_text = str(value)
        value_match = NUMBER_RE.search(value_text)
        if value_match is None:
            continue
        try:
            if Decimal(value_match.group("number").replace(",", "")) == target:
                return _normalize_category(name)
        except InvalidOperation:
            continue
    return None


def _meaningful_words(prefix: str) -> list[str]:
    words = [word for word in _TOKEN_RE.findall(prefix) if word.casefold() not in _STOPWORDS]
    return words


def _inferred_context(clause: str, match: re.Match[str]) -> _Context:
    prefix = re.sub(r"\s+", " ", clause[: match.start()]).strip(" ,:;-=")
    if not prefix:
        return _Context()

    # Keep the local claim after a conjunction when one clause contains two
    # values, e.g. "North revenue 10 and margin 12".
    pieces = re.split(r"\b(?:and|but|whereas|while)\b", prefix, flags=re.IGNORECASE)
    if len(pieces) > 1:
        prefix = pieces[-1].strip(" ,:;-=")

    cleaned = re.sub(r"\b(?:was|were|is|are|equals?|reported|reports|stood|stands|had|has)\b", " ", prefix, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,:;-=")
    if not cleaned:
        return _Context()

    subject = category = None
    if ":" in cleaned:
        left, right = cleaned.rsplit(":", 1)
        left_words = _meaningful_words(left)
        right_words = _meaningful_words(right)
        if left_words and right_words:
            subject = " ".join(left_words)
            category = " ".join(right_words)
        elif right_words:
            category = " ".join(right_words)
    if subject is None or category is None:
        possessive = re.search(
            r"(?P<subject>[A-Za-z][A-Za-z0-9 &'/-]*)['’]s\s+(?P<category>[A-Za-z][A-Za-z0-9 &'/-]*)$",
            cleaned,
        )
        if possessive:
            subject = subject or possessive.group("subject")
            category = category or possessive.group("category")

    if subject is None or category is None:
        for separator in (" for ", " of ", " in "):
            if separator in f" {cleaned.casefold()} ":
                parts = re.split(
                    rf"\b{re.escape(separator.strip())}\b",
                    cleaned,
                    maxsplit=1,
                    flags=re.IGNORECASE,
                )
                if len(parts) != 2:
                    continue
                before, after = parts
                before_words = _meaningful_words(before)
                after_words = _meaningful_words(after)
                if before_words and after_words:
                    category = category or " ".join(before_words)
                    subject = subject or " ".join(after_words)
                    break

    words = _meaningful_words(cleaned)
    if subject is None and category is None and words:
        category_words = [word.casefold() for word in words]
        first_is_category = category_words[0] in _CATEGORY_WORDS or category_words[0] in _CATEGORY_ALIASES
        if len(words) == 1 or first_is_category:
            category = " ".join(words)
        else:
            # The first one or two leading labels are the subject; the rest is
            # the metric. This handles "North revenue" and "North America revenue".
            subject_count = 2 if len(words) > 2 and words[0][:1].isupper() and words[1][:1].isupper() else 1
            subject = " ".join(words[:subject_count])
            category = " ".join(words[subject_count:]) or None

    return _Context(
        subject=_normalize_subject(subject),
        category=_normalize_category(category),
    )


def _claim_context(item: EvidenceItem, text_context: _Context, clause: str, match: re.Match[str]) -> _Context:
    inferred = _inferred_context(clause, match)
    row_category = _row_category(item, match)
    local_unit, _ = _unit_near_number(clause, match)
    local_periods = _extract_periods(clause)
    return _Context(
        subject=(text_context.subject or _item_context(item).subject or inferred.subject),
        category=(row_category or text_context.category or _item_context(item).category or inferred.category),
        unit=(local_unit or text_context.unit or _item_context(item).unit),
        period=("|".join(local_periods) if local_periods else text_context.period or _item_context(item).period),
    )


def _claims_for_item(item: EvidenceItem) -> list[_NumericClaim]:
    text = item.text_content or ""
    if not text:
        return []
    text_context = _label_context(text)
    item_context = _item_context(item)
    # Explicit item metadata wins over text labels, while a row-specific
    # category is selected later for each value.
    text_context = _Context(
        subject=item_context.subject or text_context.subject,
        category=item_context.category or text_context.category,
        unit=item_context.unit or text_context.unit,
        period=item_context.period or text_context.period,
    )
    claims: list[_NumericClaim] = []
    for clause in _CLAUSE_RE.split(text):
        if not clause.strip():
            continue
        periods = list(_period_spans(clause))
        for match in NUMBER_RE.finditer(clause):
            if _is_period_number(match, periods):
                continue
            try:
                raw_value = Decimal(match.group("number").replace(",", ""))
            except InvalidOperation:
                continue
            local_unit, multiplier = _unit_near_number(clause, match)
            context = _claim_context(item, text_context, clause, match)
            unit = context.unit
            if local_unit is not None:
                unit = local_unit
            value = raw_value * multiplier
            claims.append(
                _NumericClaim(
                    evidence_id=item.evidence_id,
                    value=value,
                    display_value=match.group(0).strip(),
                    subject=context.subject,
                    category=context.category,
                    unit=unit,
                    period=context.period,
                )
            )
    return claims


def _claim_key(claim: _NumericClaim) -> tuple[str | None, str, str | None, str | None]:
    # A category is the minimum semantic cue. If both claims omit a subject,
    # they can still represent the same aggregate category; a missing category
    # leaves the evidence too incomplete for a contradiction warning.
    return claim.subject, claim.category or "", claim.unit, claim.period


def _display_number(value: Decimal) -> str:
    if value == value.to_integral_value():
        return str(int(value))
    return format(value.normalize(), "f")


def _mismatch_message(first: _NumericClaim, second: _NumericClaim) -> str:
    subject = first.subject or "overall"
    unit = first.unit or "unit not specified"
    period = first.period or "period not specified"
    return (
        "Retrieved sources contain different numeric claims: numeric value mismatch "
        f"for subject '{subject}', category '{first.category}', unit '{unit}', period '{period}'. "
        f"{first.evidence_id} reports {first.display_value} while "
        f"{second.evidence_id} reports {second.display_value}."
    )


def detect_contradictions(items: list[EvidenceItem]) -> list[str]:
    """Return warnings only for comparable claims with different values.

    Claims are grouped by normalized subject/category, unit, and period. A
    missing cue on one side is not treated as a match for a populated cue, so
    different categories, units, dates, or incomplete context do not become
    false contradictions.
    """

    if len(items) < 2:
        return []

    groups: dict[tuple[str | None, str, str | None, str | None], list[_NumericClaim]] = {}
    for item in items:
        for claim in _claims_for_item(item):
            if claim.category is None:
                continue
            groups.setdefault(_claim_key(claim), []).append(claim)

    findings: list[str] = []
    seen: set[tuple[str, str, str, str]] = set()
    for claims in groups.values():
        for index, first in enumerate(claims):
            for second in claims[index + 1 :]:
                if first.evidence_id == second.evidence_id or first.value == second.value:
                    continue
                pair = (first.evidence_id, second.evidence_id, str(first.value), str(second.value))
                if pair in seen:
                    continue
                seen.add(pair)
                findings.append(_mismatch_message(first, second))
    return findings
