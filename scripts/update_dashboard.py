#!/usr/bin/env python3
import json, os, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = json.load(open(os.path.join(ROOT, "generated/latest.json"), encoding="utf-8"))
os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)

title = html.escape(data["source"]["title"])
summary = html.escape(data["script"][1])
source = html.escape(data["source"].get("link", ""))
generated = html.escape(data["generated_at"])

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ContentPilot</title>
<style>
body{{margin:0;background:#0b1020;color:#f8fafc;font-family:system-ui,sans-serif}}
main{{max-width:960px;margin:auto;padding:32px 20px}}
.card{{background:#151c31;border:1px solid #26314f;border-radius:20px;padding:24px;margin:18px 0}}
h1{{font-size:42px;margin-bottom:8px}}
.badge{{display:inline-block;padding:7px 11px;border-radius:999px;background:#1e293b;font-size:12px}}
a{{color:#7dd3fc}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}}
.step{{padding:16px;background:#0f172a;border-radius:14px}}
.status{{padding:14px;border-radius:12px;background:#102a1b;border:1px solid #1f6b3b}}
</style>
</head>
<body><main>
<h1>ContentPilot</h1>
<p class="badge">AUTOMATED CONTENT PIPELINE</p>
<div class="card">
<h2>{title}</h2>
<p>{summary}</p>
<p><small>Topic score: {data["score"]} · Candidates considered: {data["candidates_considered"]}</small></p>
<div class="status">Latest build completed. The rendered video is retained as a short-lived GitHub Actions artifact and is not stored in the repository.</div>
{"<p><a href='"+source+"' target='_blank' rel='noreferrer'>Open original source</a></p>" if source else ""}
</div>
<div class="card"><h2>Pipeline</h2><div class="grid">
<div class="step">1. Discover</div><div class="step">2. Score</div><div class="step">3. Research</div>
<div class="step">4. Script</div><div class="step">5. Render</div><div class="step">6. Publish</div>
</div></div>
<div class="card"><small>Generated {generated}</small></div>
</main></body></html>"""

open(os.path.join(ROOT, "docs", "index.html"), "w", encoding="utf-8").write(page)
