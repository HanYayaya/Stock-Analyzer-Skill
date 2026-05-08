---
name: Stock Analyzer
description: 基于价值投资框架的股票分析技能。用于分析单只股票或股票池是否值得中长期投资，强调“三好原则”（好行业、好公司、好价格）、API 优先取数、多信源校验、逆向投资检查、定价权分析和交付前自检，并支持多方法论并行输出结构化报告。
---

# Stock Analyzer

## 核心目标

基于价值投资框架，输出对单只股票或股票池的结构化判断：

- 能不能买
- 为什么买或不买
- 哪些数据支撑这个结论
- 哪些风险足以推翻这个结论

核心理念：

```text
投资价值 = 好行业 × 好公司 × 好价格
```

如果任一维度明显失真，整体结论应偏保守。

## 使用边界

做的事：

- 评估行业、公司、价格三个维度
- 识别护城河、定价权、估值陷阱和逆向机会
- 输出结构化报告，并显式披露关键数据来源和置信度

不做的事：

- 不预测短期涨跌
- 不做技术面分析
- 不提供具体交易指令
- 不替代用户独立决策

## 强制规则

以下规则不可跳过：

1. 先走 API 优先取数，再做网页补充。
2. 价格类关键数据必须避免“目标价当现价”“区间价当现价”“历史高低点当现价”。
3. 进入结论的关键定量数据必须标注来源等级。
4. 关键价格数据必须至少满足 1 个高置信 API 源加网页交叉验证；若做不到，必须显式降级披露。
5. 公司分析必须覆盖所有主要业务板块，不能只分析标签业务。
6. 周期性行业与非周期性行业必须分别使用对应 reference，不能混用行业判断口径。
7. A 股、港股、美股 / ADR 必须分别使用对应市场规则，不能混用市场估值和治理口径。
8. 分析必须纳入当前宏观、地缘政治和大宗商品等外部因素。
9. 战略投资或隐蔽资产只能作为补充加分项，不能成为核心买入逻辑。
10. 报告不得引用单日资金流向数据。
11. 报告生成后必须做交付前自检，未通过不得发布。

## 主流程

### Step 0.0 先取 API 数据

启动分析时，第一步必须执行：

```bash
python scripts/fetch_stock_data.py --symbol 0700.HK --market HK
python scripts/fetch_stock_data.py --symbol 600519 --market A
python scripts/fetch_stock_data.py --symbol AAPL --market US
```

默认输出文件为 `./account/_temp_value_analysis_<symbol>.json`。

基本市场分工：

- 港股 / 美股 / ADR：优先 `yfinance`
- A 股：优先 `AkShare`
- 网页抓取：仅作补充、兜底或冲突复核

详细协议见：

- `references/api-data-source-protocol.md`

在进入行业分析前，先判定市场类型，并读取对应市场规则：

- A 股：`references/a-share-market-rules.md`
- 港股：`references/hk-market-rules.md`
- 美股 / ADR：`references/us-market-rules.md`

### Step 0 多信源校验

先核验再分析。对价格、PE、营收、净利、ROE、股息率、负债、现金流、股东结构、行业地位等关键字段做交叉验证。

重点防错：

- 币种混淆
- 财年口径混淆
- TTM 与静态值混淆
- 目标价 / 一致预期 / 52 周区间误当现价
- 跨市场标的直接靠汇率换算推导估值

详细协议见：

- `references/data-verification-protocol.md`
- `references/api-data-source-protocol.md`

### Step 0.5 扫描近 30 天重大事件

在估值与结论前，必须补扫描近 30 天的重要变化：

- 监管公告
- 管理层变动
- 重大诉讼或处罚
- 重大合作、并购、重组
- 影响行业竞争格局或需求预期的重要新闻
- 与公司成本、供给、汇率、运价、贸易政策有关的宏观与地缘因素

如果事件足以影响核心叙事或评分，必须写进报告主文，而不是只放附录。

### Step 1 到 Step 5 完成主体分析

主体分析按以下顺序展开：

1. 先按市场规则确定数据口径、估值习惯和治理重点
2. 再按行业规则判断行业格局、需求稳定性、进入壁垒、定价权环境
3. 公司分析：先拆清主要业务板块，再判断护城河、盈利能力、财务健康、管理层质量
4. 价格 / 估值分析：判断是否便宜，以及便宜的原因；估值口径要同时服从市场规则和行业规则
5. 逆向投资检查：判断市场情绪是否制造了错误定价
6. 定价权专项：判断公司是否具备持续提价而不显著伤害需求的能力，并把战略投资/隐蔽资产仅作为补充项处理

评分规则和权重不要在主文件展开，统一看：

