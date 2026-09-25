#!/usr/bin/env python3
import json, os, subprocess, textwrap

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = json.load(open(os.path.join(ROOT, "generated/latest.json"), encoding="utf-8"))
build = os.path.join(ROOT, "build")
os.makedirs(build, exist_ok=True)

audio = os.path.join(build, "voice.wav")
video = os.path.join(ROOT, "generated", "contentpilot-latest.mp4")
subtitle = os.path.join(build, "caption.txt")

# One deterministic, free voice. This can later be replaced by a better local TTS engine.
voice_text = " ".join(data["script"])
subprocess.run(["espeak-ng", "-v", "en-us", "-s", "155", "-p", "45", "-w", audio, voice_text], check=True)

# FFmpeg text layout: title + compact body. The output is native vertical 1080x1920.
title = data["source"]["title"].replace("'", "’")
lines = "\n".join(textwrap.wrap(title, width=27))
open(subtitle, "w", encoding="utf-8").write(lines)

duration = max(12, min(58, 5 + len(voice_text) / 14))
font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

vf = (
    f"drawtext=fontfile={font}:text='CONTENTPILOT':"
    "fontcolor=white@0.65:fontsize=34:x=55:y=55,"
    f"drawtext=fontfile={font}:textfile={subtitle}:"
    "fontcolor=white:fontsize=66:line_spacing=18:"
    "x=(w-text_w)/2:y=(h-text_h)/2:"
    "box=1:boxcolor=black@0.62:boxborderw=55,"
    f"drawtext=fontfile={font}:text='Practical tech discovery':"
    "fontcolor=white@0.70:fontsize=30:x=55:y=h-90"
)

subprocess.run([
    "ffmpeg", "-y",
    "-f", "lavfi", "-i", "color=c=0b1020:s=1080x1920:r=30",
    "-i", audio,
    "-vf", vf,
    "-t", str(duration),
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "27",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "128k",
    "-shortest", video
], check=True)

print(video)
