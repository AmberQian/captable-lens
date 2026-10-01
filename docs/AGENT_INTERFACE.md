# Offline Agent screening interface

Run `python -m dilution_dashboard.agent` and send one CompanySnapshot JSON object on stdin.
Output is a versioned JSON envelope containing `status`, `warnings`,
`requires_human_review`, and the existing ScoreResult as `result`.

All CompanySnapshot fields remain required, including nullable metric fields.
`filings` may be omitted (defaults to an empty array); supplied records must follow FilingSignal.
No network requests, model calls, database writes, trading, or publishing occur.
Invalid input returns JSON with status `invalid_input` and exit code 2.
Successful screening returns exit code 0. `screened` means inputs are populated,
not that the company is safe or the evidence independently verified.
Missing metrics or absent filings produce `needs_review`; every result requires human review.

## Financial period policy

Companyfacts metrics now use annual-duration observations (330–380 days) from
10-K/20-F/40-F and amendments. Quarter and YTD observations are excluded.
Periods are selected by period end; duplicate periods use the newest filing.
The growth baseline must end 330–400 days before the latest annual period.
Tag aliases are selected in priority order, not pooled or summed.
FCF requires identical OCF and capex start/end dates.
Debt requires both current and noncurrent components at the same date; mismatched
cash/debt dates suppress the debt value. Missing components return null, never zero.

## Remaining limits

This is an annual screening baseline, not a latest-quarter or TTM engine.
Cross-metric share/revenue period alignment and source provenance are still future work.
Issuer-specific XBRL extensions and standalone debt-total tags are unsupported.
Existing filing parser and risk thresholds are heuristic; filing event deduplication,
registration vs actual issuance, and financing lifecycle modeling remain to be built.
The JSON interface exposes the existing scoring logic; it is not a hosted MCP server.
