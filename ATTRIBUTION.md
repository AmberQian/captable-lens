# CapTable Lens Attribution

CapTable Lens currently does not vendor, copy, or redistribute source code from the projects below. They are credited because their public repositories informed the integration roadmap and helped identify reliable boundaries for SEC/EDGAR ingestion, parsing, and dashboard workflows.

## Referenced Projects

| Project | URL | What We Use From It | License / Reuse Note |
| --- | --- | --- | --- |
| dgunning/edgartools | https://github.com/dgunning/edgartools | Reference for structured SEC filing and XBRL parsing. Candidate optional backend. | Project documentation describes it as MIT licensed. Verify upstream license before direct dependency or vendoring. |
| jadchaar/sec-edgar-api | https://github.com/jadchaar/sec-edgar-api | Reference for SEC REST endpoint boundaries, pagination, and fair-access rate-limit posture. | Verify upstream license before copying code. |
| sec-edgar/sec-edgar | https://github.com/sec-edgar/sec-edgar | Reference for bulk SEC filing download workflows. | GitHub search metadata shows Apache-2.0; verify upstream before reuse. |
| bellingcat/EDGAR | https://github.com/bellingcat/EDGAR | Reference for investigation-oriented SEC CLI ergonomics and broad form coverage. | Verify upstream license before copying code. |
| stefanoamorelli/sec-edgar-toolkit | https://github.com/stefanoamorelli/sec-edgar-toolkit | Reference for full-stack SEC toolkit design and Python/TypeScript SDK direction. | Project README indicates AGPL-3.0. Avoid source reuse unless CapTable Lens is distributed compatibly. |

## SEC Data

The default provider uses public SEC EDGAR endpoints directly:

- Company ticker mapping: `https://www.sec.gov/files/company_tickers_exchange.json`
- Company submissions: `https://data.sec.gov/submissions/CIK##########.json`
- XBRL company facts: `https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json`
- Filing archive documents under `https://www.sec.gov/Archives/edgar/data/`

Automated access should use a clear User-Agent with contact information and respect SEC fair-access guidance.

