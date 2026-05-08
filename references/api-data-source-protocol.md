# API 优先取数协议

本文件定义 `Stock Analyzer` 的 API-first 数据获取机制，统一说明 `yfinance + AkShare` 的职责分工、调用顺序、降级策略和引用规范。

## 1. 核心原则

- 能用 API 就不用网页抓取
- 网页抓取只作补充、兜底或冲突复核
- 报告中的关键价格和财务字段优先来自结构化 API 字段
- 任何跨市场标的都必须独立取数，禁止直接汇率换算推导

## 2. 为什么优先使用 API

| 维度 | 网页抓取 | API 取数 |
|---|---|---|
| 精度 | 易受网页展示和排版影响 | 字段结构化、口径明确 |
| 稳定性 | 页面改版即失效 | 脚本和字段更可复用 |
| 审计性 | 难复现 | 输出 JSON 可归档 |
| 速度 | 相对慢 | 相对快 |
| 风险 | 容易把目标价、区间值误当现价 | 更容易锁定明确字段 |

典型错误：

```text
把目标价、52 周区间、分析师一致预期当成当前股价
```

API 的价值就在于优先读取 `regularMarketPrice`、`marketCap`、`trailingPE` 这类明确字段。

## 3. 双引擎职责分工

### 3.1 yfinance

适用：

- 港股
- 美股
- ADR
- 全球指数

常用字段：

- `regularMarketPrice`
- `marketCap`
- `trailingPE`
- `priceToBook`
- `priceToSalesTrailing12Months`
- `dividendYield`
- `returnOnEquity`
- `profitMargins`
- `grossMargins`
- `freeCashflow`
- `operatingCashflow`
- `fiftyTwoWeekHigh`
- `fiftyTwoWeekLow`

### 3.2 AkShare

适用：

- A 股主力
- 港股补充
- 本土财务摘要、主营构成、分红和宏观数据

常用接口：

- `stock_zh_a_spot_em`
- `stock_individual_info_em`
- `stock_financial_abstract`
- `stock_dividend_cninfo`
- `stock_main_business_em`
- `stock_hk_spot_em`
- `stock_financial_hk_analysis_indicator_em`

## 4. 市场分工

### 4.1 A 股

- 主引擎：`AkShare`
- 重点：财务摘要、主营构成、分红、实控人与治理
- 参考：`references/a-share-market-rules.md`

### 4.2 港股

- 主引擎：`yfinance`
- 补充：`AkShare`
- 重点：HKD 币种、AH 双重上市、流动性折价、高股息可持续性
- 参考：`references/hk-market-rules.md`

### 4.3 美股 / ADR

- 主引擎：`yfinance`
- 重点：GAAP、FCF、回购、指引和 ADR 结构风险
- 参考：`references/us-market-rules.md`

## 5. 调用顺序

```text
Step 0.0 API 优先
  ├─ 港股 / 美股 / ADR：先 yfinance
  ├─ A 股：先 AkShare
  ├─ 若关键字段缺失：换另一引擎或补网页复核
  └─ 若跨市场：A/H/ADR 三端分别独立取数
```

## 6. 标准调用入口

启动分析时，第一步应执行：

```bash
python scripts/fetch_stock_data.py --symbol 0700.HK --market HK
python scripts/fetch_stock_data.py --symbol 600519 --market A
python scripts/fetch_stock_data.py --symbol AAPL --market US
```

常用参数：

- `--symbol`
- `--market`
- `--output`
- `--output-dir`

## 7. 哪些字段必须先走 API

以下字段禁止跳过 API 直接引用网页：

| 字段 | 典型 API 字段 |
|---|---|
| 当前股价 / 收盘价 | `regularMarketPrice` / `current` |
| 总市值 | `marketCap` |
| PE / PB / PS | `trailingPE` / `priceToBook` / `priceToSalesTrailing12Months` |
| 股息率 / 派息率 | `dividendYield` / `payoutRatio` |
| ROE / 净利率 / 毛利率 | `returnOnEquity` / `profitMargins` / `grossMargins` |
| 三大报表核心字段 | 各引擎财务接口 |
| 52 周高低点 | `fiftyTwoWeekHigh` / `fiftyTwoWeekLow` |

## 8. 哪些场景允许补网页

以下情况允许或需要网页补充：

1. API 返回空值或报错
2. API 没有对应字段，例如近期管理层发言、近 30 天监管事件
3. 需要复核异常值
4. 行业格局、市占率、竞争格局等定性信息

## 9. 信源等级映射

| 等级 | 含义 | 典型来源 |
|:---:|---|---|
| `Tier 0` | API 直取 | yfinance / AkShare / 官方 API |
| `Tier 1` | 一级官方 | 年报、公告、交易所、监管部门 |
| `Tier 2` | 二级权威 | Bloomberg、Reuters、FT、WSJ、专业数据库网页 |
| `Tier 3` | 三级参考 | 财经媒体、行业资讯平台 |
| `Tier 4` | 单源弱信源 | 仅 1 源或多站互抄 |
| `Tier 5` | 传闻 | 股吧、匿名贴、供应链传闻 |

## 10. Step 8 复验要求

交卷前自检时：

- 复验源不得与 Step 0 完全重叠
- 若 Step 0 用了 yfinance，Step 8 应优先补 AkShare 或网页权威源
- 若 Step 0 用了 AkShare，Step 8 应优先补网页权威源或另一 API

## 11. 常见陷阱

| 陷阱 | 说明 | 应对 |
|---|---|---|
| 把目标价当现价 | 网页最常见错误 | 只认明确 API 字段 |
| 股息率小数与百分比混淆 | 0.0085 不等于 0.0085% | 输出时统一换算并标注 |
| 周期底部 PE 虚高 | 利润太低导致失真 | 参考周期行业规则 |
| 港股/AH 币种错配 | HKD/CNY 混用 | 强制显式标注币种 |
| ADR 与底层业务混淆 | 交易标的与经营主体口径错位 | 参考美股/ADR 规则 |

## 12. 降级与异常处理

如果 API 失败：

1. 先尝试另一引擎
2. 再降级到网页补充
3. 报告中必须显式披露降级状态

禁止行为：

- 实际靠网页抓取，却伪装成 API 取数
- 不披露字段来源和降级过程
