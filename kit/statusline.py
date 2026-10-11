#!/usr/bin/env python3
import json
import math
import os
import sys
import tempfile
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CACHE_FILE = os.path.expanduser("~/.claude/statusline-cache.json")
GRAD = "⣀⣄⣤⣦⣶⣷⣿"
LCAP = ""
RCAP = ""

FG = (26, 27, 38)
MODEL_BG = (247, 118, 142)
COST_BG = (224, 175, 104)
CTX_BG = (67, 255, 175)
FIVE_BG = (122, 162, 247)
SEVEN_BG = (187, 154, 247)

WARN_FG = (125, 26, 46)


def fg(rgb):
    return f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m"


def bg(rgb):
    return f"\033[48;2;{rgb[0]};{rgb[1]};{rgb[2]}m"


def reset():
    return "\033[0m"


def bold():
    return "\033[1m"


def gradient_bar(pct, width):
    if pct is None:
        return " " * width
    p = max(0.0, min(100.0, float(pct))) / 100.0
    total = p * width
    out = []
    levels = len(GRAD) - 1
    for i in range(width):
        cell = total - i
        if cell >= 1:
            out.append(GRAD[-1])
        elif cell <= 0:
            out.append(" ")
        else:
            idx = round(cell * levels)
            idx = max(0, min(levels, idx))
            out.append(GRAD[idx])
    return "".join(out)


def pill(text, bg_rgb, fg_rgb=FG, bold_text=True):
    parts = []
    parts.append(fg(bg_rgb))
    parts.append(LCAP)
    parts.append(reset())
    parts.append(bg(bg_rgb))
    parts.append(fg(fg_rgb))
    if bold_text:
        parts.append(bold())
    parts.append(text)
    parts.append(reset())
    parts.append(fg(bg_rgb))
    parts.append(RCAP)
    parts.append(reset())
    return "".join(parts)


def num(v):
    if v is None or isinstance(v, bool):
        return None
    try:
        value = float(v)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def load_cache():
    try:
        with open(CACHE_FILE) as f:
            cache = json.load(f)
            if not isinstance(cache, dict):
                return {}
            # Preserve the old observation's age when upgrading a legacy cache.
            # A statusline invocation without rate_limits is not a fresh report.
            if cache.get("usage_schema") != 2:
                cache["_legacy_mtime"] = int(os.fstat(f.fileno()).st_mtime)
            return cache
    except Exception:
        return {}


def save_cache(d, filename=CACHE_FILE):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=os.path.dirname(filename),
                                         prefix=".statusline-cache-", suffix=".tmp", delete=False) as f:
            temporary = f.name
            json.dump(d, f, allow_nan=False)
        # Readers see either complete version. Windhawk opens with delete sharing.
        for attempt in range(4):
            try:
                os.replace(temporary, filename)
                temporary = None
                break
            except PermissionError:
                if attempt == 3:
                    raise
                time.sleep(0.01)
    except Exception:
        pass
    finally:
        if temporary:
            try:
                os.unlink(temporary)
            except OSError:
                pass


def usage_window(window, cache, prefix, now, duration):
    """Keep the percentage, deadline and observation from the same report."""
    window = window if isinstance(window, dict) else {}
    used = num(window.get("used_percentage"))
    if used is not None and 0 <= used <= 100:
        deadline = num(window.get("resets_at"))
        if (deadline is None or deadline <= 0 or deadline != int(deadline)
                or deadline > now + duration + 300):
            deadline = None
        return used, int(deadline) if deadline else None, now
    used = num(cache.get(prefix))
    if used is None or not 0 <= used <= 100:
        return None, None, None
    observed = num(cache.get(prefix + "_observed_at"))
    if observed is None and cache.get("usage_schema") != 2:
        observed = num(cache.get("_legacy_mtime"))
    return used, num(cache.get(prefix + "_resets_at")), observed


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}

    cache = load_cache()

    model = (data.get("model") or {}).get("display_name") or cache.get("model") or "Claude"
    cost = num(((data.get("cost") or {}).get("total_cost_usd")))
    if cost is None:
        cost = num(cache.get("cost"))
    ctx_pct = num(((data.get("context_window") or {}).get("used_percentage")))
    if ctx_pct is None:
        ctx_pct = num(cache.get("ctx"))
    rl = data.get("rate_limits") or {}
    if not isinstance(rl, dict):
        rl = {}
    observed_now = int(time.time())
    session_id = data.get("session_id")
    if (isinstance(session_id, str) and 0 < len(session_id) < 200
            and all(c.isalnum() or c in "-_" for c in session_id)
            and ctx_pct is not None and 0 <= ctx_pct <= 100):
        # Keep GSD's context monitor working with this custom status line.
        save_cache({"used_pct": ctx_pct, "remaining_percentage": 100 - ctx_pct,
                    "timestamp": observed_now},
                   os.path.join(tempfile.gettempdir(), f"claude-ctx-{session_id}.json"))
    five_pct, five_reset, five_observed = usage_window(
        rl.get("five_hour"), cache, "five", observed_now, 5 * 3600)
    seven_pct, seven_reset, seven_observed = usage_window(
        rl.get("seven_day"), cache, "seven", observed_now, 7 * 86400)

    save_cache({
        "model": model,
        "cost": cost,
        "ctx": ctx_pct,
        "five": five_pct,
        "seven": seven_pct,
        "usage_schema": 2,
        "five_resets_at": five_reset,
        "five_observed_at": five_observed,
        "seven_resets_at": seven_reset,
        "seven_observed_at": seven_observed,
    })

    bar_w = 7

    segments = []
    segments.append(pill(f" {model} ", MODEL_BG))

    if cost is not None:
        cost_fg = WARN_FG if cost >= 5.0 else FG
        segments.append(pill(f" ${cost:.2f} ", COST_BG, cost_fg))

    ctx_bar = gradient_bar(ctx_pct, bar_w)
    ctx_label = f"{int(round(ctx_pct))}%" if ctx_pct is not None else "--"
    ctx_fg = WARN_FG if (ctx_pct is not None and ctx_pct >= 80) else FG
    segments.append(pill(f" ctx {ctx_bar} {ctx_label} ", CTX_BG, ctx_fg))

    if five_pct is not None:
        five_bar = gradient_bar(five_pct, bar_w)
        five_label = f"{int(round(five_pct))}%"
        five_fg = WARN_FG if five_pct >= 80 else FG
        segments.append(pill(f" 5h {five_bar} {five_label} ", FIVE_BG, five_fg))

    if seven_pct is not None:
        seven_label = f"{int(round(seven_pct))}%"
        segments.append(pill(f" 7d {seven_label} ", SEVEN_BG, FG))

    sys.stdout.write(" ".join(segments))


if __name__ == "__main__":
    main()
