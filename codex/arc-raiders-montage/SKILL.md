---
name: arc-raiders-montage
description: Build reusable ARC Raiders gameplay montages from a footage folder and optional music, using temporal shield/impact/knock-flare detection, candidate ranking, perceptual deduplication, music-aware duration planning, DaVinci Resolve rendering, FFmpeg verification, and optional VLC visual checking. Use when the user asks to edit, highlight, montage, clip, or sync ARC Raiders gameplay, especially when they mention red flares, shield pops, knocks, a song, a target duration, or a review pass.
---

# ARC Raiders Montage

Use this skill for a new montage request instead of rebuilding the first project by hand. Only `footage_path` is mandatory; infer the other settings conservatively and state the defaults used.

## Workflow

1. Convert the natural-language request into a temporary JSON config. Use [references/config.schema.json](references/config.schema.json) and [references/example-config.json](references/example-config.json). `target_duration` defaults to `auto`, never 60 seconds.
2. Run the offline planner:

   ```powershell
   python scripts/arc_montage.py plan --config C:\path\to\config.json
   ```

   This inventories source media, excludes prior exports/proxies/previews, reuses the cache for unchanged files, runs a HUD-seeded coarse scan followed by high-frame-rate candidate verification, ranks events, rejects duplicates, and writes a versioned manifest plus HTML review page beside the requested output.

3. Use review-first mode when `review_required` is true, detection confidence is uncertain, or the user asks for previews only. Show the generated `.review.html`; do not render until the user approves. An approved manifest may set `approved: false` on rejected clips.
4. In automatic mode, use only high-confidence unique candidates. Never pad with weak or repeated footage merely to hit a target. Exact and range requests must report when there is not enough strong unique material.
5. When music is supplied, analyze its transients before finalizing the sequence. Shift each source in-point so the detected shield break, knock flare, or chosen impact payoff lands on the nearest viable beat, and record both `payoff_record_time` and `sync_beat_time` in the manifest. For action montages, default to hard cuts and natural flash cuts made by the shield/flare frames themselves; avoid transitions that obscure the payoff. A `full_song` request must end at the song duration when enough qualifying material exists and must report a shortage instead of adding sub-threshold clips.
6. For Resolve output, first verify the Resolve Free bridge is live. The user may need to run `Workspace > Scripts > cli_anything_daemon` in Resolve. Then run:

   ```powershell
   python scripts/run_resolve.py --manifest C:\path\to\run.manifest.json --mode both
   ```

   This creates a new uniquely named timeline, preserves existing timelines/exports, keeps source-frame-rate conversions separate from timeline frame rate, mixes game audio under the music, and renders H.264/AAC using the requested settings.
7. Verify every rendered file before handing it off:

   ```powershell
   python scripts/arc_montage.py verify --input C:\path\to\render.mp4
   ```

   Require a video stream, an audio stream, and successful FFmpeg video/audio decoding. When `review_required` or the user requests visual QA, use the Computer Use skill to open the final file in VLC and visually confirm gameplay is displayed while it plays.

## Detection and deduplication rules

Preserve useful 1–5 second buildup according to style. Treat ordinary shield hits separately from full shield breaks/pops. A high-confidence event must be an ordered sequence: ammo-HUD change or corroborated firing activity, a target-centered impact, an optional blue-white shield burst/radial sparks, and a later persistent red knock flare spatially linked to the impact. Never claim shot evidence merely because a colored effect was found.

Use normalized HUD regions so 16:9 source resolutions can share calibration. The bottom-right crop supplies weapon identity and ammo-glyph changes; the reticle/action crop supplies impact, shield, spark, and flare evidence; the lowest bottom-left player-status crop supplies a capped incoming-damage penalty. A player-status drop is not an automatic rejection because outgoing and incoming damage can occur together. Reject isolated background flares, unrelated explosions, reload/swap-only HUD changes, screen-edge player-damage effects, and unrelated ARC electrical effects.

The default detector profile is `accurate`: scan the bottom-right HUD at 8 FPS, run a 3 FPS visual fallback, merge decode ranges while preserving each firing seed, and verify only those windows at up to 30 FPS. Account for HUD sampling uncertainty before the observed ammo change and retain post-impact time for late Aphelion flares. `APHELION`, `EQUALIZER`, and `TEMPEST` are recognized with bundled label masks and receive a ranking boost by default. Unknown weapon identity is neutral, not a hard rejection. Use `preferred_weapon_mode: only` only when the user explicitly wants no other weapons. Color-only fallback events remain tier C/review-only because they do not prove firing. Keep `minimum_event_tier: B` for automatic knock/shield-break selection; use `C` only for wider review.

Use source intervals, stable event IDs, source hashes, perceptual frame hashes, and temporal/audio similarity where practical; stop before rendering if the final manifest contains a hard duplicate.

## Cache and safety

The cache lives under `.arc-raiders-montage-cache` by default and records source identity, metadata, candidate events, engagement windows, scores, duplicate groups, and generated review artifacts. Reuse unchanged entries only when both the source fingerprint and detector signature match; detector, ROI, sampling, threshold, or weapon-template changes must invalidate cached analysis. Ranking-only preferences may reuse analysis. Honor `force_rescan`. Ranking and duration selection are per-request decisions and must not be inherited from an older montage. Never delete or overwrite a pre-existing Resolve timeline or export; use the versioned manifest stem.

## Existing-project migration

The original project helpers remain usable at the project level. This skill reuses their proven Resolve patterns—media-pool import/recheck, page-switch settling, `is None` proxy checks, declarative `AppendToTimeline`, markers, and explicit H.264/AAC render settings—through the generic scripts in this folder. See [README.md](README.md) for command examples and migration notes.

For cache details and source-cache invalidation, see [references/cache-layout.md](references/cache-layout.md). For the original-helper migration map, see [references/migration.md](references/migration.md).
