from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntegrationSource:
    name: str
    url: str
    license_note: str
    useful_for: str
    status: str


INTEGRATION_SOURCES = [
    IntegrationSource(
        name="dgunning/edgartools",
        url="https://github.com/dgunning/edgartools",
        license_note="MIT according to project documentation.",
        useful_for="Structured SEC filing, XBRL, insider, 13F, S-1, and 424B parsing.",
        status="Reference now; good candidate for an optional parser backend.",
    ),
    IntegrationSource(
        name="jadchaar/sec-edgar-api",
        url="https://github.com/jadchaar/sec-edgar-api",
        license_note="Check upstream license before vendoring or redistributing.",
        useful_for="Lightweight wrapper over SEC REST endpoints with pagination and fair-access rate limiting.",
        status="Reference now; our direct SEC client mirrors the same endpoint boundaries.",
    ),
    IntegrationSource(
        name="sec-edgar/sec-edgar",
        url="https://github.com/sec-edgar/sec-edgar",
        license_note="Apache-2.0 appears in GitHub search metadata; verify upstream before reuse.",
        useful_for="Bulk filing downloads across many companies and form types.",
        status="Reference now; useful if CapTable Lens expands into bulk historical backfills.",
    ),
    IntegrationSource(
        name="bellingcat/EDGAR",
        url="https://github.com/bellingcat/EDGAR",
        license_note="Check upstream license before reuse.",
        useful_for="CLI ergonomics for searching and retrieving broad SEC form types.",
        status="Reference now; useful for future investigation-style search commands.",
    ),
    IntegrationSource(
        name="stefanoamorelli/sec-edgar-toolkit",
        url="https://github.com/stefanoamorelli/sec-edgar-toolkit",
        license_note="AGPL-3.0 according to the project README; avoid code copying unless the project accepts AGPL obligations.",
        useful_for="Python and TypeScript EDGAR toolkit patterns, XBRL extraction, and full-stack SDK direction.",
        status="Reference only unless explicitly choosing AGPL-compatible distribution.",
    ),
]


def integration_sources_as_rows() -> list[dict[str, str]]:
    return [source.__dict__.copy() for source in INTEGRATION_SOURCES]

