---
name: blender-autorig
description: Give an unrigged 3D mesh a skeleton and skinning weights — UniRig, Rigify/GameRig, Tripo auto-rig, RigAnything/SkinTokens. Use this whenever a GLB/FBX/OBJ has no armature and needs one, when a character can't be posed or animated, when hair or clothing needs a rig to bind to, when someone says "rig this", "add bones", "make it animatable", "auto rig", "skin this mesh", or when a Tripo/text-to-3D generation lands as static geometry. Also use before fitting clothing to a body, since the rig is what the clothing binds to.
---

# Auto-rigging meshes in Blender

Rigging is the gate on almost everything else: you can't pose, animate, or cleanly bind clothing to a mesh that has no armature. This skill covers picking a rigger and driving it end to end.

Local Blender is `C:\Program Files\Blender Foundation\Blender 5.1\blender.exe`. See `blender-headless` for how to run it from the CLI, and `blender-fit-assets` for what to do once a rig exists.

## Pick the rigger

| Situation | Use | Why |
|---|---|---|
| Arbitrary mesh, no skeleton, want it local and repeatable | **UniRig** | ML auto-rig from VAST-AI (Tripo's lab). Handles humanoids, animals, props. Produces skeleton *and* skinning weights. |
| Model was generated on Tripo and the account owns it | **Tripo web auto-rig** | 20 credits, humanoid preset, exports a 41-bone Mixamo-style skeleton. Fastest path when it applies. Procedure and account gotchas are in the vault note `Tripo Rig and DCC Bridge`. |
| Want a hand-authored control rig for a game engine | **Rigify + GameRig** | Rigify ships with Blender; GameRig is a Rigify feature set producing engine-compatible bone hierarchies. |
| UniRig's skinning comes out poor | **RigAnything**, **SkinTokens** | Same problem, different papers. Worth trying before hand-weighting. |

Prefer whichever gives a skeleton the downstream consumer expects. If the target is Mixamo animations or a game engine, bone *names* matter as much as bone placement — check them before accepting a rig.

## UniRig

Repo: `VAST-AI-Research/UniRig`. Weights on HuggingFace (`VAST-AI/UniRig`).

Install (from the repo README; needs CUDA):

```bash
conda create -n UniRig python=3.11
conda activate UniRig
python -m pip install torch torchvision
python -m pip install -r requirements.txt
python -m pip install spconv-{your-cuda-version}
python -m pip install torch_scatter torch_cluster -f https://data.pyg.org/whl/torch-{your-torch-version}+{your-cuda-version}.html --no-cache-dir
python -m pip install numpy==1.26.4
```

Three stages, run in order:

```bash
# 1. skeleton
bash launch/inference/generate_skeleton.sh --input model.glb --output results/model_skeleton.fbx

# 2. skinning weights (input is the skeleton from stage 1)
bash launch/inference/generate_skin.sh --input results/model_skeleton.fbx --output results/model_skin.fbx

# 3. merge the rig back onto the original mesh, keeping its materials
bash launch/inference/merge.sh --source results/model_skin.fbx --target model.glb --output results/model_rigged.glb
```

Batch variants take `--input_dir` / `--output_dir` instead of `--input` / `--output`. Both stages also accept `--skeleton_task` / `--skin_task` pointing at a config under `configs/task/` when you need a non-default checkpoint.

Notes that save time:
- The `.sh` scripts are bash — on this machine run them from Git Bash or WSL, not PowerShell.
- Merge onto the **original** file, not the intermediate FBX. Stage 1 and 2 outputs carry the rig, not your materials.
- UniRig rigs one mesh at a time. For a character split across body, hair, and clothing, rig the body and bind the rest to that armature (see `blender-fit-assets`) rather than rigging each piece separately — separate skeletons cannot be animated together.

## Rigify / GameRig

GameRig (`Arminando/GameRig`) is a Rigify feature set, developed against Blender 4.5 LTS and 5.0 — verify it loads on 5.1 before relying on it, since Rigify updates routinely break feature sets.

Install: Edit > Preferences > Add-ons, enable **Rigify**, then *Install Feature Set From File...* with the release zip from the repo's releases page.

Use: build the metarig the normal Rigify way, then press **Generate GameRig** instead of Generate Rig. v2.0 converts standard rig types to their `game.` equivalents automatically.

## Always verify the rig

An auto-rigger can return a file that imports cleanly and is still useless — bones floating outside the mesh, or weights on the wrong limb. Check the result headlessly rather than trusting the exit code:

```python
import bpy, json
arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
report = {
    "armatures": [(a.name, len(a.data.bones)) for a in arms],
    "meshes": [(m.name, len(m.vertex_groups), [mod.type for mod in m.modifiers])
               for m in bpy.data.objects if m.type == 'MESH'],
}
print(json.dumps(report, indent=2))
```

What you want to see: one armature, a plausible bone count (a humanoid under ~20 bones is suspiciously coarse), and every mesh carrying an `ARMATURE` modifier plus vertex groups whose names match bone names. Zero vertex groups means the skin stage did not take.

Then pose-test: rotate an arm bone 45° and render a frame. Weights that look fine in rest pose fall apart the moment anything moves, and a single posed render catches it in seconds.

## Known local quirks

- Tripo FBX imports with front axis **+X**, not -Y. Fix on import or the rig will face sideways.
- Blender 5.1.1's render engine enum is `BLENDER_EEVEE` (the valid set is `BLENDER_EEVEE`, `BLENDER_WORKBENCH`, `CYCLES`). `BLENDER_EEVEE_NEXT` was the 4.2–4.4 spelling and raises a TypeError here.
- Armature `show_in_front` and bone display don't appear in an F12 render — to *see* bones in an image, build cone geometry along them.

## Codex Compatibility

This skill was ported from a Claude skill. Interpret Claude Code-specific wording using Codex equivalents:

- Use `functions.shell_command` for shell commands, filesystem inspection, and running Blender.
- Use `apply_patch` to create or edit script files instead of the Write/Edit tools. The warning about heredocs mangling Windows backslashes still applies — author scripts as real files, then run them.
- Use `update_plan` to track multi-step work (import, scale, align, bind, render, verify).
- References to other skills (`blender-autorig`, `blender-fit-assets`, `blender-headless`) are sibling directories under `~/.codex/skills/`; read them directly.
- Where the skill says to look at a rendered PNG, attach or open the image so it is actually inspected — a render nobody looks at verifies nothing.
