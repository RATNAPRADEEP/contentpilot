#!/usr/bin/env python3
import json, os, re, textwrap, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG=json.load(open(os.path.join(ROOT,"data/config.json"),encoding="utf-8"))
OUT=os.path.join(ROOT,"generated")
os.makedirs(OUT,exist_ok=True)

def clean(s):
    return re.sub(r"\\s+"," ",re.sub(r"<[^>]+>"," ",s or "")).strip()

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"ContentPilot/0.1"})
    with urllib.request.urlopen(req,timeout=20) as r:
        return r.read()

items=[]
for url in CFG["feeds"]:
    try:
        root=ET.fromstring(fetch(url))
        for node in root.findall(".//item")[:20]:
            title=clean(node.findtext("title"))
            link=clean(node.findtext("link"))
            desc=clean(node.findtext("description"))
            if title:
                items.append({"title":title,"link":link,"description":desc})
    except Exception as e:
        print("feed failed",url,e)

def score(x):
    text=(x["title"]+" "+x["description"]).lower()
    keys=["ai","agent","github","open source","developer","automation","tool","launch"]
    return sum(text.count(k) for k in keys)

items.sort(key=score,reverse=True)
chosen=items[0] if items else {
    "title":"How automation is changing everyday work",
    "link":"",
    "description":"A practical look at reusable automation workflows."
}

title=chosen["title"]
description=chosen["description"]
summary=f"This story explores {title}. The key idea is to understand what changed, why it matters, and what someone can do with it."
script=[
    f"Here is something interesting: {title}.",
    summary,
    "The useful part is not just the headline. Look at the underlying problem, the workflow, and what can be reused.",
    "If this is useful, save it and follow for the next practical discovery."
]

payload={
    "generated_at":datetime.now(timezone.utc).isoformat(),
    "source":chosen,
    "score":score(chosen),
    "hook":script[0],
    "script":script,
    "format":CFG["channel"]
}
json.dump(payload,open(os.path.join(OUT,"latest.json"),"w",encoding="utf-8"),indent=2)
with open(os.path.join(OUT,"latest.txt"),"w",encoding="utf-8") as f:
    f.write("\n\n".join(script))
print("Selected:",title)
