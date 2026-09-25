#!/usr/bin/env python3
import json, math, os, re, struct, subprocess, wave, zlib
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = json.load(open(os.path.join(ROOT, "generated/latest.json"), encoding="utf-8"))
build = os.path.join(ROOT, "build")
os.makedirs(build, exist_ok=True)
video = os.path.join(ROOT, "generated", "contentpilot-latest.mp4")
font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
regular = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

scripts = data["script"]
scene_count = len(scripts)

def safe(text):
    return re.sub(r"[^A-Za-z0-9 .,:!?&'’()\-_/]", "", text).strip()

def wrap(text, width=28, max_lines=4):
    words = text.split()
    lines, line = [], ""
    for word in words:
        cand = (line + " " + word).strip()
        if len(cand) <= width:
            line = cand
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return "\n".join(lines[:max_lines])

def run(cmd):
    subprocess.run(cmd, check=True)

def duration(path):
    out = subprocess.check_output([
        "ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=noprint_wrappers=1:nokey=1",path
    ], text=True).strip()
    return float(out)

# ---------- Original anime-inspired characters ----------
# Original procedural character designs. They are not based on an existing
# anime, film, game, manga, celebrity, or other copyrighted character.
def make_character(path, kind, mood):
    W, H = 520, 760
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im, "RGBA")

    def poly(points, fill, outline=None, width=1):
        d.polygon(points, fill=fill)
        if outline:
            d.line(points + [points[0]], fill=outline, width=width, joint="curve")

    def glow(cx, cy, r, color):
        layer = Image.new("RGBA", (W, H), (0,0,0,0))
        ld = ImageDraw.Draw(layer, "RGBA")
        for rr in range(r, 0, -10):
            alpha = int(color[3] * (1 - rr/r) * 0.18)
            ld.ellipse((cx-rr, cy-rr, cx+rr, cy+rr), fill=(*color[:3], max(0,alpha)))
        im.alpha_composite(layer.filter(ImageFilter.GaussianBlur(14)))

    if kind == "human":
        skin=(241,178,137,255); skin2=(211,137,105,255)
        hair=(38,25,38,255); hair_hi=(67,42,69,255)
        jacket=(44,62,92,255); shirt=(238,241,245,255)
        ink=(24,24,34,255); white=(255,255,255,255)

        poly([(85,760),(108,565),(178,515),(342,515),(412,565),(450,760)], jacket, ink, 5)
        poly([(178,525),(260,620),(342,525),(315,760),(205,760)], shirt, (70,78,92,255), 3)
        d.rounded_rectangle((214,455,306,555), 28, fill=skin, outline=skin2, width=4)
        d.ellipse((132,270,190,365), fill=skin, outline=skin2, width=4)
        d.ellipse((330,270,388,365), fill=skin, outline=skin2, width=4)
        d.ellipse((150,125,370,490), fill=skin, outline=ink, width=5)
        poly([(145,250),(125,190),(153,170),(132,122),(190,138),(181,78),
              (232,105),(260,52),(281,105),(336,70),(327,132),(382,112),
              (360,188),(372,255),(335,220),(310,155),(267,178),(226,148),
              (190,205)], hair, ink, 5)
        poly([(166,169),(188,105),(215,135),(260,82),(288,126),(335,102),(317,160),
              (275,142),(238,165),(201,145)], hair_hi)
        d.arc((183,255,236,292), 190, 350, fill=ink, width=8)
        d.arc((282,255,335,292), 190, 350, fill=ink, width=8)
        for box, iris in [((180,275,241,345),(58,112,176,255)),((279,275,340,345),(58,112,176,255))]:
            d.ellipse(box, fill=white, outline=ink, width=5)
            x=(box[0]+box[2])//2; y=(box[1]+box[3])//2+4
            d.ellipse((x-18,y-22,x+18,y+25), fill=iris, outline=ink, width=3)
            d.ellipse((x-7,y-18,x+7,y+18), fill=(20,28,55,255))
            d.ellipse((x-10,y-15,x-2,y-7), fill=white)
        d.line((258,330,250,380,270,382), fill=skin2, width=5)
        if mood=="shocked":
            d.ellipse((242,400,278,445), fill=(115,45,55,255), outline=ink, width=4)
        elif mood=="talk":
            d.ellipse((238,398,282,438), fill=(95,38,48,255), outline=ink, width=3)
        elif mood=="happy":
            d.arc((225,390,295,450), 10, 170, fill=(120,42,55,255), width=8)
        else:
            d.arc((230,395,290,435), 15, 165, fill=(120,42,55,255), width=6)
        d.line((112,590,45,675), fill=jacket, width=45)
        d.line((405,590,475,650), fill=jacket, width=45)
        d.ellipse((22,650,78,704), fill=skin, outline=skin2, width=4)
        d.ellipse((448,628,500,682), fill=skin, outline=skin2, width=4)

    else:
        skin=(174,228,242,255); skin2=(72,174,204,255)
        hair=(22,74,110,255); hair_hi=(50,154,190,255)
        suit=(19,126,157,255); suit2=(33,190,205,255)
        ink=(8,28,42,255); white=(239,255,255,255)
        glow(260,330,230,(32,205,235,150))
        poly([(88,760),(115,570),(188,510),(332,510),(405,570),(438,760)], suit, ink, 5)
        poly([(190,520),(260,610),(330,520),(310,760),(210,760)], suit2, (95,236,240,255), 3)
        d.rounded_rectangle((215,455,305,550), 28, fill=skin, outline=skin2, width=4)
        d.ellipse((142,112,378,490), fill=skin, outline=ink, width=5)
        poly([(138,245),(124,178),(155,152),(136,103),(193,124),(182,62),
              (232,96),(265,42),(286,102),(343,62),(330,127),(391,105),
              (366,180),(380,252),(338,218),(310,145),(270,175),(226,142),
              (188,202)], hair, ink, 5)
        poly([(158,165),(190,91),(218,124),(262,78),(291,121),(342,92),(320,150),
              (278,136),(236,159),(198,139)], hair_hi)
        d.line((190,190,225,175,248,193), fill=(142,248,255,210), width=4)
        d.line((296,190,320,175), fill=(142,248,255,210), width=4)
        for box in [(175,270,242,347),(278,270,345,347)]:
            d.ellipse(box, fill=(8,45,62,255), outline=ink, width=5)
            x=(box[0]+box[2])//2; y=(box[1]+box[3])//2
            d.ellipse((x-17,y-23,x+17,y+23), fill=(64,235,245,255))
            d.ellipse((x-6,y-20,x+7,y+20), fill=(3,34,52,255))
            d.ellipse((x-10,y-16,x-2,y-8), fill=white)
        d.line((257,330,250,380,270,382), fill=skin2, width=5)
        if mood=="shocked":
            d.ellipse((240,398,280,448), fill=(5,38,54,255), outline=ink, width=4)
        elif mood=="talk":
            d.ellipse((237,397,283,441), fill=(4,42,58,255), outline=ink, width=3)
        elif mood=="happy":
            d.arc((225,390,295,450), 10, 170, fill=(5,55,70,255), width=8)
        else:
            d.arc((230,395,290,435), 15, 165, fill=(5,55,70,255), width=6)
        d.line((112,590,45,675), fill=suit2, width=45)
        d.line((405,590,475,650), fill=suit2, width=45)
        d.ellipse((20,650,80,710), fill=skin, outline=skin2, width=4)
        d.ellipse((445,628,505,688), fill=skin, outline=skin2, width=4)
        for y in range(180,735,42):
            d.line((120,y,400,y), fill=(190,255,255,32), width=2)

    im.save(path, "PNG")

