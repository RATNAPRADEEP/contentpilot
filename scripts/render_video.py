#!/usr/bin/env python3
import json, math, os, re, struct, subprocess, wave, zlib
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = json.load(open(os.path.join(ROOT, "generated/latest.json"), encoding="utf-8"))
theme = data.get("theme", "").lower()
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
def make_character(path, kind, mood, step=0):
    W, H = 520, 1050
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

    if kind in ("human", "maya"):
        skin=(241,178,137,255); skin2=(211,137,105,255)
        hair=(38,25,38,255); hair_hi=(67,42,69,255)
        jacket=(44,62,92,255); shirt=(238,241,245,255)
        ink=(24,24,34,255); white=(255,255,255,255)
        if kind == "maya":
            hair=(72,35,74,255); hair_hi=(120,65,122,255)
            jacket=(86,54,88,255); shirt=(250,236,245,255)

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
        if step == 0:
            d.line((112,590,52,675), fill=jacket, width=45)
            d.line((405,590,472,655), fill=jacket, width=45)
            d.ellipse((25,652,82,708), fill=skin, outline=skin2, width=4)
            d.ellipse((445,633,502,689), fill=skin, outline=skin2, width=4)
            left_leg=(205,755,175,1000); right_leg=(315,755,350,1000)
        else:
            d.line((112,590,68,645), fill=jacket, width=45)
            d.line((405,590,448,675), fill=jacket, width=45)
            d.ellipse((40,620,95,675), fill=skin, outline=skin2, width=4)
            d.ellipse((420,652,478,708), fill=skin, outline=skin2, width=4)
            left_leg=(205,755,235,1000); right_leg=(315,755,285,1000)
        d.line([left_leg[:2], left_leg[2:]], fill=jacket, width=58)
        d.line([right_leg[:2], right_leg[2:]], fill=jacket, width=58)
        d.ellipse((145 if step==0 else 205,980,215 if step==0 else 270,1030), fill=(28,30,42,255))
        d.ellipse((325 if step==0 else 260,980,395 if step==0 else 330,1030), fill=(28,30,42,255))

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
        if step == 0:
            d.line((112,590,45,675), fill=suit2, width=45)
            d.line((405,590,475,650), fill=suit2, width=45)
            d.ellipse((20,650,80,710), fill=skin, outline=skin2, width=4)
            d.ellipse((445,628,505,688), fill=skin, outline=skin2, width=4)
            left_leg=(210,755,180,1000); right_leg=(310,755,345,1000)
        else:
            d.line((112,590,70,645), fill=suit2, width=45)
            d.line((405,590,450,675), fill=suit2, width=45)
            d.ellipse((42,620,98,675), fill=skin, outline=skin2, width=4)
            d.ellipse((420,652,480,708), fill=skin, outline=skin2, width=4)
            left_leg=(210,755,235,1000); right_leg=(310,755,285,1000)
        d.line([left_leg[:2], left_leg[2:]], fill=suit2, width=58)
        d.line([right_leg[:2], right_leg[2:]], fill=suit2, width=58)
        d.ellipse((150 if step==0 else 205,980,220 if step==0 else 270,1030), fill=(5,38,54,255))
        d.ellipse((320 if step==0 else 260,980,390 if step==0 else 330,1030), fill=(5,38,54,255))
        for y in range(180,735,42):
            d.line((120,y,400,y), fill=(190,255,255,32), width=2)

    im.save(path, "PNG")

human=os.path.join(build,"character-human.png")
human_shock=os.path.join(build,"character-human-shock.png")
robot=os.path.join(build,"character-ai.png")
robot_happy=os.path.join(build,"character-ai-happy.png")
human_talk=os.path.join(build,"character-arjun-talk-a.png")
human_talk_b=os.path.join(build,"character-arjun-talk-b.png")
robot_talk=os.path.join(build,"character-maya-talk-a.png")
robot_talk_b=os.path.join(build,"character-maya-talk-b.png")
make_character(human,"human","neutral",0)
make_character(human_shock,"human","shocked",1)
make_character(human_talk,"human","talk",0)
make_character(human_talk_b,"human","talk",1)
make_character(robot,"robot","neutral",0)
make_character(robot_happy,"robot","happy",1)
make_character(robot_talk,"robot","talk",0)
make_character(robot_talk_b,"robot","talk",1)


