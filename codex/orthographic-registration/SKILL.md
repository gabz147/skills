---
name: orthographic-registration
description: Register front, side, back, and top orthographic reference views into a shared Blender coordinate contract. Use when a 3D model must match multi-view wireframes/templates, when side/back/top silhouettes are off, or before adding depth to a front-locked contour model.
---

## Local Codex execution notes

Ported from RobLe3/cc-blender-skill v1.3.0, commit `11016c9a5847897491dde935c346571bd7548e3d`, September 8, 2026 by astra.

- Use the available command/file/image tools for Claude `Bash`, `Read`, `Glob`, `Grep`, and `Write` examples. Discover actual Blender MCP tools before calling them. A name in an upstream skill does not make the tool available.
- Local analysis Python: `C:/Users/Tarlu/Developer/blender-reference-tools/.venv/Scripts/python.exe`. This isolated environment has OpenCV, NumPy, SciPy, Pillow and scikit-image. In PowerShell invoke a quoted executable with `&`. Script paths are relative to `C:/Users/Tarlu/.codex/skills/orthographic-registration`.
- The installed reconstruction subset is `reference-to-3d`, `reference-analysis-validator`, `orthographic-registration`, `contour-to-mesh`, and `multiview-fit-loop`. Other upstream skill names below are optional specialties, not installed dependencies. Check for their SKILL.md before reading them; otherwise implement the required bpy step using the existing `blender-headless`, `blender-fit-assets`, or `blender-autorig` skill. Do not install extra packages or modify skills as an automatic failure-repair action.
- Live Blender MCP controls the scene connected on `127.0.0.1:9876`. Inspect the scene and file path first. If tools are unavailable in this session, read `../blender-headless/SKILL.md` and run scripts against a new numbered copy using `--background --factory-startup --disable-autoexec --python-exit-code 1`. Do not overwrite the user's open scene or earlier saves.
- Before any live scene mutation, verify the Blender PID, file path and expected scene identity in the same command that will edit it. Save a numbered recovery copy with `bpy.ops.wm.save_as_mainfile(filepath=..., copy=True)` first. A localhost port alone is not scene identity. Tests must use a separate port plus PID and random scene-token assertions.
- Put manifests, masks, reports, scripts and numbered .blend saves in the user's project folder. `/tmp` and `/path/to` in upstream examples are placeholders, not deliverable locations. Open rendered images and overlays before reporting visual success.
- User instructions and their chosen view priorities control the reference contract. Front-view priority below is a logo/mascot default, not permission to disregard supplied side/back anatomy. Register common scale, axes, projection and crop before diagnosing conflicting views. Depth/height and depth/width are different ratios and their inequality alone is not a conflict.
- The bundled scripts are measurement helpers. Inspect JSON fields, masks, extraction errors and missing views; exit zero is not a quality gate. A bbox summary is not silhouette, part-count, landmark, anatomical or aesthetic validation. Compare matching modalities; do not accept wireframe-vs-beauty IoU. Set project-specific thresholds and check every required view.
- Alpha extraction only works when alpha encodes the subject. An opaque RGBA drawing otherwise measures the whole canvas. For drawings, crop each annotated view and choose an explicit mask mode. Generated file-role guesses and largest-component selection need visual verification.
- Contour recipes use external contours and centroid-filtered Delaunay triangles. They may fill holes, omit smaller components or cross concave boundaries. Inspect topology and the rendered silhouette; they are starting geometry, not watertight retopology or a complete character reconstruction. A textured 2.5D front skin is not a solved full 3D/anatomy model.


# Orthographic Registration

This skill prevents the common failure where the front view looks plausible but the side/back/top views are wrong.

## Coordinate contract

- Front view defines `X/Z` silhouette.
- Side view defines `Y/Z` depth envelope.
- Top view defines `X/Y` spread.
- Back view defines rear silhouette/material only; it must not rewrite the front silhouette.

## Workflow

1. Run `scripts/register_views.py` on the available view images.
2. Create orthographic reference planes/image empties with a single shared scale.
3. Align centerline and bbox centers before modeling.
4. Lock front X/Z boundary vertices.
5. Add Y depth from side/top envelopes using modifiers/displacement or vertex groups.
6. Validate all four cameras before export.

## Failure policy

If views disagree, front brand read wins. Document the conflict in `registration_report.json`.


## Front-plane rotation rule

In this Blender coordinate convention, the front camera looks along the Y axis and the reference silhouette lives in the X/Z plane. Therefore 2D rotations inside the front view are rotations around the **Y axis**, not around Z. Use `rotation_euler = (0, angle, 0)` for 2D component orientation in the front projection. Z rotation spins objects into/out of screen-space incorrectly for X/Z-plane meshes.

## Sources distilled

- Blender Image Empty/reference image controls for orthographic blueprints.
- OpenCV homography/alignment and geometric transforms for view registration.
