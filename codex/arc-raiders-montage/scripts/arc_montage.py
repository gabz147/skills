#!/usr/bin/env python3
"""Reusable ARC Raiders montage planner.

This script deliberately uses only the Python standard library plus ffmpeg and
ffprobe. It produces an analysis cache, candidate/review reports, and a
Resolve-ready manifest. Resolve itself is driven by resolve_montage.py.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import faulthandler
import hashlib
import html
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Iterable

try:  # Optional acceleration; the detector retains stdlib fallbacks.
    import numpy as np
except ImportError:  # pragma: no cover - exercised on minimal installs
    np = None
try:
    from scipy import ndimage
except ImportError:  # pragma: no cover - exercised on minimal installs
    ndimage = None

SCHEMA_VERSION = 2
DETECTOR_VERSION = "hud-causal-v2"
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}
TIER_VALUE = {"C": 0, "B": 1, "A": 2, "S": 3}
EVENT_LABEL_ALIASES = {"knock": "raider_knock_flare", "knock_flare": "raider_knock_flare",
                       "raider_knock_flare": "raider_knock_flare", "shield_break": "shield_break",
                       "shield_hit": "shield_hit", "impact": "impact_candidate",
                       "impact_candidate": "impact_candidate"}
HUD_SIZE = (320, 180)
FINE_SIZE = (480, 270)
WEAPON_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "assets" / "weapon-templates"
DEFAULTS: dict[str, Any] = {
    "music_path": None,
    "target_duration": "auto",
    "output_path": None,
    "output_name": None,
    "montage_style": "balanced",
    "highlight_rules": ["raider knock flare", "shield pop", "shield break"],
    "event_priority": ["raider_knock_flare", "shield_break", "shield_hit", "impact_candidate"],
    "resolution": "1920x1080",
    "frame_rate": 60,
    "game_audio_level": 0.35,
    "music_level": 1.0,
    "render_enabled": False,
    "review_required": None,
    "force_rescan": False,
    "analysis_fps": 3.0,
    "hud_analysis_fps": 8.0,
    "fine_analysis_fps": 30.0,
    "detector_profile": "accurate",
    "preferred_weapons": ["APHELION", "EQUALIZER", "TEMPEST"],
    "preferred_weapon_mode": "boost",
    "minimum_event_tier": "B",
    "hud_roi": [0.84, 0.72, 1.0, 1.0],
    "player_status_roi": [0.0, 0.84, 0.19, 1.0],
    "reticle_roi": [0.38, 0.30, 0.62, 0.70],
    "action_roi": [0.24, 0.18, 0.76, 0.92],
    "ammo_change_threshold": 0.025,
    "weapon_match_threshold": 0.42,
    "player_damage_penalty": 0.18,
    "cache_dir": None,
    "exclude_globs": [],
    "postroll_seconds": 2.0,
    "approvals_path": None,
}

GPU_DECODE_SLOTS = threading.BoundedSemaphore(4)
_STALL_TRACE_HANDLE = None

# These thresholds are part of the detector signature. They intentionally live
# outside ranking configuration so a ranking-only change can reuse analysis.
DETECTION_THRESHOLDS = {
    "ammo_noise": 0.009,
    "ammo_change_max": 0.42,
    "burst_gap_seconds": 0.85,
    "impact_min": 0.12,
    "shield_min": 0.08,
    "shield_break_min": 0.20,
    "flare_min": 0.08,
    "flare_frames": 2,
    "effect_link_radius": 0.12,
}


def die(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def run_cmd(args: list[str], *, input_data: bytes | None = None, timeout: float | None = None) -> bytes:
    try:
        p = subprocess.run(args, input=input_data, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, check=True, timeout=timeout)
    except FileNotFoundError:
        die(f"Required executable is not installed or not on PATH: {args[0]}")
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode("utf-8", "replace")[-1200:]
        die(f"Command failed ({' '.join(args[:3])}...): {detail}")
    except subprocess.TimeoutExpired:
        die(f"Command timed out ({' '.join(args[:3])}...)")
    return p.stdout


def ffprobe(path: Path, *, streams: bool = True) -> dict[str, Any]:
    args = ["ffprobe", "-v", "error", "-of", "json"]
    args += ["-show_streams", "-show_format"] if streams else ["-show_format"]
    args.append(str(path))
    return json.loads(run_cmd(args).decode("utf-8"))


def parse_time(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().lower()
    if text.endswith("ms"):
        return float(text[:-2]) / 1000.0
    if text.endswith("m") and not text.endswith("ms"):
        return float(text[:-1]) * 60.0
    if text.endswith("s"):
        return float(text[:-1])
    if ":" in text:
        parts = [float(p) for p in text.split(":")]
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
    return float(text)


def parse_duration(value: Any) -> dict[str, Any]:
    if value is None or str(value).strip().lower() in {"", "auto"}:
        return {"mode": "auto"}
    text = str(value).strip().lower().replace(" ", "")
    if text in {"full_song", "full-song", "fullsong"}:
        return {"mode": "full_song"}
    if text in {"best_available", "best-available", "bestavailable"}:
        return {"mode": "best_available"}
    match = re.fullmatch(r"(.+?)-(.+)", text)
    if match:
        lo, hi = parse_time(match.group(1)), parse_time(match.group(2))
        if lo <= 0 or hi < lo:
            raise ValueError("duration range must be positive and low <= high")
        return {"mode": "range", "min": lo, "max": hi}
    seconds = parse_time(text)
    if seconds <= 0:
        raise ValueError("duration must be positive")
    return {"mode": "exact", "seconds": seconds}


def parse_resolution(value: Any) -> tuple[int, int]:
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return int(value[0]), int(value[1])
    match = re.fullmatch(r"(\d+)x(\d+)", str(value).lower().strip())
    if not match:
        raise ValueError("resolution must look like 1920x1080")
    return int(match.group(1)), int(match.group(2))


def normalize_roi(value: Any, name: str = "roi") -> list[float]:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise ValueError(f"{name} must contain [x1, y1, x2, y2]")
    roi = [float(number) for number in value]
    x1, y1, x2, y2 = roi
    if not (0.0 <= x1 < x2 <= 1.0 and 0.0 <= y1 < y2 <= 1.0):
        raise ValueError(f"{name} coordinates must be normalized and ordered within 0..1")
    return roi


def normalized_roi_to_pixels(width: int, height: int, roi: list[float] | tuple[float, ...]) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = normalize_roi(roi)
    left = max(0, min(width - 1, int(round(width * x1))))
    top = max(0, min(height - 1, int(round(height * y1))))
    right = max(left + 1, min(width, int(round(width * x2))))
    bottom = max(top + 1, min(height, int(round(height * y2))))
    return left, top, right, bottom


def normalize_config(raw: dict[str, Any]) -> dict[str, Any]:
    cfg = dict(DEFAULTS)
    cfg.update(raw)
    if not cfg.get("footage_path"):
        raise ValueError("footage_path is required")
    footage = Path(cfg["footage_path"]).expanduser().resolve()
    if not footage.is_dir():
        raise ValueError(f"footage_path does not exist or is not a folder: {footage}")
    if cfg.get("music_path"):
        music = Path(cfg["music_path"]).expanduser().resolve()
        if not music.is_file():
            raise ValueError(f"music_path does not exist: {music}")
        cfg["music_path"] = str(music)
    cfg["footage_path"] = str(footage)
    cfg["duration_spec"] = parse_duration(cfg.get("target_duration"))
    cfg["resolution"] = "%dx%d" % parse_resolution(cfg["resolution"])
    cfg["frame_rate"] = float(cfg["frame_rate"])
    if cfg["frame_rate"] <= 0:
        raise ValueError("frame_rate must be positive")
    for name in ("analysis_fps", "hud_analysis_fps", "fine_analysis_fps"):
        cfg[name] = float(cfg[name])
        if cfg[name] <= 0:
            raise ValueError(f"{name} must be positive")
    if cfg["fine_analysis_fps"] < 1:
        raise ValueError("fine_analysis_fps must be at least 1")
    for name in ("game_audio_level", "music_level"):
        cfg[name] = float(cfg[name])
        if cfg[name] < 0:
            raise ValueError(f"{name} cannot be negative")
    cfg["highlight_rules"] = ([cfg["highlight_rules"]]
                               if isinstance(cfg["highlight_rules"], str)
                               else list(cfg["highlight_rules"] or []))
    raw_priority = cfg.get("event_priority") or []
    raw_priority = [raw_priority] if isinstance(raw_priority, str) else list(raw_priority)
    cfg["event_priority"] = []
    for value in raw_priority:
        key = str(value).strip().lower().replace(" ", "_").replace("-", "_")
        if key not in EVENT_LABEL_ALIASES:
            raise ValueError(f"unknown event_priority value: {value}")
        label = EVENT_LABEL_ALIASES[key]
        if label not in cfg["event_priority"]:
            cfg["event_priority"].append(label)
    cfg["preferred_weapons"] = list(dict.fromkeys(
        str(weapon).strip().upper() for weapon in (cfg.get("preferred_weapons") or []) if str(weapon).strip()))
    cfg["preferred_weapon_mode"] = str(cfg.get("preferred_weapon_mode") or "boost").lower()
    if cfg["preferred_weapon_mode"] not in {"boost", "only", "off"}:
        raise ValueError("preferred_weapon_mode must be boost, only, or off")
    cfg["minimum_event_tier"] = str(cfg.get("minimum_event_tier") or "B").upper()
    if cfg["minimum_event_tier"] not in TIER_VALUE:
        raise ValueError("minimum_event_tier must be S, A, B, or C")
    cfg["detector_profile"] = str(cfg.get("detector_profile") or "accurate").lower()
    if cfg["detector_profile"] not in {"fast", "balanced", "accurate"}:
        raise ValueError("detector_profile must be fast, balanced, or accurate")
    for name in ("hud_roi", "player_status_roi", "reticle_roi", "action_roi"):
        cfg[name] = normalize_roi(cfg[name], name)
    for name in ("ammo_change_threshold", "weapon_match_threshold", "player_damage_penalty"):
        cfg[name] = float(cfg[name])
        if not 0.0 <= cfg[name] <= 1.0:
            raise ValueError(f"{name} must be between 0 and 1")
    cfg["postroll_seconds"] = float(cfg["postroll_seconds"])
    if cfg["postroll_seconds"] < 0:
        raise ValueError("postroll_seconds cannot be negative")
    cfg["exclude_globs"] = list(cfg.get("exclude_globs") or [])
    cfg["cache_dir"] = str(Path(cfg["cache_dir"]).expanduser().resolve()) if cfg.get("cache_dir") else str(footage / ".arc-raiders-montage-cache")
    if cfg.get("approvals_path"):
        cfg["approvals_path"] = str(Path(cfg["approvals_path"]).expanduser().resolve())
    out_dir = Path(cfg["output_path"]).expanduser().resolve() if cfg.get("output_path") else footage
    out_dir.mkdir(parents=True, exist_ok=True)
    cfg["output_path"] = str(out_dir)
    cfg["output_name"] = cfg.get("output_name") or "arc_raiders_montage"
    cfg["render_enabled"] = bool(cfg.get("render_enabled"))
    cfg["force_rescan"] = bool(cfg.get("force_rescan"))
    if cfg.get("review_required") is None:
        cfg["review_required"] = "balanced" in str(cfg["montage_style"]).lower()
    cfg["review_required"] = bool(cfg["review_required"])
    return cfg


def load_config(path: Path) -> dict[str, Any]:
    return normalize_config(json.loads(path.read_text(encoding="utf-8")))


def sample_hash(path: Path, sample_bytes: int = 1_048_576) -> str:
    h = hashlib.sha256()
    size = path.stat().st_size
    with path.open("rb") as fh:
        h.update(fh.read(sample_bytes))
        if size > sample_bytes:
            fh.seek(max(0, size - sample_bytes))
            h.update(fh.read(sample_bytes))
    h.update(str(size).encode())
    return h.hexdigest()


def template_hashes() -> dict[str, str]:
    if not WEAPON_TEMPLATE_DIR.is_dir():
        return {}
    return {path.stem.upper(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(WEAPON_TEMPLATE_DIR.glob("*.mask"))}


def detector_signature(cfg: dict[str, Any]) -> str:
    payload = {
        "version": DETECTOR_VERSION,
        "profile": cfg["detector_profile"],
        "analysis_fps": cfg["analysis_fps"],
        "hud_analysis_fps": cfg["hud_analysis_fps"],
        "fine_analysis_fps": cfg["fine_analysis_fps"],
        "hud_roi": cfg["hud_roi"],
        "player_status_roi": cfg["player_status_roi"],
        "reticle_roi": cfg["reticle_roi"],
        "action_roi": cfg["action_roi"],
        "ammo_change_threshold": cfg["ammo_change_threshold"],
        "weapon_match_threshold": cfg["weapon_match_threshold"],
        "player_damage_penalty": cfg["player_damage_penalty"],
        "hud_size": HUD_SIZE,
        "fine_size": FINE_SIZE,
        "thresholds": DETECTION_THRESHOLDS,
        "weapon_templates": template_hashes(),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def excluded(path: Path, cfg: dict[str, Any]) -> bool:
    name = path.name.lower()
    bad_words = ("_montage", "_edit", "_export", "_preview", "_proxy", "contact_sheet")
    if any(word in name for word in bad_words):
        return True
    output_dir = Path(cfg.get("output_path") or "").resolve()
    footage_dir = Path(cfg["footage_path"]).resolve()
    if output_dir != footage_dir:
        try:
            if path.resolve().is_relative_to(output_dir):
                return True
        except AttributeError:
            if str(path.resolve()).lower().startswith(str(output_dir).lower() + os.sep):
                return True
    return any(path.match(pattern) for pattern in cfg.get("exclude_globs", []))


def inventory(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    root = Path(cfg["footage_path"])
    files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in VIDEO_EXTS and not excluded(p, cfg)]
    files.sort(key=lambda p: str(p).lower())
    result: list[dict[str, Any]] = []
    for path in files:
        stat = path.stat()
        meta = ffprobe(path)
        streams = meta.get("streams", [])
        video = next((s for s in streams if s.get("codec_type") == "video"), {})
        fps_text = video.get("r_frame_rate", "0/1")
        try:
            n, d = fps_text.split("/")
            fps = float(n) / float(d)
        except Exception:
            fps = 0.0
        duration = float(meta.get("format", {}).get("duration") or video.get("duration") or 0)
        result.append({
            "path": str(path.resolve()), "name": path.name,
            "size": stat.st_size, "mtime_ns": stat.st_mtime_ns,
            "source_hash": sample_hash(path), "duration": duration,
            "width": int(video.get("width") or 0), "height": int(video.get("height") or 0),
            "fps": fps, "codec": video.get("codec_name"),
            "has_audio": any(s.get("codec_type") == "audio" for s in streams),
        })
    return result


def cache_paths(cfg: dict[str, Any]) -> tuple[Path, Path]:
    folder = Path(cfg["cache_dir"])
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "analysis-index.json", folder / "events.json"


def load_or_inventory(cfg: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    index_path, events_path = cache_paths(cfg)
    signature = detector_signature(cfg)
    old = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() and not cfg["force_rescan"] else {}
    cache_matches = old.get("detector_signature") == signature
    old_by_path = {x["path"]: x for x in old.get("files", [])} if cache_matches else {}
    current = inventory(cfg)
    changed = [x for x in current if x["path"] not in old_by_path or x["source_hash"] != old_by_path[x["path"]].get("source_hash")]
    index = {"schema_version": SCHEMA_VERSION, "detector_version": DETECTOR_VERSION,
             "detector_signature": signature, "generated_at": time.time(), "files": current,
             "changed_files": [x["path"] for x in changed]}
    index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")
    old_events = json.loads(events_path.read_text(encoding="utf-8")) if events_path.exists() and not cfg["force_rescan"] else {"files": {}}
    if old_events.get("detector_signature") != signature:
        old_events = {"files": {}}
    return current, {"index_path": str(index_path), "events_path": str(events_path),
                     "old_events": old_events, "changed": changed, "detector_signature": signature}


def rgb_luma(frame: bytes) -> list[int]:
    if np is not None:
        rgb = np.frombuffer(frame, dtype=np.uint8).reshape(-1, 3).astype(np.uint16)
        return ((rgb[:, 0] * 3 + rgb[:, 1] * 4 + rgb[:, 2]) // 8)
    return [(frame[index] * 3 + frame[index + 1] * 4 + frame[index + 2]) // 8
            for index in range(0, len(frame), 3)]


def perceptual_hash(frame: bytes, width: int, height: int) -> str:
    luma = rgb_luma(frame)
    grid = [luma[(gy * height // 8) * width + gx * width // 8]
            for gy in range(8) for gx in range(8)]
    mean = sum(grid) / max(1, len(grid))
    return "".join("1" if value >= mean else "0" for value in grid)


def frame_features(frame: bytes, width: int, height: int,
                   center_roi: list[float] | tuple[float, ...] = (.38, .30, .62, .70)) -> dict[str, Any]:
    total = max(1, width * height)
    left, top, right, bottom = normalized_roi_to_pixels(width, height, center_roi)
    center_total = max(1, (right - left) * (bottom - top))
    if np is not None:
        rgb = np.frombuffer(frame, dtype=np.uint8).reshape(height, width, 3).astype(np.int16)
        r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
        maximum = rgb.max(axis=2)
        blue_mask = (b > r + 24) & (b > g + 10) & (b > 110)
        red_mask = (r * 100 > g * 125) & (r * 100 > b * 118) & (r > 90)
        edge = np.zeros((height, width), dtype=bool)
        edge[:, :max(1, int(width * .12))] = True
        edge[:, int(width * .88):] = True
        edge[:max(1, int(height * .10)), :] = True
        edge[int(height * .90):, :] = True
        center_max = maximum[top:bottom, left:right]
        center_blue_mask = blue_mask[top:bottom, left:right]
        return {"bright": float(np.count_nonzero(maximum > 220)) / total,
                "blue": float(np.count_nonzero(blue_mask)) / total,
                "red": float(np.count_nonzero(red_mask)) / total,
                "center_bright": float(np.count_nonzero(center_max > 215)) / center_total,
                "center_blue": float(np.count_nonzero(center_blue_mask)) / center_total,
                "edge_red": float(np.count_nonzero(red_mask & edge)) / total,
                "phash": perceptual_hash(frame, width, height)}
    bright = blue = red = center_bright = center_blue = edge_red = 0
    for y in range(height):
        for x in range(width):
            index = (y * width + x) * 3
            r, g, b = frame[index], frame[index + 1], frame[index + 2]
            maximum = max(r, g, b)
            is_blue = b > r + 24 and b > g + 10 and b > 110
            is_red = r > g * 1.25 and r > b * 1.18 and r > 90
            bright += maximum > 220
            blue += is_blue
            red += is_red
            if left <= x < right and top <= y < bottom:
                center_bright += maximum > 215
                center_blue += is_blue
            if (x < width * .12 or x > width * .88 or y < height * .10 or y > height * .90) and is_red:
                edge_red += 1
    return {"bright": bright / total, "blue": blue / total, "red": red / total,
            "center_bright": center_bright / center_total, "center_blue": center_blue / center_total,
            "edge_red": edge_red / total, "phash": perceptual_hash(frame, width, height)}


def iter_scaled_frames(path: Path, start: float, duration: float, fps: float, width: int, height: int,
                       roi: list[float] | tuple[float, ...] | None = None,
                       _allow_cuda: bool = True) -> Iterable[tuple[float, bytes]]:
    filters: list[str] = []
    use_cuda = (_allow_cuda and shutil.which("nvidia-smi") is not None
                and GPU_DECODE_SLOTS.acquire(blocking=False))
    if use_cuda:
        filters.extend(("hwdownload", "format=nv12"))
    if roi is not None:
        x1, y1, x2, y2 = normalize_roi(roi)
        filters.append("crop=trunc(iw*%.8f/2)*2:trunc(ih*%.8f/2)*2:trunc(iw*%.8f/2)*2:trunc(ih*%.8f/2)*2" %
                       (x2 - x1, y2 - y1, x1, y1))
    filters.extend((f"fps={fps}", f"scale={width}:{height}:flags=bilinear"))
    size = width * height * 3
    # Fatal-only logging prevents heavily corrupted captures from filling the
    # stderr pipe with one warning per damaged frame and deadlocking stdout.
    command = ["ffmpeg", "-v", "fatal"]
    if use_cuda:
        command.extend(("-hwaccel", "cuda", "-hwaccel_output_format", "cuda"))
    command.extend(["-ss", f"{max(0, start):.3f}",
               "-t", f"{max(.1, duration):.3f}", "-i", str(path), "-an", "-vf", ",".join(filters),
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
    try:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        die("ffmpeg is required for ARC Raiders event analysis")
    index = 0
    assert proc.stdout is not None
    while True:
        raw = proc.stdout.read(size)
        if len(raw) != size:
            break
        yield start + index / fps, raw
        index += 1
    return_code = proc.wait()
    if use_cuda:
        GPU_DECODE_SLOTS.release()
    if return_code:
        detail = proc.stderr.read().decode("utf-8", "replace")[-800:] if proc.stderr else ""
        if use_cuda and index == 0:
            yield from iter_scaled_frames(path, start, duration, fps, width, height, roi, _allow_cuda=False)
            return
        die(f"FFmpeg frame analysis failed for {path.name}: {detail}")


_WEAPON_TEMPLATES: dict[str, tuple[str, ...]] | None = None


def load_weapon_templates() -> dict[str, tuple[str, ...]]:
    global _WEAPON_TEMPLATES
    if _WEAPON_TEMPLATES is not None:
        return _WEAPON_TEMPLATES
    templates: dict[str, tuple[str, ...]] = {}
    for path in sorted(WEAPON_TEMPLATE_DIR.glob("*.mask")) if WEAPON_TEMPLATE_DIR.is_dir() else []:
        rows = [line.strip() for line in path.read_text(encoding="ascii").splitlines()
                if line.strip() and set(line.strip()) <= {"0", "1"}]
        if rows and len({len(row) for row in rows}) == 1:
            templates[path.stem.upper()] = tuple(rows)
    _WEAPON_TEMPLATES = templates
    return templates


def integral_image(values: list[int], width: int, height: int) -> list[int]:
    stride = width + 1
    result = [0] * (stride * (height + 1))
    for y in range(height):
        row_sum = 0
        for x in range(width):
            row_sum += values[y * width + x]
            result[(y + 1) * stride + x + 1] = result[y * stride + x + 1] + row_sum
    return result


def rectangle_mean(integral: list[int], width: int, height: int,
                   left: int, top: int, right: int, bottom: int) -> float:
    left, top = max(0, left), max(0, top)
    right, bottom = min(width, right), min(height, bottom)
    if right <= left or bottom <= top:
        return 0.0
    stride = width + 1
    total = (integral[bottom * stride + right] - integral[top * stride + right]
             - integral[bottom * stride + left] + integral[top * stride + left])
    return total / ((right - left) * (bottom - top))


def normalize_binary_mask(mask: bytearray, width: int, height: int,
                          output_width: int = 96, output_height: int = 16) -> tuple[str, ...]:
    if width <= 0 or height <= 0:
        return tuple("0" * output_width for _ in range(output_height))
    rows = []
    for y in range(output_height):
        source_y = min(height - 1, y * height // output_height)
        rows.append("".join("1" if mask[source_y * width + min(width - 1, x * width // output_width)] else "0"
                            for x in range(output_width)))
    return tuple(rows)


def extract_weapon_mask(luma: list[int], width: int, height: int) -> tuple[tuple[str, ...] | None, int | None]:
    if np is not None:
        pixels = np.asarray(luma, dtype=np.uint16).reshape(height, width)
        search_left, search_right = int(width * .44), int(width * .89)
        search_top, search_bottom = int(height * .25), int(height * .65)
        radius = max(2, round(height * .022))
        kernel = radius * 2 + 1
        padded = np.pad(pixels, radius, mode="edge")
        integral = np.pad(padded, ((1, 0), (1, 0)), mode="constant").cumsum(0).cumsum(1)
        local = (integral[kernel:, kernel:] - integral[:-kernel, kernel:]
                 - integral[kernel:, :-kernel] + integral[:-kernel, :-kernel]) / (kernel * kernel)
        ink = (pixels < 175) & (local > 175)
        search = ink[search_top:search_bottom, search_left:search_right]
        row_counts = np.count_nonzero(search, axis=1)
        relative_peak = int(np.argmax(row_counts)) if row_counts.size else 0
        peak_y = search_top + relative_peak
        if not row_counts.size or row_counts[relative_peak] < max(4, width // 80):
            return None, None
        half_band = max(4, round(height * .033))
        top, bottom = max(search_top, peak_y - half_band), min(search_bottom, peak_y + half_band + 1)
        band = ink[top:bottom, search_left:search_right]
        columns = np.flatnonzero(np.any(band, axis=0))
        if not columns.size:
            return None, peak_y
        left, right = search_left + int(columns[0]), search_left + int(columns[-1]) + 1
        if right - left < width * .08:
            return None, peak_y
        crop = ink[top:bottom, left:right]
        ys = np.minimum(crop.shape[0] - 1, np.arange(16) * crop.shape[0] // 16)
        xs = np.minimum(crop.shape[1] - 1, np.arange(96) * crop.shape[1] // 96)
        sampled = crop[np.ix_(ys, xs)]
        return tuple("".join("1" if value else "0" for value in row) for row in sampled), peak_y
    integral = integral_image(luma, width, height)
    search_left, search_right = int(width * .44), int(width * .89)
    search_top, search_bottom = int(height * .25), int(height * .65)
    ink = bytearray(width * height)
    row_counts = [0] * height
    radius = max(2, round(height * .022))
    for y in range(search_top, search_bottom):
        for x in range(search_left, search_right):
            value = luma[y * width + x]
            local = rectangle_mean(integral, width, height, x - radius, y - radius, x + radius + 1, y + radius + 1)
            if value < 175 and local > 175:
                ink[y * width + x] = 1
                row_counts[y] += 1
    peak_y = max(range(search_top, search_bottom), key=lambda y: row_counts[y], default=search_top)
    if row_counts[peak_y] < max(4, width // 80):
        return None, None
    half_band = max(4, round(height * .033))
    top, bottom = max(search_top, peak_y - half_band), min(search_bottom, peak_y + half_band + 1)
    columns = [sum(ink[y * width + x] for y in range(top, bottom)) for x in range(search_left, search_right)]
    nonzero = [index for index, count in enumerate(columns) if count]
    if not nonzero:
        return None, peak_y
    left = search_left + min(nonzero)
    right = search_left + max(nonzero) + 1
    if right - left < width * .08:
        return None, peak_y
    cropped = bytearray((right - left) * (bottom - top))
    for y in range(top, bottom):
        for x in range(left, right):
            cropped[(y - top) * (right - left) + x - left] = ink[y * width + x]
    return normalize_binary_mask(cropped, right - left, bottom - top), peak_y


def mask_similarity(left: tuple[str, ...], right: tuple[str, ...]) -> float:
    if not left or not right or len(left) != len(right) or len(left[0]) != len(right[0]):
        return 0.0
    height, width = len(left), len(left[0])
    left_rows = [int(row, 2) for row in left]
    right_rows = [int(row, 2) for row in right]
    row_mask = (1 << width) - 1
    best = 0.0
    for dy in range(-2, 3):
        for dx in range(-3, 4):
            intersection = union = 0
            for y in range(height):
                other_y = y - dy
                shifted = right_rows[other_y] if 0 <= other_y < height else 0
                shifted = ((shifted << dx) & row_mask) if dx >= 0 else (shifted >> -dx)
                intersection += (left_rows[y] & shifted).bit_count()
                union += (left_rows[y] | shifted).bit_count()
            best = max(best, intersection / max(1, union))
    return best


def recognize_weapon(mask: tuple[str, ...] | None, threshold: float) -> tuple[str | None, float, dict[str, float]]:
    if not mask:
        return None, 0.0, {}
    scores = {name: mask_similarity(mask, template) for name, template in load_weapon_templates().items()}
    if not scores:
        return None, 0.0, {}
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    name, score = ordered[0]
    runner_up = ordered[1][1] if len(ordered) > 1 else 0.0
    if score < threshold or score - runner_up < .05:
        return None, score, scores
    return name, score, scores


def pooled_bright_signature(luma: list[int], width: int, height: int, peak_y: int,
                            output_width: int = 48, output_height: int = 16) -> tuple[int, int]:
    left, right = int(width * .16), int(width * .52)
    top = max(0, peak_y + int(height * .045))
    bottom = min(height, peak_y + int(height * .22))
    if right <= left or bottom <= top:
        return 0, output_width * output_height
    bits = 0
    for out_y in range(output_height):
        y0 = top + out_y * (bottom - top) // output_height
        y1 = top + (out_y + 1) * (bottom - top) // output_height
        for out_x in range(output_width):
            x0 = left + out_x * (right - left) // output_width
            x1 = left + (out_x + 1) * (right - left) // output_width
            pixels = [luma[y * width + x] for y in range(y0, max(y0 + 1, y1))
                      for x in range(x0, max(x0 + 1, x1))]
            if pixels and sum(value > 205 for value in pixels) / len(pixels) >= .18:
                bits |= 1 << (out_y * output_width + out_x)
    return bits, output_width * output_height


def pooled_bright_signature_rgb(frame: bytes, width: int, height: int, peak_y: int,
                                output_width: int = 48, output_height: int = 16) -> tuple[int, int]:
    left, right = int(width * .16), int(width * .52)
    top = max(0, peak_y + int(height * .045))
    bottom = min(height, peak_y + int(height * .22))
    if right <= left or bottom <= top:
        return 0, output_width * output_height
    if np is not None:
        rgb = np.frombuffer(frame, dtype=np.uint8).reshape(height, width, 3).astype(np.uint16)
        luma = (rgb[:, :, 0] * 3 + rgb[:, :, 1] * 4 + rgb[:, :, 2]) // 8
        bits = 0
        for out_y in range(output_height):
            y0 = top + out_y * (bottom - top) // output_height
            y1 = max(y0 + 1, top + (out_y + 1) * (bottom - top) // output_height)
            for out_x in range(output_width):
                x0 = left + out_x * (right - left) // output_width
                x1 = max(x0 + 1, left + (out_x + 1) * (right - left) // output_width)
                if np.mean(luma[y0:y1, x0:x1] > 205) >= .18:
                    bits |= 1 << (out_y * output_width + out_x)
        return bits, output_width * output_height
    bits = 0
    for out_y in range(output_height):
        y0 = top + out_y * (bottom - top) // output_height
        y1 = top + (out_y + 1) * (bottom - top) // output_height
        for out_x in range(output_width):
            x0 = left + out_x * (right - left) // output_width
            x1 = left + (out_x + 1) * (right - left) // output_width
            bright = pixels = 0
            for y in range(y0, max(y0 + 1, y1)):
                for x in range(x0, max(x0 + 1, x1)):
                    index = (y * width + x) * 3
                    luma = (frame[index] * 3 + frame[index + 1] * 4 + frame[index + 2]) // 8
                    bright += luma > 205
                    pixels += 1
            if pixels and bright / pixels >= .18:
                bits |= 1 << (out_y * output_width + out_x)
    return bits, output_width * output_height


def locate_weapon_peak_rgb(frame: bytes, width: int, height: int) -> int | None:
    """Cheap per-frame anchor tracking; full template matching runs less often."""
    search_left, search_right = int(width * .44), int(width * .89)
    search_top, search_bottom = int(height * .25), int(height * .65)
    offset = max(2, round(height * .022))
    if np is not None:
        rgb = np.frombuffer(frame, dtype=np.uint8).reshape(height, width, 3).astype(np.uint16)
        luma = (rgb[:, :, 0] * 3 + rgb[:, :, 1] * 4 + rgb[:, :, 2]) // 8
        region = luma[search_top:search_bottom, search_left:search_right]
        padded = np.pad(region, ((offset, offset), (offset, offset)), mode="edge")
        neighbors = (padded[offset:-offset, :-2 * offset] + padded[offset:-offset, 2 * offset:]
                     + padded[:-2 * offset, offset:-offset] + padded[2 * offset:, offset:-offset]) / 4
        row_counts = np.count_nonzero((region < 175) & (neighbors > 175), axis=1)
        relative_peak = int(np.argmax(row_counts)) if row_counts.size else 0
        return search_top + relative_peak if row_counts[relative_peak] >= max(4, width // 80) else None
    row_counts = [0] * height

    def luma_at(x: int, y: int) -> int:
        index = (y * width + x) * 3
        return (frame[index] * 3 + frame[index + 1] * 4 + frame[index + 2]) // 8

    for y in range(search_top, search_bottom):
        for x in range(search_left, search_right):
            value = luma_at(x, y)
            if value >= 175:
                continue
            neighbors = (luma_at(max(search_left, x - offset), y),
                         luma_at(min(search_right - 1, x + offset), y),
                         luma_at(x, max(search_top, y - offset)),
                         luma_at(x, min(search_bottom - 1, y + offset)))
            if sum(neighbors) / len(neighbors) > 175:
                row_counts[y] += 1
    peak_y = max(range(search_top, search_bottom), key=lambda y: row_counts[y], default=search_top)
    return peak_y if row_counts[peak_y] >= max(4, width // 80) else None


def signature_distance(left: int | None, right: int | None, size: int) -> float:
    if left is None or right is None or size <= 0:
        return 1.0
    return (left ^ right).bit_count() / size


def hud_observation(timestamp: float, frame: bytes, width: int, height: int, cfg: dict[str, Any],
                    *, recognize_label: bool = True, known_peak_y: int | None = None) -> dict[str, Any]:
    weapon = None
    confidence = 0.0
    scores: dict[str, float] = {}
    peak_y = known_peak_y
    label_scanned = bool(recognize_label or peak_y is None)
    mask_present = False
    if recognize_label or peak_y is None:
        luma = rgb_luma(frame)
        mask, detected_peak_y = extract_weapon_mask(luma, width, height)
        mask_present = mask is not None
        peak_y = detected_peak_y if detected_peak_y is not None else known_peak_y
        weapon, confidence, scores = recognize_weapon(mask, cfg["weapon_match_threshold"])
        ammo, ammo_size = pooled_bright_signature(luma, width, height, peak_y, 48, 16) if peak_y is not None else (None, 768)
    else:
        detected_peak_y = locate_weapon_peak_rgb(frame, width, height)
        peak_y = detected_peak_y if detected_peak_y is not None else known_peak_y
        ammo, ammo_size = pooled_bright_signature_rgb(frame, width, height, peak_y, 48, 16)
    return {"time": timestamp, "weapon": weapon, "weapon_confidence": round(confidence, 4),
            "weapon_scores": {name: round(score, 4) for name, score in scores.items()},
            "weapon_peak_y": peak_y, "weapon_label_scanned": label_scanned,
            "weapon_mask_present": mask_present, "ammo_signature": ammo, "ammo_signature_size": ammo_size}


def dominant_weapon(observations: list[dict[str, Any]]) -> tuple[str | None, float]:
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}
    for observation in observations:
        weapon = observation.get("weapon")
        if weapon:
            totals[weapon] = totals.get(weapon, 0.0) + float(observation.get("weapon_confidence") or 0)
            counts[weapon] = counts.get(weapon, 0) + 1
    if not totals:
        return None, 0.0
    weapon = max(totals, key=totals.get)
    return weapon, totals[weapon] / max(1, counts[weapon])


def group_ammo_bursts(observations: list[dict[str, Any]], cfg: dict[str, Any]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    threshold = float(cfg["ammo_change_threshold"])
    noise = DETECTION_THRESHOLDS["ammo_noise"]
    maximum = DETECTION_THRESHOLDS["ammo_change_max"]
    for index in range(1, len(observations)):
        previous, current = observations[index - 1], observations[index]
        previous_peak, current_peak = previous.get("weapon_peak_y"), current.get("weapon_peak_y")
        if previous_peak is not None and current_peak is not None and abs(previous_peak - current_peak) > 3:
            continue
        size = int(current.get("ammo_signature_size") or previous.get("ammo_signature_size") or 0)
        distance = signature_distance(previous.get("ammo_signature"), current.get("ammo_signature"), size)
        if not threshold <= distance <= maximum:
            continue
        before_weapon, after_weapon = previous.get("weapon"), current.get("weapon")
        if before_weapon and after_weapon and before_weapon != after_weapon:
            continue
        next_distance = 1.0
        if index + 1 < len(observations):
            following = observations[index + 1]
            next_distance = signature_distance(current.get("ammo_signature"), following.get("ammo_signature"), size)
        stable_after = next_distance <= max(noise, threshold * .65)
        continuous = threshold <= next_distance <= maximum
        stable_before = False
        if index >= 2:
            earlier = observations[index - 2]
            stable_before = signature_distance(earlier.get("ammo_signature"), previous.get("ammo_signature"), size) <= max(
                noise, threshold * .65)
        local = observations[max(0, index - 3):min(len(observations), index + 4)]
        weapon, weapon_confidence = dominant_weapon(local)
        changes.append({"time": current["time"], "weapon": weapon,
                        "weapon_confidence": round(weapon_confidence, 4),
                        "fire_confidence": round(.76 if stable_before and stable_after else .70 if continuous else .58, 4),
                        "ammo_change": round(distance, 4),
                        "ammo_change_kind": "stable_glyph_change" if stable_after else "continuous_glyph_change" if continuous else "glyph_change"})
    if not changes:
        return []
    bursts: list[dict[str, Any]] = []
    gap = DETECTION_THRESHOLDS["burst_gap_seconds"]
    for change in changes:
        if bursts and change["time"] - bursts[-1]["shot_times"][-1] <= gap and (
                not change["weapon"] or not bursts[-1]["weapon"] or change["weapon"] == bursts[-1]["weapon"]):
            burst = bursts[-1]
            burst["shot_times"].append(change["time"])
            burst["fire_confidence"] = max(burst["fire_confidence"], change["fire_confidence"])
            burst["ammo_changes"].append(change["ammo_change"])
            if change["weapon_confidence"] > burst["weapon_confidence"]:
                burst["weapon"], burst["weapon_confidence"] = change["weapon"], change["weapon_confidence"]
            burst["ammo_change_kinds"].append(change["ammo_change_kind"])
        else:
            bursts.append({"shot_times": [change["time"]], "weapon": change["weapon"],
                           "weapon_confidence": change["weapon_confidence"], "fire_confidence": change["fire_confidence"],
                           "ammo_changes": [change["ammo_change"]], "ammo_change_kinds": [change["ammo_change_kind"]],
                           "candidate_sources": ["ammo_hud"]})
    for burst in bursts:
        latency = 1.6 if burst["weapon"] == "APHELION" else .9 if burst["weapon"] == "EQUALIZER" else 1.2
        burst["first_shot_time"] = burst["shot_times"][0]
        burst["shot_time_uncertainty"] = 1.0 / float(cfg["hud_analysis_fps"])
        burst["start"] = max(0.0, burst["first_shot_time"] - .4)
        burst["end"] = burst["shot_times"][-1] + latency + 1.4
    return bursts


def scan_hud_candidates(file_info: dict[str, Any], cfg: dict[str, Any]) -> list[dict[str, Any]]:
    width, height = HUD_SIZE
    observations: list[dict[str, Any]] = []
    label_interval = max(1, round(float(cfg["hud_analysis_fps"]) / 2.0))
    last_weapon = None
    last_weapon_confidence = 0.0
    last_weapon_time = -999.0
    last_peak_y = None
    for index, (timestamp, frame) in enumerate(iter_scaled_frames(
            Path(file_info["path"]), 0.0, float(file_info["duration"]),
            cfg["hud_analysis_fps"], width, height, cfg["hud_roi"])):
        recognize_label = index % label_interval == 0
        observation = hud_observation(timestamp, frame, width, height, cfg,
                                      recognize_label=recognize_label, known_peak_y=last_peak_y)
        new_peak_y = observation.get("weapon_peak_y")
        anchor_changed = bool(last_peak_y is not None and new_peak_y is not None
                              and abs(new_peak_y - last_peak_y) > 3)
        if anchor_changed and not recognize_label:
            observation = hud_observation(timestamp, frame, width, height, cfg,
                                          recognize_label=True, known_peak_y=None)
            new_peak_y = observation.get("weapon_peak_y")
        if anchor_changed:
            last_weapon = None
            last_weapon_confidence = 0.0
            last_weapon_time = -999.0
        if observation.get("weapon_peak_y") is not None:
            last_peak_y = observation["weapon_peak_y"]
        if observation.get("weapon"):
            last_weapon = observation["weapon"]
            last_weapon_confidence = observation["weapon_confidence"]
            last_weapon_time = timestamp
        elif observation.get("weapon_label_scanned") and observation.get("weapon_mask_present"):
            last_weapon = None
            last_weapon_confidence = 0.0
            last_weapon_time = -999.0
        elif timestamp - last_weapon_time <= 1.0:
            observation["weapon"] = last_weapon
            observation["weapon_confidence"] = last_weapon_confidence
        observations.append(observation)
    return group_ammo_bursts(observations, cfg)


def coarse_visual_candidates(file_info: dict[str, Any], cfg: dict[str, Any]) -> list[dict[str, Any]]:
    width, height = 160, 90
    active: list[tuple[float, float]] = []
    groups: list[list[tuple[float, float]]] = []
    last_active = -999.0
    for timestamp, frame in iter_scaled_frames(Path(file_info["path"]), 0.0, float(file_info["duration"]),
                                               cfg["analysis_fps"], width, height):
        feat = frame_features(frame, width, height, cfg["reticle_roi"])
        score = (feat["center_blue"] * 1.8 + feat["center_bright"] * .65 + feat["blue"] * .6
                 + feat["red"] * .25 - feat["edge_red"] * .4)
        is_active = feat["center_blue"] >= .018 or (feat["center_bright"] >= .045 and score >= .05)
        if is_active and timestamp - last_active <= 1.2:
            active.append((timestamp, score))
            last_active = timestamp
        elif is_active:
            if active:
                groups.append(active)
            active = [(timestamp, score)]
            last_active = timestamp
        elif active and timestamp - last_active > 1.2:
            groups.append(active)
            active = []
    if active:
        groups.append(active)
    candidates = []
    for group in groups:
        peak_time, peak_score = max(group, key=lambda item: item[1])
        pseudo_shot = max(0.0, peak_time - .3)
        candidates.append({"start": max(0.0, peak_time - .75), "end": peak_time + 1.6,
                           "first_shot_time": pseudo_shot, "shot_times": [pseudo_shot],
                           "shot_time_uncertainty": 1.0 / float(cfg["analysis_fps"]),
                           "weapon": None, "weapon_confidence": 0.0,
                           "fire_confidence": round(min(.48, .30 + peak_score), 4),
                           "ammo_changes": [], "ammo_change_kinds": [],
                           "candidate_sources": ["visual_fallback"]})
    return candidates


def merge_candidate_windows(candidates: list[dict[str, Any]], duration: float, gap: float = 1.0,
                            max_group_duration: float = 15.0) -> list[dict[str, Any]]:
    """Merge decode ranges while preserving every logical firing seed."""
    merged: list[dict[str, Any]] = []
    for candidate in sorted(candidates, key=lambda item: (item["start"], item["end"])):
        item = {**candidate, "start": max(0.0, float(candidate["start"])),
                "end": min(duration, float(candidate["end"])),
                "shot_times": list(candidate.get("shot_times") or []),
                "ammo_changes": list(candidate.get("ammo_changes") or []),
                "ammo_change_kinds": list(candidate.get("ammo_change_kinds") or []),
                "candidate_sources": list(candidate.get("candidate_sources") or [])}
        prospective_end = max(merged[-1]["end"], item["end"]) if merged else item["end"]
        if (merged and item["start"] <= merged[-1]["end"] + gap
                and prospective_end - merged[-1]["start"] <= max_group_duration):
            merged[-1]["end"] = prospective_end
            merged[-1]["seeds"].append(item)
        else:
            merged.append({"start": item["start"], "end": item["end"], "seeds": [item]})
    return [group for group in merged if group["end"] > group["start"]]


def candidate_windows(file_info: dict[str, Any], cfg: dict[str, Any]) -> list[dict[str, Any]]:
    hud = scan_hud_candidates(file_info, cfg)
    fallback: list[dict[str, Any]] = []
    # Visual-only seeds are capped at tier C. Skip their second full-video
    # decode when the requested montage cannot admit C-tier material.
    admits_visual_fallback = TIER_VALUE.get(str(cfg.get("minimum_event_tier", "B")).upper(), 1) <= TIER_VALUE["C"]
    if admits_visual_fallback and (cfg["detector_profile"] == "accurate" or
                                   (cfg["detector_profile"] == "balanced" and not hud)):
        fallback = coarse_visual_candidates(file_info, cfg)
    return merge_candidate_windows(hud + fallback, float(file_info["duration"]))


def connected_components(mask: bytearray, width: int, height: int, origin: tuple[int, int] = (0, 0),
                         min_area: int = 1) -> list[dict[str, Any]]:
    if np is not None and ndimage is not None:
        binary = np.asarray(mask, dtype=bool).reshape(height, width)
        labels, count = ndimage.label(binary, structure=np.ones((3, 3), dtype=np.uint8))
        if not count:
            return []
        areas = np.bincount(labels.ravel())
        objects = ndimage.find_objects(labels)
        components: list[dict[str, Any]] = []
        origin_x, origin_y = origin
        for label_id, bounds in enumerate(objects, 1):
            area = int(areas[label_id])
            if area < min_area or bounds is None:
                continue
            y_slice, x_slice = bounds
            ys, xs = np.nonzero(labels[y_slice, x_slice] == label_id)
            components.append({"area": area,
                               "centroid": [origin_x + x_slice.start + float(xs.mean()),
                                            origin_y + y_slice.start + float(ys.mean())],
                               "bbox": [origin_x + x_slice.start, origin_y + y_slice.start,
                                        origin_x + x_slice.stop, origin_y + y_slice.stop]})
        return sorted(components, key=lambda component: component["area"], reverse=True)
    work = bytearray(mask)
    components: list[dict[str, Any]] = []
    origin_x, origin_y = origin
    for start in range(width * height):
        if not work[start]:
            continue
        work[start] = 0
        stack = [start]
        area = sum_x = sum_y = 0
        min_x = min_y = 10**9
        max_x = max_y = -1
        while stack:
            index = stack.pop()
            y, x = divmod(index, width)
            area += 1
            sum_x += x
            sum_y += y
            min_x, max_x = min(min_x, x), max(max_x, x)
            min_y, max_y = min(min_y, y), max(max_y, y)
            for next_y in range(max(0, y - 1), min(height, y + 2)):
                for next_x in range(max(0, x - 1), min(width, x + 2)):
                    next_index = next_y * width + next_x
                    if work[next_index]:
                        work[next_index] = 0
                        stack.append(next_index)
        if area >= min_area:
            components.append({"area": area, "centroid": [origin_x + sum_x / area, origin_y + sum_y / area],
                               "bbox": [origin_x + min_x, origin_y + min_y,
                                        origin_x + max_x + 1, origin_y + max_y + 1]})
    return sorted(components, key=lambda component: component["area"], reverse=True)


def component_summary(components: list[dict[str, Any]], center: tuple[float, float], max_distance: float,
                      area_scale: float = 35.0) -> tuple[float, list[float] | None, int]:
    best_score, best_centroid, best_area = 0.0, None, 0
    for component in components:
        x, y = component["centroid"]
        distance = math.hypot(x - center[0], y - center[1])
        if distance > max_distance:
            continue
        closeness = 1.0 - distance / max_distance
        box_width = max(1, component["bbox"][2] - component["bbox"][0])
        box_height = max(1, component["bbox"][3] - component["bbox"][1])
        fill = component["area"] / (box_width * box_height)
        aspect = max(box_width, box_height) / max(1, min(box_width, box_height))
        compactness = .30 + .70 * min(1.0, fill * 3.0)
        if aspect > 4.0 or (max(box_width, box_height) > max_distance * 1.35 and fill < .20):
            compactness *= .25
        score = (min(1.0, math.sqrt(component["area"] / max(1.0, area_scale)))
                 * (.35 + .65 * closeness) * compactness)
        if score > best_score:
            best_score, best_centroid, best_area = score, [round(x, 3), round(y, 3)], component["area"]
    return round(best_score, 4), best_centroid, best_area


def player_status_fill(frame: bytes, width: int, height: int, roi: list[float]) -> float:
    left, top, right, bottom = normalized_roi_to_pixels(width, height, roi)
    if np is not None:
        rgb = np.frombuffer(frame, dtype=np.uint8).reshape(height, width, 3)[top:bottom, left:right].astype(np.int16)
        if not rgb.size:
            return 0.0
        r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
        cyan = (b > 115) & (g > 85) & (b > r + 22)
        white = (rgb.min(axis=2) > 175) & (rgb.max(axis=2) - rgb.min(axis=2) < 48)
        return float(np.mean(cyan | white))
    colored = total = 0
    for y in range(top, bottom):
        for x in range(left, right):
            index = (y * width + x) * 3
            r, g, b = frame[index], frame[index + 1], frame[index + 2]
            cyan = b > 115 and g > 85 and b > r + 22
            white = min(r, g, b) > 175 and max(r, g, b) - min(r, g, b) < 48
            colored += cyan or white
            total += 1
    return colored / max(1, total)


def effect_frame_evidence(timestamp: float, frame: bytes, baseline: bytes, width: int, height: int,
                          cfg: dict[str, Any]) -> dict[str, Any]:
    left, top, right, bottom = normalized_roi_to_pixels(width, height, cfg["action_roi"])
    roi_width, roi_height = right - left, bottom - top
    if np is not None:
        rgb = np.frombuffer(frame, dtype=np.uint8).reshape(height, width, 3).astype(np.int16)
        base = np.frombuffer(baseline, dtype=np.uint8).reshape(height, width, 3).astype(np.int16)
        roi_rgb, roi_base = rgb[top:bottom, left:right], base[top:bottom, left:right]
        r, g, b = roi_rgb[:, :, 0], roi_rgb[:, :, 1], roi_rgb[:, :, 2]
        base_r, base_b = roi_base[:, :, 0], roi_base[:, :, 2]
        maximum, base_maximum = roi_rgb.max(axis=2), roi_base.max(axis=2)
        bright_mask = (maximum > 212) & (maximum - base_maximum > 24)
        blue_mask = (b > 105) & (b > r + 22) & (b > g + 8) & (b - base_b > 16)
        red_mask = (r > 95) & (r * 100 > g * 116) & (r * 100 > b * 112) & (r - base_r > 16)
    else:
        bright_mask = bytearray(roi_width * roi_height)
        blue_mask = bytearray(roi_width * roi_height)
        red_mask = bytearray(roi_width * roi_height)
        for y in range(top, bottom):
            for x in range(left, right):
                source_index = (y * width + x) * 3
                target_index = (y - top) * roi_width + x - left
                r, g, b = frame[source_index], frame[source_index + 1], frame[source_index + 2]
                base_r, base_g, base_b = baseline[source_index], baseline[source_index + 1], baseline[source_index + 2]
                maximum, base_maximum = max(r, g, b), max(base_r, base_g, base_b)
                bright_mask[target_index] = maximum > 212 and maximum - base_maximum > 24
                blue_mask[target_index] = b > 105 and b > r + 22 and b > g + 8 and b - base_b > 16
                red_mask[target_index] = r > 95 and r > g * 1.16 and r > b * 1.12 and r - base_r > 16
    bright_components = connected_components(bright_mask, roi_width, roi_height, (left, top), 1)
    blue_components = connected_components(blue_mask, roi_width, roi_height, (left, top), 2)
    red_components = connected_components(red_mask, roi_width, roi_height, (left, top), 2)
    reticle_left, reticle_top, reticle_right, reticle_bottom = normalized_roi_to_pixels(width, height, cfg["reticle_roi"])
    reticle = ((reticle_left + reticle_right) / 2, (reticle_top + reticle_bottom) / 2)
    max_distance = max(8.0, min(width, height) * .26)
    area_factor = (width * height) / (320 * 180)
    bright_score, bright_centroid, bright_area = component_summary(bright_components, reticle, max_distance, 28.0 * area_factor)
    blue_score, blue_centroid, blue_area = component_summary(blue_components, reticle, max_distance, 24.0 * area_factor)
    red_score, red_centroid, red_area = component_summary(red_components, reticle, max_distance, 22.0 * area_factor)
    core = (blue_centroid if blue_centroid and blue_score >= bright_score * .65 else bright_centroid)
    core = core or blue_centroid or red_centroid or [reticle[0], reticle[1]]
    spark_count = sum(1 for component in bright_components if component["area"] <= 18 * area_factor and
                      math.hypot(component["centroid"][0] - core[0], component["centroid"][1] - core[1]) <= max_distance)
    if np is not None:
        r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
        red_all = (r > 95) & (r * 100 > g * 116) & (r * 100 > b * 112) & (r - base[:, :, 0] > 16)
        edge = np.zeros((height, width), dtype=bool)
        edge[:, :max(1, int(width * .09))] = True; edge[:, int(width * .91):] = True
        edge[:max(1, int(height * .08)), :] = True; edge[int(height * .92):, :] = True
        edge_red, edge_pixels = int(np.count_nonzero(red_all & edge)), int(np.count_nonzero(edge))
    else:
        edge_red = edge_pixels = 0
        for y in range(height):
            for x in range(width):
                if not (x < width * .09 or x > width * .91 or y < height * .08 or y > height * .92):
                    continue
                index = (y * width + x) * 3
                r, g, b = frame[index], frame[index + 1], frame[index + 2]
                base_r = baseline[index]
                edge_red += r > 95 and r > g * 1.16 and r > b * 1.12 and r - base_r > 16
                edge_pixels += 1
    return {"time": timestamp, "bright_score": bright_score, "bright_centroid": bright_centroid,
            "bright_area": bright_area, "blue_score": blue_score, "blue_centroid": blue_centroid,
            "blue_area": blue_area, "red_score": red_score, "red_centroid": red_centroid,
            "red_area": red_area, "spark_count": spark_count,
            "status_fill": round(player_status_fill(frame, width, height, cfg["player_status_roi"]), 5),
            "edge_red": round(edge_red / max(1, edge_pixels), 5),
            "phash": perceptual_hash(frame, width, height)}


def spatially_linked(left: list[float] | tuple[float, float] | None,
                     right: list[float] | tuple[float, float] | None, radius: float) -> bool:
    return bool(left and right and math.hypot(float(left[0]) - float(right[0]),
                                              float(left[1]) - float(right[1])) <= radius)


def classify_causal_sequence(frames: list[dict[str, Any]], candidate: dict[str, Any],
                             cfg: dict[str, Any]) -> dict[str, Any] | None:
    if not frames:
        return None
    shot_times = sorted(float(value) for value in candidate.get("shot_times") or [candidate.get("first_shot_time", frames[0]["time"])])
    first_shot, last_shot = shot_times[0], shot_times[-1]
    shot_uncertainty = max(.05, float(candidate.get("shot_time_uncertainty") or 0))
    weapon = candidate.get("weapon")
    latency = 1.6 if weapon == "APHELION" else .9 if weapon == "EQUALIZER" else 1.2
    impact_frames = [frame for frame in frames if first_shot - shot_uncertainty <= frame["time"] <= last_shot + latency]
    if not impact_frames:
        return None
    for frame in impact_frames:
        frame["impact_score"] = round(frame["bright_score"] * .58 + frame["blue_score"] * .42
                                      + min(.15, frame["spark_count"] * .025), 4)
        frame["red_dominant"] = bool(frame["red_score"] >= .12
                                     and frame["red_score"] > frame["blue_score"] * 1.15
                                     and frame["red_score"] > frame["bright_score"] * .80)
    minimum_impact = DETECTION_THRESHOLDS["impact_min"]
    non_flare_impacts = [frame for frame in impact_frames if not frame["red_dominant"]
                         and frame["impact_score"] >= minimum_impact]
    impact_pool = non_flare_impacts or [frame for frame in impact_frames if frame["impact_score"] >= minimum_impact]
    if not impact_pool:
        return None
    peak_impact = max(frame["impact_score"] for frame in impact_pool)
    onset_threshold = max(minimum_impact, peak_impact * .82)
    impact = next(frame for frame in impact_pool if frame["impact_score"] >= onset_threshold)
    impact_centroid = (impact.get("blue_centroid") if impact.get("blue_centroid")
                       and impact["blue_score"] >= impact["bright_score"] * .65 else impact.get("bright_centroid"))
    impact_centroid = impact_centroid or impact.get("blue_centroid") or impact.get("red_centroid")
    if not impact_centroid:
        return None
    action_left, action_top, action_right, action_bottom = normalize_roi(cfg["action_roi"])
    link_radius = DETECTION_THRESHOLDS["effect_link_radius"] * min(
        (action_right - action_left) * FINE_SIZE[0], (action_bottom - action_top) * FINE_SIZE[1])
    shield_candidates = [frame for frame in frames if impact["time"] - .10 <= frame["time"] <= impact["time"] + .50
                         and frame["blue_score"] >= DETECTION_THRESHOLDS["shield_min"]
                         and spatially_linked(impact_centroid, frame.get("blue_centroid"), link_radius)]
    shield = max(shield_candidates, key=lambda frame: frame["blue_score"], default=None)
    frame_step = min((right["time"] - left["time"] for left, right in zip(frames, frames[1:])
                      if right["time"] > left["time"]), default=1 / 30)
    red_hits = [frame for frame in frames if frame["time"] > impact["time"] + frame_step * .45
                and frame["time"] <= impact["time"] + 1.4
                and frame["red_score"] >= DETECTION_THRESHOLDS["flare_min"]
                and spatially_linked(impact_centroid, frame.get("red_centroid"), link_radius)]
    flare_groups: list[list[dict[str, Any]]] = []
    for frame in red_hits:
        if flare_groups and frame["time"] - flare_groups[-1][-1]["time"] <= frame_step * 2.5:
            flare_groups[-1].append(frame)
        else:
            flare_groups.append([frame])
    persistent = [group for group in flare_groups if len(group) >= DETECTION_THRESHOLDS["flare_frames"]]
    flare_group = max(persistent, key=lambda group: max(frame["red_score"] for frame in group), default=[])
    flare = max(flare_group, key=lambda frame: frame["red_score"], default=None)
    before_status = [frame["status_fill"] for frame in frames if frame["time"] <= first_shot]
    after_status = [frame["status_fill"] for frame in frames if first_shot <= frame["time"] <= impact["time"] + .75]
    status_drop = max(0.0, (max(before_status) if before_status else frames[0]["status_fill"])
                      - (min(after_status) if after_status else frames[0]["status_fill"]))
    edge_peak = max((frame["edge_red"] for frame in frames if first_shot <= frame["time"] <= impact["time"] + .75), default=0.0)
    player_damage = min(1.0, max(0.0, status_drop - .012) * 9 + edge_peak * 4)
    strong_break = bool(shield and shield["blue_score"] >= DETECTION_THRESHOLDS["shield_break_min"]
                        and impact["bright_score"] >= .12
                        and (impact["spark_count"] >= 2 or
                             (shield["blue_score"] >= .35 and impact["bright_score"] >= .25)))
    if flare:
        label = "raider_knock_flare"
    elif strong_break:
        label = "shield_break"
    elif shield:
        label = "shield_hit"
    else:
        label = "impact_candidate"
    fire_confidence = float(candidate.get("fire_confidence") or .3)
    confidence = (.12 + fire_confidence * .24 + impact["impact_score"] * .30
                  + (shield["blue_score"] * .14 if shield else 0)
                  + (flare["red_score"] * .24 if flare else 0)
                  - player_damage * float(cfg["player_damage_penalty"]))
    confidence = max(0.0, min(1.0, confidence))
    confirmed_fire = "ammo_hud" in (candidate.get("candidate_sources") or [])
    tier = ("S" if confirmed_fire and label == "raider_knock_flare" and confidence >= .82
            else "A" if confirmed_fire and label == "raider_knock_flare"
            else "B" if confirmed_fire and label == "shield_break" else "C")
    payoff = flare or shield or impact
    final_effect_time = flare_group[-1]["time"] if flare_group else payoff["time"]
    causal = ["ammo_hud_change" if confirmed_fire else "visual_activity_seed", "target_impact"]
    if shield:
        causal.append("shield_event")
    if flare:
        causal.append("spatially_linked_knock_flare")
    reasons = [f"fire={fire_confidence:.2f}", f"impact={impact['impact_score']:.2f}"]
    if weapon:
        reasons.append(f"weapon={weapon}")
    if shield:
        reasons.append(f"shield={shield['blue_score']:.2f}")
    if flare:
        reasons.append(f"flare={flare['red_score']:.2f}/{len(flare_group)}f")
    if player_damage:
        reasons.append(f"player_damage_penalty={player_damage:.2f}")
    if not confirmed_fire:
        reasons.append("unconfirmed_fire_review_only")
    return {"event_time": payoff["time"], "payoff_time": payoff["time"], "first_shot_time": first_shot,
            "final_effect_time": final_effect_time, "label": label, "tier": tier,
            "confidence": round(confidence, 4), "weapon": weapon,
            "weapon_confidence": round(float(candidate.get("weapon_confidence") or 0), 4),
            "causal_sequence": causal,
            "evidence": {"fire_confidence": round(fire_confidence, 4), "shot_times": shot_times,
                         "shot_time_uncertainty": round(shot_uncertainty, 4),
                         "confirmed_fire": confirmed_fire,
                         "ammo_change_count": len(candidate.get("ammo_changes") or []),
                         "ammo_change_kinds": candidate.get("ammo_change_kinds") or [],
                         "candidate_sources": candidate.get("candidate_sources") or [],
                         "impact_time": impact["time"], "impact_confidence": impact["impact_score"],
                         "impact_centroid": impact_centroid, "bright_impact_core": impact["bright_score"] >= .12,
                         "spark_count": impact["spark_count"],
                         "shield_time": shield["time"] if shield else None,
                         "shield_confidence": shield["blue_score"] if shield else 0.0,
                         "flare_time": flare["time"] if flare else None,
                         "flare_confidence": flare["red_score"] if flare else 0.0,
                         "flare_frames": len(flare_group), "player_status_drop": round(status_drop, 5),
                         "player_damage_confidence": round(player_damage, 4),
                         "peak_phash": payoff["phash"], "temporal_frames": len(frames),
                         "diagnostic_reasons": reasons}}


def stable_event_id(event: dict[str, Any]) -> str:
    anchor_value = event.get("first_shot_time")
    if anchor_value is None:
        anchor_value = event.get("event_time")
    anchor = float(anchor_value if anchor_value is not None else 0)
    identity = "%s|%.3f|%s" % (event.get("source_hash") or event.get("source"), anchor, event.get("label"))
    return "event-" + hashlib.sha1(identity.encode("utf-8")).hexdigest()[:14]


def temporal_median_frame(frames: list[bytes]) -> bytes:
    if not frames:
        return b""
    if len(frames) == 1:
        return frames[0]
    if np is not None:
        selected = np.stack([np.frombuffer(frame, dtype=np.uint8) for frame in frames[-3:]], axis=0)
        return np.median(selected, axis=0).astype(np.uint8).tobytes()
    size = len(frames[0])
    selected = frames[-3:]
    output = bytearray(size)
    for index in range(size):
        values = sorted(frame[index] for frame in selected)
        output[index] = values[len(values) // 2]
    return bytes(output)


def detect_events(file_info: dict[str, Any], cfg: dict[str, Any]) -> list[dict[str, Any]]:
    duration = float(file_info.get("duration") or 0)
    if duration <= 0:
        return []
    events: list[dict[str, Any]] = []
    source_fps = float(file_info.get("fps") or cfg["fine_analysis_fps"])
    fine_fps = max(1.0, min(float(cfg["fine_analysis_fps"]), source_fps))
    width, height = FINE_SIZE
    for group in candidate_windows(file_info, cfg):
        start, end = group["start"], group["end"]
        raw_frames = list(iter_scaled_frames(Path(file_info["path"]), start, end - start, fine_fps, width, height))
        if not raw_frames:
            continue
        for candidate in group.get("seeds", []):
            seed_frames = [(timestamp, frame) for timestamp, frame in raw_frames
                           if candidate["start"] - 1e-6 <= timestamp <= candidate["end"] + 1e-6]
            if not seed_frames:
                continue
            first_shot_value = candidate.get("first_shot_time")
            first_shot = float(seed_frames[0][0] if first_shot_value is None else first_shot_value)
            baseline_cutoff = first_shot - max(.05, float(candidate.get("shot_time_uncertainty") or 0))
            baseline_frames = [frame for timestamp, frame in seed_frames if timestamp < baseline_cutoff][-3:]
            baseline = temporal_median_frame(baseline_frames) if baseline_frames else seed_frames[0][1]
            evidence_frames = [effect_frame_evidence(timestamp, frame, baseline, width, height, cfg)
                               for timestamp, frame in seed_frames]
            event = classify_causal_sequence(evidence_frames, candidate, cfg)
            if not event or event["confidence"] < .28:
                continue
            event.update({"source": file_info["path"], "source_hash": file_info["source_hash"],
                          "source_fps": source_fps,
                          "start": max(0.0, event["first_shot_time"] - 3.0),
                          "end": min(duration, event["final_effect_time"] + 2.0)})
            event["duration"] = event["end"] - event["start"]
            event["id"] = stable_event_id(event)
            events.append(event)
    return events


def hamming(a: str, b: str) -> int:
    return sum(x != y for x, y in zip(a, b))


def audio_fingerprint(event: dict[str, Any], cache: dict[str, tuple[float, ...]]) -> tuple[float, ...]:
    key = "%s|%.2f" % (event["source"], event["event_time"])
    if key in cache:
        return cache[key]
    try:
        raw = run_cmd(["ffmpeg", "-v", "fatal", "-ss", str(max(0.0, event["event_time"] - 2.0)), "-t", "4",
                       "-i", event["source"], "-vn", "-ac", "1", "-ar", "2000", "-f", "s16le", "-"], timeout=15)
        import array
        samples = array.array("h")
        samples.frombytes(raw[:len(raw) - (len(raw) % 2)])
        size = max(1, len(samples) // 16)
        values = [math.sqrt(sum(float(x) * float(x) for x in samples[i:i + size]) / max(1, len(samples[i:i + size])))
                  for i in range(0, len(samples), size)][:16]
        scale = max(values) or 1.0
        result = tuple(round(v / scale, 4) for v in values)
    except (SystemExit, OSError, subprocess.TimeoutExpired):
        result = ()
    cache[key] = result
    return result


def audio_similarity(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    if not left or not right:
        return 0.0
    size = min(len(left), len(right))
    distance = sum(abs(left[i] - right[i]) for i in range(size)) / size
    return max(0.0, 1.0 - distance)


def deduplicate(events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ordered = sorted((dict(event) for event in events),
                     key=lambda e: (-TIER_VALUE.get(str(e.get("tier") or "C"), 0),
                                    -int(bool(e.get("weapon"))), -e["confidence"], e["source"], e["start"]))
    kept: list[dict[str, Any]] = []
    groups: list[dict[str, Any]] = []
    audio_cache: dict[str, tuple[float, ...]] = {}
    for event in ordered:
        event["id"] = event.get("id") or stable_event_id(event)
        duplicate_of = None
        for prior in kept:
            same_file = event["source"] == prior["source"]
            overlap = same_file and event["start"] < prior["end"] and prior["start"] < event["end"]
            similar = hamming(event["evidence"]["peak_phash"], prior["evidence"]["peak_phash"]) <= 8
            audio_sim = audio_similarity(audio_fingerprint(event, audio_cache), audio_fingerprint(prior, audio_cache)) if similar and not same_file else 0.0
            event_payoff = event.get("event_time")
            prior_payoff = prior.get("event_time")
            payoff_distance = abs(float(event_payoff if event_payoff is not None else 0)
                                  - float(prior_payoff if prior_payoff is not None else 0))
            event_shot = event.get("first_shot_time")
            prior_shot = prior.get("first_shot_time")
            event_shot = event_payoff if event_shot is None else event_shot
            prior_shot = prior_payoff if prior_shot is None else prior_shot
            shot_distance = abs(float(event_shot if event_shot is not None else 0)
                                - float(prior_shot if prior_shot is not None else 0))
            causal_close = min(payoff_distance, shot_distance) <= .65 + 1e-6
            same_file_duplicate = overlap and causal_close
            same_file_similar = same_file and similar and payoff_distance <= 1.0 + 1e-6
            cross_capture_duplicate = not same_file and similar and audio_sim >= .88
            if same_file_duplicate or same_file_similar or cross_capture_duplicate:
                duplicate_of = prior["id"]
                break
        if duplicate_of:
            event["duplicate_of"] = duplicate_of
            groups.append({"event": event["id"], "duplicate_of": duplicate_of, "reason": "interval_overlap_or_perceptual_audio_similarity"})
        else:
            kept.append(event)
    return kept, groups


def music_duration(path: str | None) -> float:
    if not path:
        return 0.0
    try:
        return float(ffprobe(Path(path), streams=False).get("format", {}).get("duration") or 0)
    except SystemExit:
        return 0.0


def beat_times(path: str | None, duration: float) -> list[float]:
    if not path or duration <= 0:
        return [0.0]
    raw = run_cmd(["ffmpeg", "-v", "error", "-i", path, "-t", str(duration), "-vn", "-ac", "1", "-ar", "2000", "-f", "s16le", "-"])
    if not raw:
        return [0.0]
    import array
    samples = array.array("h")
    samples.frombytes(raw[:len(raw) - (len(raw) % 2)])
    block = 100  # 50 ms
    energies = []
    for i in range(0, len(samples), block):
        chunk = samples[i:i + block]
        energies.append(sum(abs(x) for x in chunk) / max(1, len(chunk)))
    if not energies:
        return [0.0]
    ranked = sorted(energies, reverse=True)
    # Retain the stronger 40% of short-window energy peaks. The previous
    # descending-percentile index admitted nearly every subdivision and made
    # "nearest beat" effectively meaningless.
    threshold = ranked[min(len(ranked) - 1, max(0, int(len(ranked) * .40)))]
    beats: list[float] = []
    for i, energy in enumerate(energies):
        if energy < threshold:
            continue
        left = energies[i - 1] if i else 0
        right = energies[i + 1] if i + 1 < len(energies) else 0
        t = i * .05
        if energy >= left and energy >= right and (not beats or t - beats[-1] >= .30):
            beats.append(t)
    return beats or [0.0]


def style_buildup(style: str) -> float:
    text = str(style).lower()
    if "aggressive" in text or "short" in text:
        return 1.5
    if "cinematic" in text or "slow" in text:
        return 5.0
    return 3.0


def choose_duration(spec: dict[str, Any], song: float, count: int) -> tuple[float, float]:
    mode = spec["mode"]
    available = max(0.0, count * 4.5)
    if mode == "exact":
        return spec["seconds"], spec["seconds"]
    if mode == "range":
        return spec["min"], min(spec["max"], max(spec["min"], available))
    if mode == "full_song":
        return song, song
    if mode == "best_available":
        return 0.0, min(song or 120.0, available or 0.0)
    auto = min(song or 120.0, max(20.0, min(120.0, available or 20.0)))
    return auto * .75, auto


def rank_events(events: list[dict[str, Any]], cfg: dict[str, Any]) -> list[dict[str, Any]]:
    rules = " ".join(str(x).lower() for x in cfg["highlight_rules"])
    preferred = set(cfg.get("preferred_weapons") or [])
    mode = cfg.get("preferred_weapon_mode", "boost")
    minimum_tier = TIER_VALUE[cfg.get("minimum_event_tier", "B")]
    priority = list(cfg.get("event_priority") or [])
    ranked = []
    for event in events:
        tier = str(event.get("tier") or "C").upper()
        if TIER_VALUE.get(tier, 0) < minimum_tier:
            continue
        weapon = str(event.get("weapon") or "").upper()
        is_preferred = bool(weapon and weapon in preferred)
        if mode == "only" and not is_preferred:
            continue
        score = TIER_VALUE.get(tier, 0) * 2.0 + float(event["confidence"])
        if event["label"] == "raider_knock_flare" and "knock" in rules:
            score += .35
        if event["label"] == "shield_break" and ("shield" in rules or "pop" in rules):
            score += .25
        if event["label"] == "shield_hit" and "hit" not in rules:
            score -= .08
        if mode == "boost" and is_preferred:
            score += .22
        if event["label"] in priority:
            score += (len(priority) - priority.index(event["label"])) * .03
        event = dict(event)
        event["preferred_weapon"] = is_preferred
        event["rank_score"] = round(score, 4)
        ranked.append(event)
    return sorted(ranked, key=lambda e: (-e["rank_score"], e["source"], e["start"]))


def plan_manifest(cfg: dict[str, Any], events: list[dict[str, Any]], duplicate_groups: list[dict[str, Any]]) -> dict[str, Any]:
    song_seconds = music_duration(cfg.get("music_path"))
    beats = beat_times(cfg.get("music_path"), song_seconds)
    buildup = style_buildup(cfg["montage_style"])
    ranked = rank_events(events, cfg)
    approvals_path = cfg.get("approvals_path")
    approvals = json.loads(Path(approvals_path).read_text(encoding="utf-8")) if approvals_path and Path(approvals_path).is_file() else {}
    rejected_ids = set(approvals.get("rejected_ids", []))
    approved_ids = set(approvals.get("approved_ids", []))
    if rejected_ids:
        ranked = [event for event in ranked if event.get("id") not in rejected_ids]
    if approved_ids:
        ranked = [event for event in ranked if event.get("id") in approved_ids]
    min_target, max_target = choose_duration(cfg["duration_spec"], song_seconds, len(ranked))
    chosen: list[dict[str, Any]] = []
    cursor = 0.0
    seen_sources: list[tuple[str, float, float]] = []
    for event in ranked:
        shot_anchor = event.get("first_shot_time")
        final_anchor = event.get("final_effect_time")
        shot_anchor = event["event_time"] if shot_anchor is None else shot_anchor
        final_anchor = event["event_time"] if final_anchor is None else final_anchor
        natural_start = max(0.0, float(shot_anchor) - buildup)
        payoff = float(event["event_time"])
        desired_payoff = cursor + max(.65, payoff - natural_start)
        viable_beats = [beat for beat in beats
                        if cursor + .30 <= beat <= cursor + 20.0
                        and beat <= cursor + payoff]
        if not viable_beats:
            continue
        sync_beat = min(viable_beats, key=lambda beat: abs(beat - desired_payoff))
        # Move the source in-point so the detected shield break/flare lands on
        # the chosen music transient. The edit remains continuous; only the
        # amount of pre-impact buildup changes.
        start = max(0.0, payoff - (sync_beat - cursor))
        payoff_record_time = cursor + (payoff - start)
        end = min(event["end"], float(final_anchor) + float(cfg["postroll_seconds"]))
        length = max(.5, end - start)
        if any(event["source"] == src and start < e and s < end for src, s, e in seen_sources):
            continue
        if max_target > 0 and cursor + length > max_target:
            length = max_target - cursor
            end = start + length
        if length < .5 or payoff_record_time > cursor + length - .12:
            continue
        transition = "natural_flash_cut" if event.get("label") in {"raider_knock_flare", "shield_break"} else "hard_cut"
        chosen.append({**event, "clip_start": round(start, 3), "clip_end": round(end, 3),
                       "record_start": round(cursor, 3), "record_end": round(cursor + length, 3),
                       "payoff_record_time": round(payoff_record_time, 3),
                       "sync_beat_time": round(sync_beat, 3), "transition_in": transition})
        seen_sources.append((event["source"], start, end))
        cursor += length
        if cursor >= max_target and max_target > 0:
            break
    if (max_target > 0 and cursor < max_target and chosen
            and cfg["duration_spec"]["mode"] == "full_song"):
        shortfall = max_target - cursor
        last = chosen[-1]
        try:
            source_duration = float(ffprobe(Path(last["source"]), streams=False).get("format", {}).get("duration") or 0)
        except SystemExit:
            source_duration = 0.0
        available_tail = max(0.0, source_duration - float(last["clip_end"]))
        extension = min(shortfall, available_tail)
        if extension > 0:
            last["clip_end"] = round(float(last["clip_end"]) + extension, 3)
            last["record_end"] = round(float(last["record_end"]) + extension, 3)
            last["outro_extension_seconds"] = round(extension, 3)
            cursor += extension
    if min_target and cursor < min_target:
        # Refuse weak padding; the caller can review candidates or add footage.
        warning = f"Only {cursor:.1f}s of strong unique clips fit; requested minimum is {min_target:.1f}s."
    else:
        warning = None
    output_dir = Path(cfg["output_path"])
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(cfg["output_name"])).strip("._") or "arc_raiders_montage"
    run_id = time.strftime("%Y%m%d-%H%M%S")
    manifest_path = output_dir / f"{stem}_{run_id}.manifest.json"
    manifest = {
        "schema_version": SCHEMA_VERSION, "detector_version": DETECTOR_VERSION,
        "detector_signature": detector_signature(cfg), "created_at": time.time(), "run_id": run_id,
        "config": cfg, "song_duration": song_seconds, "content_duration": round(cursor, 3),
        "target_window": [min_target, max_target], "warning": warning,
        "beat_sync": {"detected_beats": len(beats), "strategy": "payoff_on_nearest_transient",
                      "transition_strategy": "hard_cuts_and_natural_shield_or_flare_flash_cuts"},
        "clips": chosen, "duplicate_groups": duplicate_groups,
        "timeline": {"resolution": cfg["resolution"], "frame_rate": cfg["frame_rate"],
                      "game_audio_level": cfg["game_audio_level"], "music_level": cfg["music_level"]},
        "output": {"directory": str(output_dir), "stem": f"{stem}_{run_id}"},
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def write_contact_sheets(events: list[dict[str, Any]], cfg: dict[str, Any]) -> dict[str, str]:
    """Create small cached visual review artifacts for the strongest events."""
    artifact_dir = Path(cfg["cache_dir"]) / "artifacts" / "contact-sheets"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, str] = {}
    for source in sorted({e["source"] for e in events}):
        selected = sorted((e for e in events if e["source"] == source), key=lambda e: -e["confidence"])[:12]
        if not selected:
            continue
        safe = hashlib.sha1(source.encode("utf-8")).hexdigest()[:12]
        content_identity = "|".join(str(event.get("id") or event.get("source_hash") or "") for event in selected)
        event_signature = hashlib.sha1(content_identity.encode("utf-8")).hexdigest()[:10]
        output = artifact_dir / f"{safe}-{detector_signature(cfg)[:12]}-{event_signature}.jpg"
        if output.exists() and not cfg["force_rescan"]:
            outputs[source] = str(output)
            continue
        with tempfile.TemporaryDirectory(prefix="arc-contact-") as temp:
            frames = []
            for index, event in enumerate(selected):
                frame = Path(temp) / f"frame-{index:02d}.jpg"
                try:
                    run_cmd(["ffmpeg", "-v", "error", "-ss", str(event["event_time"]), "-i", source,
                             "-frames:v", "1", "-vf", "scale=320:-2", "-q:v", "5", "-y", str(frame)])
                    frames.append(frame)
                except SystemExit:
                    pass
            if frames:
                pattern = str(Path(temp) / "frame-%02d.jpg")
                try:
                    run_cmd(["ffmpeg", "-v", "error", "-framerate", "1", "-i", pattern,
                             "-vf", "tile=4x3:padding=4:margin=4", "-frames:v", "1", "-q:v", "5", "-y", str(output)])
                    outputs[source] = str(output)
                except SystemExit:
                    pass
    return outputs


def write_review(manifest: dict[str, Any]) -> Path:
    path = Path(manifest["manifest_path"]).with_suffix(".review.html")
    approvals_path = path.with_suffix(".approvals.json")
    if not approvals_path.exists():
        approvals_path.write_text(json.dumps({"approved_ids": [], "rejected_ids": [], "labels": {},
                                               "instructions": "Add IDs to approved/rejected lists. Optional labels can record knock, shield_break, shield_hit, or a false-positive reason."}, indent=2), encoding="utf-8")
    manifest["review"] = {"html": str(path), "approvals_template": str(approvals_path)}
    Path(manifest["manifest_path"]).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    rows = []
    for i, clip in enumerate(manifest["clips"], 1):
        evidence = clip.get("evidence", {})
        reasons = ", ".join(str(reason) for reason in evidence.get("diagnostic_reasons", []))
        rows.append("<tr><td>%d</td><td><code>%s</code></td><td>%s</td><td>%s</td><td>%s</td>"
                    "<td>%.2fs&ndash;%.2fs</td><td>%.2f</td><td>%.2f</td><td>%.2f</td><td>%.2f</td><td>%s</td></tr>" % (
                        i, html.escape(clip["id"]), html.escape(Path(clip["source"]).name),
                        html.escape(clip.get("tier", "C")), html.escape(clip.get("weapon") or "unknown"),
                        clip["clip_start"], clip["clip_end"], clip["rank_score"],
                        float(evidence.get("fire_confidence") or 0), float(evidence.get("impact_confidence") or 0),
                        float(evidence.get("player_damage_confidence") or 0), html.escape(reasons)))
    doc = """<!doctype html><meta charset='utf-8'><title>ARC Raiders montage review</title>