def make_scene_background(path, theme, scene_index):
    """Create an original illustrated environment locally; no stock footage."""
    W, H = 1080, 1920
    im = Image.new("RGB", (W, H), (18, 24, 40))
    d = ImageDraw.Draw(im)

    if "morning" in theme:
        for y in range(0, 1250):
            t = y / 1250
            c = (int(35-10*t), int(50-12*t), int(75-18*t))
            d.line((0, y, W, y), fill=c)
        d.rounded_rectangle((100,170,520,650),24,fill=(24,33,53),outline=(74,90,118),width=8)
        d.rectangle((125,195,495,625),fill=(119,157,190))
        d.ellipse((250,270,390,410),fill=(246,190,91))
        d.polygon([(65,135),(205,145),(185,650),(80,700)],fill=(66,47,73))
        d.polygon([(555,145),(695,135),(670,700),(570,650)],fill=(66,47,73))
        for y in range(1250,H):
            d.line((0,y,W,y),fill=(112,78,70))
        d.rounded_rectangle((120,1370,960,1810),40,fill=(113,77,84),outline=(145,102,106),width=6)
        d.rounded_rectangle((150,760,930,1110),35,fill=(50,45,57),outline=(91,82,99),width=8)
        d.rounded_rectangle((115,930,965,1230),35,fill=(198,198,203),outline=(130,130,140),width=6)
        d.rounded_rectangle((250,1000,930,1240),30,fill=(92,74,105))
        d.rounded_rectangle((175,965,410,1080),25,fill=(232,229,222),outline=(180,178,176),width=5)
        d.rounded_rectangle((700,680,930,880),18,fill=(92,63,55),outline=(125,89,72),width=7)
        d.rectangle((730,875,760,1010),fill=(72,48,43))
        d.rectangle((870,875,900,1010),fill=(72,48,43))
        d.rectangle((800,565,825,690),fill=(61,48,48))
        d.polygon([(740,565),(885,565),(850,475),(775,475)],fill=(236,192,108),outline=(130,96,58))
        d.rounded_rectangle((755,710,875,775),12,fill=(22,27,34),outline=(245,196,72),width=5)
        d.text((786,726),"07:00",fill=(245,196,72))
        d.rounded_rectangle((480,1210,590,1265),12,fill=(28,32,40),outline=(150,160,180),width=4)
        for box in [(780,220,900,350),(620,250,700,330)]:
            d.rounded_rectangle(box,12,fill=(53,67,92),outline=(99,115,140),width=4)
        for x,y in [(1000,780),(980,740),(1030,720)]:
            d.ellipse((x-28,y-80,x+28,y),fill=(56,112,76))
        d.rectangle((980,800,1040,900),fill=(134,91,66))
    else:
        for y in range(H):
            t = y / H
            d.line((0,y,W,y),fill=(int(18+20*t),int(25+18*t),int(42+20*t)))
        d.rounded_rectangle((70,180,1010,880),30,fill=(35,48,70),outline=(80,100,125),width=6)
        d.rounded_rectangle((120,260,960,760),25,fill=(14,22,38))
        d.rounded_rectangle((90,900,990,1260),35,fill=(74,61,78),outline=(110,90,105),width=6)
        d.rounded_rectangle((120,1320,960,1810),40,fill=(45,55,70),outline=(75,88,105),width=6)
    im.save(path, "PNG")

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

