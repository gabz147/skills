# ARC Raiders Montage Skill

This skill turns a short request into a repeatable montage plan. It scans ARC Raiders recordings, detects temporal shield/impact/knock sequences, ranks and deduplicates them, fits strong clips to the requested music/duration, adds setup and payoff markers for finishing, builds a non-destructive Resolve timeline, renders H.264/AAC, and verifies both streams.

The detector uses two passes. A normalized bottom-right HUD crop identifies supported weapon labels and ammo-glyph changes; only candidate firing windows are then decoded at high frame rate for reticle-linked impacts, blue-white shield effects, sparks, and later persistent red knock flares. A low-rate visual fallback protects footage with a hidden or unreadable HUD. Bottom-left player-status changes reduce confidence when the effect is probably incoming damage.

## Quick commands

Create a config from `references/example-config.json`, change the paths, then run:

```powershell
python scripts/arc_montage.py review --config C:\path\to\config.json
```

After approving the manifest:

```powershell
python scripts/run_resolve.py --manifest C:\path\to\run.manifest.json --mode both
python scripts/arc_montage.py verify --input C:\path\to\arc_raiders_montage_YYYYMMDD-HHMMSS.mp4
```

For a preview-only request, use `render_enabled: false`. For automatic editing, set `review_required: false`. If Resolve is unavailable, the planner still produces the manifest and HTML review page; render later with `run_resolve.py --mode render`.

## Detection preferences

`APHELION` and `EQUALIZER` receive a ranking boost by default. Set `preferred_weapon_mode` to `only` only when all other weapons should be excluded, or `off` to disable the boost. `minimum_event_tier: B` keeps confirmed knocks and shield breaks; `C` also exposes ordinary shield hits and incomplete impacts for review.

The default `accurate` profile scans the HUD at 8 FPS, performs a 3 FPS fallback scan, and verifies merged candidates at up to 30 FPS. `balanced` runs the fallback only when a source yields no HUD candidates; `fast` is HUD-only. The ROIs are normalized `[x1, y1, x2, y2]` coordinates and can be calibrated for a different HUD scale:

```json
{
  "preferred_weapons": ["APHELION", "EQUALIZER"],
  "preferred_weapon_mode": "boost",
  "event_priority": ["knock", "shield_break", "shield_hit"],
  "minimum_event_tier": "B",
  "hud_roi": [0.84, 0.72, 1.0, 1.0],
  "player_status_roi": [0.0, 0.84, 0.19, 1.0],
  "reticle_roi": [0.38, 0.30, 0.62, 0.70],
  "action_roi": [0.24, 0.18, 0.76, 0.92]
}
```

## Duration examples

`30s`, `2m`, `45-75s`, `full_song`, `best_available`, and `auto` are supported. `auto` estimates a useful length from the song and strong unique clips. `best_available` may be shorter than a nominal target. The planner never repeats weak footage just to fill time.

## Migration notes

The first project's `build_arc_raiders_montage.py` and `render_arc_raiders_montage.py` remain untouched. The reusable version moves their stable patterns into `arc_montage.py`, `resolve_montage.py`, and `run_resolve.py`, while replacing hard-coded paths, 60-second assumptions, fixed source FPS, same-name timeline deletion, and missing post-render verification.

## Limitations

Weapon recognition currently bundles masks for Aphelion and Equalizer; other weapons remain `unknown` and are neutral in boost mode. Ammo analysis detects stable glyph changes rather than performing full numeric OCR, so a reload can seed a candidate but should fail the required reticle-impact verification. The detector is a lightweight standard-library/FFmpeg heuristic rather than a trained vision model. Review-first mode is recommended for uncertain footage, a different HUD scale, or unusual lighting. VLC visual verification is intentionally performed by the agent through the Windows app rather than silently assumed from metadata.
