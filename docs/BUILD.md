# Build once, then play on the phone

## 1. Get your files

You need your own **original Android ARM64 game APK, version 3.7.1**, the original
`20240404193219.bin.e` master-data file, and an extracted Android resource dump.
The guarded binary patch supports the tested 3.7.1 ARM64 APK; other binaries may
be rejected. The scripts read your originals and work on separate copies.

## 2. Install the build tools

Use macOS or Linux with:

- Git, Make, Go 1.25.8 or newer, `protoc`, and `apktool`.
- Python 3.11.9 or newer, available as `python3.11`. Run the build with it; an
  older `python3` (such as macOS's 3.9) cannot run it.
- JDK 21, with `JAVA_HOME` pointing to it. Newer JDKs fail in Android's build.
  Android Studio's bundled JDK works:
  `export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"`.
- Android SDK platform 36, build-tools 36.0.0, and NDK 27.2.12479018.

Install the SDK components with Android Studio's SDK Manager. The build finds
the SDK at `~/Library/Android/sdk` on macOS or `~/Android/Sdk` on Linux if
`ANDROID_HOME` is unset. Build dependencies need Internet access on the computer.
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
same key to update your installation without removing its data. To reuse a key:

```sh
python3.11 scripts/build.py --apk /path/to/game.apk --master /path/to/master.bin.e \
  --keystore /path/to/lunar-local.keystore
```

Use this integration's key format (alias `lunar-local`, local-build password
`android`). Keep the file private. Keys and game files are ignored by Git.

## 4. Prepare the phone's game files

Copy `resource_dump_android.7z` to the phone and choose it in the launcher
(**Choose → Archive (.7z or .zip)**). Only revision 0 is used: the server
always serves it, and the dump's 817 other revisions are 28 GB of old catalogs.
The app unpacks revision 0 only, decompressing just the parts of the archive
that hold it. A `.zip` of the dump works too.

Or extract `revisions/0` yourself, on the computer
(`7zz x resource_dump_android.7z 'revisions/0/*' -oandroid-dump`) or on the
phone (for example ZArchiver), and choose the folder (**Choose → Extracted
folder: copy into the app**). It copies revision 0 only, so a full extraction works too.

**Extracted folder: use in place** (Android 11+) reads the folder where it is
instead of copying it, saving 21 GB. It needs **All files access**, which the
app asks you to turn on in Settings once. The app links the folder rather than
owning it: choosing other files later removes only the link. If the folder is
moved or deleted, the launcher says so; choose it again.

The import refuses a dump whose revision 0 points at files in other revisions;
the tested dump does not. `scripts/prepare_assets.py --source <extracted folder>`
is optional: it writes a checked, ready `phone-assets/assets` folder with only
revision 0, which is smaller to copy. Its output is about 20.9 GB. Allow at least 50 GB free on the phone during import; the game's cache
may need more. Patched master data is already bundled in the APK.

## 5. Install and play

1. Install `bunker.apk` on an ARM64 Android 9+ phone.
2. Open it. Under **1 Game files**, tap **Choose** and select the `.7z` or the copied folder.
3. Wait for import. It first counts the files, then shows a progress bar with
   the time left. Lunar Tear starts and the game opens. Tap **Deploy** to retry.

Subsequent launches start the server and game automatically. In-game download
prompts load files from this same phone, including in airplane mode.

The APK uses a different signature from the publisher's APK. Preserve existing
saves before removing a conflicting installation. A later build signed with
your same local key can update this installation normally.

Tap the Lunar Tear notification to return to the Bunker (the launcher). **Open Pod Programs** opens:

- Content presets, custom configuration, master import/export and rollback.
- Player inventory, gems/materials, costumes, weapons, companions and upgrades.
- Karma, slabs, debris, memoir sets and stats.
- Automatic game-save snapshots, manual backups and restoration.
- **Users**: the player marked IN USE is the one the game signs in as on this
  device. **Use this player** switches to another player in the save, and
  **New player** starts a fresh one; the previous player is always kept, and
  the save is backed up first.

Pod Programs stops the game while editing. Its first launch prepares names from your
imported resources. Close Pod Programs and tap Deploy to resume with the changed data.

**⋮ → Display** chooses light, dark or the phone's setting (the default) for the
Bunker and Pod Programs.

Each time the server starts, the launcher checks that the game can reach it on
its three local ports (8003, 8080 and 3000) and that it is this app's server
answering. If another app already uses one of the ports, the launcher names the
port instead of starting. **⋮ → Check server** runs the same check while the
server is running. If you cannot free the port, build with an offset, which
moves all three ports (experimental; use the same offset for every update):

```sh
python3.11 scripts/build.py --apk /path/to/game.apk --master /path/to/master.bin.e \
  --keystore /path/to/lunar-local.keystore --port-offset 30000
```

The server log is also saved between sessions in
`Android/data/<package>/files/logs/server.log` (moved to `server.log.1` at
5 MB). Read it with `adb pull`, no root needed, or use **⋮ → Export server
log**, which saves a ZIP with the log and the phone's model and Android version.

Use **⋮ → Stop server** when finished. If Samsung pauses the server, set the
app's battery usage to **Unrestricted**.

VPN, proxy and "network accelerator" apps no longer slow the game down. Android
sends even requests to `127.0.0.1` through the phone's proxy, which cannot
reach the game's server on the phone, so loading used to stall for minutes
(working only in airplane mode). The app now sends the game's requests to its
own server directly; everything else still uses the phone's proxy.

## Build in the browser (no tools to install)

The [web builder](https://lovelyzy7.github.io/bunker-jp-en/) runs the same
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
  handed to the page as a Blob built in the worker. A 12 GB phone built a 日服
  APK in 44 s in Chrome, with the same SHA-256 as the desktop build; an older
  phone can still run out of memory for a 300 MB APK.
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
a ZIP or a bare `game.db`, checks it before replacing
anything, and keeps the current save as a safety copy. A save from another
device takes over this device's player: open the game once on a new device
first, so it has a player to take over.

Tools keeps the latest 50 game-database snapshots and can restore them on the
phone. Those snapshots remain inside the app and are removed by uninstalling.
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

Edit overlays or patches rather than generated copies. `scripts/prepare.py`
refuses to overwrite edits to generated sources. Source pins live in both Git
submodule entries and `upstream.lock.json`; update them together only after
testing an upstream upgrade. Do not use `git submodule update --remote` for a
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

With a development ARM64 Android emulator connected, the standalone companion's
JNI smoke test can be run using `cd android && ./gradlew connectedDebugAndroidTest`.
It does not install or clear the combined game's save. Full device testing is
separate from these checks; see [validation](VALIDATION.md).

The small asset-preparation safety checks need no game files:

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
```
