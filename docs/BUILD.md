# Build once, then play on the phone

## 1. Get your files

You need your own **original Android ARM64 game APK, version 3.7.1**, the original
`20240404193219.bin.e` master-data file, and an extracted Android resource dump.
The guarded binary patch supports the tested 3.7.1 ARM64 APK. It may reject
other binaries. The scripts read your original files and change only copies.

## 2. Install the build tools

Use macOS or Linux with:

- Git, Make, Go 1.25.8 or newer, `protoc`, and `apktool`.
- Python 3.11.9 or newer, available as `python3.11`. Run the build with it. An
  older `python3` (such as macOS's 3.9) cannot run it.
- JDK 21, with `JAVA_HOME` pointing to it. The Android build fails with newer JDKs.
  Android Studio's bundled JDK works:
  `export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"`.
- Android SDK platform 36, build-tools 36.0.0, and NDK 27.2.12479018.

Install the SDK components with Android Studio's SDK Manager. If `ANDROID_HOME` is not
set, the build looks for the SDK at `~/Library/Android/sdk` on macOS or `~/Android/Sdk` on
Linux. The computer needs Internet access to download build dependencies.
On macOS with Homebrew: `brew install go protobuf apktool python@3.11`.

This project builds Android only. There is no iPhone or iPad build: `ios/` was removed and no
IPA is produced or accepted.

## 3. Clone and build

```sh
git clone --recurse-submodules https://github.com/veritr1x/bunker.git
cd bunker
python3.11 scripts/build.py \
  --apk /path/to/original-game.apk \
  --master /path/to/20240404193219.bin.e
```

If you already cloned without submodules, run:

```sh
git submodule update --init --recursive
```

The build prepares the pinned sources, installs build-only Python packages in a
local virtual environment, generates protobuf code, runs Go tests and Android
lint, and signs the combined APK.

Your APK is **`artifacts/bunker.apk`**. Its checksum is in
`artifacts/SHA256SUMS`. Keep **`inputs/lunar-local.keystore`**: later APKs need the
same key to update the installed app without deleting its data. To reuse a key:

```sh
python3.11 scripts/build.py --apk /path/to/game.apk --master /path/to/master.bin.e \
  --keystore /path/to/lunar-local.keystore
```

Use this project's key format (alias `lunar-local`, local-build password
`android`). Keep the file private. Git ignores keys and game files.

## 4. Prepare the phone's game files

Copy `resource_dump_android.7z` to the phone and choose it in the launcher
(**Choose → Archive (.7z or .zip)**). Only revision 0 is used, because the
server always serves it. The dump's 817 other revisions are 28 GB of old catalogs.
The app unpacks only revision 0. It decompresses only the parts of the archive
that hold it. A `.zip` of the dump works too.

Or extract `revisions/0` yourself, on the computer
(`7zz x resource_dump_android.7z 'revisions/0/*' -oandroid-dump`) or on the
phone (for example ZArchiver), and choose the folder (**Choose → Extracted
folder: copy into the app**). The app copies only revision 0, so a full extraction works too.

**Extracted folder: use in place** (Android 11+) reads the folder from where it
is instead of copying it. This saves 21 GB. It needs **All files access**. The
app asks you once to turn it on in Settings. The app only links to the folder;
it does not own it. If you choose other files later, the app removes only the
link. If the folder is moved or deleted, the launcher tells you. Choose it again.

The import refuses a dump if its revision 0 points to files in other revisions.
The tested dump does not do this. `scripts/prepare_assets.py --source <extracted folder>`
is optional. It writes a ready `phone-assets/assets` folder with only revision 0
and checks it. This folder is smaller to copy. Its output is about 20.9 GB.
Allow at least 50 GB free on the phone during import. The game's cache may need
more. The APK already includes patched master data.

## 5. Install and play

1. Install `bunker.apk` on an ARM64 Android 9+ phone.
2. Open it. Under **1 Game files**, tap **Choose** and select the `.7z` or the copied folder.
3. Wait for the import. It first counts the files, then shows a progress bar with
   the time left. Lunar Tear starts and the game opens. Tap **Deploy** to retry.

Later launches start the server and the game automatically. When the game asks
to download files, it loads them from this phone, even in airplane mode.

The APK is signed with a different key than the publisher's APK. Before you
remove a conflicting installation, back up its saves. A later build signed with
the same local key can update this app normally.

Tap the Lunar Tear notification to return to the Bunker (the launcher). **Open Pod Programs** opens:

- Content presets, custom configuration, master import/export and rollback.
- Player inventory, gems/materials, costumes, weapons, companions and upgrades.
- Karma, slabs, debris, memoir sets and stats.
- Automatic game-save snapshots, manual backups and restoration.
- **Users**: the player marked IN USE is the one the game signs in as on this
  device. **Use this player** switches to another player in the save, and
  **New player** starts a fresh one; the previous player is always kept, and
  the save is backed up first.