<style>body{font:14px system-ui;background:#111;color:#eee;padding:2rem}table{border-collapse:collapse;width:100%%}td,th{padding:.5rem;border-bottom:1px solid #444;text-align:left}</style>
<h1>ARC Raiders Montage Review</h1><p>Manifest: <code>%s</code></p><p>Content duration: %.2fs. Duplicates rejected: %d.</p>
<table><tr><th>#</th><th>ID</th><th>Source</th><th>Tier</th><th>Weapon</th><th>Source interval</th><th>Score</th><th>Fire</th><th>Impact</th><th>Player damage</th><th>Evidence</th></tr>%s</table>
""" % (html.escape(manifest["manifest_path"]), manifest["content_duration"], len(manifest["duplicate_groups"]), "".join(rows))
    path.write_text(doc, encoding="utf-8")
    return path


def verify_output(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"render output is missing or empty: {path}")
    info = ffprobe(path)
    streams = info.get("streams", [])
    video = [s for s in streams if s.get("codec_type") == "video"]
    audio = [s for s in streams if s.get("codec_type") == "audio"]
    if not video or not audio:
        raise ValueError("output must contain at least one video stream and one audio stream")
    for selector in ("0:v:0", "0:a:0"):
        run_cmd(["ffmpeg", "-v", "error", "-xerror", "-i", str(path), "-map", selector, "-f", "null", "-"])
    result = {"path": str(path), "size": path.stat().st_size, "duration": float(info.get("format", {}).get("duration") or 0),
              "video": {"codec": video[0].get("codec_name"), "width": video[0].get("width"), "height": video[0].get("height"), "fps": video[0].get("r_frame_rate")},
              "audio": {"codec": audio[0].get("codec_name"), "channels": audio[0].get("channels"), "sample_rate": audio[0].get("sample_rate")},
              "video_decode": "ok", "audio_decode": "ok", "vlc_visual_check": "manual_or_computer_use"}
    report = path.with_suffix(path.suffix + ".verification.json")
    report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def analyse(cfg: dict[str, Any]) -> dict[str, Any]:
    files, cache = load_or_inventory(cfg)
    old_events = cache["old_events"].get("files", {})
    events_by_file: dict[str, Any] = {}
    changed = {x["path"] for x in cache["changed"]}
    events_path = Path(cache["events_path"])
    reusable = [info for info in files if info["path"] not in changed and info["path"] in old_events]
    pending = [info for info in files if info not in reusable]
    for info in reusable:
        events_by_file[info["path"]] = old_events[info["path"]]

    def checkpoint(info: dict[str, Any], detected: list[dict[str, Any]]) -> None:
        events_by_file[info["path"]] = detected
        file_index = len(events_by_file)
        # Checkpoint each source so a multi-hour library scan is resumable.
        events_path.write_text(json.dumps({"schema_version": SCHEMA_VERSION, "detector_version": DETECTOR_VERSION,
                                           "detector_signature": cache["detector_signature"],
                                           "generated_at": time.time(), "incomplete": file_index < len(files),
                                           "files": events_by_file}, indent=2), encoding="utf-8")
        print(f"Analyzed {file_index}/{len(files)}: {Path(info['path']).name}", file=sys.stderr, flush=True)

    # Finish tiny tails sequentially. This avoids a rare Windows pipe stall
    # observed when only two long CUDA decoders remain after a large thread
    # pool has drained.
    workers = min(6, len(pending))
    if 0 < len(pending) <= 2:
        for info in pending:
            checkpoint(info, detect_events(info, cfg))
    elif pending:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_info = {executor.submit(detect_events, info, cfg): info for info in pending}
            for future in concurrent.futures.as_completed(future_to_info):
                info = future_to_info[future]
                checkpoint(info, future.result())
    events = [e for group in events_by_file.values() for e in group]
    minimum_tier = TIER_VALUE.get(str(cfg.get("minimum_event_tier", "B")).upper(), TIER_VALUE["B"])
    eligible_events = [event for event in events
                       if TIER_VALUE.get(str(event.get("tier") or "C").upper(), 0) >= minimum_tier]
    unique, groups = deduplicate(eligible_events)
    contact_sheets = write_contact_sheets(unique, cfg)
    events_path.write_text(json.dumps({"schema_version": SCHEMA_VERSION, "detector_version": DETECTOR_VERSION,
                                       "detector_signature": cache["detector_signature"],
                                       "generated_at": time.time(), "files": events_by_file,
                                       "events": events, "unique_events": unique, "duplicate_groups": groups,
                                       "contact_sheets": contact_sheets}, indent=2), encoding="utf-8")
    return {"files": files, "events": unique, "duplicate_groups": groups, "contact_sheets": contact_sheets, "cache": cache}


def main(argv: list[str] | None = None) -> int:
    global _STALL_TRACE_HANDLE
    if os.environ.get("ARC_MONTAGE_TRACE_STALLS") == "1":
        _STALL_TRACE_HANDLE = open(Path(tempfile.gettempdir()) / "arc-montage-stall.log", "w", encoding="utf-8")
        faulthandler.dump_traceback_later(30, repeat=True, file=_STALL_TRACE_HANDLE)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["analyze", "plan", "review", "verify", "run"])
    parser.add_argument("--config", required=False)
    parser.add_argument("--footage-path")
    parser.add_argument("--music-path")
    parser.add_argument("--target-duration")
    parser.add_argument("--output-path")
    parser.add_argument("--output-name")
    parser.add_argument("--force-rescan", action="store_true")
    parser.add_argument("--input", help="manifest or render output for review/verify")
    args = parser.parse_args(argv)
    if args.command == "verify":
        print(json.dumps(verify_output(Path(args.input)), indent=2)); return 0
    if not args.config and not args.footage_path:
        die("--config or --footage-path is required")
    if args.config:
        cfg = load_config(Path(args.config))
    else:
        cfg = normalize_config({"footage_path": args.footage_path, "music_path": args.music_path,
                                "target_duration": args.target_duration or "auto", "output_path": args.output_path,
                                "output_name": args.output_name, "force_rescan": args.force_rescan})
    analysis = analyse(cfg)
    manifest = plan_manifest(cfg, analysis["events"], analysis["duplicate_groups"])
    review = write_review(manifest)
    if args.command in {"analyze", "plan"}:
        print(json.dumps({"manifest": manifest["manifest_path"], "review": str(review), "approvals_template": manifest["review"]["approvals_template"], "files": len(analysis["files"]),
                          "candidates": len(analysis["events"]), "duplicates_rejected": len(analysis["duplicate_groups"])}, indent=2)); return 0
    if args.command == "review":
        print(json.dumps({"manifest": manifest["manifest_path"], "review": str(review), "review_required": cfg["review_required"]}, indent=2)); return 0
    if cfg["review_required"]:
        print(json.dumps({"status": "awaiting_review", "manifest": manifest["manifest_path"], "review": str(review)}, indent=2)); return 0
    if args.command == "run" and cfg["render_enabled"]:
        runner = Path(__file__).with_name("run_resolve.py")
        completed = subprocess.run([sys.executable, str(runner), "--manifest", manifest["manifest_path"], "--mode", "both"], text=True, capture_output=True)
        if completed.returncode:
            die(completed.stderr or completed.stdout or "Resolve render failed")
        print(completed.stdout); return 0
    print(json.dumps({"status": "planned", "manifest": manifest["manifest_path"], "review": str(review),
                      "render_enabled": cfg["render_enabled"]}, indent=2)); return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        die(str(exc))
