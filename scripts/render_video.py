#!/usr/bin/env python3
import json, math, os, re, struct, subprocess, urllib.request, wave, zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = json.load(open(os.path.join(ROOT, "generated/latest.json"), encoding="utf-8"))
build = os.path.join(ROOT, "build")
os.makedirs(build, exist_ok=True)
video = os.path.join(ROOT, "generated", "contentpilot-latest.mp4")
font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
regular = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

scripts = data["script"]
scene_count = len(scripts)
weights = [max(1, len(s.split())) for s in scripts]
total_words = sum(weights)
total_duration = max(28, min(48, total_words / 2.35))
durations = [total_duration*w/total_words for w in weights]

def safe(text):
    return re.sub(r"[^A-Za-z0-9 .,:!?&'’()\-_/]", "", text).strip()

def wrap(text, width=25, max_lines=7):
    words=text.split(); lines=[]; line=""
    for word in words:
        cand=(line+" "+word).strip()
        if len(cand)<=width: line=cand
        else:
            if line: lines.append(line)
            line=word
    if line: lines.append(line)
    return "\n".join(lines[:max_lines])

def png_rgba(path, w, h, draw_fn):
    px=bytearray(w*h*4)
    def setp(x,y,c):
        if 0<=x<w and 0<=y<h:
            i=(y*w+x)*4; px[i:i+4]=bytes(c)
    def rect(x0,y0,x1,y1,c):
        for y in range(max(0,y0),min(h,y1)):
            for x in range(max(0,x0),min(w,x1)): setp(x,y,c)
    def circle(cx,cy,r,c):
        rr=r*r
        for y in range(max(0,int(cy-r)),min(h,int(cy+r)+1)):
            for x in range(max(0,int(cx-r)),min(w,int(cx+r)+1)):
                if (x-cx)*(x-cx)+(y-cy)*(y-cy)<=rr: setp(x,y,c)
    def line(x0,y0,x1,y1,th,c):
        dx=x1-x0; dy=y1-y0; n=max(abs(dx),abs(dy),1)
        for k in range(n+1):
            x=int(x0+dx*k/n); y=int(y0+dy*k/n)
            rect(x-th,y-th,x+th+1,y+th+1,c)
    draw_fn(setp,rect,circle,line)
    raw=bytearray()
    for y in range(h): raw.append(0); raw.extend(px[y*w*4:(y+1)*w*4])
    def chunk(t,d): return struct.pack(">I",len(d))+t+d+struct.pack(">I",zlib.crc32(t+d)&0xffffffff)
    png=b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",w,h,8,6,0,0,0))+chunk(b"IDAT",zlib.compress(bytes(raw),9))+chunk(b"IEND",b"")
    open(path,"wb").write(png)

def make_character(path, kind, mood):
    def art(setp,rect,circle,line):
        transparent=(0,0,0,0); skin=(245,190,145,255)
        if kind=="robot":
            body=(62,190,210,255); dark=(20,45,65,255); eye=(240,255,255,255)
            rect(105,205,255,430,body); rect(92,125,268,245,dark); circle(180,185,58,body)
            rect(125,160,150,188,eye); rect(210,160,235,188,eye)
            if mood=="shocked": rect(158,208,202,230,(5,10,20,255))
            else: rect(155,210,205,218,(5,10,20,255))
            line(180,125,180,82,5,body); circle(180,70,10,(255,220,80,255))
            rect(78,430,282,465,dark)
        else:
            shirt=(244,140,65,255) if kind=="human" else (100,110,230,255)
            circle(180,165,62,skin); rect(105,225,255,430,shirt)
            rect(118,105,242,145,(35,25,20,255))
            circle(155,162,9,(20,20,20,255)); circle(205,162,9,(20,20,20,255))
            if mood=="happy":
                line(150,205,210,205,5,(120,30,30,255))
            elif mood=="shocked":
                circle(180,210,15,(120,30,30,255))
            else:
                line(152,212,208,212,4,(120,30,30,255))
            rect(78,430,282,465,(25,30,45,255))
    png_rgba(path,360,500,art)