Pod Programs stops the game while you edit. The first time it opens, it prepares
names from your imported resources. Close Pod Programs and tap Deploy to resume with the changed data.

Use **⋮ → Display** to choose light, dark or the phone's setting (the default) for
the Bunker and Pod Programs.

Each time the server starts, the launcher checks that the game can reach it on
its three local ports (8003, 8080 and 3000). It also checks that the server
answering is this app's own. If another app already uses one of the ports, the
launcher does not start the server. It shows which port is taken instead. **⋮ → Check server** runs the same check while the
server is running. If you cannot free the port, build with an offset. The
offset moves all three ports. This is experimental; use the same offset for every update:

```sh
python3.11 scripts/build.py --apk /path/to/game.apk --master /path/to/master.bin.e \
  --keystore /path/to/lunar-local.keystore --port-offset 30000
```

The server log is also kept between sessions in
`Android/data/<package>/files/logs/server.log`. At 5 MB, it is moved to
`server.log.1`. Read it with `adb pull` (no root needed), or use **⋮ → Export server
log**. It saves a ZIP with the log, the phone's model and the Android version.

Use **⋮ → Stop server** when finished. If Samsung pauses the server, set the
app's battery usage to **Unrestricted**.

VPN, proxy and "network accelerator" apps no longer slow the game down. Android
sends even requests to `127.0.0.1` through the phone's proxy. The proxy cannot
reach the game's server on the phone. So loading used to stall for minutes, and
it worked only in airplane mode. The app now sends the game's requests to its
own server directly. Everything else still uses the phone's proxy.

## Build in the browser (no tools to install)

