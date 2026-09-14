# Migration from the Original ARC Raiders Montage Helpers

The original project scripts remain unchanged:

- `build_arc_raiders_montage.py`
- `render_arc_raiders_montage.py`

They are still useful as a record of the first edit, but they contain fixed absolute paths, a fixed 60-second cut list, one song offset, one timeline name, and one output stem. Do not run them for a new montage unless intentionally recreating that exact edit.

The reusable skill replaces their hard-coded values with a run manifest. The generic Resolve bridge payloads preserve the working patterns from those helpers:

- import missing media and re-fetch Media Pool handles after a Resolve page switch;
- use `is None` semantics for Resolve proxy objects rather than truthiness;
- append declarative source in/out + record-frame edits;
- add beat/event markers;
- use MP4/H.264 with AAC audio and timeline-derived mark in/out;
- wait for the render to finish, then verify both streams through FFmpeg.

Unlike the original helpers, this skill never deletes a same-named timeline. It reserves a new output stem, creates a new `..._v###` Resolve timeline, rejects hard duplicates, and keeps game audio separate from the music track.
