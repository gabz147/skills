---
name: multiview-fit-loop
description: Closed-loop compare-adjust-repeat workflow for fitting Blender models to supplied front/side/back/top templates and originals. Use when the user asks to compare the product to templates/originals and adjust until it fits across all dimensions, or when all views must pass measurable bbox/centroid/silhouette/edge validation before export.
---

## Local Codex execution notes

Ported from RobLe3/cc-blender-skill v1.3.0, commit `11016c9a5847897491dde935c346571bd7548e3d`, September 8, 2026 by astra.

- Use the available command/file/image tools for Claude `Bash`, `Read`, `Glob`, `Grep`, and `Write` examples. Discover actual Blender MCP tools before calling them. A name in an upstream skill does not make the tool available.
- Local analysis Python: `C:/Users/Tarlu/Developer/blender-reference-tools/.venv/Scripts/python.exe`. This isolated environment has OpenCV, NumPy, SciPy, Pillow and scikit-image. In PowerShell invoke a quoted executable with `&`. Script paths are relative to `C:/Users/Tarlu/.codex/skills/multiview-fit-loop`.
- The installed reconstruction subset is `reference-to-3d`, `reference-analysis-validator`, `orthographic-registration`, `contour-to-mesh`, and `multiview-fit-loop`. Other upstream skill names below are optional specialties, not installed dependencies. Check for their SKILL.md before reading them; otherwise implement the required bpy step using the existing `blender-headless`, `blender-fit-assets`, or `blender-autorig` skill. Do not install extra packages or modify skills as an automatic failure-repair action.
- Live Blender MCP controls the scene connected on `127.0.0.1:9876`. Inspect the scene and file path first. If tools are unavailable in this session, read `../blender-headless/SKILL.md` and run scripts against a new numbered copy using `--background --factory-startup --disable-autoexec --python-exit-code 1`. Do not overwrite the user's open scene or earlier saves.
- Before any live scene mutation, verify the Blender PID, file path and expected scene identity in the same command that will edit it. Save a numbered recovery copy with `bpy.ops.wm.save_as_mainfile(filepath=..., copy=True)` first. A localhost port alone is not scene identity. Tests must use a separate port plus PID and random scene-token assertions.
- Put manifests, masks, reports, scripts and numbered .blend saves in the user's project folder. `/tmp` and `/path/to` in upstream examples are placeholders, not deliverable locations. Open rendered images and overlays before reporting visual success.
- User instructions and their chosen view priorities control the reference contract. Front-view priority below is a logo/mascot default, not permission to disregard supplied side/back anatomy. Register common scale, axes, projection and crop before diagnosing conflicting views. Depth/height and depth/width are different ratios and their inequality alone is not a conflict.
- The bundled scripts are measurement helpers. Inspect JSON fields, masks, extraction errors and missing views; exit zero is not a quality gate. A bbox summary is not silhouette, part-count, landmark, anatomical or aesthetic validation. Compare matching modalities; do not accept wireframe-vs-beauty IoU. Set project-specific thresholds and check every required view.
- Alpha extraction only works when alpha encodes the subject. An opaque RGBA drawing otherwise measures the whole canvas. For drawings, crop each annotated view and choose an explicit mask mode. Generated file-role guesses and largest-component selection need visual verification.
- Contour recipes use external contours and centroid-filtered Delaunay triangles. They may fill holes, omit smaller components or cross concave boundaries. Inspect topology and the rendered silhouette; they are starting geometry, not watertight retopology or a complete character reconstruction. A textured 2.5D front skin is not a solved full 3D/anatomy model.


# Multiview Fit Loop

This skill closes the missing loop: **render → compare → adjust → render again**. It is mandatory when a user says the model still does not fit the templates/originals.

## Required loop

1. Render flat, material-independent silhouettes for every available template view: front, side, back, top.
2. Extract the template object mask, excluding labels, cyan guides, and background.
3. Compare template vs render per view:
   - bbox center and size
   - centroid drift
   - silhouette coverage/IoU where modality is valid
   - visual overlay
4. Convert measured deltas into model/camera/recipe adjustments.
5. Rebuild or transform the model.
6. Repeat until all hard gates pass or document the remaining conflict.

## Constraint inconsistency gate

Before forcing adjustments, check whether the supplied orthographic templates are mutually consistent. Compare the same physical axis after registering scale, projection and crop. For example, normalized side depth must agree with normalized top depth; depth/height and depth/width need not equal each other. When this occurs, stop claiming final fit, write a conflict report, and create separate variants or ask which view is canonical.

## Hard gates

- all required views have validation reports and overlays;
- bbox center drift <= 1.5% of image width;
- bbox size drift <= 3% for front, <= 5% for side/top/back first-pass depth;
- structural part count exact;
- texture UV regions still valid after geometry changes.

## View mask rule

For annotated wireframes, choose a template mask mode that isolates the intended construction/object lines and excludes guide colors, labels, captions, and background annotations. For Blender validation renders, use a flat white silhouette on black, not beauty renders with glow/context elements.

## Scripts

- `scripts/multiview_fit_report.py` compares view pairs and writes JSON + overlays. The local port accepts `--reference-mode`, `--render-mode`, and `--required-views`. Its summary is explicitly a bbox diagnostic; run the reference-analysis-validator for silhouette measurements and evaluate the manifest separately.

## Adjustment rule

Prefer changing recipe parameters or source geometry over camera scale tricks. Camera scale may be used only after model dimensions are correct.