human=os.path.join(build,"character-human.png")
human_shock=os.path.join(build,"character-human-shock.png")
robot=os.path.join(build,"character-ai.png")
robot_happy=os.path.join(build,"character-ai-happy.png")
human_talk=os.path.join(build,"character-human-talk.png")
robot_talk=os.path.join(build,"character-ai-talk.png")
make_character(human,"human","neutral")
make_character(human_shock,"human","shocked")
make_character(human_talk,"human","talk")
make_character(robot,"robot","neutral")
make_character(robot_happy,"robot","happy")
make_character(robot_talk,"robot","talk")

# ---------- Procedural comedy audio ----------
def music_wav(path, seconds, style):
    sr=44100; n=int(seconds*sr); buf=[0.0]*n
    scales={
        "playful":[523.25,659.25,783.99,659.25],
        "curious":[392.0,466.16,587.33,523.25],
        "tension":[220.0,233.08,261.63,233.08],
        "chaos":[330.0,392.0,311.13,466.16],
        "punchline":[659.25,783.99,987.77,1046.5]
    }
    notes=scales.get(style,scales["playful"]); beat=0.28
    for k in range(int(seconds/beat)+1):
        f=notes[k%len(notes)]
        start=int(k*beat*sr)
        length=min(int(beat*0.72*sr),n-start)
        for j in range(max(0,length)):
            t=j/sr
            env=min(1,t*35,max(0,(length/sr-t)*9))
            val=0.09*env*math.sin(2*math.pi*f*t)+0.045*env*math.sin(2*math.pi*(f/2)*t)
            if 0<=start+j<n: buf[start+j]+=val
    with wave.open(path,"wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<h",max(-32767,min(32767,int(v*32767)))) for v in buf))

