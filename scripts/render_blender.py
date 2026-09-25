#!/usr/bin/env python3
"""
ContentPilot 3D renderer.
Creates original 3D human characters and a fully 3D bedroom in Blender,
then combines the rendered scenes with generated voice, music, SFX and subtitles.

The characters are procedural 3D designs, not copies of real people or existing
copyrighted characters. They are deliberately built with depth so the camera can
move around them instead of using flat 2D cut-outs.
"""
import bpy, math, os, json, subprocess, wave, struct, re, shutil
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "generated", "latest.json")
BUILD = os.path.join(ROOT, "build3d")
VIDEO = os.path.join(ROOT, "generated", "contentpilot-latest.mp4")
os.makedirs(BUILD, exist_ok=True)
data = json.load(open(DATA, encoding="utf-8"))
scripts = data["script"]
plans = data.get("scene_plan", [])

FPS = 18
W, H = 540, 960

def run(cmd):
    subprocess.run(cmd, check=True)

def probe(path):
    return float(subprocess.check_output(
        ["ffprobe","-v","error","-show_entries","format=duration",
         "-of","default=noprint_wrappers=1:nokey=1",path], text=True).strip())

def safe(s):
    return re.sub(r"[^A-Za-z0-9 .,:!?&'’()\\-_/]", "", s).strip()

def mat(name, color, metallic=0.0, rough=0.5):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*color,1)
    bs.inputs["Roughness"].default_value=rough
    bs.inputs["Metallic"].default_value=metallic
    return m

SKIN=mat("Skin",(0.64,0.34,0.22),0,0.48)
SKIN2=mat("SkinSoft",(0.78,0.48,0.32),0,0.52)
HAIR=mat("DarkHair",(0.025,0.018,0.025),0,0.32)
SHIRT=mat("ArjunShirt",(0.08,0.15,0.28),0,0.44)
PANTS=mat("ArjunPants",(0.055,0.065,0.08),0,0.55)
SHOE=mat("Shoes",(0.018,0.022,0.03),0,0.3)
WHITE=mat("EyeWhite",(0.93,0.93,0.9),0,0.22)
IRIS=mat("Iris",(0.06,0.22,0.55),0.05,0.25)
BLACK=mat("Pupil",(0.003,0.004,0.006),0,0.15)
BYTE_SKIN=mat("ByteSkin",(0.22,0.55,0.62),0.25,0.28)
BYTE_BODY=mat("ByteBody",(0.035,0.23,0.29),0.45,0.24)
BYTE_GLOW=mat("ByteGlow",(0.05,0.7,0.9),0.55,0.2)
WALL=mat("WarmWall",(0.39,0.31,0.30),0,0.72)
FLOOR=mat("WoodFloor",(0.22,0.13,0.10),0,0.7)
BED=mat("BedFrame",(0.12,0.075,0.07),0,0.62)
SHEET=mat("Sheet",(0.72,0.70,0.68),0,0.76)
PILLOW=mat("Pillow",(0.86,0.83,0.78),0,0.8)
RUG=mat("Rug",(0.30,0.18,0.19),0,0.9)
WOOD=mat("Wood",(0.30,0.17,0.12),0,0.6)
GOLD=mat("Gold",(0.7,0.42,0.10),0.65,0.25)
GLASS=mat("Glass",(0.08,0.22,0.31),0.1,0.15)
LAMP=mat("Lamp",(0.95,0.65,0.26),0,0.35)

def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for d in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        pass

