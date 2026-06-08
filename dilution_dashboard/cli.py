from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .dashboard import render_dashboard
from .facts import snapshot_metrics
from .integrations import INTEGRATION_SOURCES
from .market_data import MarketDataError, resolve_market_caps
from .models import CompanySnapshot, FilingSignal
from .parser import parse_filing
from .providers import DirectSecProvider, EdgarProvider
from .report import write_daily_report
from .scoring import score_company
from .sec_client import SecClientError
from .storage import save_scores


FINANCING_FORMS = {"S-3", "S-3ASR", "S-1", "424B5", "424B3", "8-K", "10-Q", "10-K"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="captable-lens")
    sub = parser.add_subparsers(dest="cmd", required=True)

    fetch = sub.add_parser("fetch", help="Fetch SEC filings and score a ticker watchlist")
    fetch.add_argument("tickers", nargs="*", help="Ticker symbols")
    fetch.add_argument("--watchlist", help="File containing one ticker per line")
    fetch.add_argument("--user-agent", required=True, help="SEC User-Agent, include contact email")
    fetch.add_argument("--db", default="data/dilution.sqlite")
    fetch.add_argument("--cache-dir", default=".cache/sec")
    fetch.add_argument("--limit", type=int, default=80)
    fetch.add_argument("--market-caps", help="Optional JSON map that overrides fetched market caps")
    fetch.add_argument("--market-provider", choices=["yahoo", "none"], default="yahoo")
    fetch.add_argument("--market-cache-dir", default=".cache/market")
    fetch.add_argument("--market-cache-hours", type=float, default=12)

    dash = sub.add_parser("dashboard", help="Render static HTML dashboard from the SQLite database")
    dash.add_argument("--db", default="data/dilution.sqlite")
    dash.add_argument("--out", default="dist/index.html")

    demo = sub.add_parser("demo", help="Create demo scores and render the dashboard without network access")
    demo.add_argument("--db", default="data/dilution.sqlite")
    demo.add_argument("--out", default="dist/index.html")

    report = sub.add_parser("report", help="Render a Chinese daily dilution report from the SQLite database")
    report.add_argument("--db", default="data/dilution.sqlite")
    report.add_argument("--html-out", default="dist/report.html")
    report.add_argument("--csv-out", default="dist/report.csv")

    workbench = sub.add_parser("workbench", help="Render both the interactive dashboard and daily report")
    workbench.add_argument("--db", default="data/dilution.sqlite")
    workbench.add_argument("--dashboard-out", default="dist/index.html")
    workbench.add_argument("--report-out", default="dist/report.html")
    workbench.add_argument("--csv-out", default="dist/report.csv")

    sub.add_parser("sources", help="List referenced open-source projects and integration status")

    args = parser.parse_args(argv)
    if args.cmd == "fetch":
        return run_fetch(args)
    if args.cmd == "dashboard":
        render_dashboard(args.db, args.out)
        print(f"Dashboard written to {Path(args.out).resolve()}")
        return 0
    if args.cmd == "demo":
        save_scores(args.db, demo_scores())
        render_dashboard(args.db, args.out)
        print(f"Demo dashboard written to {Path(args.out).resolve()}")
        return 0
    if args.cmd == "report":
        write_daily_report(args.db, args.html_out, args.csv_out)
        print(f"Daily report written to {Path(args.html_out).resolve()}")
        print(f"CSV report written to {Path(args.csv_out).resolve()}")
        return 0
    if args.cmd == "workbench":
        render_dashboard(args.db, args.dashboard_out)
        write_daily_report(args.db, args.report_out, args.csv_out)
        print(f"Workbench dashboard written to {Path(args.dashboard_out).resolve()}")
        print(f"Daily report written to {Path(args.report_out).resolve()}")
        print(f"CSV report written to {Path(args.csv_out).resolve()}")
        return 0
    if args.cmd == "sources":
        print_sources()
        return 0
    return 1


def run_fetch(args: argparse.Namespace) -> int:
    tickers = collect_tickers(args.tickers, args.watchlist)
    if not tickers:
        print("No tickers supplied.", file=sys.stderr)
        return 2

    try:
        market_caps = resolve_market_caps(
            tickers,
            manual_path=args.market_caps,
            provider=args.market_provider,
            cache_dir=args.market_cache_dir,
            max_age_seconds=int(args.market_cache_hours * 60 * 60),
        )
        print(f"[market] resolved market caps for {len(market_caps)}/{len(tickers)} tickers")
    except MarketDataError as exc:
        print(f"[market warning] {exc}", file=sys.stderr)
        print("[market warning] continuing without fetched market caps; use --market-caps JSON or retry later", file=sys.stderr)
        market_caps = resolve_market_caps(tickers, manual_path=args.market_caps, provider="none")
    provider = DirectSecProvider(args.user_agent, args.cache_dir)
    ticker_map = provider.ticker_map()
    scores = []

    for ticker in tickers:
        meta = ticker_map.get(ticker.upper())
        if not meta:
            print(f"[skip] {ticker}: ticker not found in SEC ticker map", file=sys.stderr)
            continue
        print(f"[fetch] {ticker.upper()} {meta['name']}")
        try:
            filings = build_filing_signals(provider, meta, args.limit)
            facts = provider.companyfacts(meta["cik"])
        except SecClientError as exc:
            print(f"[error] {ticker}: {exc}", file=sys.stderr)
            continue

        metrics = snapshot_metrics(facts)
        snapshot = CompanySnapshot(
            ticker=meta["ticker"],
            cik=meta["cik"],
            company_name=meta["name"],
            exchange=meta["exchange"],
            market_cap_usd=market_caps.get(meta["ticker"]),
            diluted_shares_latest=metrics["diluted_shares_latest"],
            diluted_shares_prior=metrics["diluted_shares_prior"],
            revenue_latest=metrics["revenue_latest"],
            revenue_prior=metrics["revenue_prior"],
            free_cash_flow_latest=metrics["free_cash_flow_latest"],
            debt_latest=metrics["debt_latest"],
            cash_latest=metrics["cash_latest"],
            filings=filings,
        )
        scores.append(score_company(snapshot))

    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    save_scores(args.db, scores)
    print(f"Saved {len(scores)} scored companies to {Path(args.db).resolve()}")
    return 0


