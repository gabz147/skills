"""Run inside the Resolve Free bridge daemon.

The runner injects MANIFEST_PATH and MODE before executing this file. Keeping
the Resolve-specific code here preserves the working page-switch and proxy
handle patterns from the original ARC Raiders project.
"""
import json
import math
import os
import re
import time

MANIFEST_PATH = globals().get("MANIFEST_PATH") or os.environ.get("ARC_MONTAGE_MANIFEST")
MODE = globals().get("MODE", "build")
if not MANIFEST_PATH:
    raise RuntimeError("MANIFEST_PATH must be injected by run_resolve.py")
with open(MANIFEST_PATH, "r", encoding="utf-8") as fh:
    manifest = json.load(fh)
cfg = manifest["config"]
clips = [c for c in manifest.get("clips", []) if c.get("approved", True) is not False]
fps = float(manifest["timeline"]["frame_rate"])
width, height = [int(x) for x in cfg["resolution"].split("x")]


def canonical(value):
    return os.path.normcase(os.path.normpath(value))


def audit_clip_intervals():
    for index, clip in enumerate(clips):
        start, end = float(clip["clip_start"]), float(clip["clip_end"])
        if end <= start:
            raise RuntimeError("Montage clip has an empty or reversed source interval: " + clip.get("id", str(index)))
        for prior in clips[:index]:
            if canonical(clip["source"]) != canonical(prior["source"]):
                continue
            prior_start, prior_end = float(prior["clip_start"]), float(prior["clip_end"])
            overlap = max(0.0, min(end, prior_end) - max(start, prior_start))
            shorter = max(.001, min(end - start, prior_end - prior_start))
            payoff = clip.get("event_time")
            prior_payoff = prior.get("event_time")
            payoff_close = (payoff is not None and prior_payoff is not None
                            and abs(float(payoff) - float(prior_payoff)) <= .65 + 1e-6)
            if overlap / shorter >= .80 or (overlap > 0 and payoff_close):
                raise RuntimeError("Resolve preflight rejected duplicate/overlapping source intervals: %s and %s" %
                                   (prior.get("id", "unknown"), clip.get("id", "unknown")))


def media_map():
    media_pool = project.GetMediaPool()
    root = media_pool.GetRootFolder()
    return media_pool, {canonical((c.GetClipProperty() or {}).get("File Path", "")): c for c in (root.GetClipList() or [])}


def import_required(media_pool, by_path):
    required = list(dict.fromkeys([c["source"] for c in clips] + ([cfg["music_path"]] if cfg.get("music_path") else [])))
    missing = [p for p in required if canonical(p) not in by_path]
    if missing:
        imported = media_pool.ImportMedia(missing)
        if imported is None:
            raise RuntimeError("Resolve could not import the montage media")
        media_pool, by_path = media_map()
    unresolved = [p for p in required if canonical(p) not in by_path]
    if unresolved:
        raise RuntimeError("Resolve did not expose required media: " + "; ".join(unresolved))
    return media_pool, by_path


def unique_timeline_name(base):
    names = {project.GetTimelineByIndex(i).GetName() for i in range(1, project.GetTimelineCount() + 1)
             if project.GetTimelineByIndex(i) is not None}
    if base not in names:
        return base
    i = 2
    while f"{base}_{i:02d}" in names:
        i += 1
    return f"{base}_{i:02d}"


def set_audio_level(item, level):
    if level is None or level <= 0:
        return
    db = 20.0 * math.log10(float(level))
    for key in ("Audio Level", "Volume"):
        try:
            if item.SetProperty(key, db):
                return
        except Exception:
            pass


