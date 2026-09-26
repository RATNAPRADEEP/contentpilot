#!/usr/bin/env python3
import bpy, math, os, json, subprocess, wave, struct, re, shutil
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D=json.load(open(os.path.join(ROOT,"generated","latest.json"),encoding="utf-8"))
OUT=os.path.join(ROOT,"generated","contentpilot-latest.mp4")
B=os.path.join(ROOT,"build3d"); os.makedirs(B,exist_ok=True)
S=D["script"]; P=D.get("scene_plan",[])
FPS,W,H=24,540,960

def run(c): subprocess.run(c,check=True)
def dur(p): return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",p],text=True))
def safe(s): return re.sub(r"[^A-Za-z0-9 .,:!?&'’()\-_/]","",s).strip()
def M(n,c,metal=0,rough=.5):
    m=bpy.data.materials.get(n) or bpy.data.materials.new(n); m.diffuse_color=(*c,1); m.use_nodes=True
    b=m.node_tree.nodes.get("Principled BSDF"); b.inputs["Base Color"].default_value=(*c,1); b.inputs["Roughness"].default_value=rough; b.inputs["Metallic"].default_value=metal
    return m
SKIN=M("skin",(.50,.23,.12),0,.5); SKIN2=M("skin2",(.68,.34,.20),0,.5); HAIR=M("hair",(.015,.01,.008),0,.28)
BLUE=M("shirt",(.06,.15,.38),0,.42); DARK=M("pants",(.035,.045,.065),0,.55); SHOE=M("shoe",(.01,.012,.015),.05,.25)
WHITE=M("white",(.96,.96,.93),0,.2); IRIS=M("iris",(.05,.20,.55),.05,.2); BLACK=M("black",(.002,.002,.003),0,.15)
CYAN=M("cyan",(.15,.62,.72),.2,.28); AIBODY=M("aibody",(.02,.15,.21),.45,.25); GLOW=M("glow",(.03,.65,.95),.4,.18)
WALL=M("wall",(.42,.34,.30),0,.72); FLOOR=M("floor",(.24,.13,.075),0,.65); WOOD=M("wood",(.28,.14,.075),0,.55)
BED=M("bed",(.12,.065,.05),0,.62); SHEET=M("sheet",(.78,.75,.70),0,.78); BLANK=M("blank",(.26,.15,.20),0,.78); PILLOW=M("pillow",(.9,.87,.8),0,.82)
LAMP=M("lamp",(.95,.60,.24),0,.32); GLASS=M("glass",(.06,.18,.26),.1,.12); PAPER=M("paper",(.82,.76,.60),0,.9); GREEN=M("green",(.05,.25,.1),0,.8)

def clear():
    bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
def cube(n,l,s,m,b=0):
    bpy.ops.mesh.primitive_cube_add(location=l); o=bpy.context.object; o.name=n; o.scale=s; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(m)
    if b: x=o.modifiers.new("soft","BEVEL"); x.width=b; x.segments=3
    return o
def sphere(n,l,s,m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=l); o=bpy.context.object; o.name=n; o.scale=s; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(m); bpy.ops.object.shade_smooth(); return o
def cyl(n,a,b,r,m):
    a,b=Vector(a),Vector(b); v=b-a; bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=r,depth=v.length,location=(a+b)/2); o=bpy.context.object; o.name=n; o.rotation_mode="QUATERNION"; o.rotation_quaternion=v.to_track_quat("Z","Y"); o.data.materials.append(m); return o
def look(o,t): o.rotation_euler=(Vector(t)-o.location).to_track_quat("-Z","Y").to_euler()
def key(o,p,f): o.keyframe_insert(data_path=p,frame=f)

