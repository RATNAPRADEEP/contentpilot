#!/usr/bin/env python3
import json, os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "data/config.json"), encoding="utf-8"))
OUT = os.path.join(ROOT, "generated")
os.makedirs(OUT, exist_ok=True)

# Original fictional sketches built from ordinary real-world situations.
# No real people, brands, copyrighted characters, song lyrics, clips, or source
# dialogue are used. Real-world situations are only the starting point.
# Persistent original character bible. These identities are reused across episodes.
# Visual designs remain original and can be expanded with new poses/expressions later.
CHARACTERS = {
    "arjun": {"name": "Arjun", "type": "human", "description": "young adult, practical, expressive, easily stressed by everyday problems"},
    "byte": {"name": "Byte", "type": "ai", "description": "friendly humanoid AI, literal-minded, calm, unexpectedly funny"},
    "maya": {"name": "Maya", "type": "human", "description": "confident young adult, observant, dry sense of humor"}
}



# Per-scene visual plan: every spoken line has an explicit actor, action, and
# visual focus. The renderer uses this instead of generic character animation.
SCENE_PLANS = {
    "When the QR Payment Says 'Pending'": [
        {"actor":"arjun","action":"paying","focus":"phone_pending"},
        {"actor":"arjun","action":"waiting","focus":"counter"},
        {"actor":"arjun","action":"checking_phone","focus":"phone_pending"},
        {"actor":"arjun","action":"waiting","focus":"counter"},
        {"actor":"arjun","action":"impatient","focus":"phone_pending"},
        {"actor":"arjun","action":"refreshing","focus":"phone_pending"}
    ],
    "The Delivery Is Five Minutes Away": [
        {"actor":"arjun","action":"checking_tracker","focus":"delivery_tracker"},
        {"actor":"arjun","action":"sitting","focus":"phone"},
        {"actor":"arjun","action":"watching_tracker","focus":"delivery_tracker"},
        {"actor":"arjun","action":"waiting","focus":"delivery_tracker"},
        {"actor":"arjun","action":"checking_tracker","focus":"delivery_tracker"},
        {"actor":"arjun","action":"staring_at_tracker","focus":"delivery_tracker"}
    ],
    "The Apartment Lift Stops at Every Floor": [
        {"actor":"arjun","action":"pressing_button","focus":"lift_panel"},
        {"actor":"byte","action":"door_closing","focus":"lift"},
        {"actor":"byte","action":"door_opening","focus":"lift"},
        {"actor":"arjun","action":"surprised","focus":"floor_display"},
        {"actor":"arjun","action":"waiting","focus":"lift"},
        {"actor":"arjun","action":"exasperated","focus":"floor_display"}
    ],
    "When the Power Goes Out During Your Presentation": [
        {"actor":"arjun","action":"presenting","focus":"projector"},
        {"actor":"byte","action":"power_off","focus":"dark_projector"},
        {"actor":"arjun","action":"panicking","focus":"dark_projector"},
        {"actor":"arjun","action":"presenting_from_memory","focus":"notes"},
        {"actor":"arjun","action":"embarrassed","focus":"notes"}
    ],
    "The Group Chat Before an Exam": [
        {"actor":"arjun","action":"studying","focus":"exam_notes"},
        {"actor":"byte","action":"sticker","focus":"chat"},
        {"actor":"arjun","action":"serious","focus":"exam_notes"},
        {"actor":"byte","action":"sticker","focus":"chat"},
        {"actor":"arjun","action":"asking","focus":"chat"},
        {"actor":"byte","action":"seen","focus":"chat"},
        {"actor":"arjun","action":"dry_smile","focus":"chat"}
    ],
    "When the Bus Arrives After You Stop Checking": [
        {"actor":"arjun","action":"waiting","focus":"bus_stop"},
        {"actor":"arjun","action":"checking_phone","focus":"phone"},
        {"actor":"byte","action":"bus_arrives","focus":"bus"},
        {"actor":"arjun","action":"running","focus":"bus"},
        {"actor":"byte","action":"bus_leaves","focus":"bus"},
        {"actor":"arjun","action":"stunned","focus":"bus_stop"}
    ],
    "The Shopping Cart You Abandoned": [
        {"actor":"arjun","action":"rejecting_purchase","focus":"cart"},
        {"actor":"byte","action":"notification","focus":"cart"},
        {"actor":"arjun","action":"checking_time","focus":"cart"},
        {"actor":"byte","action":"saved_item","focus":"cart"},
        {"actor":"arjun","action":"resigned","focus":"cart"},
        {"actor":"byte","action":"reminder","focus":"cart"},
        {"actor":"arjun","action":"exasperated","focus":"cart"}
    ],
    "The Alarm Clock Negotiation": [
        {"actor":"byte","action":"alarm_ringing","focus":"alarm"},
        {"actor":"arjun","action":"sleepy","focus":"bed"},
        {"actor":"byte","action":"keeping_record","focus":"record_book"},
        {"actor":"arjun","action":"negotiating","focus":"bed"},
        {"actor":"byte","action":"showing_record","focus":"record_book"},
        {"actor":"arjun","action":"pleading","focus":"bed"},
        {"actor":"byte","action":"showing_backup","focus":"backup_files"},
        {"actor":"arjun","action":"getting_up","focus":"bed"}
    ]
}

