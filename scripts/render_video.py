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
    """Create original anime-inspired full-body characters with human-like proportions."""
    W, H = 520, 1050
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im, "RGBA")

    def poly(points, fill, outline=None, width=1):
        d.polygon(points, fill=fill)
        if outline:
            d.line(points + [points[0]], fill=outline, width=width, joint="curve")

    def line(points, fill, width):
        d.line(points, fill=fill, width=width, joint="curve")

    is_robot = kind == "robot"
    if is_robot:
        skin, skin2 = (170,225,239,255), (65,160,190,255)
        hair, hair2 = (18,66,101,255), (43,137,174,255)
        top, top2 = (20,122,153,255), (42,184,198,255)
        shoe = (7,34,48,255)
        iris = (48,225,238,255)
        glow_col = (35,210,235,150)
    else:
        skin, skin2 = (239,174,133,255), (198,119,91,255)
        hair, hair2 = (39,27,42,255), (74,45,74,255)
        top, top2 = (43,60,90,255), (238,241,245,255)
        shoe = (27,29,40,255)
        iris = (62,112,180,255)

    ink = (22,25,34,255)
    white = (255,255,255,255)

    # soft character glow for Byte only
    if is_robot:
        glow_layer = Image.new("RGBA",(W,H),(0,0,0,0))
        gd = ImageDraw.Draw(glow_layer,"RGBA")
        gd.ellipse((125,90,395,430), fill=glow_col)
        im.alpha_composite(glow_layer.filter(ImageFilter.GaussianBlur(28)))

    # Hair behind head
    d.ellipse((155,105,365,390), fill=hair, outline=ink, width=5)
    poly([(150,245),(135,190),(165,160),(145,112),(198,132),(190,75),
          (235,108),(260,48),(286,108),(337,76),(328,133),(380,112),
          (362,190),(370,255),(335,215),(310,158),(268,180),(225,150),
          (185,215)], hair, ink, 5)
    poly([(170,165),(194,110),(220,138),(260,92),(291,130),(335,105),
          (318,160),(275,145),(237,168),(200,148)], hair2)

    # Neck and shoulders
    d.rounded_rectangle((226,335,294,430), 18, fill=skin, outline=skin2, width=4)
    poly([(145,405),(205,370),(315,370),(375,405),(400,610),
          (340,665),(180,665),(120,610)], top, ink, 5)

    # Collar / shirt detail
    if is_robot:
        poly([(202,382),(260,438),(318,382),(305,555),(215,555)], top2, (80,230,235,255), 3)
        line([(260,438),(260,560)], (170,255,255,150), 4)
    else:
        poly([(205,382),(260,440),(315,382),(298,550),(222,550)], top2, (95,100,120,255), 3)
        poly([(242,425),(260,445),(278,425),(270,485),(250,485)], (35,39,55,255))

    # Face over hair
    d.ellipse((158,125,362,365), fill=skin, outline=ink, width=5)
    # ears
    d.ellipse((142,220,175,285), fill=skin, outline=skin2, width=3)
    d.ellipse((345,220,378,285), fill=skin, outline=skin2, width=3)

    # Anime eyes, smaller and more natural
    for cx in (205,315):
        d.ellipse((cx-27,235,cx+27,300), fill=white, outline=ink, width=4)
        d.ellipse((cx-12,245,cx+12,294), fill=iris, outline=ink, width=2)
        d.ellipse((cx-5,250,cx+6,291), fill=(15,27,45,255))
        d.ellipse((cx-9,250,cx-2,258), fill=white)
    line([(181,218),(222,210)], ink, 5)
    line([(298,210),(339,218)], ink, 5)
    line([(258,285),(251,320),(270,322)], skin2, 4)

    if mood == "shocked":
        d.ellipse((242,338,278,382), fill=(92,38,48,255), outline=ink, width=4)
        line([(180,205),(216,195)], ink, 4)
        line([(304,195),(340,205)], ink, 4)
    elif mood == "talk":
        d.ellipse((240,338,280,378), fill=(94,39,50,255), outline=ink, width=3)
    elif mood == "happy":
        d.arc((225,326,295,388), 10, 170, fill=(110,40,52,255), width=7)
    else:
        d.arc((230,332,290,370), 15, 165, fill=(110,40,52,255), width=5)

    # Waist and hips: explicit torso taper so the body is not a triangle.
    d.rounded_rectangle((185,570,335,700), 35, fill=top, outline=ink, width=4)
    d.rounded_rectangle((168,650,352,745), 30, fill=top, outline=ink, width=5)
    if is_robot:
        d.rounded_rectangle((205,585,315,655), 20, fill=(25,154,177,255), outline=(90,235,240,255), width=3)

    # Arms, with slight pose difference for natural movement.
    if step == 0:
        left_arm = [(135,420),(92,535),(78,610)]
        right_arm = [(385,420),(430,520),(445,590)]
    else:
        left_arm = [(135,420),(105,500),(125,575)]
        right_arm = [(385,420),(420,545),(400,625)]
    line(left_arm, top, 42)
    line(right_arm, top, 42)
    d.ellipse((left_arm[-1][0]-22,left_arm[-1][1]-22,left_arm[-1][0]+22,left_arm[-1][1]+22), fill=skin, outline=skin2, width=3)
    d.ellipse((right_arm[-1][0]-22,right_arm[-1][1]-22,right_arm[-1][0]+22,right_arm[-1][1]+22), fill=skin, outline=skin2, width=3)

    # Legs separated at the hips with visible waist/upper legs.
    if step == 0:
        left_leg = (215,725,195,975)
        right_leg = (305,725,325,975)
    else:
        left_leg = (215,725,235,975)
        right_leg = (305,725,285,975)
    line([left_leg[:2],left_leg[2:]], top, 58)
    line([right_leg[:2],right_leg[2:]], top, 58)
    d.ellipse((165 if step==0 else 205,950,235 if step==0 else 275,1010), fill=shoe, outline=ink, width=4)
    d.ellipse((305 if step==0 else 265,950,375 if step==0 else 335,1010), fill=shoe, outline=ink, width=4)

    # Clothing seams and highlights
    line([(175,610),(345,610)], (255,255,255,35), 3)
    line([(205,700),(190,930)], (255,255,255,28), 3)
    line([(315,700),(330,930)], (255,255,255,28), 3)
    # Small breathing/bounce anchor detail
    d.ellipse((247,655,273,681), fill=(255,255,255,35))

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
        # Warm, layered bedroom: wall, window, bed, nightstand, lamp, rug and floor.
        for y in range(0, 1180):
            t = y / 1180
            c = (int(32-8*t), int(48-10*t), int(72-15*t))
            d.line((0, y, W, y), fill=c)
        # window and dawn light
        d.rounded_rectangle((95,150,515,650),26,fill=(22,31,49),outline=(78,96,124),width=8)
        d.rectangle((120,175,490,625),fill=(125,166,201))
        d.ellipse((245,255,385,395),fill=(250,190,88))
        d.polygon([(60,125),(195,140),(178,675),(75,720)],fill=(67,48,75))
        d.polygon([(555,140),(690,125),(665,720),(570,675)],fill=(67,48,75))
        # wall art
        d.rounded_rectangle((720,190,875,345),16,fill=(42,55,78),outline=(98,116,143),width=5)
        d.rounded_rectangle((755,225,840,310),12,fill=(29,40,59),outline=(135,150,170),width=3)
        d.ellipse((780,248,815,283),fill=(246,190,90))
        # bed and pillows
        d.rounded_rectangle((90,735,990,1180),38,fill=(47,43,55),outline=(91,82,99),width=8)
        d.rounded_rectangle((120,900,960,1215),34,fill=(199,199,204),outline=(130,130,140),width=6)
        d.rounded_rectangle((165,925,410,1060),25,fill=(238,235,229),outline=(180,178,176),width=5)
        d.rounded_rectangle((420,925,665,1060),25,fill=(228,226,223),outline=(180,178,176),width=5)
        d.rounded_rectangle((245,1010,930,1225),28,fill=(99,77,111))
        # nightstand and lamp
        d.rounded_rectangle((720,570,930,860),18,fill=(96,66,57),outline=(132,94,74),width=7)
        d.rectangle((748,850,778,1010),fill=(72,48,43))
        d.rectangle((872,850,902,1010),fill=(72,48,43))
        d.rectangle((805,465,832,575),fill=(61,48,48))
        d.polygon([(745,465),(895,465),(855,370),(785,370)],fill=(238,193,107),outline=(130,96,58))
        d.rounded_rectangle((770,675,885,745),12,fill=(22,27,34),outline=(245,196,72),width=5)
        d.text((795,690),"07:00",fill=(245,196,72))
        # phone on bed
        d.rounded_rectangle((470,1170,590,1235),14,fill=(28,32,40),outline=(150,160,180),width=4)
        # floor and a real rug, not a giant empty panel
        for y in range(1215,H):
            shade=int(104 + 12*(y-1215)/(H-1215))
            d.line((0,y,W,y),fill=(shade,72,62))
        d.rounded_rectangle((250,1450,830,1730),65,fill=(126,83,91),outline=(163,112,116),width=7)
        d.ellipse((335,1510,745,1665),outline=(163,112,116),width=4)
        # small floor objects
        d.ellipse((130,1660,200,1695),fill=(42,44,54))
        d.ellipse((880,1660,950,1695),fill=(42,44,54))
        # plant
        d.rectangle((975,760,1025,900),fill=(133,91,66))
        d.ellipse((940,650,1010,790),fill=(58,116,78))
        d.ellipse((985,600,1045,760),fill=(52,104,72))
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

    # Full comedy render: original characters + illustrated environment + voice,
    # music, SFX and readable subtitles. No stock footage or copyrighted characters.
    subtitle_style = (
        "drawbox=x=85:y=1605:w=910:h=190:color=000000@0.62:t=fill,"
        "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
        "textfile='"+scene_txt+"':fontcolor=white:fontsize=38:line_spacing=10:x=115:y=1640"
    )

    fc=(
        "[0:v]scale=1080:1920[m];"
        "[1:v]scale=360:730[h0s];"
        "[2:v]scale=360:730[r0s];"
        "[3:v]scale=380:770[h1s];"
        "[4:v]scale=380:770[r1s];"
        "[m][h0s]overlay=x='20+12*sin(t*1.7)':y='560+5*sin(t*4)':enable='lt(mod(t,0.75),0.38)'[c1];"
        "[c1][h1s]overlay=x='15+14*sin(t*1.7)':y='545+5*sin(t*4)':enable='gte(mod(t,0.75),0.38)'[c2];"
        "[c2][r0s]overlay=x='700+8*sin(t*1.6+1)':y='560+4*sin(t*4+1)':enable='lt(mod(t,0.75),0.38)'[c3];"
        "[c3][r1s]overlay=x='685+10*sin(t*1.6+1)':y='545+4*sin(t*4+1)':enable='gte(mod(t,0.75),0.38)'[c4];"
        "[c4]"+subtitle_style+"[v];"
        "[5:a]apad,atrim=duration="+f"{dur:.2f}"+",asetpts=PTS-STARTPTS[voice];"
        "[6:a]apad,atrim=duration="+f"{dur:.2f}"+",asetpts=PTS-STARTPTS[music];"
        "[7:a]apad,atrim=duration="+f"{dur:.2f}"+",asetpts=PTS-STARTPTS[sfx];"
        "[voice][music][sfx]amix=inputs=3:duration=longest:weights='1 0.14 0.30':normalize=0,"
        "alimiter=limit=0.92[a]"
    )

    cmd=[
        "ffmpeg","-y",
        "-loop","1","-i",background,"-i",h0,"-i",r0,"-i",h1,"-i",r1,
        "-i",voice,"-i",music,"-i",sfx,
        "-filter_complex",fc,"-map","[v]","-map","[a]","-t",f"{dur:.2f}",
        "-r","30","-c:v","libx264","-preset","veryfast","-crf","23","-pix_fmt","yuv420p",
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
