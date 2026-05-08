#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
export_report.py — 将 Markdown 分析报告导出为 PDF

依赖：
    pip install markdown playwright
    python -m playwright install chromium

用法：
    python scripts/export_report.py --input ./examples/SZ002170-芭田股份+20260508.md
    python scripts/export_report.py --input ./examples/SZ002170-芭田股份+20260508.md --output ./examples/SZ002170-芭田股份+20260508.pdf

说明：
- 先将 Markdown 转为 HTML，再交给 Chromium 打印为 PDF
- 临时 HTML 会在导出完成后自动删除
- 更适合保留 emoji、表格、标题层级和整体排版
"""

from __future__ import annotations

import argparse
import html
import os
import re
import sys
import tempfile
from pathlib import Path


try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def _escape_attr(text: str) -> str:
    return html.escape(text, quote=True)


def _remove_front_matter(text: str) -> str:
    lines = text.splitlines()
    if len(lines) >= 3 and lines[0].strip() == "---":
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                return "\n".join(lines[idx + 1 :])
    return text


def _build_html(markdown_text: str, title: str) -> str:
    import markdown

    body_html = markdown.markdown(
        markdown_text,
        extensions=[
            "tables",
            "fenced_code",
            "sane_lists",
        ],
        output_format="html5",
    )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{_escape_attr(title)}</title>
  <style>
    :root {{
      --text: #111827;
      --muted: #4b5563;
      --line: #d1d5db;
      --soft: #f8fafc;
      --soft-2: #eef2f7;
      --accent: #0f172a;
    }}
    @page {{
      size: A4;
      margin: 16mm 14mm 18mm 14mm;
    }}
    html, body {{
      margin: 0;
      padding: 0;
      color: var(--text);
      background: white;
      font-family: "Microsoft YaHei", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji", Arial, sans-serif;
      font-size: 12.2px;
      line-height: 1.65;
      -webkit-font-smoothing: antialiased;
      text-rendering: geometricPrecision;
    }}
    body {{
      padding: 0;
    }}
    .page {{
      width: 100%;
      box-sizing: border-box;
    }}
    h1, h2, h3, h4, h5, h6 {{
      color: var(--accent);
      line-height: 1.25;
      margin: 1.05em 0 0.45em;
      page-break-after: avoid;
      break-after: avoid-page;
      font-weight: 700;
    }}
    h1 {{
      font-size: 24px;
      margin-top: 0;
      padding-bottom: 0.35em;
      border-bottom: 1px solid var(--line);
    }}
    h2 {{ font-size: 18px; }}
    h3 {{ font-size: 15px; }}
    h4 {{ font-size: 13px; }}
    h5, h6 {{ font-size: 12px; }}
    p {{
      margin: 0.35em 0 0.7em;
      orphans: 3;
      widows: 3;
      overflow-wrap: anywhere;
      word-break: break-word;
    }}
    strong {{ font-weight: 700; }}
    em {{ font-style: italic; }}
    a {{
      color: #0f172a;
      text-decoration: none;
      word-break: break-all;
    }}
    hr {{
      border: none;
      border-top: 1px solid var(--line);
      margin: 1em 0 1.15em;
    }}
    blockquote {{
      margin: 0.8em 0;
      padding: 0.7em 1em;
      border-left: 4px solid #cbd5e1;
      background: var(--soft);
      color: var(--muted);
      break-inside: avoid;
    }}
    ul, ol {{
      margin: 0.3em 0 0.7em 1.35em;
      padding: 0;
    }}
    li {{
      margin: 0.15em 0;
      overflow-wrap: anywhere;
    }}
    code {{
      font-family: "Cascadia Mono", "Consolas", "Courier New", monospace;
      font-size: 0.92em;
      background: #f1f5f9;
      padding: 0.12em 0.34em;
      border-radius: 4px;
    }}
    pre {{
      background: #0b1020;
      color: #e5e7eb;
      padding: 12px 14px;
      border-radius: 8px;
      overflow: auto;
      font-family: "Cascadia Mono", "Consolas", "Courier New", monospace;
      font-size: 11px;
      line-height: 1.55;
      white-space: pre-wrap;
      word-break: break-word;
      break-inside: avoid;
    }}
    pre code {{
      background: transparent;
      padding: 0;
      color: inherit;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 0.8em 0 1.05em;
      table-layout: fixed;
      break-inside: auto;
      page-break-inside: auto;
    }}
    thead {{
      display: table-header-group;
    }}
    tr {{
      break-inside: avoid;
      page-break-inside: avoid;
    }}
    th, td {{
      border: 1px solid var(--line);
      padding: 7px 8px;
      vertical-align: top;
      text-align: left;
      overflow-wrap: anywhere;
      word-break: break-word;
    }}
    th {{
      background: var(--soft-2);
      font-weight: 700;
    }}
    img {{
      max-width: 100%;
      height: auto;
    }}
    .note {{
      color: var(--muted);
    }}
    .emoji {{
      font-family: "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji", "Microsoft YaHei", sans-serif;
    }}
  </style>
</head>
<body>
  <div class="page">
    {body_html}
  </div>
</body>
</html>"""


def export_pdf(input_path: Path, output_path: Path) -> None:
    from playwright.sync_api import sync_playwright

    markdown_text = input_path.read_text(encoding="utf-8")
    markdown_text = _remove_front_matter(markdown_text)

    html_text = _build_html(markdown_text, input_path.stem)

    temp_html = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
            temp_html = Path(f.name)
            f.write(html_text)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": 1240, "height": 1754},
                device_scale_factor=1,
            )
            page.goto(temp_html.as_uri(), wait_until="load")
            page.emulate_media(media="print")
            page.pdf(
                path=str(output_path),
                format="A4",
                print_background=True,
                margin={"top": "16mm", "right": "14mm", "bottom": "18mm", "left": "14mm"},
                prefer_css_page_size=True,
            )
            browser.close()
    finally:
        if temp_html and temp_html.exists():
            try:
                temp_html.unlink()
            except Exception:
                pass


def main() -> int:
    parser = argparse.ArgumentParser(description="将 Markdown 分析报告导出为 PDF")
    parser.add_argument("--input", required=True, help="输入 Markdown 文件路径")
    parser.add_argument("--output", default=None, help="输出 PDF 文件路径")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"[ERROR] 输入文件不存在: {input_path}", file=sys.stderr)
        return 1

    output_path = Path(args.output).resolve() if args.output else input_path.with_suffix(".pdf")

    try:
        export_pdf(input_path, output_path)
    except Exception as e:
        print(f"[ERROR] 导出失败: {e}", file=sys.stderr)
        return 1

    print(f"[OK] PDF 导出完成 -> {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