def cube(name, loc, scale, material, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod=o.modifiers.new("SoftEdges","BEVEL"); mod.width=bevel; mod.segments=3
    o.data.materials.append(material)
    return o

def uv(name, loc, scale, material, seg=32, rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return o

def cyl_between(name, a, b, radius, material, vertices=24):
    a,b=Vector(a),Vector(b); v=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=v.length, location=(a+b)/2)
    o=bpy.context.object; o.name=name
    o.rotation_mode="QUATERNION"; o.rotation_quaternion=v.to_track_quat("Z","Y")
    o.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return o

def text_obj(body, loc, size, material, rot=(math.pi/2,0,0), align="CENTER"):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    o=bpy.context.object; o.data.body=body; o.data.align_x=align; o.data.size=size
    o.data.extrude=0.008; o.data.bevel_depth=0.002; o.data.materials.append(material)
    return o

def look_at(obj, target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()

def add_light(kind, loc, energy, color, size=3):
    if kind=="AREA":
        bpy.ops.object.light_add(type="AREA", location=loc)
    else:
        bpy.ops.object.light_add(type=kind, location=loc)
    l=bpy.context.object; l.data.energy=energy; l.data.color=color
    if hasattr(l.data,"shape"): l.data.shape="DISK"; l.data.size=size
    return l

def make_bedroom(action):
    # Real room volume: floor + three walls + ceiling trim. No flat background card.
    cube("Floor",(0,0,0),(5.2,5.2,0.12),FLOOR,0.04)
    cube("BackWall",(0,5.0,3.2),(5.2,0.12,3.2),WALL,0.04)
    cube("LeftWall",(-5.1,0,3.2),(0.12,5.0,3.2),WALL,0.04)
    cube("RightWall",(5.1,0,3.2),(0.12,5.0,3.2),WALL,0.04)
    # floor boards
    for y in [-4,-3,-2,-1,0,1,2,3,4]:
        cube("FloorBoard",(0,y,0.14),(5.0,0.012,0.008),WOOD,0)
    # large bed with mattress, headboard, pillows, blanket
    cube("BedBase",(0.8,2.3,0.65),(2.9,1.7,0.42),BED,0.16)
    cube("Mattress",(0.8,2.3,1.12),(2.75,1.58,0.28),SHEET,0.12)
    cube("Blanket",(1.2,2.45,1.45),(2.25,1.38,0.12),RUG,0.10)
    cube("Headboard",(0.8,3.78,2.05),(2.95,0.18,1.55),BED,0.10)
    for x in (-1.0,0.4,1.8):
        uv("Pillow",(x,3.25,1.55),(0.62,0.45,0.18),PILLOW)
    # nightstand + drawer
    cube("Nightstand",(3.65,3.15,1.15),(0.7,0.65,0.95),WOOD,0.08)
    cube("Drawer",(3.65,2.48,1.2),(0.48,0.04,0.28),BED,0.03)
    # lamp
    cyl_between("LampStem",(3.65,3.15,2.1),(3.65,3.15,3.0),0.07,WOOD)
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.48, radius2=0.25, depth=0.55, location=(3.65,3.15,3.2))
    bpy.context.object.data.materials.append(LAMP)
    # alarm clock
    cube("AlarmClock",(3.65,2.72,2.05),(0.48,0.12,0.28),BLACK,0.05)
    text_obj("07:00",(3.65,2.57,2.05),0.22,GOLD,rot=(math.pi/2,0,0))
    # window with frame and curtains
    cube("WindowGlass",(-2.8,4.82,4.0),(1.7,0.06,1.15),GLASS,0.02)
    cube("WindowFrameH",(-2.8,4.70,4.0),(1.8,0.04,0.06),WOOD)
    cube("WindowFrameV",(-2.8,4.70,4.0),(0.06,0.04,1.2),WOOD)
    for x in (-4.15,-1.45):
        cube("Curtain",(x,4.55,4.0),(0.45,0.15,1.55),RUG,0.12)
    # wall art
    cube("PictureFrame",(1.9,4.82,4.4),(0.9,0.05,0.7),WOOD,0.04)
    cube("Picture",(1.9,4.73,4.4),(0.76,0.03,0.56),GLASS,0.02)
    # rug
    cube("Rug",(0.0,-0.4,0.16),(2.5,1.65,0.035),RUG,0.10)
    # plant
    cube("PlantPot",(-3.9,3.5,0.75),(0.35,0.35,0.6),WOOD,0.05)
    for dx,dy,dz in [(-.4,0,1.8),(.2,.1,2.0),(.4,-.1,1.7)]:
        uv("Leaf",(-3.9+dx,3.5+dy,0.75+dz),(0.38,0.16,0.75),mat("LeafMat",(0.06,0.24,0.10),0,0.8))
    # phone on bed
    cube("Phone",(0.0,1.15,1.48),(0.34,0.62,0.04),BLACK,0.05)
    # practical warm/cool lighting
    add_light("AREA",(-2.5,1.0,5.8),850,(1.0,0.78,0.58),4.0)
    add_light("AREA",(3.4,-1.0,4.5),600,(0.62,0.75,1.0),3.0)
    bpy.ops.object.light_add(type="POINT", location=(3.65,3.15,3.25))
    bpy.context.object.data.energy=180; bpy.context.object.data.color=(1.0,0.56,0.25)

def make_character(name, loc, ai=False):
    skin=BYTE_SKIN if ai else SKIN
    body=BYTE_BODY if ai else SHIRT
    pants=BYTE_BODY if ai else PANTS
    parts=[]
    # proportions: adult human scale, head intentionally smaller than chibi proportions
    parts.append(uv(name+"_torso",(loc[0],loc[1],2.55),(0.48,0.30,0.78),body))
    parts.append(uv(name+"_hips",(loc[0],loc[1],1.82),(0.43,0.28,0.30),pants))
    parts.append(uv(name+"_head",(loc[0],loc[1],4.15),(0.38,0.34,0.47),skin))
    parts.append(cyl_between(name+"_neck",(loc[0],loc[1],3.55),(loc[0],loc[1],3.82),0.16,skin))
    # ears
    for sx in (-1,1):
        parts.append(uv(name+"_ear",(loc[0]+sx*0.36,loc[1],4.12),(0.08,0.10,0.15),skin))
    # hair cap + front locks
    parts.append(uv(name+"_hair",(loc[0],loc[1]+0.02,4.48),(0.40,0.36,0.25),HAIR if not ai else BYTE_BODY))
    for sx in (-.24,0,.24):
        parts.append(uv(name+"_bang",(loc[0]+sx,loc[1]-0.29,4.36),(0.13,0.07,0.24),HAIR if not ai else BYTE_BODY))
    # eyes on front (-Y)
    for sx in (-0.14,0.14):
        parts.append(uv(name+"_eye",(loc[0]+sx,loc[1]-0.315,4.19),(0.105,0.055,0.11),WHITE))
        parts.append(uv(name+"_iris",(loc[0]+sx,loc[1]-0.365,4.19),(0.045,0.025,0.055),IRIS if not ai else BYTE_GLOW))
        parts.append(uv(name+"_pupil",(loc[0]+sx,loc[1]-0.387,4.19),(0.020,0.012,0.035),BLACK))
    # nose + mouth
    parts.append(uv(name+"_nose",(loc[0],loc[1]-0.34,4.03),(0.045,0.04,0.07),SKIN2))
    parts.append(cube(name+"_mouth",(loc[0],loc[1]-0.355,3.92),(0.09,0.025,0.025),BLACK,0.02))
    # arms/legs
    for side in (-1,1):
        sx=loc[0]+side*0.53
        parts.append(cyl_between(name+"_upperarm",(sx*1.0,loc[1],3.05),(loc[0]+side*0.70,loc[1],2.35),0.13,body))
        parts.append(cyl_between(name+"_forearm",(loc[0]+side*0.70,loc[1],2.35),(loc[0]+side*0.72,loc[1],1.75),0.115,skin))
        parts.append(uv(name+"_hand",(loc[0]+side*0.72,loc[1],1.66),(0.13,0.12,0.16),skin))
        parts.append(cyl_between(name+"_leg",(loc[0]+side*0.20,loc[1],1.65),(loc[0]+side*0.22,loc[1],0.65),0.17,pants))
        parts.append(cube(name+"_shoe",(loc[0]+side*0.22,loc[1]-0.12,0.43),(0.20,0.34,0.12),SHOE,0.08))
    if ai:
        # subtle chest light, not a toy/robot scanline effect
        parts.append(uv(name+"_chestlight",(loc[0],loc[1]-0.30,2.55),(0.11,0.035,0.11),BYTE_GLOW))
    for p in parts:
        p["cp_name"]=name
    return parts

def pose_character(name, action, frame, end, ai=False):
    objs=[o for o in bpy.context.scene.objects if o.get("cp_name")==name]
    # Whole-character movement is subtle; limb motion uses object rotations around local origins.
    phase=frame/max(1,end)
    dx=0.025*math.sin(phase*math.pi*2)
    for o in objs:
        if o.name.endswith("_torso") or o.name.endswith("_head") or o.name.endswith("_hips"):
            base=o.location.copy(); o.location.x += dx
    # sleeping: place Arjun low and turned sideways by moving the whole collection
    if action=="sleepy" and not ai:
        for o in objs:
            o.location.z -= 0.65
            o.rotation_euler.y = math.radians(62)
    # exaggerated but still human-scale gestures
    for o in objs:
        if "upperarm" in o.name or "forearm" in o.name:
            if action in ("negotiating","pleading","asking"):
                o.rotation_euler.x=math.radians(-25 + 12*math.sin(phase*math.pi*2))
                o.rotation_euler.z=math.radians(18 if "upperarm" in o.name else 8)
            elif action in ("alarm_ringing","showing_record","showing_backup"):
                o.rotation_euler.x=math.radians(-35)
            elif action in ("getting_up","running"):
                o.rotation_euler.x=math.radians(20*math.sin(phase*math.pi*2))
            else:
                o.rotation_euler.x=math.radians(8*math.sin(phase*math.pi*2))

def setup_camera(index, action):
    bpy.ops.object.camera_add(location=(7.4,-11.0,6.0))
    cam=bpy.context.object
    angles=[
        (7.2,-11.5,5.6),(4.8,-12.8,5.0),(8.6,-8.8,5.4),
        (1.0,-13.8,5.3),(-5.5,-11.0,5.6),(6.5,-10.0,7.4),
        (3.0,-13.0,4.6),(-4.0,-12.5,6.5)
    ]
    x,y,z=angles[index%len(angles)]
    cam.location=(x,y,z)
    look_at(cam,(0.4,1.5,2.4))
    bpy.context.scene.camera=cam
    return cam

def music_wav(path, seconds, style):
    sr=44100; n=int(seconds*sr); buf=[0.0]*n
    scales={"playful":[523.25,659.25,783.99,659.25],"curious":[392,466.16,587.33,523.25],
            "tension":[220,233.08,261.63,233.08],"chaos":[330,392,311.13,466.16],
            "punchline":[659.25,783.99,987.77,1046.5]}
    notes=scales.get(style,scales["playful"]); beat=0.28
    for k in range(int(seconds/beat)+1):
        f=notes[k%len(notes)]; start=int(k*beat*sr)
        ln=min(int(beat*.72*sr),n-start)
        for j in range(max(0,ln)):
            t=j/sr; env=min(1,t*35,max(0,(ln/sr-t)*9))
            buf[start+j]+=0.07*env*math.sin(2*math.pi*f*t)+0.025*env*math.sin(2*math.pi*f*.5*t)
    with wave.open(path,"wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<h",max(-32767,min(32767,int(v*32767)))) for v in buf))

