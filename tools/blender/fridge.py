import bpy, bmesh, math, sys
from mathutils import Vector
OUT=sys.argv[sys.argv.index('--')+1]; ANGLE=float(sys.argv[sys.argv.index('--')+2]) if len(sys.argv)>sys.argv.index('--')+2 else 0
bpy.ops.wm.read_factory_settings(use_empty=True)
W,D,H=0.70,0.66,1.70          # body
FZ=0.58                       # freezer height (top section)
G=0.012                       # gap
T=0.055                       # door thickness
R=0.035                       # corner radius
def mat(name,c,rough=0.45,metal=0.0):
    m=bpy.data.materials.new(name); m.use_nodes=True; b=m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value=(*c,1); b.inputs['Roughness'].default_value=rough; b.inputs['Metallic'].default_value=metal; return m
M_BODY=mat('Body',(0.93,0.95,0.96)); M_DOOR=mat('Door',(0.95,0.96,0.97),0.32); M_HANDLE=mat('Handle',(0.62,0.66,0.72),0.3,0.6)
M_IN=mat('Interior',(0.86,0.93,0.97),0.6); M_SEAL=mat('Seal',(0.16,0.17,0.2),0.8); M_FOOT=mat('Foot',(0.18,0.19,0.22),0.7); M_BIN=mat('Bin',(0.70,0.84,0.93),0.35); M_FROST=mat('Frost',(0.97,0.99,1.0),0.9)
def box(name,size,loc,m,bevel=0.0,seg=3,parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.active_object; o.name=name; o.scale=size; bpy.ops.object.transform_apply(scale=True)
    if bevel>0:
        bv=o.modifiers.new('bv','BEVEL'); bv.width=bevel; bv.segments=seg; bv.limit_method='NONE'; bpy.ops.object.modifier_apply(modifier='bv')
    o.data.materials.append(m)
    if parent: o.parent=parent
    bpy.ops.object.shade_smooth()
    return o
# --- body: one shell, the freezer cavity cut into the front-top
body=box('Body',(W,D,H),(0,0,H/2),M_BODY,R,4)
cav_w,cav_d,cav_h=W-0.09,D-0.08,FZ-0.085
cav=box('Cav',(cav_w,cav_d,cav_h),(0,-D/2+cav_d/2-0.001,H-0.045-cav_h/2),M_IN,0.012,2)
bm=body.modifiers.new('cut','BOOLEAN'); bm.operation='DIFFERENCE'; bm.object=cav; bpy.context.view_layer.objects.active=body; bpy.ops.object.modifier_apply(modifier='cut')
# the cut surfaces take the interior colour
body.data.materials.append(M_IN); 
for p in body.data.polygons:
    c=p.center
    if abs(c.x)<cav_w/2-1e-3 and c.y>-D/2+0.002 and c.y<-D/2+cav_d+0.002 and c.z>H-0.045-cav_h-1e-3 and c.z<H-0.045+1e-3 and not (c.y<-D/2+0.004):
        p.material_index=1
bpy.data.objects.remove(cav,do_unlink=True)
# interior: a shelf, two bins, a frost layer on the back
def inter(name,size,loc,m,b=0.01): 
    o=box(name,size,loc,m,b,2); o.parent=body; return o
zt=H-0.045; zb=zt-cav_h; yb=-D/2+0.04
import random; random.seed(7)
inter('Shelf',(cav_w-0.04,cav_d-0.12,0.018),(0,yb+(cav_d-0.12)/2+0.06,zb+cav_h*0.66),M_FROST,0.006)
hh=0.09; zz=zb+cav_h*0.66+0.02
inter('Bin',(cav_w-0.1,cav_d-0.2,hh),(0,yb+0.02+(cav_d-0.2)/2+0.05,zz+hh/2),M_BIN,0.012)
ins=box('BinIn',(cav_w-0.12,cav_d-0.22,hh-0.02),(0,yb+0.02+(cav_d-0.2)/2+0.05,zz+hh/2+0.02),M_IN,0.01,2); ins.parent=body
# --- frost: lumps and drifts on the back wall, the ceiling, the corners and the floor edge; icicles under the shelf
xl,xr=-cav_w/2+0.01,cav_w/2-0.01; yback=-D/2+cav_d
M_FROST2=mat('Rime',(0.90,0.95,0.99),0.9)
def patch(x,y,z,rx,rz,axis):   # a thin, flat frost patch lying on a wall (axis: the wall's normal)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=9,ring_count=5,location=(x,y,z)); o=bpy.context.active_object
    if axis=='y': o.scale=(rx,0.0022,rz)
    elif axis=='x': o.scale=(0.0022,rx,rz)
    else: o.scale=(rx,rz,0.0022)
    bpy.ops.object.transform_apply(scale=True); return o
ps=[]
for i in range(26): ps.append(patch(random.uniform(xl+0.05,xr-0.05),yback-0.001,random.uniform(zb+0.05,zt-0.05),random.uniform(0.025,0.075),random.uniform(0.02,0.06),'y'))
for sx in (xl,xr):
    for i in range(9): ps.append(patch(sx+(0.001 if sx<0 else -0.001),random.uniform(-D/2+0.12,yback-0.05),random.uniform(zb+0.05,zt-0.05),random.uniform(0.03,0.07),random.uniform(0.02,0.05),'x'))
for i in range(10): ps.append(patch(random.uniform(xl+0.05,xr-0.05),random.uniform(-D/2+0.12,yback-0.05),zt-0.001,random.uniform(0.03,0.07),random.uniform(0.03,0.07),'z'))
for nm,sz,lc in (('RimTop',(cav_w-0.02,0.03,0.022),(0,yback-0.014,zt-0.011)),('RimL',(0.024,0.03,cav_h-0.02),(xl+0.012,yback-0.014,(zt+zb)/2)),('RimR',(0.024,0.03,cav_h-0.02),(xr-0.012,yback-0.014,(zt+zb)/2)),('RimBack',(cav_w-0.02,0.03,0.02),(0,yback-0.014,zb+0.01))):
    r=box(nm,sz,lc,M_FROST,0.01,2); ps.append(r)
bpy.ops.object.select_all(action='DESELECT')
for o in ps: o.select_set(True)
bpy.context.view_layer.objects.active=ps[0]; bpy.ops.object.join(); fr=bpy.context.active_object; fr.name='Frost'; bpy.ops.object.transform_apply(location=True,rotation=True,scale=True); fr.data.materials.clear(); fr.data.materials.append(M_FROST2); fr.parent=body; bpy.ops.object.shade_smooth()
ics=[]
for i in range(7):    # a few fine icicles under the shelf and along the ceiling
    h=random.uniform(0.025,0.055); x=random.uniform(xl+0.06,xr-0.06); y=random.uniform(-D/2+0.15,yback-0.06); z=(zb+cav_h*0.66-0.005) if i<4 else zt-0.01
    bpy.ops.mesh.primitive_cone_add(vertices=5,radius1=random.uniform(0.005,0.009),depth=h,location=(x,y,z-h/2)); c=bpy.context.active_object; c.rotation_euler=(math.pi,0,0); ics.append(c)
bpy.ops.object.select_all(action='DESELECT')
for o in ics: o.select_set(True)
bpy.context.view_layer.objects.active=ics[0]; bpy.ops.object.join(); ic=bpy.context.active_object; ic.name='Icicles'; bpy.ops.object.transform_apply(location=True,rotation=True,scale=True); ic.data.materials.append(M_FROST2); ic.parent=body; bpy.ops.object.shade_smooth()
# some frosted boxes in the upper bin, for scale
for i,(bx,by,bz) in enumerate(((-0.17,0.05,0.07),(0.12,0.02,0.06))):
    pk=box('Pack%d'%i,(0.16,0.12,0.06),(bx,yb+0.02+(cav_d-0.2)/2+0.05+by,zz+0.02+0.03+bz*0.2),M_FROST,0.008,2); pk.parent=body
# --- hinges: two brackets on the body and two pins
for nm,hz in (('HingeUp',H-0.03),('HingeLow',H-FZ+0.03)):
    pl=box(nm+'Plate',(0.03,0.05,0.06),(-W/2-0.008,-D/2-0.02,hz),M_HANDLE,0.006,2); pl.parent=body
    bpy.ops.mesh.primitive_cylinder_add(vertices=10,radius=0.011,depth=0.075,location=(-W/2-0.003,-D/2-0.03,hz)); pn=bpy.context.active_object; pn.name=nm+'Pin'; pn.data.materials.append(M_HANDLE); pn.parent=body; bpy.ops.object.shade_smooth()
# --- lower door (closed, solid), a handle
lz=(H-FZ-G)/2
ld=box('FridgeDoor',(W-0.012,T,H-FZ-G*1.5),(0,-D/2-T/2+0.004,lz),M_DOOR,R*0.9,4)
lh=box('FridgeHandle',(0.026,0.04,0.42),(W/2-0.075,-D/2-T-0.012,lz+0.40),M_HANDLE,0.011,3)
# --- freezer door: pivot at the left hinge, so it can swing in the game
pivot=bpy.data.objects.new('FreezerHinge',None); bpy.context.collection.objects.link(pivot); pivot.location=(-W/2+0.006,-D/2-0.001,H-FZ/2-0.005)
fh_h=FZ-G*0.5-0.004
fd=box('FreezerDoor',(W-0.012,T,fh_h),(0,-T/2,0),M_DOOR,R*0.9,4,parent=None); fd.parent=pivot; fd.location=(W/2-0.006,-T/2,0)
sw,sh=W-0.075,fh_h-0.07; st=0.022
for nm,sz,lc in (('SealT',(sw,0.012,st),(0,T/2+0.003,sh/2-st/2)),('SealB',(sw,0.012,st),(0,T/2+0.003,-sh/2+st/2)),('SealL',(st,0.012,sh),(-sw/2+st/2,T/2+0.003,0)),('SealR',(st,0.012,sh),(sw/2-st/2,T/2+0.003,0))):
    sp=box(nm,sz,lc,M_SEAL,0.004,2); sp.parent=fd
for k,zz in enumerate((-0.17,0.0,0.17)):   # door-inside shelf ledges
    lg=box('Ledge%d'%k,(sw-0.1,0.03,0.014),(0,T/2+0.022,zz),M_BIN,0.006,2); lg.parent=fd
fhd=box('FreezerHandle',(0.026,0.04,0.30),(0,0,0),M_HANDLE,0.011,3); fhd.parent=fd; fhd.location=(W/2-0.075,-T/2-0.016,-0.08)
# --- feet
for sx in (-1,1):
    for sy in (-1,1):
        f=box('Foot',(0.07,0.07,0.04),(sx*(W/2-0.07),sy*(D/2-0.08),0.02),M_FOOT,0.015,2)
# --- open the freezer for the preview / the animation
pivot.rotation_euler=(0,0,math.radians(-ANGLE))
sc=bpy.context.scene
if ANGLE==0:
    pivot.rotation_mode='XYZ'; sc.frame_start=1; sc.frame_end=24
    pivot.rotation_euler=(0,0,0); pivot.keyframe_insert('rotation_euler',frame=1)
    pivot.rotation_euler=(0,0,math.radians(-108)); pivot.keyframe_insert('rotation_euler',frame=24)
    pivot.rotation_euler=(0,0,0)
    for o in bpy.data.objects:
        pass
    pivot.animation_data.action.name='FreezerOpen'
# --- export
bpy.ops.object.select_all(action='SELECT')
tris=sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH')
if ANGLE==0:
    bpy.ops.export_scene.gltf(filepath=OUT,export_format='GLB',export_apply=True,export_animations=True,export_yup=True)
    print('exported',OUT)
else:
    sc.render.engine='CYCLES'; sc.cycles.samples=48; sc.cycles.device='CPU'; sc.render.resolution_x=900; sc.render.resolution_y=1000
    w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(0.22,0.28,0.4,1); w.node_tree.nodes['Background'].inputs[1].default_value=1.0
    bpy.ops.mesh.primitive_plane_add(size=8,location=(0,0,0)); fl=bpy.context.active_object; fl.data.materials.append(mat('Floor',(0.77,0.60,0.40),0.8))
    for loc,en in (((2.5,-3,3.2),420),((-3,-2.5,1.6),160)):
        bpy.ops.object.light_add(type='AREA',location=loc); l=bpy.context.active_object; l.data.energy=en; l.data.size=2.5
        l.rotation_euler=(Vector((0,0,0.9))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(location=(1.7,-3.6,1.25)); cam=bpy.context.active_object; cam.data.lens=40
    cam.location=eval(__import__('os').environ.get('CAM','(1.7,-3.6,1.25)'))
    cam.rotation_euler=(Vector((0,0,0.9))-cam.location).to_track_quat('-Z','Y').to_euler(); sc.camera=cam
    sc.render.filepath=OUT; bpy.ops.render.render(write_still=True); print('rendered',OUT)
print('faces',tris)
