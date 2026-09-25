#!/usr/bin/env python3
import json, os, re, subprocess, urllib.request
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = json.load(open(os.path.join(ROOT, "generated/latest.json"), encoding="utf-8"))
build = os.path.join(ROOT, "build")
os.makedirs(build, exist_ok=True)

audio = os.path.join(build, "voice.wav")
video = os.path.join(ROOT, "generated", "contentpilot-latest.mp4")
image = os.path.join(build, "source.jpg")

voice_text = " ... ".join(data["script"])
subprocess.run([
    "espeak-ng", "-v", "en-us", "-s", "148", "-p", "42",
    "-w", audio, voice_text
], check=True)

source_image = data.get("source", {}).get("image", "")
has_image = False
if source_image:
    try:
        req = urllib.request.Request(source_image, headers={"User-Agent": "ContentPilot/1.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            raw = response.read()
        if len(raw) > 5000:
            open(image, "wb").write(raw)
            has_image = True
    except Exception as exc:
        print(f"source image unavailable: {exc}")

font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
regular = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
title = data["source"]["title"]
domain = data.get("source", {}).get("domain", "public source")
scripts = data["script"]

# Keep each scene readable while letting the narration drive the timing.
weights = [max(1, len(s.split())) for s in scripts]
total_words = sum(weights)
total_duration = max(28, min(52, total_words / 2.15))
starts, cursor = [], 0.0
for weight in weights:
    starts.append(cursor)
    cursor += total_duration * weight / total_words

def safe(text):
    return re.sub(r"[^A-Za-z0-9 .,:!?&'’()\-_/]", "", text).strip()

def wrap(text, width=28, max_lines=7):
    words = text.split()
    lines, line = [], ""
    for word in words:
        candidate = (line + " " + word).strip()
        if len(candidate) <= width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return "\n".join(lines[:max_lines])

for i, text in enumerate(scripts):
    with open(os.path.join(build, f"scene_{i}.txt"), "w", encoding="utf-8") as f:
        f.write(wrap(safe(text)))

title_path = os.path.join(build, "title.txt")
with open(title_path, "w", encoding="utf-8") as f:
    f.write(wrap(safe(title), 24, 5))

domain_path = os.path.join(build, "domain.txt")
with open(domain_path, "w", encoding="utf-8") as f:
    f.write(domain.upper())

# A clean editorial system: moving background, source visual, kinetic cards,
# progress bar, scene labels and high-contrast captions.
filters = [
    "drawbox=x=0:y=0:w=iw:h=ih:color=0x070b16@1:t=fill",
    "drawbox=x=35:y=35:w=iw-70:h=ih-70:color=0x111827@1:t=fill",
    f"drawtext=fontfile={font}:text='CONTENTPILOT':fontcolor=white@0.70:fontsize=30:x=58:y=58",
    f"drawtext=fontfile={regular}:textfile='{domain_path}':fontcolor=white@0.50:fontsize=23:x=w-340:y=63",
]

if has_image:
    # The image occupies the visual canvas; the text layer remains readable.
    filters.insert(0, f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=8:1")
    filters.append(f"drawbox=x=0:y=0:w=iw:h=ih:color=0x000000@0.42:t=fill")
else:
    # Fallback visual: an abstract AI/network motif made entirely in FFmpeg.
    filters.extend([
        "drawbox=x=90:y=500:w=900:h=620:color=0x101a33@1:t=fill",
        "drawbox=x=150:y=610:w=220:h=130:color=0x182a4a@1:t=fill",
        "drawbox=x=430:y=790:w=220:h=130:color=0x182a4a@1:t=fill",
        "drawbox=x=710:y=610:w=220:h=130:color=0x182a4a@1:t=fill",
        "drawbox=x=430:y=470:w=220:h=130:color=0x243b63@1:t=fill",
        "drawbox=x=370:y=665:w=60:h=5:color=white@0.28:t=fill",
        "drawbox=x=537:y=600:w=6:h=190:color=white@0.28:t=fill",
        "drawbox=x=650:y=850:w=65:h=5:color=white@0.28:t=fill",
    ])

labels = ["HOOK", "THE SIGNAL", "THE INTERESTING PART", "WHY IT MATTERS", "TAKEAWAY"]

for i, (text, start) in enumerate(zip(scripts, starts)):
    end = starts[i + 1] if i + 1 < len(starts) else total_duration
    textfile = os.path.join(build, f"scene_{i}.txt")
    filters.append(
        f"drawbox=x=52:y=285:w=976:h=1320:color=0x05070d@0.50:t=fill:"
        f"enable='between(t,{start:.2f},{end:.2f})'"
    )
    filters.append(
        f"drawtext=fontfile={font}:text='{labels[i]}':fontcolor=white@0.62:fontsize=27:x=78:y=330:"
        f"enable='between(t,{start:.2f},{end:.2f})'"
    )
    filters.append(
        f"drawtext=fontfile={font}:textfile='{textfile}':fontcolor=white:fontsize=55:"
        f"line_spacing=15:x=82:y=520:enable='between(t,{start:.2f},{end:.2f})'"
    )
    # Large active-scene progress indicator.
    filters.append(
        f"drawbox=x=58:y=h-92:w=(iw-116)*{(i+1)/len(scripts):.3f}:h=8:color=white@0.85:t=fill:"
        f"enable='between(t,{start:.2f},{end:.2f})'"
    )
    filters.append(
        f"drawtext=fontfile={regular}:text='{i+1}/5':fontcolor=white@0.55:fontsize=22:x=w-115:y=h-125:"
        f"enable='between(t,{start:.2f},{end:.2f})'"
    )

# End-card source credit.
filters.append(
    f"drawtext=fontfile={regular}:text='SOURCE: {safe(domain)}':fontcolor=white@0.55:fontsize=20:x=58:y=h-55"
)

vf = ",".join(filters)
inputs = ["ffmpeg", "-y"]
if has_image:
    inputs += ["-loop", "1", "-i", image]
else:
    inputs += ["-f", "lavfi", "-i", "color=c=0b1020:s=1080x1920:r=30"]
inputs += ["-i", audio]

subprocess.run(inputs + [
    "-vf", vf, "-t", f"{total_duration:.2f}",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "25",
    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
    "-shortest", video
], check=True)

print(video)
