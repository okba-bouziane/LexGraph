"""Render docs/eval-report.md (headings + tables) to a small HTML page for the screenshot."""

import html
import sys
from pathlib import Path

src = Path(sys.argv[1]).read_text().splitlines()
out = [
    "<meta charset=utf-8><style>body{font:15px system-ui;margin:32px;max-width:760px;color:#1b1f27}"
    "table{border-collapse:collapse;margin:8px 0 24px}td,th{border:1px solid #dfe3ea;padding:6px 12px;text-align:right}"
    "td:first-child,th:first-child{text-align:left}th{background:#f1f3f7}</style>"
]
rows: list[str] = []
for line in src + [""]:
    if line.startswith("|"):
        if set(line.replace("|", "").strip()) <= set("-"):
            continue
        rows.append(line)
        continue
    if rows:
        out.append("<table>")
        for i, r in enumerate(rows):
            cells = [html.escape(c.strip()) for c in r.strip("|").split("|")]
            tag = "th" if i == 0 else "td"
            out.append("<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in cells) + "</tr>")
        out.append("</table>")
        rows = []
    if line.startswith("# "):
        out.append(f"<h1>{html.escape(line[2:])}</h1>")
    elif line.startswith("## "):
        out.append(f"<h2>{html.escape(line[3:])}</h2>")
    elif line.strip():
        out.append(f"<p>{html.escape(line)}</p>")
Path(sys.argv[2]).write_text("\n".join(out))
