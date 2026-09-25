#!/usr/bin/env python3
import json, os, re, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = json.load(open(os.path.join(ROOT, "generated/latest.json"), encoding="utf-8"))
build = os.path.join(ROOT, "build")
os.makedirs(build, exist_ok=True)

audio = os.path.join(build, "voice.wav")
video = os.path.join(ROOT, "generated", "contentpilot-latest.mp4")
voice_text = " ".join(data["script"])

subprocess.run([
    "espeak-ng", "-v", "en-us", "-s", "150", "-p", "45",
    "-w", audio, voice_text
], check=True)

font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
regular = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def esc(text):
    return text.replace("\\", "\\\\").replace(":", "\:").replace("'", "\\'")

def wrap(text, width=28):
    words = text.split()
    lines, line = [], ""
    for word in words:
        if len(line) + len(word) + 1 <= width:
            line = (line + " " + word).strip()
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return "\\n".join(lines[:7])

# Estimate each scene's time from its spoken word count.
scripts = data["script"]
weights = [max(1, len(s.split())) for s in scripts]
total = sum(weights)
total_duration = max(18, min(58, total / 2.35))
starts = []
cursor = 0.0
for weight in weights:
    starts.append(cursor)
    cursor += total_duration * weight / total

filters = [
    "drawbox=x=0:y=0:w=iw:h=ih:color=0x0b1020@1:t=fill",
    f"drawtext=fontfile={font}:text='CONTENTPILOT':fontcolor=white@0.55:fontsize=32:x=55:y=55",
    f"drawtext=fontfile={font}:text='TECH SIGNAL / {data.get('score', 0)}':fontcolor=white@0.50:fontsize=26:x=w-340:y=58"
]

labels = ["HOOK", "SOURCE", "SOURCE DETAIL", "TAKEAWAY", "FOLLOW"]
for i, (text, start) in enumerate(zip(scripts, starts)):
    end = starts[i + 1] if i + 1 < len(starts) else total_duration
    filters.append(
        f"drawtext=fontfile={font}:text='{labels[i]}':"
        f"fontcolor=white@0.62:fontsize=28:x=55:y=260:"
        f"enable='between(t,{start:.2f},{end:.2f})'"
    )
    filters.append(
        f"drawtext=fontfile={font}:text='{esc(wrap(text))}':"
        f"fontcolor=white:fontsize=58:line_spacing=16:"
        f"x=70:y=(h-text_h)/2:box=1:boxcolor=black@0.48:boxborderw=42:"
        f"enable='between(t,{start:.2f},{end:.2f})'"
    )
    progress = int(((i + 1) / len(scripts)) * 100)
    filters.append(
        f"drawtext=fontfile={regular}:text='{progress}%':"
        f"fontcolor=white@0.55:fontsize=25:x=55:y=h-115:"
        f"enable='between(t,{start:.2f},{end:.2f})'"
    )

vf = ",".join(filters)
subprocess.run([
    "ffmpeg", "-y",
    "-f", "lavfi", "-i", "color=c=0b1020:s=1080x1920:r=30",
    "-i", audio,
    "-vf", vf,
    "-t", f"{total_duration:.2f}",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "27",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "128k",
    "-shortest", video
], check=True)

print(video)
