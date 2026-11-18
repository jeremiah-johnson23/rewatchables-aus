#!/usr/bin/env python3
"""Render audit/streaming-audit.json as the HTML body of the audit summary email.

Reads TARGET (branch the results went to) and RUN_URL from the environment.
"""

import html
import json
import os
from pathlib import Path

data = json.loads((Path(__file__).parent.parent / "audit" / "streaming-audit.json").read_text())
rows = data["rows"]
grades = {k: sum(1 for r in rows if r["grade"] == k) for k in ("verified", "likely", "suspect", "missing", "hand")}
changed = [r for r in rows if r.get("applied") and (r.get("added") or r.get("removed"))]
flagged = [r for r in rows if r["grade"] in ("suspect", "missing")]

out = [
    f"<h3>Streaming audit {data['date']}</h3>",
    f"<p>{len(rows)} films checked: {grades['verified']} verified, {grades['likely']} likely, "
    f"{grades['suspect']} suspect, {grades['missing']} missing.<br>"
    f"{len(changed)} films had their streaming updated. Results on <b>{html.escape(os.environ.get('TARGET', ''))}</b>.</p>",
]
if flagged:
    out.append("<p><b>Needs a hand check</b> (stored streaming kept):</p><ul>")
    for r in flagged:
        jw = r.get("jw") or {}
        link = f" - <a href='{jw['url']}'>JustWatch</a>" if jw.get("url") else ""
        out.append(f"<li>{html.escape(r['title'])} ({r['year']}): {html.escape('; '.join(r['reasons']))}{link}</li>")
    out.append("</ul>")
hand = [r for r in rows if r["grade"] == "hand"]
if hand:
    out.append("<p><b>Known hand checks</b> (JustWatch can't match these automatically):</p><ul>")
    for r in hand:
        out.append(f"<li>{html.escape(r['title'])} ({r['year']}): {html.escape(r['reasons'][0])}</li>")
    out.append("</ul>")
out.append(f"<p><a href='{os.environ.get('RUN_URL', '')}'>Workflow run</a></p>")
print("".join(out))
