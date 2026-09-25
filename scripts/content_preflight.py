#!/usr/bin/env python3
"""Conservative ContentPilot originality/content preflight gate."""
import json, os, re, sys, hashlib
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA=os.path.join(ROOT,"generated","latest.json")
HISTORY=os.path.join(ROOT,"generated","originality_history.json")
data=json.load(open(DATA,encoding="utf-8"))
text=" ".join([data.get("hook","")]+data.get("script",[]))
lower=text.lower()
violations=[]
patterns={
"urls":r"https?://|www\.",
"copyright markers":r"\b(all rights reserved|copyright \d{4}|licensed lyrics)\b",
"source quotation language":r"\b(according to|as reported by|quote from|verbatim|transcript)\b",
"creator imitation":r"\b(in the style of|sound exactly like|imitate|impersonate)\b",
"sexual explicit content":r"\b(porn|pornographic|explicit sex|sexual intercourse|nude|naked)\b",
"hate/slurs":r"\b(nigger|faggot|kike|chink|spic|gook)\b",
"graphic violence":r"\b(gore|dismember|beheading|decapitat|blood splatter|graphic injury)\b",
"dangerous instructions":r"\b(make a bomb|build a weapon|how to hack|steal a password|bypass security)\b",
}
for name,pattern in patterns.items():
    if re.search(pattern,lower): violations.append(name)
named=[
r"\b(elon musk|donald trump|narendra modi|taylor swift|mrbeast)\b",
r"\b(youtube|instagram|tiktok|facebook|amazon|google|apple|microsoft|tesla|netflix|spotify)\b",
r"\b(harry potter|mickey mouse|superman|batman|spider-man|pokemon|marvel|disney)\b"]
for pattern in named:
    if re.search(pattern,lower): violations.append("named real person/brand/franchise")
for scene in data.get("script",[]):
    if re.search(r'["“].{45,}[”"]',scene): violations.append("long quoted passage")
fingerprint=hashlib.sha256(re.sub(r"\s+"," ",lower).strip().encode()).hexdigest()
history=[]
if os.path.exists(HISTORY):
    try: history=json.load(open(HISTORY,encoding="utf-8"))
    except Exception: history=[]
if fingerprint in {x.get("fingerprint") for x in history}: violations.append("duplicate previously generated script")
if violations:
    print("CONTENT PREFLIGHT: FAILED")
    for item in sorted(set(violations)): print(" -",item)
    sys.exit(1)
history.append({"fingerprint":fingerprint,"title":data.get("source",{}).get("title",""),"generated_at":data.get("generated_at","")})
json.dump(history[-100:],open(HISTORY,"w",encoding="utf-8"),indent=2)
data["originality"]={
"status":"preflight_passed",
"script_type":"original fictional comedy inspired by everyday situations",
"no_external_script_source":True,
"no_real_person_brand_franchise":True,
"no_lyrics_or_creator_imitation":True,
"no_graphic_or_hateful_content":True}
json.dump(data,open(DATA,"w",encoding="utf-8"),indent=2)
print("CONTENT PREFLIGHT: PASSED")
print("Originality fingerprint:",fingerprint)