# Generate reusable original character assets for this run.
human=os.path.join(build,"character-human.png")
robot=os.path.join(build,"character-ai.png")
human_shock=os.path.join(build,"character-human-shock.png")
robot_happy=os.path.join(build,"character-ai-happy.png")
make_character(human,"human","neutral")
make_character(robot,"robot","neutral")
make_character(human_shock,"human","shocked")
make_character(robot_happy,"robot","happy")

def tone(freq, duration, volume=0.25, sr=44100):
    n=int(duration*sr); out=[]
    for i in range(n):
        t=i/sr; env=min(1,t*30, max(0,(duration-t)*20))
        out.append(int(32767*volume*env*math.sin(2*math.pi*freq*t)))
    return out

def music_wav(path, duration, style):
    sr=44100; n=int(duration*sr); buf=[0.0]*n
    scales={
        "playful":[523.25,659.25,783.99,659.25],
        "curious":[392.0,466.16,587.33,523.25],
        "tension":[220.0,233.08,261.63,233.08],
        "chaos":[330.0,392.0,311.13,466.16],
        "punchline":[659.25,783.99,987.77,783.99]
    }
    notes=scales.get(style,scales["playful"])
    beat=0.32
    for k in range(int(duration/beat)+1):
        f=notes[k%len(notes)]
        start=int(k*beat*sr); length=min(int(beat*0.8*sr),n-start)
        for j in range(max(0,length)):
            t=j/sr; env=min(1,t*35,max(0,(length/sr-t)*8))
            val=0.11*env*math.sin(2*math.pi*f*t)+0.055*env*math.sin(2*math.pi*(f/2)*t)
            if 0<=start+j<n: buf[start+j]+=val
    with wave.open(path,"wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<h",max(-32767,min(32767,int(v*32767)))) for v in buf))

def sfx_wav(path, duration, scene):
    sr=44100; n=int(duration*sr); buf=[0.0]*n
    def add(start, vals):
        for j,v in enumerate(vals):
            if 0<=start+j<n: buf[start+j]+=v
    events=[("pop",0.15),("whoosh",min(0.55,duration*0.45))]
    if scene==2: events=[("error",0.0),("buzz",max(0.15,duration*0.55))]
    if scene==4: events=[("ding",0.0),("pop",max(0.15,duration*0.45))]
    for typ,at in events:
        st=int(at*sr)
        length=int(min(0.5,duration-at)*sr)
        vals=[]
        for j in range(length):
            t=j/sr; env=min(1,t*80,max(0,(length/sr-t)*12))
            if typ=="pop": v=math.sin(2*math.pi*(180+700*t)*t)*0.30*env
            elif typ=="whoosh": v=math.sin(2*math.pi*(180+1800*t)*t)*0.16*env
            elif typ=="error": v=(math.sin(2*math.pi*95*t)+0.5*math.sin(2*math.pi*140*t))*0.20*env
            elif typ=="buzz": v=math.sin(2*math.pi*70*t)*0.16*env
            else: v=math.sin(2*math.pi*(900+900*t)*t)*0.22*env
            vals.append(v)
        add(st,vals)
    with wave.open(path,"wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<h",max(-32767,min(32767,int(v*32767)))) for v in buf))

voice_text=" ... ".join(scripts)
voice=os.path.join(build,"voice.wav")
subprocess.run(["espeak-ng","-v","en-us","-s","154","-p","50","-w",voice,voice_text],check=True)

backgrounds=data.get("background_urls",[])
bg_files=[]
for i in range(scene_count):
    p=os.path.join(build,f"bg_{i}.mp4")
    url=backgrounds[i%len(backgrounds)] if backgrounds else ""
    ok=False
    if url:
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"ContentPilot/2.0"})
            with urllib.request.urlopen(req,timeout=25) as r:
                raw=r.read()
            if len(raw)>50000:
                open(p,"wb").write(raw); ok=True
        except Exception as exc:
            print("background download failed:",i,exc)
    bg_files.append(p if ok else "")

# Find voice scene boundaries from word weights.
starts=[]; cur=0.0
for d in durations:
    starts.append(cur); cur+=d

