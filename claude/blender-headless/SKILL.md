---
name: blender-headless
description: Drive Blender from the command line or an agent instead of the GUI — bpy scripting, batch GLB/FBX import, headless renders, blender-mcp, BlenderProc, fake-bpy-module stubs. Use this whenever Blender work needs to happen without a human clicking, when someone says "script this in Blender", "import these models", "render a check image", "run blender headless", "batch process these .blend files", or when an agent needs to inspect or modify a .blend and verify the result. Also use as the execution layer under any rigging or asset-fitting task.
---

# Driving Blender headlessly

Blender's GUI is not the interface for agent work — a scripted run is reproducible, reviewable, and its result can be verified without anyone looking at a viewport. This skill is the execution layer under `blender-autorig` and `blender-fit-assets`.

Local install: `C:\Program Files\Blender Foundation\Blender 5.1\blender.exe`.

## The basic invocation

```bash
"C:/Program Files/Blender Foundation/Blender 5.1/blender.exe" \
  -b scene.blend --factory-startup --python script.py -- --arg value
```

- `-b` is background (no window). Drop it only when a human needs to watch.
- `--factory-startup` ignores user prefs and add-ons, so a run behaves the same everywhere. Omit it when the script depends on an installed add-on.
- Everything after the bare `--` goes to your script, readable via `sys.argv[sys.argv.index("--") + 1:]`.
- Without an input .blend, Blender starts from the default scene — delete the default cube before measuring anything.

**Write the script to a file with the Write tool, then point Blender at it.** Piping Python through a shell heredoc mangles backslashes in Windows paths — this has already corrupted a script on this machine once. A real file removes the escaping layer entirely.

## Always emit a machine-readable report

The headless run's stdout is buried in Blender's own logging. Have the script write a JSON report and read that instead — this is what makes the result verifiable rather than assumed:

```python
import bpy, json, pathlib

report = {
    "objects": len(bpy.data.objects),
    "meshes": {o.name: len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH'},
    "armatures": {o.name: len(o.data.bones) for o in bpy.data.objects if o.type == 'ARMATURE'},
    "collections": {c.name: len(c.all_objects) for c in bpy.data.collections},
    "materials": [m.name for m in bpy.data.materials],
}
pathlib.Path(r"C:\path\to\report.json").write_text(json.dumps(report, indent=2))
```

## Importing assets into their own collection

Multi-asset scenes stay workable when each source file lands in its own collection — you can hide, move, or delete an asset as a unit. `import_scene.gltf` drops everything into the active collection, so capture what's new and relink it:

```python
import bpy

def import_into_collection(path, name):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)          # .obj/.fbx have their own operators
    new = [o for o in bpy.data.objects if o not in before]
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    for ob in new:
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        coll.objects.link(ob)
    return coll, new
```

Import at authored origin and don't invent offsets — for a body plus hair plus clothing, a shared origin is the point, and guessed offsets have to be undone later. Fix alignment deliberately (see `blender-fit-assets`), not as a side effect of import.

## Rendering a check image

```python
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'   # 5.1.1 enum: BLENDER_EEVEE | BLENDER_WORKBENCH | CYCLES
scene.render.resolution_x = scene.render.resolution_y = 900
scene.render.filepath = r"C:\path\to\check.png"
bpy.ops.render.render(write_still=True)
```

A render is the cheapest real verification available headlessly. Read the resulting PNG back and look at it — a script that reports "177 objects imported" tells you nothing about whether the character looks right.

Note: armature `show_in_front` and bone overlays don't appear in an F12 render. To see bones in an image, build cone geometry along them.

## Tooling

**`ahujasid/blender-mcp`** — the highest-leverage option when an agent needs a live conversation with Blender instead of a script-and-report loop. Two halves: `addon.py` installed in Blender (opens a socket server), and an MCP server the client launches:

```json
{ "mcpServers": { "blender": { "command": "uvx", "args": ["--python", "3.11", "blender-mcp"] } } }
```

Or `claude mcp add blender uvx blender-mcp`. Blender must be running with the add-on enabled and its server started. Upgrading means replacing `addon.py` *and* re-adding the MCP server.

**`DLR-RM/BlenderProc`** — `pip install blenderproc`, then `blenderproc run your_script.py`. It manages its own Blender install and is the reference for deterministic, procedural scene assembly and batch rendering. Worth reading even if you don't adopt it.

**`nutti/fake-bpy-module`** — `pip install fake-bpy-module-<version>` gives bpy autocomplete and type checking in the editor. bpy has an enormous API surface and no stubs by default; this is the difference between writing scripts and guessing at attribute names.

**`KhronosGroup/glTF-Blender-IO`** — the actual importer/exporter source. Read it when a GLB comes in with wrong axes, broken materials, or lost node names, instead of guessing at operator flags.

**`agmmnn/awesome-blender`** — curated index for anything not covered here.

## Gotchas

- Tripo-generated FBX imports with front axis **+X**, not -Y.
- `bpy.ops` depends on context. In background mode there is no active view layer state to rely on — prefer direct data-API calls (`bpy.data`, modifier objects, matrices) over operators, and set `bpy.context.view_layer.objects.active` explicitly when an operator is unavoidable.
- Save explicitly with `bpy.ops.wm.save_as_mainfile(filepath=...)`; a background run discards everything otherwise.
- Keep long-running work out of the user's GUI session — a headless run against a copy of the .blend can't corrupt the file they have open.
