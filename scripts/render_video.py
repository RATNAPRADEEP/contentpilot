#!/usr/bin/env python3
import json, os, subprocess, textwrap, math

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data=json.load(open(os.path.join(ROOT,"generated/latest.json"),encoding="utf-8"))
build=os.path.join(ROOT,"build"); os.makedirs(build,exist_ok=True)
audio=os.path.join(build,"voice.wav")
video=os.path.join(ROOT,"generated","contentpilot-latest.mp4")

text=" ".join(data["script"])
# espeak-ng is installed by the workflow; it keeps the MVP free.
subprocess.run(["espeak-ng","-w",audio,text],check=True)

# 1080x1920 vertical video. Text-only slides are intentional for the first MVP:
# they are deterministic, fast and can be replaced by richer renderers later.
duration=max(12, min(55, 4 + len(text)/14))
font="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
draw=(
    "drawtext=fontfile="+font+
    ":textfile="+os.path.join(ROOT,"generated","latest.txt")+
    ":fontcolor=white:fontsize=62:line_spacing=18:"+
    "x=(w-text_w)/2:y=(h-text_h)/2:"
    "box=1:boxcolor=black@0.65:boxborderw=45"
)
subprocess.run([
    "ffmpeg","-y","-f","lavfi","-i",
    "color=c=0x111827:s=1080x1920:r=30",
    "-i",audio,
    "-vf",draw,
    "-t",str(duration),
    "-c:v","libx264","-pix_fmt","yuv420p",
    "-c:a","aac","-shortest",video
],check=True)
print(video)
