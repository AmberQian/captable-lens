from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .models import ScoreResult


SCHEMA = """
create table if not exists scores (
    ticker text primary key,
    company_name text not null,
    risk_score integer not null,
    accretive_score integer not null,
    predatory_score integer not null,
    overhang_score integer not null,
    verdict text not null,
    reasons_json text not null,
    metrics_json text not null,
    filings_json text not null,
    updated_at text not null default current_timestamp
);
"""


def open_db(path: str | Path) -> sqlite3.Connection:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(SCHEMA)
    return conn


def save_scores(path: str | Path, scores: Iterable[ScoreResult]) -> None:
    conn = open_db(path)
    with conn:
        for score in scores:
            conn.execute(
                """
                insert into scores (
                    ticker, company_name, risk_score, accretive_score, predatory_score,
                    overhang_score, verdict, reasons_json, metrics_json, filings_json, updated_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, current_timestamp)
                on conflict(ticker) do update set
                    company_name=excluded.company_name,
                    risk_score=excluded.risk_score,
                    accretive_score=excluded.accretive_score,
                    predatory_score=excluded.predatory_score,
                    overhang_score=excluded.overhang_score,
                    verdict=excluded.verdict,
                    reasons_json=excluded.reasons_json,
                    metrics_json=excluded.metrics_json,
                    filings_json=excluded.filings_json,
                    updated_at=current_timestamp
                """,
                (
                    score.ticker,
                    score.company_name,
                    score.risk_score,
                    score.accretive_score,
                    score.predatory_score,
                    score.overhang_score,
                    score.verdict,
                    json.dumps(score.reasons),
                    json.dumps(score.metrics),
                    json.dumps([filing.__dict__ for filing in score.filings]),
                ),
            )
    conn.close()


def load_scores(path: str | Path) -> list[dict]:
    conn = open_db(path)
    rows = conn.execute(
        """
        select ticker, company_name, risk_score, accretive_score, predatory_score,
               overhang_score, verdict, reasons_json, metrics_json, filings_json, updated_at
        from scores
        order by risk_score desc, predatory_score desc, ticker asc
        """
    ).fetchall()
    conn.close()
    result = []
    for row in rows:
        result.append(
            {
                "ticker": row[0],
                "company_name": row[1],
                "risk_score": row[2],
                "accretive_score": row[3],
                "predatory_score": row[4],
                "overhang_score": row[5],
                "verdict": row[6],
                "reasons": json.loads(row[7]),
                "metrics": json.loads(row[8]),
                "filings": json.loads(row[9]),
                "updated_at": row[10],
            }
        )
    return result