def sfx_wav(path, seconds, scene):
    sr=44100; n=int(seconds*sr); buf=[0.0]*n
    events=[("pop",0.0),("whoosh",max(0.18,seconds*0.55))]
    if scene in (1,3): events=[("ding",0.0),("error",max(0.20,seconds*0.55))]
    if scene==5: events=[("pop",0.0),("ding",max(0.18,seconds*0.55))]
    for typ,at in events:
        st=int(at*sr); length=max(1,int(min(0.42,seconds-at)*sr))
        for j in range(length):
            t=j/sr; env=min(1,t*80,max(0,(length/sr-t)*12))
            if typ=="pop": v=math.sin(2*math.pi*(180+700*t)*t)*0.25*env
            elif typ=="whoosh": v=math.sin(2*math.pi*(180+1800*t)*t)*0.12*env
            elif typ=="error": v=(math.sin(2*math.pi*95*t)+0.5*math.sin(2*math.pi*140*t))*0.18*env
            else: v=math.sin(2*math.pi*(900+900*t)*t)*0.20*env
            if st+j<n: buf[st+j]+=v
    with wave.open(path,"wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<h",max(-32767,min(32767,int(v*32767)))) for v in buf))

styles=["playful","curious","tension","chaos","punchline","playful"]
segments=[]
background_url = data.get("background_urls", [""])[0] if data.get("background_urls") else ""
background = os.path.join(build, "real-world-background.mp4")
if background_url:
    run(["curl", "-L", "--fail", "--retry", "3", "-o", background, background_url])
    print("Using real-world background:", background_url)