def bedroom():
    cube("floor",(0,0,0),(5.2,5.2,.12),FLOOR,.04); cube("back",(0,5,3.1),(5.2,.12,3.1),WALL,.04); cube("left",(-5.1,0,3.1),(.12,5,3.1),WALL,.04); cube("right",(5.1,0,3.1),(.12,5,3.1),WALL,.04)
    for y in range(-4,5): cube("board",(0,y,.14),(5,.012,.008),WOOD)
    cube("bedbase",(.8,2.55,.62),(2.9,1.55,.4),BED,.15); cube("mattress",(.8,2.55,1.12),(2.78,1.48,.28),SHEET,.12); cube("blanket",(1.05,2.65,1.43),(2.3,1.3,.12),BLANK,.1); cube("headboard",(.8,3.9,2.05),(2.95,.18,1.55),BED,.1)
    for x in (-1,.35,1.7): sphere("pillow",(x,3.45,1.55),(.62,.42,.18),PILLOW)
    cube("table",(3.7,3.15,1.1),(.68,.62,.9),WOOD,.08); cube("drawer",(3.7,2.52,1.2),(.48,.035,.26),BED,.03); cyl("lamp",(3.7,3.15,2),(3.7,3.15,3),.07,WOOD)
    bpy.ops.mesh.primitive_cone_add(vertices=32,radius1=.48,radius2=.25,depth=.55,location=(3.7,3.15,3.2)); bpy.context.object.data.materials.append(LAMP)
    cube("window",(-2.8,4.82,4.05),(1.7,.05,1.15),GLASS,.02); cube("curtainL",(-4.3,4.5,4.05),(.42,.14,1.55),BLANK,.1); cube("curtainR",(-1.3,4.5,4.05),(.42,.14,1.55),BLANK,.1)
    cube("art",(1.8,4.82,4.3),(.85,.05,.62),WOOD,.04); cube("art2",(1.8,4.72,4.3),(.7,.03,.48),GLASS,.02); cube("rug",(-.1,-.5,.16),(2.45,1.55,.035),BLANK,.1)
    cube("pot",(-3.9,3.45,.72),(.34,.34,.56),WOOD,.04)
    for dx,dy,dz in [(-.35,0,1.45),(.15,.05,1.8),(.42,-.05,1.5)]: sphere("leaf",(-3.9+dx,3.45+dy,.72+dz),(.36,.15,.65),GREEN)
    for typ,loc,en,col,size in [("AREA",(-2.7,-.5,5.8),900,(1,.76,.56),4.5),("AREA",(3.4,-1,4.8),650,(.58,.72,1),3.2),("POINT",(3.7,3.15,3.2),220,(1,.5,.2),2)]:
        bpy.ops.object.light_add(type=typ,location=loc); l=bpy.context.object; l.data.energy=en; l.data.color=col
        if hasattr(l.data,"size"): l.data.size=size

def char(name,x,y,ai=False):
    skin,body,pants=(CYAN,AIBODY,AIBODY) if ai else (SKIN,BLUE,DARK)
    r=bpy.data.objects.new(name+"_root",None); bpy.context.collection.objects.link(r); r.location=(x,y,0); q={}
    def add(o,k): o.parent=r; q[k]=o
    add(sphere(name+"torso",(0,0,2.55),(.52,.32,.78),body),"torso"); add(sphere(name+"hips",(0,0,1.82),(.44,.29,.28),pants),"hips"); add(sphere(name+"head",(0,0,4.15),(.38,.34,.47),skin),"head")
    add(cyl(name+"neck",(0,0,3.52),(0,0,3.82),.16,skin),"neck"); add(sphere(name+"hair",(0,.03,4.48),(.4,.36,.24),HAIR if not ai else AIBODY),"hair")
    for side in (-1,1):
        add(sphere(name+"eye",(side*.14,-.315,4.19),(.105,.055,.11),WHITE),f"eye{side}"); add(sphere(name+"iris",(side*.14,-.365,4.19),(.045,.025,.055),GLOW if ai else IRIS),f"iris{side}")
        add(cyl(name+"ua",(side*.5,0,3.02),(side*.7,0,2.35),.13,body),f"ua{side}"); add(cyl(name+"fa",(side*.7,0,2.35),(side*.72,0,1.75),.115,skin),f"fa{side}")
        add(sphere(name+"hand",(side*.72,0,1.66),(.13,.12,.16),skin),f"hand{side}"); add(cyl(name+"leg",(side*.2,0,1.65),(side*.22,0,.65),.17,pants),f"leg{side}"); add(cube(name+"shoe",(side*.22,-.12,.43),(.2,.34,.12),SHOE,.07),f"shoe{side}")
    add(sphere(name+"nose",(0,-.34,4.03),(.045,.04,.07),SKIN2),"nose"); add(cube(name+"mouth",(0,-.355,3.92),(.09,.025,.025),BLACK,.015),"mouth")
    if ai: add(sphere(name+"light",(0,-.31,2.55),(.11,.035,.11),GLOW),"light")
    return r,q

