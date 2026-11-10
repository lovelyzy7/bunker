"""Mods: gameplay changes the player turns on, for the whole device.

The original project implements this module in full here (android_mods.py); in
this build the web route and the settings model live in web/routes/mods.py (the
Pod Programs panel's route package), and this module re-exports them so the
launcher's create_app wiring (android_runtime) and the tools tests keep the
original's call face (android_mods.router, android_mods.read_settings, ...).

Writes mods.json in the save folder, which the server reads again whenever it
changes (internal/mods), so a mod takes effect on the next call that uses it.
Every mod is off without the file: Bunker plays like the original game.
"Original" removes the file; "Comfort" turns on the Comfort Mod's set and
"Everything" every mod but the challenges.

Most mods come from the Lunar Tear Comfort Mod by NavHobbyDev (MIT):
https://github.com/NavHobbyDev/lunar-tear-comfort-mod
"""
from web.routes.mods import (  # noqa: F401
    CHALLENGE_KEYS,
    COMFORT_KEYS,
    COMFORT_MOD,
    GROUPS,
    HARD_ENEMIES,
    KEYS,
    KIND,
    MAX_MULTIPLIER,
    OFF,
    PRESETS,
    bonus_view,
    challenge_bonus,
    comfort_on,
    form_value,
    mods_path,
    preset_of,
    read_settings,
    router,
    save_settings,
    saved_message,
    validate,
    write_settings,
)
