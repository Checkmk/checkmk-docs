#!/usr/bin/env python3
"""Fetch the Checkmk Dictionary page from Confluence and save as markdown."""

import json
import os
import re
import sys
import urllib.request
import urllib.error
from html.parser import HTMLParser

PAGE_ID = "103711357"
BASE_URL = "https://wiki.lan.checkmk.net"
OUTPUT = os.path.join(os.path.dirname(__file__), "checkmk-dictionary.md")


class HTMLToMarkdown(HTMLParser):
    """Convert Confluence export HTML to markdown, preserving table structure."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._out = []
        self._in_table = False
        self._in_row = False
        self._in_cell = False
        self._cell_buf = []
        self._row_cells = []
        self._table_rows = []

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        if t == "table":
            self._in_table = True
            self._table_rows = []
        elif t == "tr" and self._in_table:
            self._in_row = True
            self._row_cells = []
        elif t in ("td", "th") and self._in_row:
            self._in_cell = True
            self._cell_buf = []
        elif t in ("br", "p") and self._in_cell:
            self._cell_buf.append(" ")
        elif t == "li" and not self._in_table:
            self._out.append("\n- ")
        elif t in ("h1", "h2", "h3", "h4", "h5", "h6") and not self._in_table:
            self._out.append("\n" + "#" * min(int(t[1]) + 1, 6) + " ")
        elif t in ("br",) and not self._in_table:
            self._out.append("\n")
        elif t == "p" and not self._in_table:
            self._out.append("\n")

    def handle_endtag(self, tag):
        t = tag.lower()
        if t == "table":
            if self._in_cell:
                self._close_cell()
            if self._row_cells:
                self._table_rows.append(list(self._row_cells))
            self._flush_table()
            self._in_table = False
            self._in_row = False
            self._in_cell = False
            self._row_cells = []
        elif t == "tr" and self._in_table:
            if self._in_cell:
                self._close_cell()
            if self._row_cells:
                self._table_rows.append(list(self._row_cells))
            self._row_cells = []
            self._in_row = False
        elif t in ("td", "th") and self._in_cell:
            self._close_cell()
        elif t in ("p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "div") and not self._in_table:
            self._out.append("\n")

    def handle_data(self, data):
        if self._in_cell:
            self._cell_buf.append(data)
        elif not self._in_table:
            self._out.append(data)

    def _close_cell(self):
        content = " ".join("".join(self._cell_buf).split())
        content = content.replace("|", "\\|")
        self._row_cells.append(content)
        self._cell_buf = []
        self._in_cell = False

    def _flush_table(self):
        rows = self._table_rows
        if not rows:
            return
        ncols = max(len(r) for r in rows)
        if ncols == 0:
            return
        self._out.append("\n\n")
        for i, row in enumerate(rows):
            padded = row + [""] * (ncols - len(row))
            self._out.append("| " + " | ".join(padded) + " |\n")
            if i == 0:
                self._out.append("|" + "|".join([" --- "] * ncols) + "|\n")
        self._out.append("\n")

    def get_result(self):
        text = "".join(self._out)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def fetch():
    token = os.environ.get("CONFLUENCE_TOKEN", "")
    if not token:
        print("fetch_confluence.py: CONFLUENCE_TOKEN not set, skipping.", file=sys.stderr)
        return None

    url = f"{BASE_URL}/rest/api/content/{PAGE_ID}?expand=body.export_view"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except urllib.error.URLError as e:
        print(f"fetch_confluence.py: could not reach Confluence: {e}", file=sys.stderr)
        return None

    title = data.get("title", "Checkmk Dictionary")
    raw_html = data["body"]["export_view"]["value"]

    parser = HTMLToMarkdown()
    parser.feed(raw_html)
    text = parser.get_result()

    content = f"# {title}\n\n{text}\n"

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(content)

    return content


if __name__ == "__main__":
    content = fetch()
    if content:
        # Inject the fetched content directly into Claude's context for this session.
        # This runs on SessionStart, so the content is always fresh.
        hook_output = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": content,
            }
        }
        print(json.dumps(hook_output))
