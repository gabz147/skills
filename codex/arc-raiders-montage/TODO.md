# ARC Raiders Montage Skill — Implementation TODO

## Discovery and guardrails

- [x] Inspect the existing montage build/render helpers and identify reusable Resolve patterns.
- [x] Inspect local Codex skill structure, metadata conventions, and validation tooling.
- [x] Create the skill scaffold in the user-level Codex skills directory.
- [x] Preserve the original project helpers and existing Resolve timelines/exports unchanged.
- [x] Add explicit preflight checks for input folders, music, output targets, Resolve bridge, and render completion.

## Inputs and configuration

- [x] Define and validate a portable JSON configuration schema for all requested inputs.
- [x] Normalize exact, range, `full_song`, `best_available`, and `auto` duration modes.
- [x] Infer safe defaults when optional values are omitted; require only `footage_path`.
- [x] Add optional user config support without embedding machine-specific paths.

## Analysis and cache

- [x] Inventory gameplay media while excluding exports, proxies, previews, and non-gameplay files.
- [x] Cache source fingerprints, metadata, events, engagement windows, scores, duplicate groups, and contact sheets; reserve proxy storage for optional future generation.
- [x] Reuse unchanged cache entries and rescan only new/changed files; support `force_rescan`.
- [x] Detect temporal shield-hit, shield-break, and Raider-flare candidates using frame sequences and causal context.
- [x] Rank candidate engagement windows while keeping 1–5 seconds of useful buildup.

## HUD-aware causal detector v2

- [x] Add normalized bottom-right HUD, reticle/action, and bottom-left player-status regions.
- [x] Detect ammo-glyph changes, merge Equalizer-style firing bursts, and suppress weapon/anchor swaps.
- [x] Bundle and validate Aphelion/Equalizer word masks; keep unknown weapons neutral.
- [x] Verify candidate windows at up to 30 FPS with ordered, spatially linked impact/shield/flare evidence.
- [x] Account for HUD sampling uncertainty, projectile latency, and post-impact flare follow-through.
- [x] Apply a capped incoming-player-damage penalty without erasing simultaneous outgoing knocks.
- [x] Preserve separate logical events inside shared decode windows and deduplicate by causal timing rather than broad edit handles.
- [x] Add stable event IDs, detector-signature cache invalidation, and source/event-scoped contact sheets.
- [x] Add event tiers/priorities, preferred-weapon ranking, first-shot clip starts, payoff timing, and diagnostic review evidence.
- [x] Add standard-library unit coverage plus a synthetic FFmpeg end-to-end detector/cache/review smoke test.

## Dedupe, planning, and review

- [x] Reject duplicate intervals, alternate trims, repeated events, overlapping DVR captures, and perceptually/audio-similar duplicates.
- [x] Build a per-request edit manifest whose ranking is independent of previous montage choices.
- [x] Implement music-aware duration fitting without filling time with weak clips; add editable setup/payoff markers for finishing.
- [x] Generate a candidate + deduplication report and a review-first HTML page/contact sheet.
- [x] Stop automatic rendering when a hard duplicate remains after final timeline audit.

## Timeline, render, and verification

- [x] Build a new, versioned Resolve timeline without deleting or overwriting existing timelines.
- [x] Add editable music/game-audio mix controls and beat markers for shield pops/final hits/knocks.
- [x] Render non-destructively as H.264/AAC with configurable resolution and frame rate.
- [x] Verify the finished file via ffprobe, FFmpeg video/audio decoding, and optional VLC visual playback.

## Documentation and validation

- [x] Document commands, defaults, review/automatic modes, error handling, and migration from the original helpers.
- [x] Validate the skill structure and run script smoke tests using generated sample data.
- [x] Mark all completed work here and leave known limitations explicit.

## Intentional live-test boundary

- [ ] Forward-test a Resolve build/render in a disposable Resolve project when a new montage is requested. This is intentionally deferred: the skill was syntax-checked and its non-Resolve pipeline passed a generated-media smoke test, but creating a live Resolve project/timeline would modify the user's current application state outside this implementation request.

## Validation notes

- Synthetic smoke test passed: inventory/cache reuse, temporal candidate planning, review HTML, contact-sheet artifact, and FFmpeg audio/video decode verification.
- HUD detector v2 passes 21 unit tests covering normalized ROIs/configuration, weapon masks, ammo bursts, weapon/anchor-swap suppression, HUD timing uncertainty, projectile follow-through, temporal/spatial knock causality, bright-flare ordering, incoming-damage penalties, ranking, cache signatures, resolution scaling, stable deduplication IDs, and separate nearby knocks.
- The supplied 2560x1440 reference frames classify Equalizer and Aphelion correctly while leaving Anvil unknown. A generated Equalizer ammo change → blue impact → red flare video produced one tier-S knock, one selected clip, a review page, and a reusable signed cache entry.
- All Python scripts compile and the JSON schema parses.
- The bundled `quick_validate.py` could not run because this machine's Python environments do not include PyYAML; an equivalent frontmatter/structure validation passed.
- Resolve bridge liveness was checked, but no real timeline was created during skill development; the existing project timeline and exports were left untouched.