SCENARIOS = [
    {
        "title": "When the QR Payment Says 'Pending'",
        "theme": "everyday digital payments",
        "hook": "The payment said pending, so now everyone in the shop is emotionally invested.",
        "scenes": [
            "CUSTOMER: I paid. The screen says pending.",
            "CASHIER: Okay. We wait.",
            "CUSTOMER: How long?",
            "CASHIER: Usually a few seconds.",
            "CUSTOMER: It has been two minutes.",
            "CASHIER: Congratulations. We are now both refreshing the same screen."
        ],
        "nodes": ["CUSTOMER", "CASHIER", "PENDING"]
    },
    {
        "title": "The Delivery Is Five Minutes Away",
        "theme": "food delivery and waiting",
        "hook": "The delivery tracker said five minutes, which apparently means a small emotional journey.",
        "scenes": [
            "ME: The delivery is five minutes away.",
            "FRIEND: Great. Sit down.",
            "ME: I cannot. The tracker is moving.",
            "FRIEND: It has been five minutes.",
            "ME: Now it says four minutes.",
            "FRIEND: So the food is getting closer and time is getting farther away."
        ],
        "nodes": ["TRACKER", "ME", "FOOD"]
    },
    {
        "title": "The Apartment Lift Stops at Every Floor",
        "theme": "apartment life",
        "hook": "You enter the lift for one floor and suddenly become a tourist of the entire building.",
        "scenes": [
            "ME: I am going to the third floor.",
            "LIFT: Door closing.",
            "LIFT: Door opening.",
            "ME: We stopped at the second floor.",
            "NEIGHBOR: I need the fourth.",
            "ME: At this rate, I will visit every floor before lunch."
        ],
        "nodes": ["LIFT", "ME", "NEIGHBOR"]
    },
    {
        "title": "When the Power Goes Out During Your Presentation",
        "theme": "student and office life",
        "hook": "Nothing improves public speaking like losing the screen halfway through your presentation.",
        "scenes": [
            "ME: Good morning. Today I will explain the whole project.",
            "POWER: Off.",
            "ME: Okay. New presentation. I will explain the project from memory.",
            "FRIEND: You were reading the slides.",
            "ME: I know. This is now an advanced version."
        ],
        "nodes": ["PRESENTATION", "POWER", "PANIC"]
    },
    {
        "title": "The Group Chat Before an Exam",
        "theme": "student life",
        "hook": "The group chat becomes extremely active exactly when studying becomes urgent.",
        "scenes": [
            "STUDENT: Guys, exam tomorrow. We should study.",
            "CHAT: Sticker.",
            "STUDENT: Seriously.",
            "CHAT: Another sticker.",
            "STUDENT: Has anyone finished the syllabus?",
            "CHAT: Seen by 17 people.",
            "STUDENT: Excellent. We are all equally prepared."
        ],
        "nodes": ["STUDENT", "CHAT", "EXAM"]
    },
    {
        "title": "When the Bus Arrives After You Stop Checking",
        "theme": "commuting",
        "hook": "Public transport has a sixth sense for the exact moment you stop watching for it.",
        "scenes": [
            "ME: No bus yet.",
            "ME: I will check my phone for one second.",
            "BUS: Arrives.",
            "ME: Wait!",
            "BUS: Leaves.",
            "ME: Incredible. I looked away for one second and missed the entire plot."
        ],
        "nodes": ["BUS STOP", "PHONE", "BUS"]
    },
    {
        "title": "The Shopping Cart You Abandoned",
        "theme": "online shopping habits",
        "hook": "You leave one item in a shopping cart and the internet suddenly becomes very concerned.",
        "scenes": [
            "ME: I am not buying this today.",
            "PHONE: Your cart misses you.",
            "ME: It has been twenty minutes.",
            "PHONE: We saved your item.",
            "ME: I know.",
            "PHONE: It will also remind you again tomorrow.",
            "ME: Great. Even my cart has follow-up skills."
        ],
        "nodes": ["CART", "PHONE", "ME"]
    },
    {
        "title": "The Alarm Clock Negotiation",
        "theme": "morning routines",
        "hook": "My alarm clock has started keeping evidence against me.",
        "scenes": [
            "ALARM: Wake up. It is seven.",
            "ME: Five more minutes.",
            "ALARM: You said five minutes five minutes ago.",
            "ME: I am negotiating.",
            "ALARM: Yesterday you negotiated for forty minutes.",
            "ME: Please stop keeping records.",
            "ALARM: I have backups.",
            "ME: ...I am getting up."
        ],
        "nodes": ["ALARM", "BED", "PHONE", "MORNING"]
    }
]

today = datetime.now(timezone.utc).date().toordinal()
scenario = SCENARIOS[(today + 3) % len(SCENARIOS)]
script = scenario["scenes"]

payload = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "source": {
        "title": scenario["title"],
        "full_title": scenario["title"],
        "link": "",
        "description": f"Original fictional comedy sketch inspired by the everyday situation: {scenario['theme']}.",
        "domain": "ContentPilot Original",
        "image": ""
    },
    "score": 100,
    "hook": scenario["hook"],
    "script": script,
    "scene_plan": SCENE_PLANS.get(scenario["title"], []),
    "format": CFG["channel"],
    "candidates_considered": len(SCENARIOS),
    "visual_nodes": scenario["nodes"],
    "characters": {
        "primary": ["arjun", "byte"],
        "available": list(CHARACTERS.keys()),
        "registry": CHARACTERS
    },
    "background_urls": [],
    "genre": "comedy",
    "theme": scenario["theme"],
    "original": True,
    "story": {
        "hook": "Real-life relatable setup",
        "signal": "Ordinary everyday situation",
        "mechanism": "Original fictional escalation",
        "meaning": "Light observational comedy",
        "close": "Original punchline"
    }
}

json.dump(payload, open(os.path.join(OUT, "latest.json"), "w", encoding="utf-8"), indent=2)
with open(os.path.join(OUT, "latest.txt"), "w", encoding="utf-8") as handle:
    handle.write("\n\n".join(script))

print("Comedy sketch:", scenario["title"])
print("Theme:", scenario["theme"])
print("Scenes:", len(script))
