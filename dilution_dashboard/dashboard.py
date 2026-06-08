from __future__ import annotations

import json
from pathlib import Path

from .storage import load_scores


def render_dashboard(db_path: str | Path, output_path: str | Path) -> None:
    scores = load_scores(db_path)
    payload = json.dumps(scores, ensure_ascii=False)
    html = HTML_TEMPLATE.replace("__DATA__", payload)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")


HTML_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CapTable Lens</title>
  <style>
    :root {
      --bg: #f6f7f9;
      --panel: #ffffff;
      --ink: #171a1f;
      --muted: #667085;
      --line: #d9dee7;
      --red: #b42318;
      --amber: #b54708;
      --green: #027a48;
      --blue: #175cd3;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    header {
      padding: 22px 28px 14px;
      background: var(--panel);
      border-bottom: 1px solid var(--line);
      position: sticky;
      top: 0;
      z-index: 2;
    }
    h1 {
      margin: 0 0 8px;
      font-size: 24px;
      letter-spacing: 0;
    }
    .sub { color: var(--muted); max-width: 980px; }
    .controls {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-top: 16px;
    }
    input, select {
      height: 36px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 0 10px;
      background: #fff;
      min-width: 190px;
    }
    main { padding: 22px 28px 40px; }
    .summary {
      display: grid;
      grid-template-columns: repeat(4, minmax(150px, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }
    .metric {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
    }
    .metric .label { color: var(--muted); font-size: 12px; }
    .metric .value { font-size: 24px; font-weight: 700; margin-top: 4px; }
    .grid {
      display: grid;
      grid-template-columns: 340px 1fr;
      gap: 16px;
      align-items: start;
    }
    .list {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }
    .row {
      width: 100%;
      border: 0;
      border-bottom: 1px solid var(--line);
      background: #fff;
      text-align: left;
      padding: 12px 14px;
      cursor: pointer;
    }
    .row:hover, .row.active { background: #eef4ff; }
    .ticker-line { display: flex; justify-content: space-between; gap: 10px; align-items: center; }
    .ticker { font-weight: 750; font-size: 16px; }
    .company { color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .score { font-weight: 800; }
    .pill {
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 12px;
      border: 1px solid var(--line);
      background: #fff;
    }
    .risk-high { color: var(--red); }
    .risk-mid { color: var(--amber); }
    .risk-low { color: var(--green); }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }
    .detail-head {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      border-bottom: 1px solid var(--line);
      padding-bottom: 14px;
      margin-bottom: 16px;
    }
    .bars {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      margin-bottom: 18px;
    }
    .bar-card {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
    }
    .bar-label { color: var(--muted); font-size: 12px; margin-bottom: 8px; }
    .bar-bg { height: 10px; background: #edf0f5; border-radius: 99px; overflow: hidden; }
    .bar-fill { height: 100%; background: var(--blue); }
    .bar-fill.red { background: var(--red); }
    .bar-fill.amber { background: var(--amber); }
    .bar-fill.green { background: var(--green); }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
    }
    th, td {
      padding: 10px 8px;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
      text-align: left;
    }
    th { color: var(--muted); font-size: 12px; font-weight: 650; }
    a { color: var(--blue); text-decoration: none; }
    ul { margin: 8px 0 0 18px; padding: 0; }
    .empty { color: var(--muted); padding: 40px; text-align: center; }
    footer {
      margin-top: 22px;
      color: var(--muted);
      font-size: 12px;
    }
    @media (max-width: 900px) {
      main, header { padding-left: 16px; padding-right: 16px; }
      .summary, .grid, .bars { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <h1>CapTable Lens</h1>
    <div class="sub">自动筛查 SEC 文件里的 ATM、市价发行、Shelf 注册、私募、可转债、资金用途、潜在抛压，以及增值型/掠夺性融资信号。</div>
    <div class="controls">
      <input id="search" placeholder="搜索代码或公司">
      <select id="verdict">
        <option value="">全部结论</option>
        <option value="High predatory dilution risk">高掠夺性稀释风险</option>
        <option value="Needs manual review">需要人工复核</option>
        <option value="Potentially accretive">可能是增值型融资</option>
        <option value="Low/medium dilution signal">低/中等稀释信号</option>
      </select>
    </div>
  </header>
  <main>
    <section class="summary" id="summary"></section>
    <section class="grid">
      <div class="list" id="list"></div>
      <div class="panel" id="detail"></div>
    </section>
    <footer>开源参考来源和许可证说明见 ATTRIBUTION.md。本版本没有内置或复制第三方项目源码。</footer>
  </main>
  <script>
    const data = __DATA__;
    let selectedTicker = data[0]?.ticker || null;

    const verdictText = {
      "High predatory dilution risk": "高掠夺性稀释风险",
      "Needs manual review": "需要人工复核",
      "Potentially accretive": "可能是增值型融资",
      "Low/medium dilution signal": "低/中等稀释信号"
    };
    const typeText = {
      "ATM": "ATM 市价发行",
      "Shelf Registration": "Shelf 注册",
      "Private Placement": "私募/定向发行",
      "Convertible Debt": "可转债",
      "Warrants": "认股权证",
      "Debt Financing": "债务融资",
      "Unclassified": "未分类"
    };
    const useText = {
      "growth capex": "增长型资本开支",
      "M&A": "并购",
      "debt repayment": "偿还债务",
      "working capital": "营运资金",
      "general corporate purposes": "一般公司用途",
      "unclear": "不明确"
    };
    const reasonText = {
      "registered/offering amount is above 30% of market cap": "注册/发行金额超过当前市值 30%",
      "registered/offering amount is above 15% of market cap": "注册/发行金额超过当前市值 15%",
      "diluted share count rose more than 20% versus prior baseline": "稀释后股本较基准增长超过 20%",
      "diluted share count rose more than 10% versus prior baseline": "稀释后股本较基准增长超过 10%",
      "share count growth is outpacing revenue growth": "股本增长速度快于营收增长",
      "revenue growth is outpacing share count growth": "营收增长速度快于股本增长",
      "latest free cash flow estimate is negative": "最新自由现金流估算为负",
      "latest debt exceeds latest cash balance": "最新债务高于现金余额"
    };
    const signalText = {
      "ATM program can create ongoing supply overhang": "ATM 项目可能形成持续卖股抛压",
      "convertible debt can add contingent dilution": "可转债可能带来或有稀释",
      "use of proceeds is broad or unclear": "资金用途宽泛或不明确",
      "proceeds are going to debt repayment instead of direct growth": "资金用于还债，而不是直接增长项目",
      "proceeds appear tied to growth capex": "资金看起来用于增长型资本开支",
      "proceeds appear tied to M&A": "资金看起来用于并购",
      "private placement can be constructive if investor quality and terms are strong": "若投资人质量和条款较好，私募可能是建设性融资"
    };

    const fmtMoney = value => {
      if (value === null || value === undefined) return "n/a";
      const abs = Math.abs(value);
      if (abs >= 1e9) return "$" + (value / 1e9).toFixed(2) + "B";
      if (abs >= 1e6) return "$" + (value / 1e6).toFixed(1) + "M";
      return "$" + Math.round(value).toLocaleString();
    };
    const fmtPct = value => value === null || value === undefined ? "n/a" : (value * 100).toFixed(1) + "%";
    const riskClass = score => score >= 70 ? "risk-high" : score >= 45 ? "risk-mid" : "risk-low";
    const tVerdict = value => verdictText[value] || value;
    const tType = value => typeText[value] || value;
    const tUse = value => useText[value] || value;
    const tReason = value => reasonText[value] || value;
    const tSignal = value => signalText[value] || value;

    function filtered() {
      const q = document.querySelector("#search").value.trim().toUpperCase();
      const v = document.querySelector("#verdict").value;
      return data.filter(row => {
        const text = `${row.ticker} ${row.company_name}`.toUpperCase();
        return (!q || text.includes(q)) && (!v || row.verdict === v);
      });
    }

    function renderSummary(rows) {
      const high = rows.filter(r => r.risk_score >= 70).length;
      const review = rows.filter(r => r.risk_score >= 45 && r.risk_score < 70).length;
      const avg = rows.length ? Math.round(rows.reduce((s, r) => s + r.risk_score, 0) / rows.length) : 0;
      document.querySelector("#summary").innerHTML = [
        metric("公司数量", rows.length),
        metric("高风险", high),
        metric("需复核", review),
        metric("平均风险", avg),
      ].join("");
    }

    function metric(label, value) {
      return `<div class="metric"><div class="label">${label}</div><div class="value">${value}</div></div>`;
    }

    function renderList(rows) {
      const list = document.querySelector("#list");
      if (!rows.length) {
        list.innerHTML = `<div class="empty">没有符合当前筛选条件的公司。</div>`;
        document.querySelector("#detail").innerHTML = "";
        return;
      }
      if (!rows.some(r => r.ticker === selectedTicker)) selectedTicker = rows[0].ticker;
      list.innerHTML = rows.map(row => `
        <button class="row ${row.ticker === selectedTicker ? "active" : ""}" onclick="selectTicker('${row.ticker}')">
          <div class="ticker-line"><span class="ticker">${row.ticker}</span><span class="score ${riskClass(row.risk_score)}">${row.risk_score}</span></div>
          <div class="company">${row.company_name}</div>
          <div class="pill">${tVerdict(row.verdict)}</div>
        </button>
      `).join("");
      renderDetail(rows.find(r => r.ticker === selectedTicker));
    }

    function bar(label, value, cls) {
      const width = Math.max(0, Math.min(100, Number(value) || 0));
      return `<div class="bar-card"><div class="bar-label">${label}: ${width}</div><div class="bar-bg"><div class="bar-fill ${cls}" style="width:${width}%"></div></div></div>`;
    }

    function renderDetail(row) {
      const filings = row.filings || [];
      document.querySelector("#detail").innerHTML = `
        <div class="detail-head">
          <div>
            <h2 style="margin:0 0 4px">${row.ticker} · ${row.company_name}</h2>
            <div class="pill">${tVerdict(row.verdict)}</div>
          </div>
          <div class="score ${riskClass(row.risk_score)}" style="font-size:36px">${row.risk_score}</div>
        </div>
        <div class="bars">
          ${bar("综合风险", row.risk_score, row.risk_score >= 70 ? "red" : row.risk_score >= 45 ? "amber" : "green")}
          ${bar("掠夺性信号", row.predatory_score, "red")}
          ${bar("增值型信号", row.accretive_score, "green")}
          ${bar("潜在抛压", row.overhang_score, "amber")}
        </div>
        <h3>关键指标</h3>
        <table>
          <tr><th>发行金额 / 市值</th><td>${fmtPct(row.metrics.offering_to_market_cap)}</td></tr>
          <tr><th>股本增长</th><td>${fmtPct(row.metrics.share_growth)}</td></tr>
          <tr><th>营收增长</th><td>${fmtPct(row.metrics.revenue_growth)}</td></tr>
          <tr><th>市值</th><td>${fmtMoney(row.metrics.market_cap_usd)}</td></tr>
          <tr><th>自由现金流</th><td>${fmtMoney(row.metrics.free_cash_flow_latest)}</td></tr>
          <tr><th>现金 / 债务</th><td>${fmtMoney(row.metrics.cash_latest)} / ${fmtMoney(row.metrics.debt_latest)}</td></tr>
        </table>
        <h3>自动判断理由</h3>
        ${row.reasons.length ? `<ul>${row.reasons.map(r => `<li>${tReason(r)}</li>`).join("")}</ul>` : `<p class="sub">暂未记录主要自动理由。若融资规模较大，仍建议人工复核。</p>`}
        <h3>融资相关文件</h3>
        <table>
          <thead><tr><th>日期</th><th>表格</th><th>类型</th><th>金额</th><th>资金用途</th><th>信号</th><th>链接</th></tr></thead>
          <tbody>${filings.map(f => `
            <tr>
              <td>${f.filing_date}</td>
              <td>${f.form}</td>
              <td>${tType(f.financing_type)}</td>
              <td>${fmtMoney(f.offering_amount_usd)}</td>
              <td>${tUse(f.use_of_proceeds)}</td>
              <td>
                ${(f.red_flags || []).map(x => `<div class="risk-high">${tSignal(x)}</div>`).join("")}
                ${(f.green_flags || []).map(x => `<div class="risk-low">${tSignal(x)}</div>`).join("")}
              </td>
              <td><a href="${f.filing_url}" target="_blank">SEC</a></td>
            </tr>
          `).join("")}</tbody>
        </table>
      `;
    }

    function selectTicker(ticker) {
      selectedTicker = ticker;
      render();
    }

    function render() {
      const rows = filtered();
      renderSummary(rows);
      renderList(rows);
    }

    document.querySelector("#search").addEventListener("input", render);
    document.querySelector("#verdict").addEventListener("change", render);
    render();
  </script>
</body>
</html>
"""
