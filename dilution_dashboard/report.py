from __future__ import annotations

import csv
import html
from pathlib import Path

from .storage import load_scores


def write_daily_report(db_path: str | Path, html_out: str | Path, csv_out: str | Path | None = None) -> None:
    rows = load_scores(db_path)
    html_path = Path(html_out)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(render_report(rows), encoding="utf-8")
    if csv_out:
        write_csv(rows, csv_out)


def write_csv(rows: list[dict], csv_out: str | Path) -> None:
    path = Path(csv_out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "ticker",
                "company_name",
                "verdict",
                "risk_score",
                "predatory_score",
                "accretive_score",
                "overhang_score",
                "offering_to_market_cap",
                "share_growth",
                "revenue_growth",
                "top_reasons",
            ],
        )
        writer.writeheader()
        for row in rows:
            metrics = row.get("metrics", {})
            writer.writerow(
                {
                    "ticker": row["ticker"],
                    "company_name": row["company_name"],
                    "verdict": zh_verdict(row["verdict"]),
                    "risk_score": row["risk_score"],
                    "predatory_score": row["predatory_score"],
                    "accretive_score": row["accretive_score"],
                    "overhang_score": row["overhang_score"],
                    "offering_to_market_cap": pct(metrics.get("offering_to_market_cap")),
                    "share_growth": pct(metrics.get("share_growth")),
                    "revenue_growth": pct(metrics.get("revenue_growth")),
                    "top_reasons": "；".join(zh_reason(reason) for reason in row.get("reasons", [])[:4]),
                }
            )


def render_report(rows: list[dict]) -> str:
    high = [row for row in rows if row["risk_score"] >= 70]
    review = [row for row in rows if 45 <= row["risk_score"] < 70]
    accretive = [row for row in rows if row["accretive_score"] > row["predatory_score"]]
    top_overhang = sorted(rows, key=lambda row: row["overhang_score"], reverse=True)[:20]
    top_risk = sorted(rows, key=lambda row: row["risk_score"], reverse=True)[:30]

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CapTable Lens 每日融资稀释报告</title>
  <style>
    :root {{
      --bg: #f6f7f9;
      --panel: #fff;
      --ink: #171a1f;
      --muted: #667085;
      --line: #d9dee7;
      --red: #b42318;
      --amber: #b54708;
      --green: #027a48;
      --blue: #175cd3;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    header {{
      padding: 24px 28px 18px;
      background: var(--panel);
      border-bottom: 1px solid var(--line);
    }}
    h1 {{ margin: 0 0 8px; font-size: 26px; letter-spacing: 0; }}
    h2 {{ margin: 24px 0 10px; font-size: 18px; }}
    main {{ padding: 22px 28px 42px; }}
    .sub {{ color: var(--muted); max-width: 980px; }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(4, minmax(150px, 1fr));
      gap: 12px;
      margin: 18px 0;
    }}
    .card, section {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
    }}
    .label {{ color: var(--muted); font-size: 12px; }}
    .value {{ font-size: 26px; font-weight: 760; margin-top: 4px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 9px 8px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
    th {{ color: var(--muted); font-size: 12px; }}
    .risk-high {{ color: var(--red); font-weight: 700; }}
    .risk-mid {{ color: var(--amber); font-weight: 700; }}
    .risk-low {{ color: var(--green); font-weight: 700; }}
    .pill {{
      display: inline-flex;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 2px 8px;
      font-size: 12px;
      background: #fff;
    }}
    a {{ color: var(--blue); text-decoration: none; }}
    @media (max-width: 900px) {{
      header, main {{ padding-left: 16px; padding-right: 16px; }}
      .cards {{ grid-template-columns: 1fr 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>CapTable Lens 每日融资稀释报告</h1>
    <div class="sub">面向 1000 家公司批量扫描：优先暴露 ATM/Shelf/私募/可转债/资金用途不清晰/股本增长过快等需要人工复核的融资事件。</div>
  </header>
  <main>
    <div class="cards">
      {card("扫描公司", len(rows))}
      {card("高风险", len(high), "risk-high")}
      {card("需复核", len(review), "risk-mid")}
      {card("偏增值型", len(accretive), "risk-low")}
    </div>

    <section>
      <h2>优先复核 Top 30</h2>
      {table(top_risk)}
    </section>

    <section>
      <h2>潜在抛压 Top 20</h2>
      {table(top_overhang)}
    </section>

    <section>
      <h2>可能是增值型融资</h2>
      {table(accretive[:20])}
    </section>
  </main>
</body>
</html>
"""


def card(label: str, value: int, cls: str = "") -> str:
    return f'<div class="card"><div class="label">{html.escape(label)}</div><div class="value {cls}">{value}</div></div>'


def table(rows: list[dict]) -> str:
    if not rows:
        return '<p class="sub">暂无数据。</p>'
    body = []
    for row in rows:
        metrics = row.get("metrics", {})
        reasons = "；".join(zh_reason(reason) for reason in row.get("reasons", [])[:3])
        body.append(
            "<tr>"
            f"<td><strong>{html.escape(row['ticker'])}</strong><br><span class='sub'>{html.escape(row['company_name'])}</span></td>"
            f"<td class='{risk_class(row['risk_score'])}'>{row['risk_score']}</td>"
            f"<td><span class='pill'>{html.escape(zh_verdict(row['verdict']))}</span></td>"
            f"<td>{pct(metrics.get('offering_to_market_cap'))}</td>"
            f"<td>{pct(metrics.get('share_growth'))}</td>"
            f"<td>{pct(metrics.get('revenue_growth'))}</td>"
            f"<td>{html.escape(reasons or '暂无主要自动理由')}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr>"
        "<th>公司</th><th>风险分</th><th>结论</th><th>发行/市值</th><th>股本增长</th><th>营收增长</th><th>主要理由</th>"
        "</tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table>"
    )


def pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def risk_class(score: int) -> str:
    if score >= 70:
        return "risk-high"
    if score >= 45:
        return "risk-mid"
    return "risk-low"


def zh_verdict(value: str) -> str:
    return {
        "High predatory dilution risk": "高掠夺性稀释风险",
        "Needs manual review": "需要人工复核",
        "Potentially accretive": "可能是增值型融资",
        "Low/medium dilution signal": "低/中等稀释信号",
    }.get(value, value)


def zh_reason(value: str) -> str:
    return {
        "registered/offering amount is above 30% of market cap": "注册/发行金额超过当前市值 30%",
        "registered/offering amount is above 15% of market cap": "注册/发行金额超过当前市值 15%",
        "diluted share count rose more than 20% versus prior baseline": "稀释后股本较基准增长超过 20%",
        "diluted share count rose more than 10% versus prior baseline": "稀释后股本较基准增长超过 10%",
        "share count growth is outpacing revenue growth": "股本增长速度快于营收增长",
        "revenue growth is outpacing share count growth": "营收增长速度快于股本增长",
        "latest free cash flow estimate is negative": "最新自由现金流估算为负",
        "latest debt exceeds latest cash balance": "最新债务高于现金余额",
    }.get(value, value)

