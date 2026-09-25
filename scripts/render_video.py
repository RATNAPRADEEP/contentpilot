#!/usr/bin/env python3
import json, math, os, re, struct, subprocess, wave, zlib

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

# ---------- Original illustrated characters ----------
def png_rgba(path, w, h, draw_fn):
    px = bytearray(w*h*4)
    def setp(x,y,c):
        if 0 <= x < w and 0 <= y < h:
            i=(y*w+x)*4
            px[i:i+4]=bytes(c)
    def rect(x0,y0,x1,y1,c):
        for y in range(max(0,int(y0)),min(h,int(y1))):
            for x in range(max(0,int(x0)),min(w,int(x1))):
                setp(x,y,c)
    def circle(cx,cy,r,c):
        rr=r*r
        for y in range(max(0,int(cy-r)),min(h,int(cy+r)+1)):
            for x in range(max(0,int(cx-r)),min(w,int(cx+r)+1)):
                if (x-cx)*(x-cx)+(y-cy)*(y-cy) <= rr:
                    setp(x,y,c)
    def line(x0,y0,x1,y1,th,c):
        dx=x1-x0; dy=y1-y0; n=max(abs(dx),abs(dy),1)
        for k in range(n+1):
            x=int(x0+dx*k/n); y=int(y0+dy*k/n)
            rect(x-th,y-th,x+th+1,y+th+1,c)
    draw_fn(setp,rect,circle,line)
    raw=bytearray()
    for y in range(h):
        raw.append(0)
        raw.extend(px[y*w*4:(y+1)*w*4])
    def chunk(t,d):
        return struct.pack(">I",len(d))+t+d+struct.pack(">I",zlib.crc32(t+d)&0xffffffff)
    png=b"\x89PNG\r\n\x1a\n"
    png+=chunk(b"IHDR",struct.pack(">IIBBBBB",w,h,8,6,0,0,0))
    png+=chunk(b"IDAT",zlib.compress(bytes(raw),9))+chunk(b"IEND",b"")
    open(path,"wb").write(png)

def make_character(path, kind, mood):
    def art(setp,rect,circle,line):
        skin=(247,190,145,255)
        outline=(20,25,35,255)
        if kind=="robot":
            body=(45,185,210,255); dark=(12,35,55,255); eye=(245,255,255,255)
            # antenna
            line(180,72,180,35,7,body); circle(180,23,11,(255,208,65,255))
            # head
            rect(88,82,272,235,dark); circle(180,158,66,body)
            circle(146,150,12,eye); circle(214,150,12,eye)
            if mood=="shocked":
                circle(180,199,17,(5,10,20,255))
            elif mood=="happy":
                line(150,198,210,198,6,(5,10,20,255))
            else:
                line(150,200,210,200,5,(5,10,20,255))
            # body + arms
            rect(105,235,255,435,body)
            line(105,270,45,345,18,body); line(255,270,315,345,18,body)
            rect(78,435,282,468,dark)
        else:
            shirt=(244,140,65,255)
            # hair/head
            circle(180,155,66,skin); rect(112,91,248,133,(32,24,22,255))
            circle(150,155,9,(20,20,20,255)); circle(210,155,9,(20,20,20,255))
            if mood=="shocked":
                circle(180,204,18,(125,35,35,255))
            elif mood=="happy":
                line(150,198,210,198,6,(125,35,35,255))
            else:
                line(152,208,208,208,4,(125,35,35,255))
            rect(105,235,255,430,shirt)
            line(105,270,45,345,18,skin); line(255,270,315,345,18,skin)
            rect(78,430,282,468,outline)
    png_rgba(path,360,500,art)

human=os.path.join(build,"character-human.png")
human_shock=os.path.join(build,"character-human-shock.png")
robot=os.path.join(build,"character-ai.png")
robot_happy=os.path.join(build,"character-ai-happy.png")
make_character(human,"human","neutral")
make_character(human_shock,"human","shocked")
make_character(robot,"robot","neutral")
make_character(robot_happy,"robot","happy")

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
    open(scene_txt,"w",encoding="utf-8").write(wrap(safe(text_line)))

    music=os.path.join(build,f"music_{i}.wav")
    sfx=os.path.join(build,f"sfx_{i}.wav")
    music_wav(music,dur,styles[i%len(styles)])
    sfx_wav(sfx,dur,i)

    seg=os.path.join(build,f"segment_{i}.mp4")
    h=human_shock if i in (2,4,5) else human
    r=robot_happy if i in (1,3,5) else robot

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

    # Speech-bubble style dialogue card, kinetic scene label, and large reaction zone.
    fc=(
        f"color=c={bg}:s=1080x1920:r=30[base];"
        f"[base]{motif}[m];"
        f"[1:v]scale=270:375[h];"
        f"[2:v]scale=270:375[r];"
        f"[m][h]overlay=x=60:y=730:enable='between(t,0,{dur:.2f})'[c1];"
        f"[c1][r]overlay=x=600:y=680:enable='between(t,0,{dur:.2f})'[c2];"
        f"[c2]drawbox=x=55:y=75:w=970:h=115:color=05070d@0.90:t=fill,"
        f"drawtext=fontfile={font}:text='CONTENTPILOT':fontcolor=white:fontsize=34:x=80:y=112,"
        f"drawtext=fontfile={font}:text='COMEDY':fontcolor=38bdf8:fontsize=34:x=325:y=112,"
        f"drawtext=fontfile={regular}:text='ORIGINAL SHORT':fontcolor=white@0.55:fontsize=21:x=785:y=120,"
        f"drawbox=x=70:y=1030:w=940:h=420:color=ffffff@0.96:t=fill,"
        f"drawbox=x=70:y=1030:w=16:h=420:color=38bdf8:t=fill,"
        f"drawtext=fontfile={font}:text='SCENE {i+1}':fontcolor=0f172a:fontsize=24:x=110:y=1080,"
        f"drawtext=fontfile={font}:textfile='{scene_txt}':fontcolor=0b1220:fontsize=43:line_spacing=14:x=110:y=1140,"
        f"drawtext=fontfile={regular}:text='WATCH THE REACTION →':fontcolor=0f172a@0.55:fontsize=20:x=110:y=1380,"
        f"drawtext=fontfile={regular}:text='ContentPilot Original':fontcolor=white@0.42:fontsize=17:x=75:y=1845[v];"
        f"[3:a]apad,atrim=duration={dur:.2f},asetpts=PTS-STARTPTS[voice];"
        f"[4:a]apad,atrim=duration={dur:.2f},asetpts=PTS-STARTPTS[music];"
        f"[5:a]apad,atrim=duration={dur:.2f},asetpts=PTS-STARTPTS[sfx];"
        f"[voice][music][sfx]amix=inputs=3:duration=longest:weights='1 0.16 0.28':normalize=0,"
        f"alimiter=limit=0.92[a]"
    )

    cmd=[
        "ffmpeg","-y","-f","lavfi","-i","color=c=0b1020:s=1080x1920:r=30",
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