def sfx_wav(path, seconds, scene):
    sr=44100; n=int(seconds*sr); buf=[0.0]*n
    events=[("pop",0.0),("whoosh",max(.18,seconds*.55))]
    if scene%4==1: events=[("ding",0.0),("error",max(.2,seconds*.55))]
    for typ,at in events:
        st=int(at*sr); ln=max(1,int(min(.38,seconds-at)*sr))
        for j in range(ln):
            t=j/sr; env=min(1,t*80,max(0,(ln/sr-t)*12))
            if typ=="pop": v=math.sin(2*math.pi*(180+700*t)*t)*.18*env
            elif typ=="whoosh": v=math.sin(2*math.pi*(180+1800*t)*t)*.08*env
            elif typ=="error": v=(math.sin(2*math.pi*95*t)+.5*math.sin(2*math.pi*140*t))*.14*env
            else: v=math.sin(2*math.pi*(900+900*t)*t)*.15*env
            if st+j<n: buf[st+j]+=v
    with wave.open(path,"wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<h",max(-32767,min(32767,int(v*32767)))) for v in buf))

# Render each spoken line as its own short 3D shot.
segments=[]; audios=[]; total=0.0
styles=["playful","curious","tension","chaos","punchline","playful"]
for i,line in enumerate(scripts):
    voice=os.path.join(BUILD,f"voice_{i}.wav")
    spoken=safe(line)
    run(["espeak-ng","-v","en-us","-s","156","-p","50","-w",voice,spoken])
    vd=probe(voice); dur=max(2.2,min(6.5,vd+0.30))
    audios.append((voice,dur))
    clear()
    scene=bpy.context.scene
    scene.render.engine="BLENDER_EEVEE_NEXT"
    scene.render.resolution_x=W; scene.render.resolution_y=H; scene.render.resolution_percentage=100
    scene.render.fps=FPS
    scene.render.image_settings.file_format="FFMPEG"
    scene.render.ffmpeg.format="MPEG4"; scene.render.ffmpeg.codec="H264"; scene.render.ffmpeg.constant_rate_factor="MEDIUM"
    scene.render.film_transparent=False
    scene.world.color=(0.025,0.03,0.05)
    make_bedroom(plans[i].get("action","talking") if i<len(plans) else "")
    action=plans[i].get("action","talking") if i<len(plans) else "talking"
    actor=plans[i].get("actor","arjun") if i<len(plans) else "arjun"
    arjun=make_character("arjun",(-1.1,0.3,0),False)
    byte=make_character("byte",(1.9,1.0,0),True)
    # Put characters on the floor with natural depth and slight turn toward each other.
    for o in arjun:
        o.rotation_euler.z=math.radians(-4)
    for o in byte:
        o.rotation_euler.z=math.radians(8)
    if action=="sleepy":
        for o in arjun:
            o.location.y += 1.9; o.location.z += 0.1
    if action in ("alarm_ringing","showing_record","showing_backup"):
        # Byte stands closer to the nightstand/bed.
        for o in byte: o.location.x -= 0.4
    if action in ("negotiating","pleading"):
        for o in arjun: o.location.x += 0.15; o.location.y += 0.55
    cam=setup_camera(i,action)
    scene.frame_start=1; scene.frame_end=max(2,int(dur*FPS))
    # Small camera drift gives each shot real motion instead of a still cut-out.
    base=cam.location.copy()
    cam.keyframe_insert(data_path="location",frame=1)
    cam.location.x += 0.35; cam.location.y += 0.20
    look_at(cam,(0.4,1.5,2.4)); cam.keyframe_insert(data_path="location",frame=scene.frame_end)
    for fr in (1,scene.frame_end):
        pose_character("arjun",action,fr,scene.frame_end,False)
        pose_character("byte",action,fr,scene.frame_end,True)
    out=os.path.join(BUILD,f"scene_{i}.mp4")
    scene.render.filepath=out
    bpy.ops.render.render(animation=True)
    segments.append(out)