segments=[]
styles=["playful","curious","tension","chaos","punchline"]
for i,(text,start,dur) in enumerate(zip(scripts,starts,durations)):
    scene_txt=os.path.join(build,f"scene_{i}.txt")
    open(scene_txt,"w",encoding="utf-8").write(wrap(safe(text)))
    music=os.path.join(build,f"music_{i}.wav"); sfx=os.path.join(build,f"sfx_{i}.wav")
    music_wav(music,dur,styles[i%len(styles)]); sfx_wav(sfx,dur,i)
    seg=os.path.join(build,f"segment_{i}.mp4")
    bg=bg_files[i]
    # Each scene gets real moving stock footage when available; fallback is an animated FFmpeg background.
    if bg:
        video_input=["-stream_loop","-1","-i",bg]
        base="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=1:1,drawbox=x=0:y=0:w=iw:h=ih:color=0x000000@0.38:t=fill"
    else:
        video_input=["-f","lavfi","-i","color=c=0b1020:s=1080x1920:r=30"]
        base="drawbox=x=70:y=190:w=940:h=650:color=0x13213a@1:t=fill"
    # Alternate character poses to create a real visual dialogue.
    h=human_shock if i>=2 else human
    r=robot_happy if i==4 else robot
    filter_complex=(
        f"[0:v]{base}[v0];"
        f"[v0][1:v]overlay=x=70:y=430:enable='between(t,0,{dur:.2f})'[v1];"
        f"[v1][2:v]overlay=x=650:y=390:enable='between(t,0,{dur:.2f})'[v2];"
        f"[v2]drawbox=x=48:y=80:w=984:h=100:color=0x05070d@0.88:t=fill,"
        f"drawtext=fontfile={font}:text='CONTENTPILOT COMEDY':fontcolor=white:fontsize=27:x=72:y=112,"
        f"drawtext=fontfile={regular}:text='ORIGINAL':fontcolor=white@0.48:fontsize=20:x=w-170:y=115,"
        f"drawbox=x=48:y=1010:w=984:h=650:color=0x05070d@0.92:t=fill,"
        f"drawtext=fontfile={font}:text='SCENE {i+1}/{scene_count}':fontcolor=white@0.58:fontsize=23:x=75:y=1050,"
        f"drawtext=fontfile={font}:textfile='{scene_txt}':fontcolor=white:fontsize=42:line_spacing=14:x=78:y=1120,"
        f"drawtext=fontfile={regular}:text='SETUP → ESCALATION → PUNCHLINE':fontcolor=white@0.42:fontsize=18:x=78:y=1545,"
        f"drawtext=fontfile={regular}:text='Background: Mixkit · Characters: generated by ContentPilot':fontcolor=white@0.38:fontsize=16:x=78:y=1585[v];"
        f"[3:a]atrim=duration={dur:.2f},asetpts=PTS-STARTPTS[voice];"
        f"[4:a]atrim=duration={dur:.2f},asetpts=PTS-STARTPTS[music];"
        f"[5:a]atrim=duration={dur:.2f},asetpts=PTS-STARTPTS[sfx];"
        f"[voice][music][sfx]amix=inputs=3:duration=first:weights='1 0.18 0.30':normalize=0[a]"
    )
    cmd=["ffmpeg","-y"]+video_input+["-i",h,"-i",r,"-ss",f"{start:.2f}","-i",voice,"-i",music,"-i",sfx,
         "-filter_complex",filter_complex,"-map","[v]","-map","[a]","-t",f"{dur:.2f}",
         "-r","30","-c:v","libx264","-preset","veryfast","-crf","25","-pix_fmt","yuv420p",
         "-c:a","aac","-b:a","128k","-shortest",seg]
    subprocess.run(cmd,check=True)
    segments.append(seg)

concat=os.path.join(build,"concat.txt")
with open(concat,"w",encoding="utf-8") as f:
    for seg in segments: f.write("file '"+seg.replace("'","'\\''")+"'\n")
subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",concat,"-c","copy",video],check=True)
print(video)
