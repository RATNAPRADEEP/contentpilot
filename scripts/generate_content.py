#!/usr/bin/env python3
import json, os, re, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "data/config.json"), encoding="utf-8"))
OUT = os.path.join(ROOT, "generated")
os.makedirs(OUT, exist_ok=True)

def clean(value):
    value = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", value).strip()

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "ContentPilot/0.2"})
    with urllib.request.urlopen(req, timeout=20) as response:
        return response.read()

def parse_feed(raw):
    root = ET.fromstring(raw)
    items = []
    # RSS
    for node in root.findall(".//item"):
        title = clean(node.findtext("title"))
        link = clean(node.findtext("link"))
        description = clean(node.findtext("description"))
        if title:
            items.append({"title": title, "link": link, "description": description})
    # Atom
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for node in root.findall(".//a:entry", ns):
        title = clean(node.findtext("a:title", namespaces=ns))
        description = clean(node.findtext("a:summary", namespaces=ns) or node.findtext("a:content", namespaces=ns))
        link_node = node.find("a:link", ns)
        link = link_node.attrib.get("href", "") if link_node is not None else ""
        if title:
            items.append({"title": title, "link": link, "description": description})
    return items

items = []
for url in CFG.get("feeds", []):
    try:
        items.extend(parse_feed(fetch(url)))
    except Exception as exc:
        print(f"feed failed: {url}: {exc}")

def score(item):
    text = (item["title"] + " " + item["description"]).lower()
    keywords = CFG.get("scoring_keywords", [])
    score_value = sum(text.count(k.lower()) for k in keywords)
    if any(k in text for k in ("launch", "released", "release", "new", "announced")):
        score_value += 3
    if len(item["title"]) < 120:
        score_value += 1
    return score_value

# Remove duplicates by normalized title.
unique = {}
for item in items:
    key = re.sub(r"[^a-z0-9]+", "", item["title"].lower())
    unique[key] = item
items = sorted(unique.values(), key=score, reverse=True)

chosen = items[0] if items else {
    "title": "How reusable automation changes everyday work",
    "link": "",
    "description": "A practical look at reusable automation workflows."
}

title = chosen["title"]
description = chosen["description"]
summary = (
    f"{title} is worth a look because it points to a practical change in technology. "
    "Here is the useful part: what happened, why it matters, and what you can do with it."
)

script = [
    f"Here is today's tech discovery: {title}.",
    summary,
    "The important part is not just the headline. Look at the underlying problem, the workflow, and what can be reused.",
    "That is the kind of signal worth watching if you build with technology or automation.",
    "Follow for another practical discovery tomorrow."
]

payload = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "source": chosen,
    "score": score(chosen),
    "hook": script[0],
    "script": script,
    "format": CFG["channel"],
    "candidates_considered": len(items)
}

json.dump(payload, open(os.path.join(OUT, "latest.json"), "w", encoding="utf-8"), indent=2)
with open(os.path.join(OUT, "latest.txt"), "w", encoding="utf-8") as handle:
    handle.write("\n\n".join(script))

print("Selected:", title)
print("Candidates:", len(items))