# Concatenate silent 3D shots.
concat=os.path.join(BUILD,"concat.txt")
with open(concat,"w") as f:
    for s in segments: f.write("file '"+s.replace("'","'\\\\''")+"'\n")
silent=os.path.join(BUILD,"silent.mp4")
run(["ffmpeg","-y","-f","concat","-safe","0","-i",concat,"-c","copy",silent])

# Build a single mixed audio track and SRT subtitles with exact scene timings.
audio_list=[]
srt=[]
clock=0.0
for i,(voice,dur) in enumerate(audios):
    music=os.path.join(BUILD,f"music_{i}.wav"); sfx=os.path.join(BUILD,f"sfx_{i}.wav")
    music_wav(music,dur,styles[i%len(styles)]); sfx_wav(sfx,dur,i)
    mix=os.path.join(BUILD,f"mix_{i}.wav")
    run(["ffmpeg","-y","-i",voice,"-i",music,"-i",sfx,"-filter_complex",
         "[0:a]volume=1.0[a];[1:a]volume=0.14[b];[2:a]volume=0.25[c];[a][b][c]amix=inputs=3:duration=longest:normalize=0,alimiter=limit=0.92",
         "-ar","44100","-ac","1",mix])
    audio_list.append(mix)
    def ts(x):
        ms=int(round((x-int(x))*1000)); sec=int(x); h=sec//3600; m=(sec%3600)//60; s=sec%60
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    raw=safe(line if i==len(audios)-1 else scripts[i])
    speaker,_,words=raw.partition(":")
    name="Byte" if (i<len(plans) and plans[i].get("actor")=="byte") else "Arjun"
    srt.append(f"{i+1}\\n{ts(clock)} --> {ts(clock+dur)}\\n{name}: {words.strip()}\\n")
    clock += dur

# Concatenate individual audio mixes.
alist=os.path.join(BUILD,"audio_concat.txt")
with open(alist,"w") as f:
    for a in audio_list: f.write("file '"+a.replace("'","'\\\\''")+"'\n")
audio=os.path.join(BUILD,"audio.wav")
run(["ffmpeg","-y","-f","concat","-safe","0","-i",alist,"-c","copy",audio])

srt_path=os.path.join(BUILD,"dialogue.srt")
open(srt_path,"w",encoding="utf-8").write("\\n".join(srt))

# Burn readable subtitles and mux final audio.
escaped=srt_path.replace("\\\\","/").replace(":","\\\\:")
vf=f"subtitles='{escaped}':force_style='FontName=DejaVu Sans,FontSize=18,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00101010,Outline=3,Shadow=1,MarginV=105,Alignment=2'"
run(["ffmpeg","-y","-i",silent,"-i",audio,"-vf",vf,"-map","0:v","-map","1:a","-c:v","libx264","-preset","veryfast","-crf","21","-pix_fmt","yuv420p","-c:a","aac","-b:a","128k","-shortest",VIDEO])
print("3D render complete:",VIDEO)
print("Duration:",probe(VIDEO))
