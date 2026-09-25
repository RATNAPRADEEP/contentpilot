#!/usr/bin/env python3
import json, os, random
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "data/config.json"), encoding="utf-8"))
OUT = os.path.join(ROOT, "generated")
os.makedirs(OUT, exist_ok=True)

SCENARIOS = [
    {
        "title": "When Your AI Assistant Gets Promoted",
        "theme": "AI assistant disasters",
        "hook": "I asked my AI assistant to save me ten minutes.",
        "scenes": [
            "ME: I asked my AI assistant to save me ten minutes.",
            "AI: Done. I scheduled a ten-minute meeting to discuss how we can save ten minutes.",
            "ME: That's not saving time.",
            "AI: Correct. So I scheduled another meeting to improve the first meeting.",
            "ME: Please stop.",
            "AI: Absolutely. I have added a follow-up meeting called: Please Stop."
        ],
        "nodes": ["YOU", "AI", "MEETING"],
        "background_urls": ["https://assets.mixkit.co/videos/28286/28286-720.mp4","https://assets.mixkit.co/videos/4872/4872-720.mp4","https://assets.mixkit.co/videos/4508/4508-720.mp4","https://assets.mixkit.co/videos/4607/4607-720.mp4","https://assets.mixkit.co/videos/24055/24055-720.mp4"]
    },
    {
        "title": "When the Bug Only Exists on Your Computer",
        "theme": "developer life",
        "hook": "Every developer knows the scariest sentence: It works on my machine.",
        "scenes": [
            "DEV: It works perfectly on my machine.",
            "TEAMMATE: Great. Push it.",
            "DEV: Okay.",
            "CI: Failed.",
            "DEV: Weird. It was working five seconds ago.",
            "CI: Correct. I only become aware of bugs when you are confident."
        ],
        "nodes": ["MY PC", "CI", "BUG"],
        "background_urls": ["https://assets.mixkit.co/videos/52076/52076-720.mp4","https://assets.mixkit.co/videos/48503/48503-720.mp4","https://assets.mixkit.co/videos/4508/4508-720.mp4","https://assets.mixkit.co/videos/8744/8744-720.mp4","https://assets.mixkit.co/videos/24055/24055-720.mp4"]
    },
    {
        "title": "The Meeting That Could Have Been an Email",
        "theme": "office meetings",
        "hook": "My calendar invited me to a meeting about whether we need meetings.",
        "scenes": [
            "MANAGER: Quick meeting, everyone. This will only take an hour.",
            "ME: What is it about?",
            "MANAGER: Whether our meetings are taking too much time.",
            "ME: And how long is this meeting?",
            "MANAGER: One hour.",
            "ME: Perfect. We have solved the problem by becoming the problem."
        ],
        "nodes": ["CALENDAR", "MEETING", "REGRET"],
        "background_urls": ["https://assets.mixkit.co/videos/4547/4547-720.mp4","https://assets.mixkit.co/videos/4872/4872-720.mp4","https://assets.mixkit.co/videos/4607/4607-720.mp4","https://assets.mixkit.co/videos/4508/4508-720.mp4","https://assets.mixkit.co/videos/24055/24055-720.mp4"]
    },
    {
        "title": "When Online Shopping Reads Your Mind",
        "theme": "online shopping",
        "hook": "I searched for one cheap thing online. The internet took that personally.",
        "scenes": [
            "ME: I only searched for a phone case.",
            "APP: Here are twelve premium phone cases.",
            "ME: I am not buying anything.",
            "APP: Here is a laptop you looked at three months ago.",
            "ME: How do you remember that?",
            "APP: I forget your password, but I remember your shopping dreams."
        ],
        "nodes": ["SEARCH", "RECOMMEND", "WALLET"],
        "background_urls": ["https://assets.mixkit.co/videos/4837/4837-720.mp4","https://assets.mixkit.co/videos/28286/28286-720.mp4","https://assets.mixkit.co/videos/4508/4508-720.mp4","https://assets.mixkit.co/videos/8744/8744-720.mp4","https://assets.mixkit.co/videos/231/231-720.mp4"]
    },
    {
        "title": "My Gym Motivation Has a Software Update",
        "theme": "gym motivation",
        "hook": "I downloaded a fitness app to become disciplined. It immediately became disappointed in me.",
        "scenes": [
            "APP: Day one. Let's crush this workout.",
            "ME: Absolutely.",
            "APP: Start with ten push-ups.",
            "ME: Can we start with a motivational quote?",
            "APP: Fine. Your ancestors did not evolve for this.",
            "ME: That's aggressive.",
            "APP: Great. Now do the push-ups."
        ],
        "nodes": ["MOTIVATION", "ME", "WORKOUT"],
        "background_urls": ["https://assets.mixkit.co/videos/52317/52317-720.mp4","https://assets.mixkit.co/videos/40248/40248-720.mp4","https://assets.mixkit.co/videos/52089/52089-720.mp4","https://assets.mixkit.co/videos/4506/4506-720.mp4","https://assets.mixkit.co/videos/52079/52079-720.mp4"]
    },
    {
        "title": "When Your Phone Knows You Too Well",
        "theme": "smartphone habits",
        "hook": "My phone knows my habits better than my family does.",
        "scenes": [
            "PHONE: Your screen time increased today.",
            "ME: I was busy.",
            "PHONE: You watched seventeen videos about people making sandwiches.",
            "ME: Research.",
            "PHONE: At 2:14 AM?",
            "ME: Midnight research is more advanced."
        ],
        "nodes": ["PHONE", "SCREEN TIME", "RESEARCH"],
        "background_urls": ["https://assets.mixkit.co/videos/4837/4837-720.mp4","https://assets.mixkit.co/videos/8744/8744-720.mp4","https://assets.mixkit.co/videos/231/231-720.mp4","https://assets.mixkit.co/videos/4808/4808-720.mp4","https://assets.mixkit.co/videos/28286/28286-720.mp4"]
    }
]

today = datetime.now(timezone.utc).date().toordinal()
scenario = SCENARIOS[today % len(SCENARIOS)]

# Keep the output deterministic for a given day while rotating through original sketches.
script = scenario["scenes"]
payload = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "source": {
        "title": scenario["title"],
        "full_title": scenario["title"],
        "link": "",
        "description": f"Original ContentPilot comedy sketch about {scenario['theme']}.",
        "domain": "ContentPilot Original",
        "image": ""
    },
    "score": 100,
    "hook": scenario["hook"],
    "script": script,
    "format": CFG["channel"],
    "candidates_considered": len(SCENARIOS),
    "visual_nodes": scenario["nodes"],
    "background_urls": scenario.get("background_urls", []),
    "genre": "comedy",
    "theme": scenario["theme"],
    "original": True,
    "story": {
        "hook": "Instant relatable setup",
        "signal": "Everyday situation",
        "mechanism": "Escalating misunderstanding",
        "meaning": "A recognizable human-vs-technology joke",
        "close": "Short punchline"
    }
}

json.dump(payload, open(os.path.join(OUT, "latest.json"), "w", encoding="utf-8"), indent=2)
with open(os.path.join(OUT, "latest.txt"), "w", encoding="utf-8") as handle:
    handle.write("\n\n".join(script))

print("Comedy sketch:", scenario["title"])
print("Theme:", scenario["theme"])
print("Scenes:", len(script))
