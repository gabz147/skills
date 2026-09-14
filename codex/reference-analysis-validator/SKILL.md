---
name: reference-analysis-validator
description: Measure and validate supplied reference images, wireframes, texture atlases, and Blender renders before declaring a reconstruction 1:1. Use when an asset must match a template, when visual feedback says the output is off, when part counts must be exact, or before exporting a brand mascot/logo reconstruction. Pairs with reference-to-3d, contour-to-mesh, orthographic-registration, atlas-uv-fitting, and Blender MCP.
---

## Local Codex execution notes

Ported from RobLe3/cc-blender-skill v1.3.0, commit `11016c9a5847897491dde935c346571bd7548e3d`, September 8, 2026 by astra.

- Use the available command/file/image tools for Claude `Bash`, `Read`, `Glob`, `Grep`, and `Write` examples. Discover actual Blender MCP tools before calling them. A name in an upstream skill does not make the tool available.
- Local analysis Python: `C:/Users/Tarlu/Developer/blender-reference-tools/.venv/Scripts/python.exe`. This isolated environment has OpenCV, NumPy, SciPy, Pillow and scikit-image. In PowerShell invoke a quoted executable with `&`. Script paths are relative to `C:/Users/Tarlu/.codex/skills/reference-analysis-validator`.
- The installed reconstruction subset is `reference-to-3d`, `reference-analysis-validator`, `orthographic-registration`, `contour-to-mesh`, and `multiview-fit-loop`. Other upstream skill names below are optional specialties, not installed dependencies. Check for their SKILL.md before reading them; otherwise implement the required bpy step using the existing `blender-headless`, `blender-fit-assets`, or `blender-autorig` skill. Do not install extra packages or modify skills as an automatic failure-repair action.
- Live Blender MCP controls the scene connected on `127.0.0.1:9876`. Inspect the scene and file path first. If tools are unavailable in this session, read `../blender-headless/SKILL.md` and run scripts against a new numbered copy using `--background --factory-startup --disable-autoexec --python-exit-code 1`. Do not overwrite the user's open scene or earlier saves.
- Before any live scene mutation, verify the Blender PID, file path and expected scene identity in the same command that will edit it. Save a numbered recovery copy with `bpy.ops.wm.save_as_mainfile(filepath=..., copy=True)` first. A localhost port alone is not scene identity. Tests must use a separate port plus PID and random scene-token assertions.
- Put manifests, masks, reports, scripts and numbered .blend saves in the user's project folder. `/tmp` and `/path/to` in upstream examples are placeholders, not deliverable locations. Open rendered images and overlays before reporting visual success.
- User instructions and their chosen view priorities control the reference contract. Front-view priority below is a logo/mascot default, not permission to disregard supplied side/back anatomy. Register common scale, axes, projection and crop before diagnosing conflicting views. Depth/height and depth/width are different ratios and their inequality alone is not a conflict.
- The bundled scripts are measurement helpers. Inspect JSON fields, masks, extraction errors and missing views; exit zero is not a quality gate. A bbox summary is not silhouette, part-count, landmark, anatomical or aesthetic validation. Compare matching modalities; do not accept wireframe-vs-beauty IoU. Set project-specific thresholds and check every required view.
- Alpha extraction only works when alpha encodes the subject. An opaque RGBA drawing otherwise measures the whole canvas. For drawings, crop each annotated view and choose an explicit mask mode. Generated file-role guesses and largest-component selection need visual verification.
- Contour recipes use external contours and centroid-filtered Delaunay triangles. They may fill holes, omit smaller components or cross concave boundaries. Inspect topology and the rendered silhouette; they are starting geometry, not watertight retopology or a complete character reconstruction. A textured 2.5D front skin is not a solved full 3D/anatomy model.


# Reference Analysis Validator

This skill converts “looks close” into measurable gates. For brand/logo/mascot work, **do not model or export until a source manifest and validation thresholds exist**.

## Required outputs

Create these in the asset output folder:

- `reference_manifest.json` — classified source files, expected parts, thresholds.
- `source_analysis/*.json` — image metadata, masks/components/landmarks.
- `validation/front_overlay_reference.png` — reference and render overlay.
- `validation/front_mask_validation.json` — IoU/SSIM/bbox/centroid report.

## Workflow

1. Classify sources: front, side, back, top, texture atlas, decals, maps, lightmap, aura/context.
2. Build/refresh `reference_manifest.json` with hard expected counts and view roles.
3. Extract masks/components from each source using `scripts/reference_manifest_compiler.py` or existing analyzers.
4. Render model from matching orthographic camera with reference planes hidden.
5. Compare reference mask vs render mask using `scripts/render_overlay_validator.py`.
6. Refuse final export if hard gates fail.

## Modality rule

Compare like with like. A wireframe edge mask compared against a shaded beauty render gives misleadingly low IoU. For hard gates, render a flat silhouette/matte pass from Blender or compare reference edges to render edges. Use `render_overlay_validator.py --reference-mode ... --render-mode ...` when the source and render need different mask extraction modes.

## Default validation gates

- primary structural part count: exact.
- front silhouette IoU: target >= 0.90 for rigid/logotype shapes; >= 0.82 acceptable for first mascot reconstruction pass.
- bbox center drift: <= 12 px at 1024 px validation size.
- bbox size drift: <= 3% of image dimension.
- face/eye/smile landmark drift: <= 2% of image dimension when landmarks are defined.

## Failure policy

If a repeated mismatch occurs, record the measured failure, then route to the missing specialty skill:

- wrong silhouette → `contour-to-mesh`
- wrong depth/side/back → `orthographic-registration`
- wrong textures → `atlas-uv-fitting`
- wrong whole workflow → `mascot-logo-reconstruction`

## Read when needed

- `references/metrics-and-thresholds.md` for metric definitions and recommended gates.

## Sources distilled

Official/library docs to prefer while extending this skill:

- OpenCV contour features: moments, area, perimeter, bounding rectangles.
- OpenCV shape matching / Hu moments.
- OpenCV homography and geometric transforms.
- scikit-image SSIM for perceptual comparison.
