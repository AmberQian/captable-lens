# 每日 1000 公司扫描工作台

CapTable Lens 可以扩展成每日自动扫描 1000 家公司的融资稀释工作台。推荐输出三类结果：

1. `dist/index.html`：可交互中文看板
2. `dist/report.html`：每日中文报告
3. `dist/report.csv`：可导入 Excel/Sheets 的结构化结果

## 推荐流程

```bash
python3 -m dilution_dashboard scan --watchlist examples/watchlist.test.txt \
  --user-agent "your-name your-email@example.com" \
  --limit 25
```

`--limit 25` 表示每家公司最多检查最近 25 个相关表格。对 1000 家公司，第一版不建议直接拉最近 80 个文件全文，会慢，也没必要。

## 为什么不能“暴力全文扫”

1000 家公司如果每家下载 80 个 filing 正文，就是 80,000 个文档请求。实际每日监控不需要这样做：

- 每天先拉 submissions 索引
- 只找最近的新 filing
- 只下载融资相关表格正文
- 对已下载文件走本地缓存
- 输出高风险 Top N 给人工复核

## Watchlist

真实 1000 公司 watchlist 建议单独维护，例如：

```text
examples/watchlist.test.txt
examples/watchlist.ai-infra.txt
examples/watchlist.semiconductors-optical.txt
examples/watchlist.crypto-miners.txt
examples/watchlist.smallcap-dilution-risk.txt
```

每行一个 ticker。

## 市值数据

当前版本默认用 Yahoo Finance quote endpoint 批量抓取 `marketCap`，并缓存 12 小时：

```bash
--market-provider yahoo
```

如果你有更可信的市值文件，可以用 JSON 覆盖：

```bash
--market-caps examples/market_caps.example.json
```

后续更稳定的数据源推荐优先级：

1. Polygon / Tiingo / IEX / FMP 这类 API
2. yfinance 作为个人研究 fallback
3. Bloomberg / FactSet 作为机构数据源

## 每日报告阅读方式

报告优先看：

- 高风险 Top 30
- 潜在抛压 Top 20
- 可能是增值型融资 Top 20

工作台优先看：

- `发行金额 / 市值`
- `股本增长`
- `营收增长`
- `资金用途`
- SEC 原文链接

## 定时化

本地可用 cron。GitHub 上可用 GitHub Actions schedule，但如果 watchlist 很大，要注意：

- SEC fair access
- API key secret 管理
- Actions 运行时间限制
- 生成结果是否 commit 回仓库或发布到 Pages
