from __future__ import annotations

import html
import re
from dataclasses import dataclass


MONEY_RE = re.compile(
    r"(?P<prefix>\$|US\$)?\s?(?P<num>\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s?"
    r"(?P<unit>billion|million|thousand|bn|mm|m)?",
    re.IGNORECASE,
)


FINANCING_PATTERNS = [
    ("ATM", re.compile(r"\bat[-\s]?the[-\s]?market\b|\bATM program\b|\bsales agreement\b", re.I)),
    ("Shelf Registration", re.compile(r"\bshelf registration\b|\bForm S-3\b|\bregistration statement\b", re.I)),
    ("Private Placement", re.compile(r"\bprivate placement\b|\bPIPE\b|\bsecurities purchase agreement\b", re.I)),
    ("Convertible Debt", re.compile(r"\bconvertible (senior )?notes?\b|\bconvertible debt\b", re.I)),
    ("Warrants", re.compile(r"\bwarrants?\b", re.I)),
    ("Debt Financing", re.compile(r"\bcredit facility\b|\bterm loan\b|\bsenior notes?\b|\bindenture\b", re.I)),
]

USE_PATTERNS = [
    ("growth capex", re.compile(r"\b(capital expenditures?|capex|construct|construction|facility|fab|factory|plant|capacity|expansion|manufacturing)\b", re.I)),
    ("M&A", re.compile(r"\b(acquisition|acquire|merger|M&A|business combination)\b", re.I)),
    ("debt repayment", re.compile(r"\b(repay|repayment|refinance|redeem|retire).{0,80}\b(debt|notes?|loan|facility)\b", re.I)),
    ("working capital", re.compile(r"\bworking capital\b", re.I)),
    ("general corporate purposes", re.compile(r"\bgeneral corporate purposes\b", re.I)),
]


@dataclass
class ParsedFiling:
    financing_type: str
    offering_amount_usd: float | None
    use_of_proceeds: str
    evidence: list[str]


def clean_text(raw: str, max_chars: int = 450_000) -> str:
    text = re.sub(r"<script.*?</script>", " ", raw, flags=re.I | re.S)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text[:max_chars]


def parse_filing(raw: str) -> ParsedFiling:
    text = clean_text(raw)
    financing_type = classify_financing(text)
    amount = extract_offering_amount(text)
    use = classify_use_of_proceeds(text)
    evidence = extract_evidence(text)
    return ParsedFiling(financing_type, amount, use, evidence)


def classify_financing(text: str) -> str:
    hits = [name for name, pattern in FINANCING_PATTERNS if pattern.search(text)]
    if "ATM" in hits:
        return "ATM"
    if "Convertible Debt" in hits:
        return "Convertible Debt"
    if "Private Placement" in hits:
        return "Private Placement"
    if "Shelf Registration" in hits:
        return "Shelf Registration"
    if hits:
        return hits[0]
    return "Unclassified"


def extract_offering_amount(text: str) -> float | None:
    windows = []
    for pattern in [
        r"aggregate offering price.{0,220}",
        r"maximum aggregate.{0,220}",
        r"up to.{0,160}",
        r"gross proceeds.{0,160}",
        r"sales agreement.{0,220}",
    ]:
        windows.extend(match.group(0) for match in re.finditer(pattern, text, flags=re.I))

    candidates: list[float] = []
    for window in windows[:25]:
        for match in MONEY_RE.finditer(window):
            value = _money_to_float(match)
            if value and value >= 1_000_000:
                candidates.append(value)
    if candidates:
        return max(candidates)
    return None


def classify_use_of_proceeds(text: str) -> str:
    idx = text.lower().find("use of proceeds")
    sample = text[idx : idx + 3500] if idx >= 0 else text[:80_000]
    hits = [name for name, pattern in USE_PATTERNS if pattern.search(sample)]
    if not hits:
        return "unclear"
    if "growth capex" in hits:
        return "growth capex"
    if "M&A" in hits:
        return "M&A"
    if "debt repayment" in hits:
        return "debt repayment"
    if "working capital" in hits:
        return "working capital"
    return hits[0]


def extract_evidence(text: str) -> list[str]:
    phrases = []
    for pattern in [
        r"at[-\s]?the[-\s]?market.{0,220}",
        r"use of proceeds.{0,260}",
        r"general corporate purposes.{0,180}",
        r"working capital.{0,180}",
        r"capital expenditures?.{0,180}",
        r"convertible (senior )?notes?.{0,220}",
        r"private placement.{0,220}",
    ]:
        for match in re.finditer(pattern, text, flags=re.I):
            phrase = re.sub(r"\s+", " ", match.group(0)).strip()
            if phrase and phrase not in phrases:
                phrases.append(phrase[:260])
            if len(phrases) >= 6:
                return phrases
    return phrases


def _money_to_float(match: re.Match[str]) -> float | None:
    raw = match.group("num").replace(",", "")
    try:
        value = float(raw)
    except ValueError:
        return None
    unit = (match.group("unit") or "").lower()
    if unit in {"billion", "bn"}:
        value *= 1_000_000_000
    elif unit in {"million", "mm", "m"}:
        value *= 1_000_000
    elif unit == "thousand":
        value *= 1_000
    elif match.group("prefix") in {"$", "US$"} and value < 10_000:
        return None
    return value

