# Cache, Review, and Invalidation

The cache lives at `<footage_path>/.arc-raiders-montage-cache` unless `cache_dir` overrides it. It is excluded from source discovery along with the output folder, previous exports, proxies, previews, contact sheets, and thumbnails.

```text
<cache>/
  analysis-index.json
  events.json
  artifacts/contact-sheets/<source-id>.jpg
  artifacts/proxies/ (reserved for optional low-resolution proxies)
  reports/ (optional copied run reports)
```

Each source entry stores its identity/path, sample SHA-256, file size, modification time, stream metadata, event candidates, causal evidence, and artifact paths. Analysis first samples the normalized HUD and a low-rate visual fallback, then decodes merged candidate windows at high frame rate. It records weapon confidence, ammo-glyph changes, ordered shot/impact/shield/flare timestamps, spatial linkage, player-damage evidence, tier, and the payoff frame hash. Analysis does not decide which clips a later montage must use.

Valid source analysis is reused only when its fingerprint and detector signature match. The signature includes the detector version, profiles/FPS values, normalized ROIs, causal thresholds, feature dimensions, and weapon-template contents. Ranking-only preferences are intentionally excluded. New/modified files are analyzed, and any old cache without the current signature is invalidated. `force_rescan` bypasses an otherwise valid entry. Candidate ranking, duration fitting, approval filtering, timeline placement, and duplicate groups are recomputed for every run.

The review page is intentionally static and portable. It gives each candidate a stable ID and writes a `.approvals.json` template. Add approved/rejected IDs there and set `approvals_path` in the next config. This keeps approval state out of the reusable source cache.

Duplicate detection combines source-interval overlap, engagement/causal-chain identity, perceptual frame-hash similarity, and a short audio energy fingerprint when visual similarity indicates overlapping DVR captures. A hard duplicate group allows one candidate by default. The planner performs a final selection audit, and the Resolve build payload repeats a source-frame overlap check before placing media.
