"""Frame rate and resolution for the game, applied the next time it opens.

Writes tools/display.conf, which the game's process reads before Unity starts
(DisplayPatch.java on Android). That process writes tools/display.status:
"ok", or "error=<reason>" when the game could not be changed.
"""
from __future__ import annotations

import os
from urllib.parse import urlencode

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from web import config

router = APIRouter()
templates = Jinja2Templates(directory=str(config.ROOT / "web" / "templates"))
FPS = [("30", "30 fps (game default)"), ("60", "60 fps"), ("90", "90 fps"), ("120", "120 fps"), ("max", "Screen maximum")]
RESOLUTIONS = [("default", "Game default"), ("1080", "1080p"), ("1440", "1440p"), ("native", "Screen's own resolution")]
# Above 30 fps (render_pace.c): draw 30 a second after 2 s without a touch outside battles,
# and slow down when the device reports it is hot.
IDLE = [("on", "Slow to 30 fps (cooler)"), ("off", "Keep the frame rate")]
HEAT = [("on", "Slow down (cooler)"), ("off", "Keep the frame rate")]
# The game's effects (render_effects.c): each costs GPU time every frame, more at high resolutions.
EFFECT = [("on", "On (game default)"), ("off", "Off (less GPU work)")]
EFFECTS = ("shadows", "reflections", "bloom")
# Below the screen's own resolution the picture is stretched to the screen; Android
# can use FSR 1 or SGSR instead (render_scale.c).
UPSCALE = [("off", "Plain stretching (game default)"), ("fsr", "FSR 1 (sharpest)"), ("sgsr", "SGSR (sharp, lighter)")]
DEFAULTS = {"fps": "30", "resolution": "default", "idle": "on", "heat": "on",
            "shadows": "on", "reflections": "on", "bloom": "on", "upscale": "off"}
RESTART = "Close Pod Programs and tap Deploy."


def conf_path():
    return config.DATA_DIR / "display.conf"


def read_settings(path=None):
    """The saved choices; unknown or missing values fall back to the game's own."""
    settings = dict(DEFAULTS)
    try:
        lines = (path or conf_path()).read_text().splitlines()
    except OSError:
        return settings
    allowed = {"fps": dict(FPS), "resolution": dict(RESOLUTIONS), "idle": dict(IDLE), "heat": dict(HEAT),
               **{name: dict(EFFECT) for name in EFFECTS}, "upscale": dict(UPSCALE)}
    for line in lines:
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if key in allowed and value in allowed[key]:
            settings[key] = value
    return settings


def write_settings(fps, resolution, path=None, idle="on", heat="on", shadows="on", reflections="on", bloom="on",
                   upscale="off"):
    if (fps not in dict(FPS) or resolution not in dict(RESOLUTIONS)
            or idle not in dict(IDLE) or heat not in dict(HEAT) or any(v not in dict(EFFECT) for v in (shadows, reflections, bloom))
            or upscale not in dict(UPSCALE)):
        raise ValueError("Unknown display setting")
    path = path or conf_path()
    pending = path.with_name(path.name + ".tmp")
    pending.write_text(f"fps={fps}\nresolution={resolution}\nidle={idle}\nheat={heat}\n"
                       f"shadows={shadows}\nreflections={reflections}\nbloom={bloom}\nupscale={upscale}\n")
    os.replace(pending, path)


def last_result():
    """What happened the last time the game opened with these choices, or None."""
    try:
        text = (config.DATA_DIR / "display.status").read_text().strip()
    except OSError:
        return None
    return {"ok": True} if text == "ok" else {"ok": False, "error": text.removeprefix("error=")}


@router.get("/display")
def view(request: Request, message: str = "", error: str = ""):
    return templates.TemplateResponse(request, "display.html", {"active": "display", "settings": read_settings(), "fps_options": FPS,
        "resolution_options": RESOLUTIONS, "idle_options": IDLE, "heat_options": HEAT, "effect_options": EFFECT,
        "upscale_options": UPSCALE, "result": last_result(), "message": message, "error": error})


@router.post("/display")
def save(fps: str = Form(...), resolution: str = Form(...), idle: str = Form("on"),
         heat: str = Form("on"), shadows: str = Form("on"), reflections: str = Form("on"), bloom: str = Form("on"),
         upscale: str = Form("off")):
    try:
        write_settings(fps, resolution, idle=idle, heat=heat, shadows=shadows, reflections=reflections, bloom=bloom,
                       upscale=upscale)
        # The status describes the previous choices until the game opens again.
        (config.DATA_DIR / "display.status").unlink(missing_ok=True)
    except Exception as exc:
        return redirect(error=str(exc))
    return redirect(message="Saved. " + RESTART)


def redirect(**kwargs):
    return RedirectResponse("/display?" + urlencode(kwargs), status_code=303)