for i,text_line in enumerate(scripts):
    # One voice file per scene prevents dialogue from being cut at estimated boundaries.
    voice=os.path.join(build,f"voice_{i}.wav")
    spoken=safe(text_line).replace(":", ": ")
    run(["espeak-ng","-v","en-us","-s","158","-p","50","-w",voice,spoken])
    voice_dur=duration(voice)
    dur=max(3.2,min(7.0,voice_dur+0.65))
    scene_txt=os.path.join(build,f"scene_{i}.txt")
    open(scene_txt,"w",encoding="utf-8").write(wrap(safe(text_line)))

    music=os.path.join(build,f"music_{i}.wav")
    sfx=os.path.join(build,f"sfx_{i}.wav")
    music_wav(music,dur,styles[i%len(styles)])
    sfx_wav(sfx,dur,i)

    seg=os.path.join(build,f"segment_{i}.mp4")
    h=human_shock if i in (2,4,5) else human_talk
    r=robot_happy if i in (1,3,5) else robot_talk

    # Designed animated comic environment instead of unrelated stock footage.
    # Each scene gets a different visual motif, while the characters stay consistent.
    if i % 3 == 0:
        bg="0f172a"
        motif=(
            "drawbox=x=0:y=0:w=1080:h=1920:color=0f172a:t=fill,"
            "drawbox=x=70:y=260:w=940:h=620:color=16213a:t=fill,"
            "drawbox=x=125:y=700:w=830:h=30:color=38bdf8:t=fill,"
            "drawbox=x=300:y=545:w=480:h=250:color=0b1220:t=fill,"
            "drawbox=x=345:y=585:w=390:h=170:color=1e293b:t=fill,"
            "drawbox=x=420:y=470:w=240:h=90:color=1e293b:t=fill"
        )
    elif i % 3 == 1:
        bg="111827"
        motif=(
            "drawbox=x=0:y=0:w=1080:h=1920:color=111827:t=fill,"
            "drawbox=x=65:y=270:w=950:h=520:color=1f2937:t=fill,"
            "drawbox=x=120:y=335:w=840:h=90:color=0b1220:t=fill,"
            "drawbox=x=120:y=455:w=840:h=65:color=273449:t=fill,"
            "drawbox=x=120:y=555:w=620:h=65:color=273449:t=fill,"
            "drawbox=x=120:y=655:w=720:h=65:color=273449:t=fill"
        )
    else:
        bg="172033"
        motif=(
            "drawbox=x=0:y=0:w=1080:h=1920:color=172033:t=fill,"
            "drawbox=x=65:y=250:w=950:h=650:color=21304a:t=fill,"
            "drawbox=x=110:y=300:w=860:h=95:color=0b1220:t=fill,"
            "drawbox=x=110:y=440:w=860:h=110:color=334766:t=fill,"
            "drawbox=x=110:y=600:w=690:h=110:color=334766:t=fill,"
            "drawbox=x=110:y=760:w=800:h=110:color=334766:t=fill"
        )

    # Clean short-form presentation: no dialogue panel.
    # Characters and environment stay visually dominant; dialogue is shown as
    # compact bottom subtitles with a subtle translucent background for readability.
    subtitle_style = (
        f"drawbox=x=55:y=1600:w=970:h=210:color=000000@0.62:t=fill,"
        f"drawtext=fontfile={font}:text='SCENE {i+1}':fontcolor=38bdf8:fontsize=20:x=78:y=1622,"
        f"drawtext=fontfile={font}:textfile='{scene_txt}':fontcolor=white:fontsize=38:line_spacing=10:x=78:y=1660,"
        f"drawtext=fontfile={regular}:text='ContentPilot Original':fontcolor=white@0.35:fontsize=15:x=78:y=1850"
    )

    fc=(
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=1.0:1[base];"
        f"[base]eq=brightness=-0.05:saturation=0.95[m];"
        f"[1:v]scale=270:375[h];"
        f"[2:v]scale=270:375[r];"
        f"[m][h]overlay=x='55+8*sin(t*3)':y='710+6*sin(t*6)':enable='between(t,0,{dur:.2f})'[c1];"
        f"[c1][r]overlay=x='595+8*sin(t*3+1)':y='660+6*sin(t*6+1)':enable='between(t,0,{dur:.2f})'[c2];"
        f"[c2]{subtitle_style}[v];"
        f"[3:a]apad,atrim=duration={dur:.2f},asetpts=PTS-STARTPTS[voice];"
        f"[4:a]apad,atrim=duration={dur:.2f},asetpts=PTS-STARTPTS[music];"
        f"[5:a]apad,atrim=duration={dur:.2f},asetpts=PTS-STARTPTS[sfx];"
        f"[voice][music][sfx]amix=inputs=3:duration=longest:weights='1 0.16 0.28':normalize=0,"
        f"alimiter=limit=0.92[a]"
    )


    cmd=[
        "ffmpeg","-y","-stream_loop","-1","-i",background,
        "-i",h,"-i",r,"-i",voice,"-i",music,"-i",sfx,
        "-filter_complex",fc,"-map","[v]","-map","[a]","-t",f"{dur:.2f}",
        "-r","30","-c:v","libx264","-preset","veryfast","-crf","24","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","128k",seg
    ]
    run(cmd)
    segments.append(seg)

concat=os.path.join(build,"concat.txt")
with open(concat,"w",encoding="utf-8") as f:
    for seg in segments:
        f.write("file '"+seg.replace("'","'\\''")+"'\n")

run(["ffmpeg","-y","-f","concat","-safe","0","-i",concat,"-c","copy",video])
print("Rendered:",video)
print("Duration:",duration(video))
