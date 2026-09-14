---
name: contour-to-mesh
description: Build Blender mesh surfaces directly from extracted 2D contours/masks instead of approximate primitives. Use for 1:1 mascot/logo reconstruction, exact leaf/petal silhouettes, filled wireframe shapes, shallow bas-relief forms, or when the model outline must match a front template before adding depth.
---

## Local Codex execution notes

Ported from RobLe3/cc-blender-skill v1.3.0, commit `11016c9a5847897491dde935c346571bd7548e3d`, September 8, 2026 by astra.

- Use the available command/file/image tools for Claude `Bash`, `Read`, `Glob`, `Grep`, and `Write` examples. Discover actual Blender MCP tools before calling them. A name in an upstream skill does not make the tool available.
- Local analysis Python: `C:/Users/Tarlu/Developer/blender-reference-tools/.venv/Scripts/python.exe`. This isolated environment has OpenCV, NumPy, SciPy, Pillow and scikit-image. In PowerShell invoke a quoted executable with `&`. Script paths are relative to `C:/Users/Tarlu/.codex/skills/contour-to-mesh`.
- The installed reconstruction subset is `reference-to-3d`, `reference-analysis-validator`, `orthographic-registration`, `contour-to-mesh`, and `multiview-fit-loop`. Other upstream skill names below are optional specialties, not installed dependencies. Check for their SKILL.md before reading them; otherwise implement the required bpy step using the existing `blender-headless`, `blender-fit-assets`, or `blender-autorig` skill. Do not install extra packages or modify skills as an automatic failure-repair action.
- Live Blender MCP controls the scene connected on `127.0.0.1:9876`. Inspect the scene and file path first. If tools are unavailable in this session, read `../blender-headless/SKILL.md` and run scripts against a new numbered copy using `--background --factory-startup --disable-autoexec --python-exit-code 1`. Do not overwrite the user's open scene or earlier saves.
- Before any live scene mutation, verify the Blender PID, file path and expected scene identity in the same command that will edit it. Save a numbered recovery copy with `bpy.ops.wm.save_as_mainfile(filepath=..., copy=True)` first. A localhost port alone is not scene identity. Tests must use a separate port plus PID and random scene-token assertions.
- Put manifests, masks, reports, scripts and numbered .blend saves in the user's project folder. `/tmp` and `/path/to` in upstream examples are placeholders, not deliverable locations. Open rendered images and overlays before reporting visual success.
- User instructions and their chosen view priorities control the reference contract. Front-view priority below is a logo/mascot default, not permission to disregard supplied side/back anatomy. Register common scale, axes, projection and crop before diagnosing conflicting views. Depth/height and depth/width are different ratios and their inequality alone is not a conflict.
- The bundled scripts are measurement helpers. Inspect JSON fields, masks, extraction errors and missing views; exit zero is not a quality gate. A bbox summary is not silhouette, part-count, landmark, anatomical or aesthetic validation. Compare matching modalities; do not accept wireframe-vs-beauty IoU. Set project-specific thresholds and check every required view.
- Alpha extraction only works when alpha encodes the subject. An opaque RGBA drawing otherwise measures the whole canvas. For drawings, crop each annotated view and choose an explicit mask mode. Generated file-role guesses and largest-component selection need visual verification.
- Contour recipes use external contours and centroid-filtered Delaunay triangles. They may fill holes, omit smaller components or cross concave boundaries. Inspect topology and the rendered silhouette; they are starting geometry, not watertight retopology or a complete character reconstruction. A textured 2.5D front skin is not a solved full 3D/anatomy model.


# Contour to Mesh

Use this when a reference silhouette is the contract. The mesh starts as a filled 2D contour in front-view X/Z, then gets shallow Y depth/crown after validation.

## Workflow

1. Extract or select a clean contour/mask for one structural part.
2. Generate a triangulated mesh recipe with `scripts/mask_to_mesh_recipe.py`.
3. Run the generated Blender Python to create a named `GEO_*` mesh.
4. Assign front-projected UVs immediately.
5. Add depth only as a modifier or vertex displacement that preserves X/Z boundary positions.
6. Validate the front render against the source mask.

## Hard rules

- Do not use radial duplication unless the manifest says the source is symmetric.
- Do not use a generic ellipse if a contour exists.
- Boundary vertices must keep source X/Z coordinates.
- Depth deformation may move Y and inner vertices, but must not alter front silhouette.
- One structural source part should become one named structural mesh.

## Blender pattern

Generated mesh coordinates should map image `x` to Blender `X` and image `y` to Blender `Z` with vertical flip. Use `Y` only for thickness/depth.


## Front-plane rotation rule

In this Blender coordinate convention, the front camera looks along the Y axis and the reference silhouette lives in the X/Z plane. Therefore 2D rotations inside the front view are rotations around the **Y axis**, not around Z. Use `rotation_euler = (0, angle, 0)` for 2D component orientation in the front projection. Z rotation spins objects into/out of screen-space incorrectly for X/Z-plane meshes.

## Sources distilled

- Blender Mesh API: create meshes from vertices/faces using `from_pydata`.
- Blender BMesh: use for cleanup, triangulation, normals, smoothing.
- OpenCV contours: detect and simplify boundaries.
- Delaunay triangulation: useful for filled interior meshes when filtered by mask containment.


## Part-inventory handoff

When masks come from `source-part-segmentation`, preserve the `part_inventory.json` names in Blender:
`GEO_<part_name>`, `MAT_<part_name>`, and UV layer names. Mesh generation must record:

- source image size;
- source mask path;
- contour boundary point count;
- boundary landmark points (tip, base-left, base-right, centroid/extrema) when detectable;
- atlas UV rectangle or projection mode.

For exact mascot/logo work, generate boundary vertices from the contour and add interior vertices only for surface support.
The boundary is a contract: bevels, solidify, subdivision, shrinkwrap, or sculpt passes must not move front-view X/Z boundary vertices unless a new source mask is produced.

## Hole and stroke policy

- Filled structural masks become meshes.
- Wireframe strokes guide boundaries/landmarks; they are not structural meshes unless the manifest classifies them as decorative linework.
- Holes/negative regions should be kept as separate cut masks when they affect silhouette; otherwise implement them as decals/material masks.


## Source-locked front-skin fallback

When a design sheet is painterly/stylized and separate orthographic views are not CAD-consistent, use a **front-skin** pass before sculptural interpretation:

1. choose the canonical front/master source;
2. extract the visible subject mask as a filled contour;
3. create a shallow 2.5D mesh whose X/Z boundary is that contour;
4. assign full-image front-projected UVs so the rendered front matches the source pixels;
5. add depth only along Y and behind the front surface;
6. optionally add separate relief/backing parts for side plausibility, but keep the front skin as the visual acceptance gate.

This is a generic fallback for logos/mascots where a faithful front read is more important than speculative volume. Mark it as `front_locked_visual_skin`, not as a fully solved turntable model.

## Script

- `scripts/source_locked_skin_recipe.py` extracts a largest/canonical foreground component and emits a mask + contour mesh recipe using full-image front-projected UV coordinates.
