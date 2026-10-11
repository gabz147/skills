---
name: blender-fit-assets
description: Fit hair, clothing, armor, or accessories onto a character body in Blender when each piece is a separate mesh or GLB. Use this whenever assets arrive as separate files that must end up as one wearable character, when someone says "put the hoodie on her", "fit this hair to the model", "the clothes are floating / clipping / the wrong size", "dress this character", or when parts import at mismatched scale or origin. Covers scale matching, alignment, binding to a rig, Surface Deform and Data Transfer, and verifying the fit with renders instead of guessing.
---

# Fitting hair and clothing onto a body

Separately generated body, hair, and garment meshes never arrive aligned. Getting them to read as one character is a fixed sequence, and doing it out of order wastes the most time: people usually try to eyeball a position before checking scale, then redo it.

Related: `blender-autorig` (get the body rigged first), `blender-headless` (run all of this from the CLI).

## Order of operations

1. **Measure before moving anything.** Compare bounding boxes. A garment authored at a different scale looks like a position problem and isn't.
2. **Match scale**, uniformly, using a real landmark — shoulder width or height between two known points, not the overall bbox (hair and long coats distort the bbox).
3. **Align origins**, then position by landmark: hair to skull crown, garment to shoulders and chest.
4. **Bind.** If the body is rigged, parent the garment to the same armature — this is the step that makes fitting durable instead of a one-frame trick.
5. **Resolve intersections** — shrink or mask the body under the garment.
6. **Verify with renders** from at least three angles.

If the body has no armature, stop and rig it first (`blender-autorig`). Binding clothing to an unrigged body means every future pose breaks the fit, and you will do this work twice.

## Measuring

```python
import bpy, json
from mathutils import Vector

def world_bbox(obs):
    pts = [ob.matrix_world @ Vector(c) for ob in obs for c in ob.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi, hi - lo

for coll in bpy.data.collections:
    meshes = [o for o in coll.all_objects if o.type == 'MESH']
    if not meshes:
        continue
    lo, hi, size = world_bbox(meshes)
    print(coll.name, "size", [round(v, 3) for v in size], "center",
          [round(v, 3) for v in (lo + hi) / 2])
```

One collection per source file keeps each asset movable as a unit — worth setting up at import time.

## Binding

**Rigged body, garment following the skeleton** — the durable option:

```python
garment.modifiers.new("Armature", 'ARMATURE').object = armature
```

The garment needs vertex groups named after the bones. Transfer them from the body rather than painting weights by hand:

```python
dt = garment.modifiers.new("DataTransfer", 'DATA_TRANSFER')
dt.object = body
dt.use_vert_data = True
dt.data_types_verts = {'VGROUP_WEIGHTS'}
dt.vert_mapping = 'POLYINTERP_NEAREST'
```

Transfer quality depends on the garment already sitting close to the body — another reason scale and alignment come first.

**Unrigged, or a garment that should deform with the surface** — Surface Deform binds a garment to the body mesh so body shape changes carry through:

```python
sd = garment.modifiers.new("SurfaceDeform", 'SURFACE_DEFORM')
sd.target = body
bpy.context.view_layer.objects.active = garment
bpy.ops.object.surfacedeform_bind(modifier=sd.name)
```

Bind fails silently if the garment is not enclosing/near the target — check `sd.is_bound` afterwards.

**Hair** is usually rigid: parent it to the head bone rather than skinning it, unless it's meant to swing.

## Clipping

Body poking through clothing is the most common visible defect. Options, cheapest first: a Shrinkwrap on the garment with a small offset; a Mask modifier on the body driven by a vertex group covering the hidden area; or deleting the covered body geometry outright if the garment is never removed.

The Shrinkwrap has to be **limited to the vertices that are actually penetrating**, or it does more damage than the clipping did. Build the group by testing each garment vertex against a BVH of the body: negative dot product between `(vertex - nearest_point)` and the surface normal means it is under the skin.

```python
from mathutils.bvhtree import BVHTree
bvh = BVHTree.FromPolygons(verts, faces)          # joined proxy of every body mesh
loc, nor, idx, dist = bvh.find_nearest(world_co)
inside = (world_co - loc).dot(nor) < 0
```

Then `wrap_mode='OUTSIDE_SURFACE'` with an offset around 0.01 (scene units) and `vertex_group` set to that group.

Three failure modes worth knowing before you hit them:

- **Shrinkwrapping the whole garment** pulls puffy sleeves flat onto the arms and shreds high-cut hip lines. Constrain the group by height and to the torso column as well as by penetration.
- **Adding a Smooth modifier over the corrected group** re-introduces the clipping it was meant to hide — the smoothing pulls corrected vertices back under the skin. Leave it off; the offset does the work.
- **Translating the garment to cover a gap** only trades one clipping face for the other when the garment is simply shallower than the body. Measure both depths before moving anything; if the garment is thinner than the body, the fix is a local correction, not a nudge.

## Repos worth pulling in

- **`makehumancommunity/mpfb2`** — MakeHuman for Blender. Its asset-fitting code is the readable reference implementation of this whole problem; read it before inventing a fitting algorithm.
- **`saturday06/VRM-Addon-for-Blender`** — actively maintained through Blender 5.2. Humanoid bone mapping and avatar export.
- **`absolute-quantum/cats-blender-plugin`** — merge armatures, attach clothing and hair to an avatar rig. Powerful but **last updated 2024-05 against Blender 2.9–3.x**; expect breakage on 5.x and treat it as a source of technique rather than a dependency.
- **`soupday/cc_blender_tools`** — Character Creator importer; a mature example of handling a multi-part character with hair, clothing, and materials together.
- **`Meshcapade/SMPL_blender_addon`** — parametric body, when the fit needs to be driven by body shape.

## Verify with renders, not with confidence

Fit is a visual property. Render front, side, and three-quarter views and actually look at them:

```python
import bpy, math
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'   # 5.1.1 enum; _NEXT was the 4.2-4.4 spelling
scene.render.resolution_x = scene.render.resolution_y = 900
for name, angle in (("front", 0), ("side", 90), ("three_quarter", 45)):
    # orbit the camera around Z, keep it aimed at the character, then:
    scene.render.filepath = f"//checks/{name}.png"
    bpy.ops.render.render(write_still=True)
```

If reference images were supplied, compare against them explicitly and name the differences (silhouette, hem length, hair volume) — "looks right" is not a check. Iterate until the render matches, and if two attempts fail the same way, the problem is usually upstream: wrong scale, or binding to a rig that was already bad.
