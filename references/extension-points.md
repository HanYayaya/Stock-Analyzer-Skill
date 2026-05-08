# 二次开发扩展点

本文件用于指导后续对 `Stock Analyzer` 的扩展，重点说明应该优先改哪一层，而不是直接在 `SKILL.md` 里堆实现细节。

## 1. 触发与流程

- 修改 `SKILL.md` 的 frontmatter：
  - `name` 决定 skill 标识
  - `description` 决定触发条件和使用场景
- 修改 `SKILL.md` 正文：
  - 只保留总流程、约束、资源导航
  - 详细规则尽量下沉到 `references/`

## 2. 取数与结构化输出

- 修改 `scripts/fetch_stock_data.py`
- 推荐优先扩展以下能力：
  - 新市场支持：如 ETF、指数、基金、可转债
  - 新数据源支持：如 Tushare、Alpha Vantage、Finnhub、交易所接口
  - 字段标准化：保持 `price`、`valuation`、`profitability`、`financials` 等顶层结构稳定
  - 错误分层：区分接口失败、字段缺失、格式异常、回退成功

## 3. 评分与分析规则

- 优先在 `references/` 新增或拆分规则文件，而不是继续加长 `SKILL.md`
- 推荐拆分方向：
  - `references/scoring-model.md`
  - `references/a-share-market-rules.md`
  - `references/hk-market-rules.md`
  - `references/us-market-rules.md`
  - `references/cyclical-industry-rules.md`
  - `references/non-cyclical-industry-rules.md`
  - `references/report-output-standard.md`
  - `references/data-verification-protocol.md`

## 4. 报告模板

- 修改 `templates/analysis-report.md`
- 适合在这里扩展：
  - 新评分卡
  - 多标的对比表
  - 数据来源索引
  - 自检结论区

## 5. 开发约束

- 尽量保持 JSON 输出 schema 向后兼容
- 把新增能力做成“新增字段”而不是频繁改字段名
- 如果某市场无法保证 API 质量，明确记录回退策略和置信度降级规则