- `references/scoring-model.md`

方法论参考：

- `references/analysis-principles.md`
- `references/a-share-market-rules.md`
- `references/hk-market-rules.md`
- `references/us-market-rules.md`
- `references/cyclical-industry-rules.md`
- `references/non-cyclical-industry-rules.md`
- `references/three-good-principles.md`
- `references/moat-analysis-guide.md`
- `references/valuation-traps.md`
- `references/contrarian-checklist.md`

### Step 8 交付前自检

报告完成后必须做自检，至少包括：

- 关键数据换源复验
- 核心结论反向提问验证
- 算术回验
- 一票否决项复查

自检目标不是“补格式”，而是尽可能推翻错误结论。

## 输出要求

最终报告必须遵循固定结构，不得自由改写为其他章节体系。

至少包含：

- 方法论结论总览
- 股票信息与关键数据
- 近 30 天重大事件专栏
- 行业分析
- 公司分析
- 估值分析
- 逆向投资与定价权
- 分方法论投资结论
- 风险提示
- 交卷前自检摘要

输出顺序要求：

1. 先陈列当前使用的方法论
2. 对每个方法论先给出一句话结论
3. 再陈列股票信息与关键数据
4. 在数据层先标出重点看点、可能陷阱、高质量信号、待复核项和重点板块
5. 在行业和公司分析后，可补“方法论检验问答”增强可读性
6. 最后按方法论逐一给出该方法论基于当前股票的完整观点
7. 在结论后，建议补“反事实压力测试”和“字段级数据校验表”

如果后续新增其他方法论：

- 必须在报告最前面的“方法论结论总览”中一起列出
- 必须在“分方法论投资结论”中逐个展开
- 不得只保留一个混合后的总括结论
- 《投资中最简单的事》方法论的评分结构仍需完整保留

其中分方法论投资结论必须包含：

- 方法论名称
- 一句话结论
- 基于该方法论的核心观点
- 好的部分
- 不好的部分
- 如果买
- 建议买入价格或买入区间，以及对应理由
- 如果不买
- 建议卖出价格或卖出区间，以及对应理由
- 最大风险
- 止损策略
- 止盈策略
- 持有期预期

如果使用 PE、PB、PS、EV/EBITDA 等估值口径给出买卖建议：

- 必须同步换算出对应价格
- 必须写明价格推导依据
- 不得只给倍数，不给价格

固定输出标准见：

- `references/report-output-standard.md`

报告模板见：

- `templates/analysis-report.md`

最终交付文件名必须遵循：

```text
{交易所代码}{股票代码}-{公司名称}+{YYYYMMDD}.pdf
{交易所代码}{股票代码}-{公司名称}+{YYYYMMDD}.md
```

## 资源导航

优先阅读这些文件：

- `references/api-data-source-protocol.md`：API 优先取数与市场分工
- `references/data-verification-protocol.md`：关键字段校验要求
- `references/scoring-model.md`：评分细则、权重、加减分和一票否决
- `references/analysis-principles.md`：多业务、周期、宏观、战略投资、禁引资金流向等约束
- `references/a-share-market-rules.md`：A 股的数据口径、治理重点和估值习惯
- `references/hk-market-rules.md`：港股的流动性折价、AH 口径和估值习惯
- `references/us-market-rules.md`：美股 / ADR 的 GAAP、回购、FCF 和估值习惯
- `references/cyclical-industry-rules.md`：周期行业的判断框架、领先指标和估值口径
- `references/non-cyclical-industry-rules.md`：非周期行业的判断框架、质量判断和估值口径
- `references/report-output-standard.md`：固定报告章节和必填项
- `references/methodology-extension-guide.md`：新增第二套或多套方法论时的接入规范
- `references/custom-author-methodology-intake.md`：把外部作者的文章、访谈和建议整理成正式方法论的接入规范
- `references/dang-tiered-methodology.md`：`Mr Dang投资理念方法` 的规则化版本
- `references/dang-tiered-industry-mapping.md`：`Mr Dang投资理念方法` 的行业映射规则
- `references/three-good-principles.md`：三好原则主框架
- `references/moat-analysis-guide.md`：护城河判断
- `references/valuation-traps.md`：低估值陷阱识别
- `references/contrarian-checklist.md`：逆向投资检查
- `references/extension-points.md`：后续二次开发扩展点

## 二次开发约束

扩展这个 skill 时遵循以下原则：

- 优先把新增规则放进 `references/`
- 优先把新增取数能力放进 `scripts/`
- 尽量保持 JSON 输出 schema 稳定
- 报告模板调整优先落在 `templates/`
- 不把历史沿革和长篇变更记录重新堆回 `SKILL.md`
