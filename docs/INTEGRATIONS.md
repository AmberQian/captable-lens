# Integrations Roadmap

CapTable Lens separates the project into four layers:

1. EDGAR provider
2. Filing parser
3. Dilution scoring engine
4. Dashboard/output

The current provider is `DirectSecProvider`, which calls SEC public endpoints directly through the standard library. That keeps the MVP dependency-free. The provider boundary in `dilution_dashboard/providers.py` makes it straightforward to add optional backends later.

## Candidate Backends

### edgartools

Best candidate for richer filing and XBRL parsing. It can likely replace parts of `sec_client.py`, `parser.py`, and `facts.py` once we are ready to add third-party dependencies.

Suggested future command:

```bash
python3 -m dilution_dashboard fetch --provider edgartools --watchlist examples/watchlist.txt
```

### sec-edgar-api

Useful if we want a thin, maintained wrapper around SEC REST APIs while keeping our own parsing and scoring logic.

### sec-edgar

Useful for large historical backfills where the project needs to download many filings for many tickers.

### bellingcat/EDGAR

Useful as a design reference if CapTable Lens grows investigation-style commands such as:

```bash
python3 -m dilution_dashboard search-filings --form 424B5 --query "at-the-market"
```

### sec-edgar-toolkit

Useful as a full-stack design reference, but its AGPL-3.0 licensing means we should treat it as reference-only unless we deliberately choose compatible distribution terms.

## Do Not Vendor By Default

For now, do not copy upstream code into this repository. Prefer optional dependencies, adapters, and explicit attribution. This keeps the project clean for future GitHub publication.

