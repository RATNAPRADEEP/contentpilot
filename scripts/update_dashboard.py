#!/usr/bin/env python3
import json, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d=json.load(open(os.path.join(ROOT,"generated/latest.json"),encoding="utf-8"))
os.makedirs(os.path.join(ROOT,"docs"),exist_ok=True)
html=f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ContentPilot</title>
<style>
body{{font-family:system-ui;background:#0b1020;color:#f8fafc;max-width:900px;margin:auto;padding:32px}}
.card{{background:#151c31;border:1px solid #26314f;border-radius:18px;padding:24px;margin:18px 0}}
small{{color:#94a3b8}} a{{color:#7dd3fc}}
.badge{{display:inline-block;padding:6px 10px;border-radius:999px;background:#1e293b}}
</style></head><body>
<h1>ContentPilot</h1><p class="badge">AUTOMATED CONTENT PIPELINE</p>
<div class="card"><small>Latest selected topic</small><h2>{d["source"]["title"]}</h2>
<p>{d["summary"] if "summary" in d else d["script"][1]}</p>
<p>Score: {d["score"]} · Generated: {d["generated_at"]}</p>
<a href="../generated/contentpilot-latest.mp4">Latest video artifact</a></div>
<div class="card"><h2>Pipeline</h2><p>Discover → Score → Research → Script → Render → Publish → Learn</p></div>
</body></html>"""
open(os.path.join(ROOT,"docs","index.html"),"w",encoding="utf-8").write(html)