def build():
    audit_clip_intervals()
    resolve.OpenPage("media")
    media_pool, by_path = media_map()
    media_pool, by_path = import_required(media_pool, by_path)

    # Project settings are needed at creation time. Save and restore them so
    # the reusable skill does not permanently change an existing project.
    setting_keys = ("timelineResolutionWidth", "timelineResolutionHeight", "timelineFrameRate", "timelinePlaybackFrameRate")
    previous = {key: project.GetSetting(key) for key in setting_keys}
    project.SetSetting("timelineResolutionWidth", str(width))
    project.SetSetting("timelineResolutionHeight", str(height))
    project.SetSetting("timelineFrameRate", str(fps))
    project.SetSetting("timelinePlaybackFrameRate", str(fps))

    resolve.OpenPage("edit")
    time.sleep(1.5)
    media_pool, by_path = media_map()
    media_pool, by_path = import_required(media_pool, by_path)
    name = unique_timeline_name(manifest["output"]["stem"])
    timeline = media_pool.CreateEmptyTimeline(name)
    if timeline is None:
        raise RuntimeError("Resolve could not create a new montage timeline")
    for key, value in previous.items():
        if value not in (None, ""):
            project.SetSetting(key, str(value))
    if project.SetCurrentTimeline(timeline) is False:
        raise RuntimeError("Resolve could not activate the montage timeline")
    if timeline.GetTrackCount("video") < 1:
        timeline.AddTrack("video")
    timeline.AddTrack("audio", "stereo")
    music_track = None
    if cfg.get("music_path"):
        timeline.AddTrack("audio", "stereo")
        music_track = timeline.GetTrackCount("audio")
    start_frame = timeline.GetStartFrame()

    video_infos = []
    for clip in clips:
        native_fps = float(clip.get("source_fps") or fps)
        video_infos.append({
            "mediaPoolItem": by_path[canonical(clip["source"])],
            "startFrame": max(0, round(float(clip["clip_start"]) * native_fps)),
            "endFrame": max(0, round(float(clip["clip_end"]) * native_fps) - 1),
            "mediaType": 1, "trackIndex": 1,
            "recordFrame": start_frame + round(float(clip["record_start"]) * fps),
        })
    if video_infos and media_pool.AppendToTimeline(video_infos) is None:
        raise RuntimeError("Resolve could not place montage clips")
    game_audio_infos = [dict(info, mediaType=2) for info in video_infos]
    if game_audio_infos and media_pool.AppendToTimeline(game_audio_infos) is None:
        raise RuntimeError("Resolve could not place gameplay audio")

    if cfg.get("music_path"):
        music = {
            "mediaPoolItem": by_path[canonical(cfg["music_path"])], "startFrame": 0,
            "endFrame": max(0, round(float(manifest.get("song_duration") or manifest.get("content_duration") or 1) * fps) - 1),
            "mediaType": 2, "trackIndex": music_track, "recordFrame": start_frame,
        }
        if media_pool.AppendToTimeline([music]) is None:
            raise RuntimeError("Resolve could not place the music track")

    # Resolve proxy handles are refreshed after timeline edits.
    for item in (timeline.GetItemListInTrack("audio", 1) or []):
        set_audio_level(item, cfg.get("game_audio_level", .35))
    if music_track:
        for item in (timeline.GetItemListInTrack("audio", music_track) or []):
            set_audio_level(item, cfg.get("music_level", 1.0))
    for index, clip in enumerate(clips, 1):
        record_start = start_frame + round(float(clip["record_start"]) * fps)
        timeline.AddMarker(record_start, "Blue", "engagement_start",
                           "ARC Raiders firing/setup start", 1, clip["id"] + "-start")
        payoff_time = clip.get("event_time")
        payoff_time = clip["clip_start"] if payoff_time is None else payoff_time
        payoff_offset = max(0.0, float(payoff_time) - float(clip["clip_start"]))
        timeline.AddMarker(record_start + round(payoff_offset * fps), "Red",
                           clip.get("label", "highlight"), "ARC Raiders impact/payoff beat", 1, clip["id"])
    manifest["resolve_timeline"] = name
    manifest["resolve_timeline_start_frame"] = start_frame
    manifest["resolve_previous_project_settings"] = previous
    with open(MANIFEST_PATH, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    pm.SaveProject()
    return {"status": "built", "timeline": name, "clips": len(clips), "duration": manifest.get("content_duration")}


def render():
    timeline = project.GetCurrentTimeline()
    expected = manifest.get("resolve_timeline")
    if timeline is None or (expected and timeline.GetName() != expected):
        raise RuntimeError("The planned montage timeline is not active")
    output_dir = cfg["output_path"]
    output_stem = manifest["output"]["stem"]
    resolve.OpenPage("deliver")
    time.sleep(1.5)
    if not project.SetCurrentRenderFormatAndCodec("MP4", "H264"):
        raise RuntimeError("Resolve could not select MP4/H.264")
    project.SetCurrentRenderMode(1)
    start = timeline.GetStartFrame()
    duration = max(1, round(float(manifest.get("content_duration") or 1) * fps))
    settings = {"SelectAllFrames": False, "MarkIn": start, "MarkOut": start + duration - 1,
                "TargetDir": output_dir, "CustomName": output_stem, "ExportVideo": True,
                "ExportAudio": True, "FormatWidth": width, "FormatHeight": height,
                "FrameRate": fps, "AudioCodec": "aac", "AudioSampleRate": 48000,
                "NetworkOptimization": True}
    if not project.SetRenderSettings(settings):
        raise RuntimeError("Resolve rejected the H.264/AAC render settings")
    job = project.AddRenderJob()
    if not job or not project.StartRendering([job]):
        raise RuntimeError("Resolve could not start the montage render")
    pm.SaveProject()
    return {"status": "render_started", "job": job, "output": os.path.join(output_dir, output_stem + ".mp4"), "duration": duration / fps}


result = build() if MODE == "build" else render()