def animate(r,q,a,end):
    r.keyframe_insert(data_path="location",frame=1); r.location.z=.025; key(r,"location",end//2); r.location.z=0; key(r,"location",end)
    for s in (-1,1):
        u,f=q[f"ua{s}"],q[f"fa{s}"]; u.rotation_mode=f.rotation_mode="XYZ"; ux=math.radians(8); fx=math.radians(8)
        if a in ("alarm_ringing","showing_record","showing_backup"): ux,fx=math.radians(-38),math.radians(-24)
        elif a in ("negotiating","pleading","asking"): ux,fx=math.radians(-28 if s==1 else -18),math.radians(-18)
        elif a in ("getting_up","running"): ux,fx=math.radians(22*s),math.radians(18*s)
        u.rotation_euler.x=ux; f.rotation_euler.x=fx; key(u,"rotation_euler",1); key(f,"rotation_euler",1)
        u.rotation_euler.x=ux+math.radians(15)*s; f.rotation_euler.x=fx+math.radians(12)*s; key(u,"rotation_euler",end//2); key(f,"rotation_euler",end//2)
        u.rotation_euler.x=ux; f.rotation_euler.x=fx; key(u,"rotation_euler",end); key(f,"rotation_euler",end)

def props(a):
    if a in ("alarm_ringing","sleepy"):
        cube("phone",(0,1.25,1.5),(.32,.55,.04),BLACK,.05); cube("screen",(0,1.19,1.55),(.25,.42,.012),GLOW,.01)
    if a in ("keeping_record","showing_record","showing_backup"):
        cube("book",(3.25,2.65,1.65),(.52,.1,.65),PAPER,.04)
        for z in (1.35,1.55,1.75,1.95): cube("line",(3.25,2.53,z),(.35,.01,.018),BLACK)

def audio_tone(path,seconds,style):
    sr=44100; n=int(seconds*sr); b=[0.0]*n; notes={"playful":[523,659,784,659],"tension":[220,233,261,233],"punch":[659,784,988,1047]}[style]
    for k in range(int(seconds/.28)+1):
        st=int(k*.28*sr); ln=min(int(.2*sr),n-st); f=notes[k%4]
        for j in range(max(0,ln)):
            t=j/sr; e=min(1,t*30,max(0,(ln/sr-t)*10)); b[st+j]+=.055*e*math.sin(2*math.pi*f*t)
    with wave.open(path,"wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(b"".join(struct.pack("<h",max(-32767,min(32767,int(x*32767)))) for x in b))
def sfx(path,seconds,i):
    sr=44100; n=int(seconds*sr); b=[0.0]*n
    for at,f in ((0,300+i*50),(max(.2,seconds*.6),900+i*60)):
        st=int(at*sr); ln=min(int(.24*sr),n-st)
        for j in range(max(0,ln)):
            t=j/sr; e=min(1,t*80,max(0,(ln/sr-t)*12)); b[st+j]+=.09*e*math.sin(2*math.pi*(f+700*t)*t)
    with wave.open(path,"wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(b"".join(struct.pack("<h",max(-32767,min(32767,int(x*32767)))) for x in b))
def stamp(x):
    ms=int(round((x-int(x))*1000)); z=int(x); return f"{z//3600:02d}:{z%3600//60:02d}:{z%60:02d},{ms:03d}"

if os.path.exists(OUT): os.remove(OUT)
for f in os.listdir(B):
    p=os.path.join(B,f)
    if os.path.isfile(p): os.remove(p)

segments=[]; aud=[]; subs=[]; clock=0
for i,line in enumerate(S):
    voice=os.path.join(B,f"v{i}.wav"); run(["espeak-ng","-v","en-us","-s","148","-p","50","-w",voice,safe(line)])
    d=max(2.5,min(7.0,dur(voice)+.25)); aud.append((voice,d)); clear(); sc=bpy.context.scene
    sc.render.engine="BLENDER_EEVEE_NEXT"; sc.render.resolution_x=W; sc.render.resolution_y=H; sc.render.resolution_percentage=100; sc.render.fps=FPS; sc.render.image_settings.file_format="PNG"; sc.world.color=(.018,.022,.035)
    bedroom(); a=P[i].get("action","talking") if i<len(P) else "talking"; actor=P[i].get("actor","arjun") if i<len(P) else "arjun"
    ar,aq=char("arjun",-1.05,.45); by,bq=char("byte",1.9,1,True)
    if a=="sleepy": ar.location.y=1.55; ar.location.z=.2; ar.rotation_euler.y=math.radians(62)
    if a in ("negotiating","pleading"): ar.location.x=-.75; ar.location.y=.85
    if a in ("alarm_ringing","showing_record","showing_backup","keeping_record"): by.location.x=1.45
    props(a); end=max(2,int(d*FPS)); sc.frame_start=1; sc.frame_end=end
    ang=[(7,-12.2,5.5),(4.7,-13,5),(8.4,-9.4,5.4),(1.8,-13.6,5.2),(-5,-11.2,5.8),(6.2,-10.5,7),(2.8,-13.2,4.8),(-3.8,-12,6.2)][i%8]
    bpy.ops.object.camera_add(location=ang); cam=bpy.context.object; cam.data.lens=52; sc.camera=cam; look(cam,(.35,1.55,2.45)); cam.keyframe_insert(data_path="location",frame=1)
    cam.location.x+=.45; cam.location.y+=.28; look(cam,(.35,1.55,2.45)); cam.keyframe_insert(data_path="location",frame=end)
    animate(ar,aq,a,end); animate(by,bq,a,end)
    root=by if actor=="byte" else ar; root.location.x+=.1; key(root,"location",end//2)
    fd=os.path.join(B,f"f{i}"); os.makedirs(fd); sc.render.filepath=os.path.join(fd,"f_"); bpy.ops.render.render(animation=True)
    seg=os.path.join(B,f"s{i}.mp4"); run(["ffmpeg","-y","-framerate",str(FPS),"-i",os.path.join(fd,"f_%04d.png"),"-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p",seg]); shutil.rmtree(fd); segments.append(seg)
    raw=safe(line); sp,_,words=raw.partition(":"); name="Byte" if actor=="byte" else "Arjun"; subs.append(f"{i+1}\n{stamp(clock)} --> {stamp(clock+d)}\n{name}: {words.strip()}\n"); clock+=d

ct=os.path.join(B,"concat.txt"); open(ct,"w").write("".join(f"file '{x}'\n" for x in segments)); silent=os.path.join(B,"silent.mp4")
run(["ffmpeg","-y","-f","concat","-safe","0","-i",ct,"-c","copy",silent])
alist=os.path.join(B,"alist.txt"); mixes=[]; styles=["playful","playful","tension","playful","punch","tension","punch","playful"]
for i,(v,d) in enumerate(aud):
    m=os.path.join(B,f"m{i}.wav"); x=os.path.join(B,f"x{i}.wav"); q=os.path.join(B,f"q{i}.wav"); audio_tone(m,d,styles[i%len(styles)]); sfx(x,d,i)
    run(["ffmpeg","-y","-i",v,"-i",m,"-i",x,"-filter_complex","[0:a]volume=1[a];[1:a]volume=.14[b];[2:a]volume=.22[c];[a][b][c]amix=inputs=3:duration=longest:normalize=0,alimiter=limit=.92","-ar","44100","-ac","1",q]); mixes.append(q)
open(alist,"w").write("".join(f"file '{x}'\n" for x in mixes)); audio=os.path.join(B,"audio.wav"); run(["ffmpeg","-y","-f","concat","-safe","0","-i",alist,"-c","copy",audio])
sf=os.path.join(B,"dialogue.srt"); open(sf,"w",encoding="utf-8").write("\n".join(subs)); esc=sf.replace("\\","/").replace(":","\\:")
vf=f"subtitles='{esc}':force_style='FontName=DejaVu Sans,FontSize=18,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00101010,Outline=3,Shadow=1,MarginV=85,Alignment=2'"
run(["ffmpeg","-y","-i",silent,"-i",audio,"-vf",vf,"-map","0:v","-map","1:a","-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p","-c:a","aac","-b:a","128k","-shortest",OUT])
if dur(OUT)<10: raise RuntimeError("3D output is unexpectedly short")
print("3D render complete",OUT,dur(OUT))