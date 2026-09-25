#!/usr/bin/env python3
import json, os, re, subprocess, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = json.load(open(os.path.join(ROOT, "generated/latest.json"), encoding="utf-8"))
build = os.path.join(ROOT, "build")
os.makedirs(build, exist_ok=True)

audio = os.path.join(build, "voice.wav")
video = os.path.join(ROOT, "generated", "contentpilot-latest.mp4")

# Fast, portable voice generation. The dialogue is intentionally conversational.
voice_text = " ... ".join(data["script"])
subprocess.run([
    "espeak-ng", "-v", "en-us", "-s", "154", "-p", "50",
    "-w", audio, voice_text
], check=True)

font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
regular = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
title = data["source"]["title"]
nodes = data.get("visual_nodes", ["YOU", "AI", "CHAOS"])
scripts = data["script"]
scene_count = len(scripts)

weights = [max(1, len(s.split())) for s in scripts]
total_words = sum(weights)
total_duration = max(28, min(48, total_words / 2.35))
starts, cursor = [], 0.0
for weight in weights:
    starts.append(cursor)
    cursor += total_duration * weight / total_words

def safe(text):
    return re.sub(r"[^A-Za-z0-9 .,:!?&'’()\-_/]", "", text).strip()

def wrap(text, width=27, max_lines=7):
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
    f.write(wrap(safe(title), 25, 4))

node_paths = []
for i, node in enumerate(nodes[:3]):
    p = os.path.join(build, f"node_{i}.txt")
    with open(p, "w", encoding="utf-8") as f:
        f.write(safe(node))
    node_paths.append(p)

filters = [
    "drawbox=x=0:y=0:w=iw:h=ih:color=0x080b14@1:t=fill",
    "drawbox=x=32:y=32:w=iw-64:h=ih-64:color=0x111827@1:t=fill",
    # Comic-style top frame.
    "drawbox=x=58:y=58:w=964:h=82:color=0x0a0f1d@0.94:t=fill",
    f"drawtext=fontfile={font}:text='CONTENTPILOT COMEDY':fontcolor=white@0.92:fontsize=28:x=78:y=82",
    f"drawtext=fontfile={regular}:text='ORIGINAL SHORT':fontcolor=white@0.45:fontsize=20:x=w-285:y=86",
    # Main visual stage.
    "drawbox=x=62:y=185:w=956:h=690:color=0x0b1325@1:t=fill",
    "drawbox=x=92:y=215:w=896:h=630:color=0x101b33@1:t=fill",
    # Three character/concept cards.
    "drawbox=x=105:y=315:w=250:h=300:color=0x17233c@1:t=fill",
    "drawbox=x=415:y=270:w=250:h=390:color=0x1b2946@1:t=fill",
    "drawbox=x=725:y=315:w=250:h=300:color=0x17233c@1:t=fill",
    "drawbox=x=355:y=450:w=60:h=8:color=white@0.35:t=fill",
    "drawbox=x=665:y=450:w=60:h=8:color=white@0.35:t=fill",
    f"drawtext=fontfile={font}:textfile='{node_paths[0] if len(node_paths)>0 else title_path}':fontcolor=white@0.88:fontsize=28:x=125:y=455",
    f"drawtext=fontfile={font}:textfile='{node_paths[1] if len(node_paths)>1 else title_path}':fontcolor=white@0.95:fontsize=28:x=435:y=455",
    f"drawtext=fontfile={font}:textfile='{node_paths[2] if len(node_paths)>2 else title_path}':fontcolor=white@0.88:fontsize=28:x=745:y=455",
    "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='SETUP  →  ESCALATION  →  PUNCHLINE':fontcolor=white@0.42:fontsize=19:x=250:y=705",
    # Title strip.
    "drawbox=x=100:y=760:w=880:h=80:color=0x05070d@0.92:t=fill",
    f"drawtext=fontfile={font}:textfile='{title_path}':fontcolor=white@0.82:fontsize=23:x=125:y=783",
]

for i, (text, start) in enumerate(zip(scripts, starts)):
    end = starts[i + 1] if i + 1 < scene_count else total_duration
    scene_file = os.path.join(build, f"scene_{i}.txt")
    # Active dialogue card.
    filters.append(
        f"drawbox=x=52:y=930:w=976:h=720:color=0x05070d@0.96:t=fill:"
        f"enable='between(t,{start:.2f},{end:.2f})'"
    )
    filters.append(
        f"drawtext=fontfile={font}:text='SCENE {i+1:02d}':fontcolor=white@0.58:fontsize=24:x=78:y=970:"
        f"enable='between(t,{start:.2f},{end:.2f})'"
    )
    filters.append(
        f"drawtext=fontfile={font}:textfile='{scene_file}':fontcolor=white:fontsize=43:"
        f"line_spacing=15:x=82:y=1045:enable='between(t,{start:.2f},{end:.2f})'"
    )
    # Little comic reaction bar.
    reaction = "SETUP" if i == 0 else ("ESCALATION" if i < scene_count - 1 else "PUNCHLINE")
    reaction_path = os.path.join(build, f"reaction_{i}.txt")
    with open(reaction_path, "w", encoding="utf-8") as f:
        f.write(reaction)
    filters.append(
        f"drawtext=fontfile={font}:textfile='{reaction_path}':fontcolor=white@0.45:fontsize=22:x=78:y=1515:"
        f"enable='between(t,{start:.2f},{end:.2f})'"
    )
    # Progress bar.
    filters.append(
        f"drawbox=x=58:y=h-80:w=(iw-116)*{(i+1)/scene_count:.3f}:h=7:color=white@0.82:t=fill:"
        f"enable='between(t,{start:.2f},{end:.2f})'"
    )
    filters.append(
        f"drawtext=fontfile={regular}:text='{i+1}/{scene_count}':fontcolor=white@0.45:fontsize=20:x=w-100:y=h-110:"
        f"enable='between(t,{start:.2f},{end:.2f})'"
    )

vf = ",".join(filters)
inputs = [
    "ffmpeg", "-y",
    "-f", "lavfi", "-i", "color=c=0b1020:s=1080x1920:r=30",
    "-i", audio
]

subprocess.run(inputs + [
    "-vf", vf,
    "-t", f"{total_duration:.2f}",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "25",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "128k",
    "-shortest", video
], check=True)

print(video)
