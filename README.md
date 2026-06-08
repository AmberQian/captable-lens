# CapTable Lens

CapTable Lens 用于自动化筛查一家公司的“增殖方式”：发行新股、ATM、S-3 shelf、PIPE、可转债、债务置换等融资，到底更像 accretive 还是 predatory。

第一版定位是半自动研究终端：

- 自动抓 SEC EDGAR filings
- 识别融资类型和 use of proceeds
- 计算稀释/抛压/增值信号
- 生成本地静态 HTML dashboard
- 保留人工复核入口
- 记录参考过的开源项目和许可证注意事项

## Quick Start

SEC 要求自动访问 EDGAR 时提供明确 User-Agent，并建议包含联系信息。

先看示例 dashboard：

```bash
python3 -m dilution_dashboard demo
```

打开：

```text
dist/index.html
```

抓真实 SEC 数据：

```bash
python3 -m dilution_dashboard scan --watchlist examples/watchlist.test.txt \
  --user-agent "your-name your-email@example.com"
```

然后在浏览器打开：

```text
dist/index.html
```

如果已安装为 package，也可以用 console script：

```bash
captable-lens demo
captable-lens sources
```

查看参考过的开源项目：

```bash
python3 -m dilution_dashboard sources
```

生成每日中文报告和 CSV：

```bash
python3 -m dilution_dashboard report
```

同时生成交互看板、日报和 CSV：

```bash
python3 -m dilution_dashboard workbench
```

## 输入

### Watchlist

`examples/watchlist.txt` 一行一个 ticker：

```text
AAOI
IREN
BKKT
```

已内置几组研究模板：

```text
examples/watchlist.test.txt
examples/watchlist.ai-infra.txt
examples/watchlist.semiconductors-optical.txt
examples/watchlist.crypto-miners.txt
examples/watchlist.smallcap-dilution-risk.txt
```

### Market Cap

SEC 本身不提供实时市值。CapTable Lens 默认用 Yahoo Finance quote endpoint 批量抓取 `marketCap`，并缓存 12 小时：

```bash
python3 -m dilution_dashboard fetch --watchlist examples/watchlist.txt \
  --user-agent "your-name your-email@example.com" \
  --market-provider yahoo
```

一键扫描并生成完整工作台：

```bash
python3 -m dilution_dashboard scan --watchlist examples/watchlist.ai-infra.txt \
  --user-agent "your-name your-email@example.com"
```

如果你不想自动抓市值，可以关闭：

```bash
python3 -m dilution_dashboard fetch --watchlist examples/watchlist.txt \
  --user-agent "your-name your-email@example.com" \
  --market-provider none
```

也可以用 JSON 手动覆盖，手动值优先级最高：

```json
{
  "AAOI": 1000000000,
  "IREN": 2500000000
}
```

```bash
python3 -m dilution_dashboard fetch --watchlist examples/watchlist.txt \
  --user-agent "your-name your-email@example.com" \
  --market-caps examples/market_caps.example.json
```

如果网络不可用或某些 ticker 没拿到市值，dashboard 仍会生成，但 `发行金额 / 市值` 和 overhang 判断会弱一些。后续可以接 Polygon、IEX、Tiingo、FMP、Bloomberg 或 FactSet 作为更稳定的数据源。

## 输出指标

- `Risk`: 综合风险
- `Predatory`: 掠夺性稀释信号
- `Accretive`: 增值型融资信号
- `Overhang`: ATM/shelf 未来抛压

自动红旗包括：

- ATM 或 shelf 金额超过市值 30%
- diluted shares 增长超过 20%
- 股本增长明显快于营收增长
- use of proceeds 是 `general corporate purposes`、`working capital` 或不清楚
- 负 FCF
- 债务大于现金
- convertible debt / warrants

自动绿旗包括：

- use of proceeds 指向 growth capex
- use of proceeds 指向 M&A
- private placement
- 营收增长快于股本增长

## 目录

```text
dilution_dashboard/
  providers.py     Pluggable EDGAR provider boundary
  integrations.py  Referenced OSS projects and integration status
  market_data.py   Market cap fetch/cache helpers
  sec_client.py    SEC EDGAR client with local cache
  parser.py        Filing text parser
  facts.py         XBRL companyfacts extraction
  scoring.py       Accretive/predatory scoring
  storage.py       SQLite persistence
  dashboard.py     Static HTML renderer
  cli.py           CLI entrypoint
docs/
  INTEGRATIONS.md  Integration roadmap
  DAILY_WORKBENCH.md  Daily 1000-company workflow
ATTRIBUTION.md     OSS attribution and license notes
```

## 开源项目整合

我没有直接复制第三方项目源码，而是把可复用的部分整合为 provider/adapters 路线，并注明出处：

- `dgunning/edgartools`: 后续最适合做可选 structured filing/XBRL parser backend
- `jadchaar/sec-edgar-api`: 参考 SEC REST API wrapper、pagination、fair-access rate limit 设计
- `sec-edgar/sec-edgar`: 参考大规模 filings bulk download
- `bellingcat/EDGAR`: 参考调查式 CLI 和广表格覆盖
- `stefanoamorelli/sec-edgar-toolkit`: 参考 Python/TypeScript full-stack toolkit；但 AGPL-3.0 需要谨慎

详情见 [ATTRIBUTION.md](ATTRIBUTION.md) 和 [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md)。

## 重要限制

这不是投资建议，也不是全自动交易信号。它只负责把“需要人工复核”的融资事件筛出来。

当前版本不能自动判断：

- 扩产项目是否真的有订单支撑
- 战略投资人是真协同还是财务投资
- 管理层真实动机
- 融资条款里的复杂反稀释机制

这些需要人工看公告原文、行业需求和管理层历史兑现能力。

## 下一步可扩展

- 接实时/历史 market cap API
- 增加 insider selling 数据
- 增加 short interest 和 volume overhang
- 用 LLM 对 use of proceeds 和 financing terms 做摘要
- 增加可选 `edgartools` provider
- 加行业模板，例如 AI infra、半导体、biotech、crypto miners
- GitHub Actions 每天跑 watchlist 并发布 dashboard