for i,text_line in enumerate(scripts):
    # One voice file per scene prevents dialogue from being cut at estimated boundaries.
    voice=os.path.join(build,f"voice_{i}.wav")
    spoken=safe(text_line).replace(":", ": ")
    run(["espeak-ng","-v","en-us","-s","158","-p","50","-w",voice,spoken])
    voice_dur=duration(voice)
    dur=max(3.2,min(7.0,voice_dur+0.65))
    scene_txt=os.path.join(build,f"scene_{i}.txt")
    raw = safe(text_line)
    speaker, _, words = raw.partition(":")
    ai_speakers = {"CHAT", "ALARM", "PHONE", "POWER", "LIFT"}
    speaker_name = "Byte" if speaker in ai_speakers else "Arjun"
    speaker_key = "byte" if speaker_name == "Byte" else "arjun"
    subtitle = f"{speaker_name}: {words.strip()}" if words.strip() else speaker_name
    open(scene_txt,"w",encoding="utf-8").write(wrap(subtitle, width=32, max_lines=2))

    background=os.path.join(build,f"background_{i}.png")
    make_scene_background(background, theme, i)

    music=os.path.join(build,f"music_{i}.wav")
    sfx=os.path.join(build,f"sfx_{i}.wav")
    music_wav(music,dur,styles[i%len(styles)])
    sfx_wav(sfx,dur,i)

    seg=os.path.join(build,f"segment_{i}.mp4")
    h=human_shock if i in (2,4,5) else human_talk
    r=robot_happy if i in (1,3,5) else robot_talk

    # Animated, scene-specific illustrated backgrounds.
    # Everything is generated locally with FFmpeg; no stock footage is used.
    if "morning" in theme:
        bg="0b1020"
        motif=(
            "drawbox=x=0:y=0:w=1080:h=1920:color=0b1020:t=fill,"
            "drawbox=x=70:y=170:w=940:h=560:color=18243a:t=fill,"
            "drawbox=x=120:y=220:w=380:h=420:color=263c5c:t=fill,"
            "drawbox=x=500:y=220:w=380:h=420:color=263c5c:t=fill,"
            "drawbox=x=70:y=790:w=940:h=430:color=5b4050:t=fill,"
            "drawbox=x=120:y=1040:w=840:h=500:color=7b5260:t=fill,"
            "drawbox=x='700+10*sin(t*1.8)':y='730+8*sin(t*1.8)':w=170:h=90:color=1f2937:t=fill,"
            "drawbox=x='745+10*sin(t*1.8)':y='745+8*sin(t*1.8)':w=80:h=55:color=facc15:t=fill,"
            "drawbox=x='735+10*sin(t*1.8)':y='760+8*sin(t*1.8)':w=100:h=20:color=111827:t=fill,"
            "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='07-00':fontcolor=white:fontsize=28:x='750+5*sin(t*1.8)':y='755+8*sin(t*1.8)',"
            "drawbox=x='0+30*sin(t*0.5)':y=0:w=1080:h=180:color=fbbf24@0.08:t=fill,"
            "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='MORNING NEGOTIATION':fontcolor=white@0.35:fontsize=24:x=70:y=80"
        )
    elif "digital payments" in theme:
        bg="101827"
        motif=(
            "drawbox=x=0:y=0:w=1080:h=1920:color=101827:t=fill,"
            "drawbox=x=70:y=180:w=940:h=650:color=24334a:t=fill,"
            "drawbox=x=120:y=250:w=840:h=180:color=111827:t=fill,"
            "drawbox=x='380+22*sin(t*2)':y=485:w=320:h=220:color=0f766e:t=fill,"
            "drawbox=x='430+22*sin(t*2)':y=535:w=220:h=110:color=ecfeff:t=fill,"
            "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='PAYMENT PENDING':fontcolor=white:fontsize=34:x='350+18*sin(t*2)':y=560,"
            "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='checking...':fontcolor=67e8f9:fontsize=24:x='480+18*sin(t*2)':y=615"
        )
    elif "food delivery" in theme:
        bg="17121d"
        motif=(
            "drawbox=x=0:y=0:w=1080:h=1920:color=17121d:t=fill,"
            "drawbox=x=70:y=180:w=940:h=620:color=30243b:t=fill,"
            "drawbox=x=110:y=230:w=860:h=360:color=111827:t=fill,"
            "drawbox=x='740-70*sin(t*1.4)':y='610+15*sin(t*2)':w=170:h=170:color=f59e0b:t=fill,"
            "drawbox=x='775-70*sin(t*1.4)':y='645+15*sin(t*2)':w=100:h=100:color=fff7ed:t=fill,"
            "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='5 MINUTES AWAY':fontcolor=white:fontsize=38:x='310-45*sin(t*1.4)':y=330"
        )
    elif "apartment" in theme:
        bg="0e1726"
        motif=(
            "drawbox=x=0:y=0:w=1080:h=1920:color=0e1726:t=fill,"
            "drawbox=x=140:y=170:w=800:h=760:color=263447:t=fill,"
            "drawbox=x=210:y=250:w=660:h=620:color=0b1220:t=fill,"
            "drawbox=x=225:y=265:w=630:h=500:color=334155:t=fill,"
            "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='LIFT':fontcolor=white:fontsize=34:x='500+8*sin(t*2)':y=300,"
            "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='2   3   4   5':fontcolor=94a3b8:fontsize=30:x=405:y=845,"
            "drawbox=x='270+12*sin(t*2.2)':y=1020:w=540:h=22:color=64748b:t=fill"
        )
    elif "student life" in theme:
        bg="111827"
        motif=(
            "drawbox=x=0:y=0:w=1080:h=1920:color=111827:t=fill,"
            "drawbox=x=80:y=170:w=920:h=850:color=1f2937:t=fill,"
            "drawbox=x=145:y=240:w=790:h=700:color=0b1220:t=fill,"
            "drawbox=x=185:y=310:w=710:h=90:color=243447:t=fill,"
            "drawbox=x=185:y=450:w=710:h=90:color=243447:t=fill,"
            "drawbox=x=185:y=590:w=710:h=90:color=243447:t=fill,"
            "drawbox=x='185+18*sin(t*3)':y=730:w=430:h=90:color=334155:t=fill,"
            "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='17 PEOPLE SEEN':fontcolor=fb7185:fontsize=30:x='520+12*sin(t*3)':y=760,"
            "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='EXAM TOMORROW':fontcolor=94a3b8:fontsize=26:x=360:y=255"
        )
    elif "commuting" in theme:
        bg="0b1320"
        motif=(
            "drawbox=x=0:y=0:w=1080:h=1920:color=0b1320:t=fill,"
            "drawbox=x=70:y=170:w=940:h=500:color=1e3a5f:t=fill,"
            "drawbox=x=120:y=230:w=840:h=350:color=60a5fa:t=fill,"
            "drawbox=x=70:y=670:w=940:h=250:color=334155:t=fill,"
            "drawbox=x='160+140*sin(t*0.9)':y=700:w=330:h=180:color=facc15:t=fill,"
            "drawbox=x='200+140*sin(t*0.9)':y=735:w=250:h=65:color=0f172a:t=fill,"
            "drawbox=x='200+140*sin(t*0.9)':y=825:w=70:h=35:color=111827:t=fill,"
            "drawbox=x='380+140*sin(t*0.9)':y=825:w=70:h=35:color=111827:t=fill,"
            "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='BUS STOP':fontcolor=white:fontsize=36:x=390:y=270"
        )
    elif "online shopping" in theme:
        bg="101827"
        motif=(
            "drawbox=x=0:y=0:w=1080:h=1920:color=101827:t=fill,"
            "drawbox=x=120:y=180:w=840:h=800:color=1f2937:t=fill,"
            "drawbox=x=180:y=250:w=720:h=110:color=0b1220:t=fill,"
            "drawbox=x=180:y=410:w=320:h=430:color=334155:t=fill,"
            "drawbox=x=540:y=410:w=320:h=430:color=334155:t=fill,"
            "drawbox=x='585+20*sin(t*2)':y='465+12*sin(t*2)':w=220:h=220:color=f472b6:t=fill,"
            "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='YOUR CART MISSES YOU':fontcolor=white:fontsize=30:x='250+15*sin(t*2)':y=300"
        )
    else:
        bg="101827"
        motif=(
            "drawbox=x=0:y=0:w=1080:h=1920:color=101827:t=fill,"
            "drawbox=x=70:y=170:w=940:h=620:color=1e293b:t=fill,"
            "drawbox=x=140:y=250:w=800:h=430:color=0b1220:t=fill,"
            "drawbox=x='250+35*sin(t*1.1)':y=330:w=580:h=240:color=334155:t=fill,"
            "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='PRESENTATION MODE':fontcolor=white:fontsize=34:x='340+25*sin(t*1.1)':y=360"
        )

    # The active speaker talks; the listener stays neutral/reactive.
    if speaker_key == "arjun":
        h0, h1 = human_talk, human_talk_b
        r0, r1 = robot, robot_happy
    else:
        h0, h1 = human, human_shock
        r0, r1 = robot_talk, robot_talk_b

    # Visual-only render: keep exactly the illustrated background and the two
    # original full-body characters. No title, name labels, subtitles, music,
    # sound effects, voice-over, watermarks, or dialogue panels.
    fc=(
        "[0:v]scale=1080:1920[m];"
        "[1:v]scale=350:705[h0s];"
        "[2:v]scale=350:705[r0s];"
        "[3:v]scale=370:745[h1s];"
        "[4:v]scale=370:745[r1s];"
        "[m][h0s]overlay=x='35+10*sin(t*2)':y='550+5*sin(t*5)':enable='lt(mod(t,0.8),0.4)'[c1];"
        "[c1][h1s]overlay=x='25+12*sin(t*2)':y='535+5*sin(t*5)':enable='gte(mod(t,0.8),0.4)'[c2];"
        "[c2][r0s]overlay=x='690+7*sin(t*2+1)':y='550+4*sin(t*5+1)':enable='lt(mod(t,0.8),0.4)'[c3];"
        "[c3][r1s]overlay=x='675+9*sin(t*2+1)':y='535+4*sin(t*5+1)':enable='gte(mod(t,0.8),0.4)'[v]"
    )

    cmd=[
        "ffmpeg","-y",
        "-loop","1","-i",background,"-i",h0,"-i",r0,"-i",h1,"-i",r1,
        "-filter_complex",fc,"-map","[v]","-t",f"{dur:.2f}",
        "-r","30","-c:v","libx264","-preset","veryfast","-crf","24","-pix_fmt","yuv420p",seg
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