The [web builder](https://lovelyzy7.github.io/bunker/) runs the same
assembly as this page, in the browser, for 日服 and 全球服 alike. Choose your
own game APK and `20240404193219.bin.e`; nothing is uploaded.

- **It checks your files first.** Both SHA-256 values are compared with the
  3.7.1 releases the patch offsets were read from, and the page says which file
  is wrong. A split APK exported from an installed copy can be allowed through
  under *advanced options*; a different game version cannot.
- **Progress and failures are named.** The page shows which step is running,
  and every known failure (wrong release, damaged zip, master data a content
  patcher has rewritten, out of memory) says what to do next.
- **The APK is signed while it is written**, with the public Bunker key
  (`web/signing/`), so one build updates another and keeps your saves. The
  finished card shows the build version, region, whether the Mod Menu is in it,
  the size and the APK's SHA-256.
- **Memory**: the assembly streams the patched game library from a work file
  into the new APK instead of holding it in Python, and the finished APK is
  handed to the page as a Blob built in the worker. A 12 GB phone builds a 日服
  APK in about 30–60 s in Chrome, with the same SHA-256 as the desktop build; an
  older phone can still run out of memory for a 300 MB APK.
- **Cancel while it runs.** *Stop* ends a build at once by terminating the
  worker — Python's long calls cannot be interrupted from JavaScript — and the
  next build reloads the runtime from the cache.
- **The launcher comes from the fastest source.** With a proxy chosen, the site,
  the proxy and the other known proxy are each timed with 64 KB before the
  download, and the winner fetches it; if it fails, the next one covers for it.
  A proxy has to send a CORS header, which is why only two of the public ones
  work (`gh-proxy.com`, `gh-proxy.org`).
- **Python ships with the site**: `build_site.py` copies Pyodide into
  `site/pyodide/` (about 13 MB), so the builder has no CDN to reach; the
  jsDelivr endpoints stay as fallbacks, ordered by how fast 64 KB arrives.
- **The slow parts start while you choose files.** Picking either file loads
  Python and the 25 MB launcher in the background, and a service worker keeps
  them (and Pyodide's 8 MB wasm) on the device: after one build, another one on
  the same device reads them from disk. The cache belongs to the release, so a
  new build of the site never mixes in the previous one. The step chips say
  *load runtime* / *check files* separately, and a build with the check skipped
  shows that chip struck through.
- **More than one source for the network.** Pyodide is fetched from whichever
  of jsDelivr's three endpoints answers first (`cdn`, `fastly`, `gcore`), and
  the launcher bundle has a mirror slot: `build_site.py --mirror <url>` (the
  Pages workflow reads the `BUNDLE_MIRROR` repository variable). A mirror has to
  be readable by the browser, so it needs a CORS header — GitHub's release
  downloads do not send one, which is why a release asset cannot be used. The
  page hashes whatever arrives against `mirrors.json` and refuses bytes that do
  not match, so a mirror cannot inject code into your APK.
- **What it cannot do** is the JP patcher's smali steps — Facebook login and the
  SQUARE ENIX BRIDGE transfer. Offline play creates its own anonymous account
  and uses neither.

The site is built by `.github/workflows/pages.yml` from
`web/build_site.py`; it contains no game files and refuses to publish master
data.

## Keep your saves

Stop the server and use **⋮ → Export save backup** before uninstalling or clearing
app storage. It exports `game.db`, `auth.db`, and `auth.key` in a ZIP.

To restore, stop the server and use **⋮ → Import save backup**. It accepts such
a ZIP or a bare `game.db`. It checks the file before it
replaces anything, and it keeps the current save as a safety copy. A save from
another device takes over this device's player. On a new device, open the game
once first, so it has a player to take over.

Tools keeps the latest 50 game-database snapshots and can restore them on the
phone. Those snapshots stay inside the app. Uninstalling the app deletes them.
Master-data changes have a separate history of the latest 10 versions.

## Optional: the Mod Menu

`--mod-menu` also injects the memory menu from
[bunker-modmenu](https://github.com/lovelyzy7/bunker-modmenu) (damage and defense
multipliers, no skill cooldown, God mode, forced hit, BigHunt cap lift; the
server hot-switch is gone because the server is always on this device).

```sh
git clone https://github.com/lovelyzy7/bunker-modmenu vendor/bunker-modmenu
python3.11 scripts/build.py --apk <game.apk> --master <master.bin.e> --mod-menu
```

The menu is built per release (`jp-client` or `en-client`) by its own toolchain:
it needs JDK 17+, Android SDK platform 34 and the NDK (ndk-build). Bunker runs
its injector on the finished APK and then re-signs with the build's key, because
the launcher only updates from APKs signed with the key it was built with. Use
`--mod-menu-root` or `$BUNKER_MODMENU` when the checkout lives elsewhere.

The web builder adds the same menu without a dex compiler: `tools/menu/` holds
the subclass that starts the menu and then the game, and `web/modmenu/` holds
its dex plus the menu's per release. Rebuild that folder after changing the menu:

```sh
JAVA_HOME=<jdk> ANDROID_HOME=<sdk> python3.11 scripts/make_menu_payload.py \
    --modmenu vendor/bunker-modmenu
```

A menu is a floating window, so the first launch asks for **Display over other
apps**. Without it the game starts normally, without the menu.

## Source layout and checks

- `upstream/`: pinned, unmodified submodules.
- `android/`: launcher, service, JNI build/packaging helpers and Python adapters
  (`tools/menu.py` drives the optional Mod Menu).
- `web/`: the in-browser builder. `web/build_site.py` assembles it; `.github/workflows/pages.yml` builds
  its bundles from this repository and publishes it on GitHub Pages.
- `android/tools/assemble_apk.py`: builds the APK by editing the original's files directly (with
  `axml.py` for the manifest), with no apktool or Android SDK. The web builder runs it in the browser.
- `overlays/`, `patches/`: mobile adaptations applied to upstream sources. The launcher and the game share the embedded server.
- `server/` and the third-party Python packages: generated, ignored build inputs.

Edit overlays or patches, not the generated copies. `scripts/prepare.py`
refuses to overwrite edits to generated sources. Source pins are in both the Git
submodule entries and `upstream.lock.json`. Update both together, and only after
you test an upstream upgrade. Do not use `git submodule update --remote` for a
normal build.

The Android app never runs the desktop grant helper: `android_runtime`
routes every editor write through the same Go engine compiled into the APK
(`test_services.py` proves each service is wired to that bridge). The desktop
panel still calls `tools/grant/grant`; `tools/grant/README.md` explains how to
drop in a prebuilt binary so the panel needs no Go toolchain.

The optional Mod Menu lives in two repositories: `lovelyzy7/bunker-modmenu` (the
device build, without the server hot-switch) and the upstream
`lovelyzy7/NieR-Re-In-Carnation-Mod_Menu`. `scripts/check_menu_parity.py`
compares them — every file of both menu modules, plus the menu's feature catalog
— and fails when one side changes without the other; the four files allowed to
differ are listed with their reasons in `scripts/menu_parity.allow`, and the
reviewed pair is pinned in `menu.lock.json`:

```sh
scripts/check_menu_parity.py --bunker ../bunker-modmenu --original ../NieR-Re-In-Carnation-Mod_Menu
scripts/check_menu_parity.py --update      # record the pair after reviewing a sync
```

For optional editor integration checks, use a disposable copy of a save with
player 1 and the prepared resources. The test makes its own working copies:

```sh
.build/venv/bin/pip install -r scripts/requirements-test.txt
# Fast, no save needed: every editor service is wired to the native bridge
# instead of the desktop grant executable.
.build/venv/bin/python android/tools/test_services.py

.build/venv/bin/python android/tools/test_tools.py \
  --save /path/to/game.db \
  --assets /path/to/prepared/assets \
  --master android/app/src/main/assets/lunar/20240404193219.bin.e \
  --original-master /path/to/original/20240404193219.bin.e
```

To run the standalone companion's JNI smoke test, connect a development ARM64
Android emulator and run `cd android && ./gradlew connectedDebugAndroidTest`.
It does not install or clear the combined game's save. Full device testing is
separate from these checks. See [validation](VALIDATION.md).

The small asset-preparation safety checks need no game files:

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
```
