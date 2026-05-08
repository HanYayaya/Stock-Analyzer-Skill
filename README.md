# Stock Analyzer

`Stock Analyzer` 是一个面向价值投资分析场景的股票分析技能仓库，用于对单只股票或股票池做结构化研究，并输出可交付的分析报告。

它的核心目标不是预测短期涨跌，而是回答几类更重要的问题：

- 这只股票能不能买
- 为什么买或为什么不买
- 哪些数据在支撑结论
- 哪些风险足以推翻当前判断

仓库当前支持：

- A 股
- 港股
- 美股 / ADR

并支持多方法论并行输出，目前包含：

- 《投资中最简单的事》价值投资框架
- `Mr Dang投资理念方法`

---

## 核心特点

- API 优先取数：优先用结构化数据源，而不是直接依赖网页抓取
- 多信源校验：关键价格和财务字段必须交叉验证
- 分市场规则：A 股、港股、美股 / ADR 使用不同估值和治理口径
- 分行业规则：周期行业与非周期行业分开分析
- 多方法论输出：同一份报告里可以并列输出不同方法论的一句话结论和完整观点
- 交付前自检：报告完成后必须做关键数据复验、结论反验证和算术回验

---

## 目录结构

```text
Stock Analyzer/
├─ SKILL.md
├─ README.md
├─ .gitignore
├─ scripts/
│  └─ fetch_stock_data.py
├─ templates/
│  └─ analysis-report.md
└─ references/
   ├─ a-share-market-rules.md
   ├─ hk-market-rules.md
   ├─ us-market-rules.md
   ├─ cyclical-industry-rules.md
   ├─ non-cyclical-industry-rules.md
   ├─ scoring-model.md
   ├─ report-output-standard.md
   ├─ data-verification-protocol.md
   ├─ api-data-source-protocol.md
   ├─ dang-tiered-methodology.md
   ├─ dang-tiered-industry-mapping.md
   └─ ...
```

说明：

- `SKILL.md`：主入口，定义技能定位、流程和资源导航
- `scripts/fetch_stock_data.py`：结构化取数脚本
- `templates/analysis-report.md`：报告模板
- `references/`：分析规则、市场口径、行业规则、评分模型和方法论文档

---

## 安装依赖

建议使用 Python 3.10+。

先安装基础依赖：

```bash
pip install yfinance akshare pandas
```

如果后续你自己扩展更多数据源，再按需要补充依赖。

---

## 快速开始

### 1. 获取结构化数据

先运行取数脚本：

```bash
# A 股
python scripts/fetch_stock_data.py --symbol 600519 --market A

# 港股
python scripts/fetch_stock_data.py --symbol 0700.HK --market HK

# 美股
python scripts/fetch_stock_data.py --symbol AAPL --market US
```

默认会生成一个临时 JSON 文件，用于后续分析过程引用。

说明：

- A 股优先使用 `AkShare`
- 港股、美股 / ADR 优先使用 `yfinance`
- 网页数据只用于补充、兜底或冲突复核

---

### 2. 按规则完成分析

分析时的标准顺序是：

1. 先确认市场类型
2. 读取对应市场规则
3. 判断行业属性，读取对应行业规则
4. 做多信源数据校验
5. 扫描近 30 天重大事件
6. 完成行业、公司、估值、逆向投资和定价权分析
7. 按方法论分别输出结论
8. 做交付前自检

优先阅读这些文件：

- [SKILL.md](./SKILL.md)
- [references/report-output-standard.md](./references/report-output-standard.md)
- [references/scoring-model.md](./references/scoring-model.md)
- [references/api-data-source-protocol.md](./references/api-data-source-protocol.md)
- [references/data-verification-protocol.md](./references/data-verification-protocol.md)

---

### 3. 使用报告模板

报告模板在：

- [templates/analysis-report.md](./templates/analysis-report.md)

最终报告固定结构包括：

1. 方法论结论总览
2. 股票信息与关键数据
3. 近 30 天重大事件专栏
4. 行业分析
5. 公司分析
6. 估值分析
7. 逆向投资 & 定价权
8. 分方法论投资结论
9. 风险提示
10. 交卷前自检摘要

---

## 输出文件命名

最终交付文件名统一使用：

```text
{交易所代码}{股票代码}-{公司名称}+{YYYYMMDD}.md
{交易所代码}{股票代码}-{公司名称}+{YYYYMMDD}.pdf
```

示例：

```text
SH601919-中远海控+20260507.md
SZ002170-芭田股份+20260508.pdf
```

---

## 当前分析原则

这个仓库默认遵循以下几条硬约束：

- 不把目标价、52 周区间、分析师一致预期误当现价
- 不引用单日资金流向数据
- 不把战略投资或隐蔽资产当作核心买入逻辑
- 不忽略公司非标签业务板块
- 不混用不同市场的估值和治理口径
- 不混用周期行业与非周期行业的估值方式
- 不在报告完成后跳过自检直接交付

---

## 方法论扩展

当前仓库已经支持多方法论接入。

如果你后续要新增新的投资方法论，建议先看：

- [references/methodology-extension-guide.md](./references/methodology-extension-guide.md)
- [references/custom-author-methodology-intake.md](./references/custom-author-methodology-intake.md)
- [references/extension-points.md](./references/extension-points.md)

原则是：

- 统一主报告结构
- 不把不同方法论写成互相冲突的模板
- 数据层和事实层尽量共用
- 结论层按方法论分开输出

---

## 临时文件与正式文件

- 临时结构化数据文件只用于分析过程
- 正式交付只保留 `.md` / `.pdf`
- 报告检查完成后，可以删除临时 JSON 文件

`.gitignore` 当前默认忽略：

- Python 缓存
- `account/`
- `_temp_value_analysis_*.json`

如果你后续希望把正式样例报告也纳入仓库，可以单独调整忽略规则。

---

## 后续建议

如果你准备长期维护这个仓库，建议后续继续补充：

- `requirements.txt`
- 示例输入与示例报告
- 自动化报告导出链路
- 更完整的事件扫描脚本
- 不同市场的更多估值口径支持

---

## 免责声明

本仓库用于投资分析框架研究和结构化报告生成，不构成任何实际投资建议。

投资有风险，决策需谨慎。