def build_filing_signals(provider: EdgarProvider, meta: dict, limit: int) -> list[FilingSignal]:
    signals = []
    for filing in provider.recent_filings(meta["cik"], FINANCING_FORMS, limit):
        raw = provider.filing_text(filing)
        parsed = parse_filing(raw)
        if parsed.financing_type == "Unclassified" and parsed.use_of_proceeds == "unclear":
            continue
        signals.append(
            FilingSignal(
                ticker=meta["ticker"],
                cik=meta["cik"],
                company_name=meta["name"],
                form=filing.form,
                filing_date=filing.filing_date,
                accession_number=filing.accession_number,
                filing_url=filing.archive_url,
                financing_type=parsed.financing_type,
                offering_amount_usd=parsed.offering_amount_usd,
                use_of_proceeds=parsed.use_of_proceeds,
                evidence=parsed.evidence,
            )
        )
    return signals


def collect_tickers(args_tickers: list[str], watchlist: str | None) -> list[str]:
    tickers = [t.strip().upper() for t in args_tickers if t.strip()]
    if watchlist:
        for line in Path(watchlist).read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                tickers.append(line.upper())
    return sorted(set(tickers))


def print_sources() -> None:
    print("CapTable Lens referenced open-source projects:")
    for source in INTEGRATION_SOURCES:
        print(f"\n- {source.name}")
        print(f"  URL: {source.url}")
        print(f"  Useful for: {source.useful_for}")
        print(f"  Status: {source.status}")
        print(f"  License note: {source.license_note}")


def demo_scores():
    snapshots = [
        CompanySnapshot(
            ticker="IREN",
            cik="0000000000",
            company_name="IREN Demo Case",
            exchange="Nasdaq",
            market_cap_usd=2_500_000_000,
            diluted_shares_latest=180_000_000,
            diluted_shares_prior=120_000_000,
            revenue_latest=320_000_000,
            revenue_prior=220_000_000,
            free_cash_flow_latest=-120_000_000,
            debt_latest=500_000_000,
            cash_latest=300_000_000,
            filings=[
                FilingSignal(
                    ticker="IREN",
                    cik="0000000000",
                    company_name="IREN Demo Case",
                    form="S-3",
                    filing_date="2026-01-15",
                    accession_number="demo",
                    filing_url="https://www.sec.gov/",
                    financing_type="ATM",
                    offering_amount_usd=6_000_000_000,
                    use_of_proceeds="general corporate purposes",
                )
            ],
        ),
        CompanySnapshot(
            ticker="AAOI",
            cik="0000000000",
            company_name="AAOI Demo Case",
            exchange="Nasdaq",
            market_cap_usd=1_000_000_000,
            diluted_shares_latest=48_000_000,
            diluted_shares_prior=43_000_000,
            revenue_latest=360_000_000,
            revenue_prior=250_000_000,
            free_cash_flow_latest=-15_000_000,
            debt_latest=90_000_000,
            cash_latest=120_000_000,
            filings=[
                FilingSignal(
                    ticker="AAOI",
                    cik="0000000000",
                    company_name="AAOI Demo Case",
                    form="8-K",
                    filing_date="2026-02-01",
                    accession_number="demo",
                    filing_url="https://www.sec.gov/",
                    financing_type="Private Placement",
                    offering_amount_usd=120_000_000,
                    use_of_proceeds="growth capex",
                )
            ],
        ),
        CompanySnapshot(
            ticker="BKKT",
            cik="0000000000",
            company_name="BKKT Demo Case",
            exchange="NYSE",
            market_cap_usd=200_000_000,
            diluted_shares_latest=95_000_000,
            diluted_shares_prior=40_000_000,
            revenue_latest=70_000_000,
            revenue_prior=65_000_000,
            free_cash_flow_latest=-80_000_000,
            debt_latest=60_000_000,
            cash_latest=25_000_000,
            filings=[
                FilingSignal(
                    ticker="BKKT",
                    cik="0000000000",
                    company_name="BKKT Demo Case",
                    form="424B5",
                    filing_date="2026-03-10",
                    accession_number="demo",
                    filing_url="https://www.sec.gov/",
                    financing_type="Shelf Registration",
                    offering_amount_usd=150_000_000,
                    use_of_proceeds="working capital",
                )
            ],
        ),
    ]
    return [score_company(snapshot) for snapshot in snapshots]


if __name__ == "__main__":
    raise SystemExit(main())
