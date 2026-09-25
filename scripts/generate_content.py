#!/usr/bin/env python3
import json, os, re, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "data/config.json"), encoding="utf-8"))
OUT = os.path.join(ROOT, "generated")
os.makedirs(OUT, exist_ok=True)

def clean(value):
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = re.sub(r"https?://\S+", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "ContentPilot/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()

def parse_feed(raw):
    root = ET.fromstring(raw)
    items = []
    for node in root.findall(".//item"):
        title = clean(node.findtext("title"))
        link = clean(node.findtext("link"))
        description = clean(node.findtext("description"))
        if title:
            items.append({"title": title, "link": link, "description": description})
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for node in root.findall(".//a:entry", ns):
        title = clean(node.findtext("a:title", namespaces=ns))
        description = clean(node.findtext("a:summary", namespaces=ns) or node.findtext("a:content", namespaces=ns))
        link_node = node.find("a:link", ns)
        link = link_node.attrib.get("href", "") if link_node is not None else ""
        if title:
            items.append({"title": title, "link": link, "description": description})
    return items

def find_image(link):
    if not link:
        return ""
    try:
        raw = fetch(link, timeout=12).decode("utf-8", errors="ignore")
        patterns = [
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
        ]
        for pattern in patterns:
            match = re.search(pattern, raw, re.I)
            if match:
                return match.group(1).replace("&amp;", "&")
    except Exception as exc:
        print(f"image lookup failed: {exc}")
    return ""

items = []
for url in CFG.get("feeds", []):
    try:
        items.extend(parse_feed(fetch(url)))
    except Exception as exc:
        print(f"feed failed: {url}: {exc}")

def score(item):
    text = (item["title"] + " " + item["description"]).lower()
    score_value = sum(text.count(k.lower()) for k in CFG.get("scoring_keywords", []))
    if any(k in text for k in ("launch", "released", "release", "new", "announced")):
        score_value += 3
    if len(item["title"]) < 100:
        score_value += 2
    if item.get("description") and len(item["description"]) > 100:
        score_value += 2
    return score_value

unique = {}
for item in items:
    key = re.sub(r"[^a-z0-9]+", "", item["title"].lower())
    unique[key] = item
items = sorted(unique.values(), key=score, reverse=True)

chosen = items[0] if items else {
    "title": "A practical automation idea worth knowing",
    "link": "",
    "description": "Reusable automation can turn repeated manual work into a reliable workflow."
}

title = chosen["title"].strip()
display_title = title.split(":")[0].strip() if len(title) > 70 and ":" in title else title
display_title = re.sub(r"\s+", " ", display_title).strip()
if len(display_title) > 64:
    display_title = display_title[:64].rsplit(" ", 1)[0] + "..."
description = clean(chosen["description"])
description = re.sub(r"^arXiv:\S+\s+Announce Type:\s*\w+\s*", "", description, flags=re.I)
description = re.sub(r"^Abstract:\s*", "", description, flags=re.I)
sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", description) if len(s.strip()) > 30]

def clip(text, limit=180):
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "."

evidence_1 = clip(sentences[0] if sentences else "The source describes a new technology development worth investigating.")
evidence_2 = clip(sentences[1] if len(sentences) > 1 else "The interesting part is the workflow: what the system does, how it closes the loop, and where it can be useful.")

domain = urlparse(chosen.get("link", "")).netloc.replace("www.", "")
image = find_image(chosen.get("link", ""))

# A more watchable short: hook -> explanation -> mechanism -> practical meaning -> close.
if "mobile" in title.lower() or "phone" in title.lower():
    hook = "What if an AI could learn to use your phone — and improve itself?"
elif "agent" in title.lower():
    hook = "AI agents are getting more interesting: this one learns from its own actions."
else:
    hook = f"Here is the tech signal worth knowing today: {display_title}."
script = [
    hook,
    f"Here is the signal. {evidence_1}",
    f"Here is the interesting part. {evidence_2}",
    "Why does that matter? Because the value is not just the headline. It is the workflow behind it — what gets automated, what gets checked, and what a developer could actually reuse.",
    "ContentPilot finds a fresh public signal, turns it into a visual story, and packages it for a short-form video. Check the original source before relying on any claim."
]

payload = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "source": {**chosen, "title": display_title, "full_title": title, "domain": domain, "image": image},
    "score": score(chosen),
    "hook": hook,
    "script": script,
    "format": CFG["channel"],
    "candidates_considered": len(items),
    "visual_nodes": ["AI FOR DATA", "AI FOR TRAINING", "MODEL ↔ HARNESS"] if "qwen-planner" in title.lower() else ["DISCOVER", "BUILD", "VERIFY"],
    "story": {
        "hook": "Curiosity hook",
        "signal": "What the source says",
        "mechanism": "What is interesting about it",
        "meaning": "Why it matters",
        "close": "Practical takeaway + verification"
    }
}

json.dump(payload, open(os.path.join(OUT, "latest.json"), "w", encoding="utf-8"), indent=2)
with open(os.path.join(OUT, "latest.txt"), "w", encoding="utf-8") as handle:
    handle.write("\n\n".join(script))

print("Selected:", title)
print("Candidates:", len(items))
print("Source image:", image or "none")
