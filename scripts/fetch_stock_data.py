#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
fetch_stock_data.py

用于为股票分析报告准备结构化行情和财务摘要数据。

当前支持：
- A 股：优先 AkShare
- 港股：优先 yfinance，必要时补 AkShare
- 美股 / ADR：优先 yfinance

输出结果为统一 JSON 结构，供后续报告生成与校验流程使用。
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


SUPPORTED_MARKETS = {"A", "HK", "US"}
DEFAULT_OUTPUT_DIR = os.environ.get("STOCK_ANALYZER_OUTPUT_DIR", "./account")


try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


@dataclass
class SymbolMapping:
    market: str
    input_symbol: str
    yfinance_symbol: str
    akshare_symbol: str


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return False


def clean_number(value: Any) -> Any:
    if is_missing(value):
        return None
    return value


def safe_float(value: Any) -> Optional[float]:
    if is_missing(value):
        return None
    try:
        result = float(value)
    except Exception:
        return None
    if math.isnan(result):
        return None
    return result


def pick_dict_value(data: Optional[dict], key: str, default: Any = None) -> Any:
    if not isinstance(data, dict):
        return default
    value = data.get(key, default)
    return default if is_missing(value) else value


def now_meta() -> Dict[str, str]:
    return {
        "fetch_time_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fetch_time_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def normalize_symbol(symbol: str, market: str) -> SymbolMapping:
    raw = symbol.strip().upper()
    market = market.upper()

    if market == "A":
        code = raw.zfill(6)
        if code.startswith(("60", "68", "90")):
            yf = f"{code}.SS"
        else:
            yf = f"{code}.SZ"
        return SymbolMapping(market=market, input_symbol=symbol, yfinance_symbol=yf, akshare_symbol=code)

    if market == "HK":
        if raw.endswith(".HK"):
            raw = raw[:-3]
        num = str(int(raw)) if raw.lstrip("0") else "0"
        yf = f"{int(num):04d}.HK"
        ak = f"{int(num):05d}"
        return SymbolMapping(market=market, input_symbol=symbol, yfinance_symbol=yf, akshare_symbol=ak)

    return SymbolMapping(market=market, input_symbol=symbol, yfinance_symbol=raw, akshare_symbol=raw)


def resolve_output_path(symbol: str, explicit_output: Optional[str]) -> Path:
    if explicit_output:
        path = Path(explicit_output).expanduser().resolve()
    else:
        safe_name = symbol.replace(".", "_").replace("/", "_")
        path = Path(DEFAULT_OUTPUT_DIR).joinpath(f"_temp_value_analysis_{safe_name}.json").resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_yfinance_fast_info(ticker: Any) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    try:
        fast_info = ticker.fast_info
    except Exception:
        return result

    if fast_info is None:
        return result

    for attr in (
        "last_price",
        "previous_close",
        "year_high",
        "year_low",
        "market_cap",
        "currency",
        "shares",
    ):
        try:
            result[attr] = getattr(fast_info, attr, None)
        except Exception:
            result[attr] = None
    return result


def fetch_from_yfinance(symbol: str) -> Dict[str, Any]:
    import yfinance as yf

    ticker = yf.Ticker(symbol)
    try:
        info = ticker.info or {}
    except Exception as exc:
        raise RuntimeError(f"yfinance info 获取失败: {exc}") from exc

    fast = get_yfinance_fast_info(ticker)

    market_price = pick_dict_value(info, "regularMarketPrice") or fast.get("last_price")
    previous_close = pick_dict_value(info, "regularMarketPreviousClose") or fast.get("previous_close")

    return {
        "price": {
            "current": clean_number(market_price),
            "currency": pick_dict_value(info, "currency") or fast.get("currency"),
            "previous_close": clean_number(previous_close),
            "fifty_two_week_high": clean_number(pick_dict_value(info, "fiftyTwoWeekHigh") or fast.get("year_high")),
            "fifty_two_week_low": clean_number(pick_dict_value(info, "fiftyTwoWeekLow") or fast.get("year_low")),
            "data_type": "regular_market_price",
            "source": "yfinance",
        },
        "valuation": {
            "market_cap": clean_number(pick_dict_value(info, "marketCap") or fast.get("market_cap")),
            "trailing_pe": clean_number(pick_dict_value(info, "trailingPE")),
            "forward_pe": clean_number(pick_dict_value(info, "forwardPE")),
            "price_to_book": clean_number(pick_dict_value(info, "priceToBook")),
            "price_to_sales_ttm": clean_number(pick_dict_value(info, "priceToSalesTrailing12Months")),
            "enterprise_value": clean_number(pick_dict_value(info, "enterpriseValue")),
            "ev_to_ebitda": clean_number(pick_dict_value(info, "enterpriseToEbitda")),
            "source": "yfinance",
        },
        "profitability": {
            "return_on_equity": clean_number(pick_dict_value(info, "returnOnEquity")),
            "return_on_assets": clean_number(pick_dict_value(info, "returnOnAssets")),
            "profit_margins": clean_number(pick_dict_value(info, "profitMargins")),
            "gross_margins": clean_number(pick_dict_value(info, "grossMargins")),
            "operating_margins": clean_number(pick_dict_value(info, "operatingMargins")),
            "source": "yfinance",
        },
        "financials": {
            "total_revenue_ttm": clean_number(pick_dict_value(info, "totalRevenue")),
            "net_income_ttm": clean_number(pick_dict_value(info, "netIncomeToCommon")),
            "free_cashflow_ttm": clean_number(pick_dict_value(info, "freeCashflow")),
            "operating_cashflow_ttm": clean_number(pick_dict_value(info, "operatingCashflow")),
            "total_debt": clean_number(pick_dict_value(info, "totalDebt")),
            "total_cash": clean_number(pick_dict_value(info, "totalCash")),
            "debt_to_equity": clean_number(pick_dict_value(info, "debtToEquity")),
            "current_ratio": clean_number(pick_dict_value(info, "currentRatio")),
            "quick_ratio": clean_number(pick_dict_value(info, "quickRatio")),
            "source": "yfinance",
        },
        "growth": {
            "revenue_growth_yoy": clean_number(pick_dict_value(info, "revenueGrowth")),
            "earnings_growth_yoy": clean_number(pick_dict_value(info, "earningsGrowth")),
            "earnings_quarterly_growth": clean_number(pick_dict_value(info, "earningsQuarterlyGrowth")),
            "source": "yfinance",
        },
        "dividend": {
            "dividend_yield": clean_number(pick_dict_value(info, "dividendYield")),
            "dividend_rate": clean_number(pick_dict_value(info, "dividendRate")),
            "payout_ratio": clean_number(pick_dict_value(info, "payoutRatio")),
            "five_year_avg_dividend_yield": clean_number(pick_dict_value(info, "fiveYearAvgDividendYield")),
            "source": "yfinance",
        },
        "shares": {
            "shares_outstanding": clean_number(pick_dict_value(info, "sharesOutstanding") or fast.get("shares")),
            "float_shares": clean_number(pick_dict_value(info, "floatShares")),
            "held_percent_insiders": clean_number(pick_dict_value(info, "heldPercentInsiders")),
            "held_percent_institutions": clean_number(pick_dict_value(info, "heldPercentInstitutions")),
            "source": "yfinance",
        },
        "company": {
            "long_name": pick_dict_value(info, "longName"),
            "short_name": pick_dict_value(info, "shortName"),
            "industry": pick_dict_value(info, "industry"),
            "sector": pick_dict_value(info, "sector"),
            "country": pick_dict_value(info, "country"),
            "website": pick_dict_value(info, "website"),
            "long_business_summary": pick_dict_value(info, "longBusinessSummary"),
            "source": "yfinance",
        },
        "analyst": {
            "recommendation_key": pick_dict_value(info, "recommendationKey"),
            "number_of_analyst_opinions": clean_number(pick_dict_value(info, "numberOfAnalystOpinions")),
            "target_mean_price": clean_number(pick_dict_value(info, "targetMeanPrice")),
            "target_median_price": clean_number(pick_dict_value(info, "targetMedianPrice")),
            "target_high_price": clean_number(pick_dict_value(info, "targetHighPrice")),
            "target_low_price": clean_number(pick_dict_value(info, "targetLowPrice")),
            "warning": "target_*_price 为分析师目标价，不是现价",
            "source": "yfinance",
        },
    }


def dataframe_first_match(df: Any, code_column: str, code_value: str) -> Optional[Dict[str, Any]]:
    if df is None or getattr(df, "empty", True):
        return None
    rows = df[df[code_column] == code_value]
    if rows.empty:
        return None
    return rows.iloc[0].to_dict()


def extract_latest_financial_abstract(df: Any) -> Dict[str, Any]:
    if df is None or getattr(df, "empty", True):
        return {}

    columns = list(df.columns)
    metric_col = next((c for c in columns if str(c) in {"指标", "项目"}), columns[1] if len(columns) > 1 else columns[0])
    period_col = next((c for c in columns if str(c).isdigit() and len(str(c)) == 8), columns[2] if len(columns) > 2 else columns[-1])

    result: Dict[str, Any] = {}
    for _, row in df.iterrows():
        key = str(row[metric_col])
        result[key] = clean_number(row[period_col])

    result["_latest_period"] = str(period_col)
    result["_columns"] = [str(c) for c in columns[:6]]
    return result


def fetch_a_share(symbol: str) -> Dict[str, Any]:
    import akshare as ak

    individual_info: Dict[str, Any] = {}
    quote: Dict[str, Any] = {}
    financial_abstract: Dict[str, Any] = {}

    try:
        individual_df = ak.stock_individual_info_em(symbol=symbol)
        if individual_df is not None and not individual_df.empty:
            for _, row in individual_df.iterrows():
                individual_info[str(row["item"])] = clean_number(row["value"])
    except Exception as exc:
        individual_info["_error"] = f"stock_individual_info_em 失败: {exc}"

    try:
        spot_df = ak.stock_zh_a_spot_em()
        row = dataframe_first_match(spot_df, "代码", symbol)
        if row:
            quote = {
                "current": safe_float(row.get("最新价")),
                "previous_close": safe_float(row.get("昨收")),
                "change_pct": safe_float(row.get("涨跌幅")),
                "volume": safe_float(row.get("成交量")),
                "turnover": safe_float(row.get("成交额")),
                "high_52w": safe_float(row.get("52周最高")),
                "low_52w": safe_float(row.get("52周最低")),
                "pe_ttm": safe_float(row.get("市盈率-动态")),
                "pb": safe_float(row.get("市净率")),
                "market_cap_total": safe_float(row.get("总市值")),
                "market_cap_float": safe_float(row.get("流通市值")),
            }
    except Exception as exc:
        quote["_error"] = f"stock_zh_a_spot_em 失败: {exc}"

    try:
        abstract_df = ak.stock_financial_abstract(symbol=symbol)
        financial_abstract = extract_latest_financial_abstract(abstract_df)
    except Exception as exc:
        financial_abstract["_error"] = f"stock_financial_abstract 失败: {exc}"

    return {
        "price": {
            "current": quote.get("current"),
            "currency": "CNY",
            "previous_close": quote.get("previous_close"),
            "fifty_two_week_high": quote.get("high_52w"),
            "fifty_two_week_low": quote.get("low_52w"),
            "change_pct": quote.get("change_pct"),
            "data_type": "regular_market_price",
            "source": "akshare",
        },
        "valuation": {
            "market_cap": quote.get("market_cap_total") or individual_info.get("总市值"),
            "market_cap_float": quote.get("market_cap_float") or individual_info.get("流通市值"),
            "trailing_pe": quote.get("pe_ttm"),
            "price_to_book": quote.get("pb"),
            "source": "akshare",
        },
        "company": {
            "long_name": individual_info.get("股票简称"),
            "industry": individual_info.get("行业"),
            "listing_date": str(individual_info.get("上市时间", "")),
            "total_shares": individual_info.get("总股本"),
            "float_shares": individual_info.get("流通股"),
            "source": "akshare",
        },
        "financials_abstract": financial_abstract,
        "raw_individual_info": individual_info,
    }


def fetch_hk_supplement(symbol: str) -> Dict[str, Any]:
    import akshare as ak

    quote: Dict[str, Any] = {}
    hk_financials: Dict[str, Any] = {}

    try:
        spot_df = ak.stock_hk_spot_em()
        row = dataframe_first_match(spot_df, "代码", symbol)
        if row:
            quote = {
                "current": safe_float(row.get("最新价")),
                "previous_close": safe_float(row.get("昨收")),
                "change_pct": safe_float(row.get("涨跌幅")),
                "volume": safe_float(row.get("成交量")),
                "turnover": safe_float(row.get("成交额")),
                "name": row.get("名称"),
            }
    except Exception as exc:
        quote["_error"] = f"stock_hk_spot_em 失败: {exc}"

    try:
        annual_df = ak.stock_financial_hk_analysis_indicator_em(symbol=symbol, indicator="年度")
        if annual_df is not None and not annual_df.empty:
            hk_financials = {
                str(k): (str(v) if hasattr(v, "isoformat") else clean_number(v))
                for k, v in annual_df.iloc[0].to_dict().items()
            }
    except Exception as exc:
        hk_financials["_error"] = f"stock_financial_hk_analysis_indicator_em 失败: {exc}"

    return {
        "price": {
            "current": quote.get("current"),
            "currency": "HKD",
            "previous_close": quote.get("previous_close"),
            "change_pct": quote.get("change_pct"),
            "data_type": "regular_market_price",
            "source": "akshare",
        },
        "company": {
            "long_name": quote.get("name"),
            "source": "akshare",
        },
        "financials_hk_indicator": hk_financials,
    }


def merge_hk_fallback(primary: Dict[str, Any], fallback: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(primary)

    if not merged.get("price", {}).get("current") and fallback.get("price", {}).get("current"):
        merged["price"] = fallback["price"]

    if not merged.get("company", {}).get("long_name") and fallback.get("company", {}).get("long_name"):
        merged.setdefault("company", {}).update(fallback["company"])

    merged["_akshare_hk_supplement"] = fallback
    return merged


def fetch_dataset(symbol: str, market: str) -> Dict[str, Any]:
    market = market.upper()
    mapping = normalize_symbol(symbol, market)

    engines_used = []
    engines_failed = []
    errors = []
    payload: Dict[str, Any] = {}

    if market == "A":
        try:
            payload = fetch_a_share(mapping.akshare_symbol)
            engines_used.append("akshare")
        except Exception as exc:
            engines_failed.append({"engine": "akshare", "error": str(exc)})
            errors.append(f"akshare: {exc}")

    elif market == "HK":
        try:
            payload = fetch_from_yfinance(mapping.yfinance_symbol)
            engines_used.append("yfinance")
        except Exception as exc:
            engines_failed.append({"engine": "yfinance", "error": str(exc)})
            errors.append(f"yfinance: {exc}")

        need_hk_fallback = not payload.get("price", {}).get("current")
        if need_hk_fallback:
            try:
                hk_fallback = fetch_hk_supplement(mapping.akshare_symbol)
                payload = merge_hk_fallback(payload, hk_fallback)
                engines_used.append("akshare")
            except Exception as exc:
                engines_failed.append({"engine": "akshare", "error": str(exc)})
                errors.append(f"akshare: {exc}")

    elif market == "US":
        try:
            payload = fetch_from_yfinance(mapping.yfinance_symbol)
            engines_used.append("yfinance")
        except Exception as exc:
            engines_failed.append({"engine": "yfinance", "error": str(exc)})
            errors.append(f"yfinance: {exc}")

    result = {
        "meta": {
            "symbol_input": symbol,
            "market": market,
            "symbol_normalized": {
                "yfinance": mapping.yfinance_symbol,
                "akshare": mapping.akshare_symbol,
            },
            **now_meta(),
            "engines_used": engines_used,
            "engines_failed": engines_failed,
        },
        **payload,
        "errors": errors,
    }
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="获取股票结构化数据，用于后续分析报告")
    parser.add_argument("--symbol", required=True, help="股票代码，如 600519 / 0700.HK / AAPL")
    parser.add_argument("--market", required=True, choices=["A", "HK", "US", "a", "hk", "us"], help="市场类型")
    parser.add_argument("--output", default=None, help="输出 JSON 文件路径")
    parser.add_argument("--output-dir", default=None, help="仅指定输出目录，文件名自动生成")
    parser.add_argument("--print", action="store_true", help="同时打印 JSON 内容")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.output and args.output_dir:
        print("[ERROR] --output 与 --output-dir 不能同时使用", file=sys.stderr)
        return 1

    explicit_output = None
    if args.output_dir:
        safe_name = args.symbol.replace(".", "_").replace("/", "_")
        explicit_output = str(Path(args.output_dir).joinpath(f"_temp_value_analysis_{safe_name}.json"))
    elif args.output:
        explicit_output = args.output

    try:
        data = fetch_dataset(args.symbol, args.market)
    except Exception as exc:
        print(f"[ERROR] 取数失败: {exc}", file=sys.stderr)
        return 1

    output_path = resolve_output_path(args.symbol, explicit_output)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    print(f"[OK] 取数完成 -> {output_path}")
    print(f"     使用引擎: {data['meta']['engines_used']}")
    if data["meta"]["engines_failed"]:
        print(f"     [WARN] 失败引擎: {data['meta']['engines_failed']}")

    current_price = data.get("price", {}).get("current")
    if current_price is not None:
        currency = data.get("price", {}).get("currency", "")
        print(f"     当前价格: {current_price} {currency}".rstrip())

    trailing_pe = data.get("valuation", {}).get("trailing_pe")
    if trailing_pe is not None:
        try:
            print(f"     PE-TTM: {float(trailing_pe):.2f}")
        except Exception:
            print(f"     PE-TTM: {trailing_pe}")

    if args.print:
        print("\n--- JSON 内容 ---")
        print(json.dumps(data, ensure_ascii=False, indent=2, default=str))

    return 0


if __name__ == "__main__":
    sys.exit(main())
