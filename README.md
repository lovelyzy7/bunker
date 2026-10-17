## AI usage disclosure

This is a **personal hobby project** built with extensive AI assistance from OpenAI Codex and Anthropic Claude for coding, integration, testing, and documentation. It is an unofficial, experimental project, not an official game release.

# Bunker

Run the game and its Lunar Tear server on the same Android phone or tablet. After setup, no computer connection or Internet is needed to play.

**Android only.** There is no iPhone or iPad build: this fork has no iOS support (no IPA is produced, and none is accepted).

- **One APK** with the launcher, the server, the content patcher and the save editors.

## Features

- **Offline play.** The game and its Lunar Tear server run on the same device. After setup, it
  needs no computer or Internet connection, and in-game downloads load from the device, even in
  airplane mode.
- **The Bunker**, the launcher: imports the resource dump (`.7z`, `.zip` or an extracted folder,
  copied or used in place), starts Lunar Tear and opens the game, and checks that the game can
  reach it.
- **Pod Programs**, on the device:
  - **Content patcher**: events and shops, with presets and rollback.
  - **Save data**: automatic snapshots, backups and restore.
  - **Players**: choose which player the game signs in as, or start a new one.
  - **Editors**: items, costumes, weapons, companions, upgrades, memoirs and more.
  - **Rates**: summon odds (★4/★3, costume and featured shares, the 10-draw guarantee,
    the multi-step boost) and the Global client's Special Gift Roulette chances.
  - **Display**: frame rate up to the screen's maximum refresh rate, and resolution up to the
    screen's own. Walking and battles keep their normal speed. Experimental: it uses more battery,
    and at 120 fps 1080p is easier on the GPU than the screen's own resolution.
- **Archive**, read from your game files: the whole story by season and chapter with who says
  each line, the records, every costume with its art, story and voice lines, 3D models with field
  and battle motions, the soundtrack, a gallery, the movies (full screen in landscape on Android,
  in the system player), and search. The game keeps running while it is open.
- **Missions**: daily, challenge, special and mission pass missions progress
  and pay their rewards (Lunar Tear left them at 0). Progress already in a save
  counts the first time. Also the daily quest set reward, skipping several
  quests at once, and story choices.
- **Arena**: battles against computer players on a ladder of 5,000, with decks
  raised to match yours. Points, grades, rank, win rewards, battle points,
  history, defense battles while you are away and weekly rewards. Opens after
  quest 61, as in the original. Season rewards are not paid: seasons never end.
- **Summon rates** (Pod Programs, experimental): the ★4 and ★3 rates, the
  costume and featured shares, the 10-draw guarantee and the multi-step boost;
  the game's Rates page shows them. Both files live next to the save
  (`gacha_rates.json`, `roulette_rates.json`), so the panel reads and writes the
  same values the server uses.
- **Special Gift Roulette** (Global client only): a spin after the (skipped) video
  pays free gems — 10, 30, 50, 100 or 3000 — with editable chances, up to six
  spins a day. The wheel's amounts stay fixed because the client only animates
  those five.
- **Summon details**: each banner's Details page lists its dates, cost,
  medal exchange, featured items and every item with its rate (names come
  from the Archive once it has been built).
- **Server fixes**: friend actions and other calls Lunar Tear did not answer
  no longer fail, and the shop's purchases add their items to the inventory.
  Reward icons that stayed blank after the game was closed mid-download are
  downloaded again.
- **Game Mode**: the app declares itself a game, so Android's Game Mode and Game Dashboard apply.
- **Light and dark**: follows the device, or choose one in ⋮ → Display.

## Screenshots

| The Bunker (launcher) | Options menu | Pod Programs |
| :---: | :---: | :---: |
| <img src="docs/screenshots/bunker.webp" width="220" alt="The Bunker: game files ready, Lunar Tear standing by, Deploy and Open Pod Programs"> | <img src="docs/screenshots/options.webp" width="220" alt="The options menu: data import and export, logs, display, settings, help and about"> | <img src="docs/screenshots/pod-programs.webp" width="220" alt="Pod Programs: content patcher, save data, players, items, costumes, weapons, upgrades and memoirs"> |
| **Players** | **The Bunker, dark** | **Pod Programs, dark** |
| <img src="docs/screenshots/players.webp" width="220" alt="Players: the one in use is marked, with New player to start another"> | <img src="docs/screenshots/bunker-dark.webp" width="220" alt="The Bunker in dark mode"> | <img src="docs/screenshots/pod-programs-dark.webp" width="220" alt="Pod Programs in dark mode"> |
| **Archive: characters** | **Archive: movies** | **Display: frame rate** |
| <img src="docs/screenshots/archive-characters.webp" width="220" alt="Archive characters: the playable cast with their costume counts"> | <img src="docs/screenshots/archive-movies.webp" width="220" alt="Archive movies: a movie playing above the list for Season 1"> | <img src="docs/screenshots/display-frame-rate.webp" width="220" alt="Display: frame rate choices from 30 fps to the screen maximum"> |

Light or dark follows the phone, or choose one in ⋮ → Display. Screenshots are from Android.

## Build in your browser

**[Open the web builder](https://veritr1x.github.io/bunker/)**: choose your own 3.7.1 game APK and
master data, and download the offline Android app. Everything runs in your browser; your files are
never uploaded. No tools to install. (日服 APK needs the command line: see [Regions](#regions).)

Limitations:

- **You still need your own files**: the original 3.7.1 ARM64 APK, the
  `20240404193219.bin.e` master data, and the resource dump. Other versions are refused.
- **The Android APK is signed with a public key**, so it installs as it is, and every web build
  updates over the previous one. The key ([`web/signing/bunker-key.p12`](web/signing/bunker-key.p12),
  password and alias `bunker`) is public: anyone can sign a build that installs over yours. To
  avoid that, re-sign with your own key, and keep using that key for updates. An app signed with
  a different key has to be uninstalled first, which deletes its data.
- **Use a desktop browser** with about 2 GB of free memory. Phones may run out of memory.
- **The Android web build has no in-game Facebook account link**, because that patch needs a
  decompiler. Offline play, Pod Programs, the Archive and save backup and import all work.
- **Experimental: port offset.** If another app on the device already uses the game's local
  ports (8003, 8080 or 3000), the launcher says so; a build with a port offset moves all three.
- **The resource dump is not part of the build.** Put its `.7z` on the phone and choose it in
  the app, which unpacks only what the game uses, so on Android the whole flow works without
  a computer.

To build everything locally instead, follow the step-by-step guide below.

## Updating

From version 1.0.0, Bunker checks for a newer release when the launcher opens and the device is
online, and shows **Bunker 1.1.0 is available** with **Update**, **What's new** and **Web
builder**. Nothing is checked offline, and **Check for updates** in the ⋮ menu turns it off. An
update downloads only Bunker's own files; the game files already in the app are reused.

- **Android:** Update rebuilds the app on the phone and Android asks you to confirm the
  install. The first time, allow NieR to install apps. Only builds signed with the public Bunker
  key (every web build) can update themselves; a build signed with your own key, or one older
  than 1.0.0, is updated with the web builder.
- **Your saves stay.** The first time a new version starts, it copies your save to Pod Programs
  › Save data as **Before update**, then updates it. An older Bunker refuses a save that a newer
  one has updated, instead of damaging it; install the newer version, or restore the snapshot.
- A few releases change how the game itself is patched. For those, the launcher says **This
  update needs the web builder**: build again with the same game files and install over the old app.

## Play on Android

1. Install the APK, from the web builder or your own build.
2. Open it and tap **Choose** under **Game files**, then choose the resource dump's `.7z` or an extracted folder, to copy or use in place (a progress bar shows the time left).
3. Tap **Deploy**. The server starts and the game opens.

The Bunker opens on later launches and deploys the game by itself; tap the Lunar Tear notification
to return to it. **Open Pod Programs** and **Open Archive** sit on the Bunker; Pod Programs stops the
game while it is open, so close it and tap **Deploy** to resume. Tap **⋮** for save backup and
import, the Lunar Tear log and its export, Display (light/dark/system), settings, help and about.

## The Mod Menu

An optional in-game memory menu, built from
[bunker-modmenu](https://github.com/lovelyzy7/bunker-modmenu): damage and defense
multipliers, no skill cooldown, God mode, forced hit, and the BigHunt cap lift.
The HP patches switch themselves off inside BigHunt battles, where they would
freeze the wave-end animation.

```sh
git clone https://github.com/lovelyzy7/bunker-modmenu vendor/bunker-modmenu
python3.11 scripts/build.py --apk <game.apk> --master <master.bin.e> --mod-menu
```

- **In the browser or on the command line.** The web builder's
  **进阶选项 :: MOD 菜单** adds it too: the game's launcher entry points at a
  prebuilt class (`tools/menu/MenuShim.java`) that starts the menu and then the
  game, so nothing needs a dex compiler. The command line injects it into the
  smali instead; both end up the same.
- **Overlay permission.** A menu is a floating window: the first launch asks to
  allow drawing over other apps (**Settings → Apps → NieR → Display over other
  apps**). Without it the game starts normally, without the menu.
- **One workspace per release**: `jp-client` for 日服, `en-client` for 全球服. The
  menu is picked from the same package name the rest of the build uses. The web
  builder ships `web/modmenu/`, built by
  `python3.11 scripts/make_menu_payload.py --modmenu <checkout>`.
- **Signed with your key**: Bunker injects the menu into the finished APK and
  re-signs with the build's own keystore, so updates keep working.
- **No server hot-switch.** The menu used to rewrite the game's connections to
  another server; the server is always on this device, so that was removed.
- The checkout is found at `vendor/bunker-modmenu`; use `--mod-menu-root` or
  `$BUNKER_MODMENU` when it lives elsewhere. Its build needs JDK 17+, Android
  SDK platform 34 and the NDK (ndk-build); details in its README.
- For offline, single-player use only.

## Build it yourself, step by step

Everything below runs on your computer once. Playing needs only the phone or tablet.
Commands are for macOS with [Homebrew](https://brew.sh); Linux and Windows (in WSL) work with the
same tools from your package manager.

### 1. Gather your own game files

None of these are included in this repository. Put them anywhere; the commands below use
`~/Downloads`.

| File | Needed for |
| --- | --- |
| Original game APK, version 3.7.1, ARM64 (`…nierspww_3.7.1…apk`) | Android, 全球服 (EN) |
| Original game APK, version 3.7.1, ARM64 (`…nierspjp_3.7.1…apk`) | Android, 日服 (JP) |
| Master data `20240404193219.bin.e` | both |
| Resource dump: `resource_dump_android.7z` | Android |

**Regions.** The game shipped twice, as 日服 (JP) and 全球服 (EN). One Lunar Tear
serves both from the same save, but they are different binaries, so a build is
one or the other. `scripts/build.py` reads the package name and picks the matching
client patcher; `--region` overrides it and is refused if it contradicts the APK.
To serve both, keep two Bunker builds installed, or rebuild for the other region.

- **JP is Android only.** The JP client patcher works on the APK's smali, so it
  needs apktool: use the command line, not the web builder.
- An update never crosses regions: an installed EN build only accepts an EN
  update, and a JP build only a JP one.
- **The build knows its region.** The launcher, the Pod Programs bar and the
  Archive all show `EN` or `JP` next to the title (JP in red), read from
  `assets/lunar/build.json`, so two installs are told apart at a glance. The
  Archive also follows it: an EN build reads the English scenario text and voice
  tracks, a JP build the Japanese ones (`assetbundle/text/{en,ja}`), and rebuilds
  its index once when that setting changes.

### 2. Install the tools

Both platforms:

```sh
brew install git go protobuf python@3.11 sevenzip
```

For **Android**, also:

```sh
brew install apktool
```

Then install [Android Studio](https://developer.android.com/studio) and, in its SDK Manager,
add **Android SDK Platform 36**, **Build-Tools 36.0.0** and **NDK 27.2.12479018**. Use its
bundled JDK 21 (newer JDKs break the Android build):

```sh
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"  # or the JDK 21 folder on your system
```

### 3. Get the code

```sh
git clone --recurse-submodules https://github.com/veritr1x/bunker.git
cd bunker
```

If you cloned without `--recurse-submodules`, run `git submodule update --init --recursive`.

### 4. Build

Always run the build with `python3.11`. It checks its tools first and names anything missing.
The first build downloads dependencies and takes several minutes.

**Android:**

```sh
python3.11 scripts/build.py \
  --apk ~/Downloads/<original-game>.apk \
  --master ~/Downloads/20240404193219.bin.e
```

Result: `artifacts/bunker.apk`. The first build creates a signing key in
`inputs/lunar-local.keystore`. **Keep it:** later builds must use the same key to update the
app without losing its data.

### 5. Get the game files onto the device (about 21 GB)

The simplest way is to copy the dump's `.7z` itself to the phone or tablet (step 6) and choose
it in the app. The app unpacks only `revisions/0`, which the game uses; the other 817 revisions
are 28 GB of old catalogs and are skipped. A `.zip` of the dump works too. Allow the archive's
size plus about 25 GB free while importing; you can delete the archive afterwards.

Alternatively, extract just that folder yourself:

```sh
7zz x ~/Downloads/resource_dump_android.7z 'revisions/0/*' -o"$HOME/Downloads/android-dump"
```

or on the phone with an app such as ZArchiver. A full extraction also works, since the app
copies only revision 0, but it needs about 49 GB free while extracting.

Optional: `python3.11 scripts/prepare_assets.py --source ~/Downloads/android-dump --output
phone-assets/android/assets` turns the extraction into a ready `assets` folder and checks it. Use
it when you copy files into the app with `adb push`, which skips the app's own import.

### 6. Install and play

**Android (9 or later, ARM64):**

1. Put `resource_dump_android.7z` (or the extracted folder) on the phone, for example in
   `Download`: with a USB cable, or `adb push ~/Downloads/resource_dump_android.7z /sdcard/Download/`.
2. Install the APK: open it on the phone, or run `adb install artifacts/bunker.apk`.
3. Open the installed app, tap **Choose**, then **Archive (.7z or .zip)** and pick the `.7z`, or
   **Extracted folder: copy into the app** and pick the folder containing `revisions`. It unpacks
   or copies revision 0 into the app; a progress bar shows the time left. You can delete the
   archive or folder afterwards.

   To save 21 GB, pick **Extracted folder: use in place** instead (Android 11 or later). The app
   asks you to turn on **All files access** for NieR in Settings once, then reads the folder where
   it is. Keep the folder there: if it is moved or deleted, choose it again.
4. Tap **Deploy**. The server starts on the phone and the game opens.

### 7. Update later

```sh
git pull
git submodule update --init --recursive
```

Then build again with the same command. On Android, the build reuses `inputs/lunar-local.keystore`
automatically. Either way, export a save backup from
**⋮** first; **⋮ → Import save backup** restores it, including on another device.

### Troubleshooting

| Message or symptom | Fix |
| --- | --- |
| `Missing <tool>` | Install it as in step 2; the build lists each missing tool. |
| Errors mentioning `filter` or `tarfile` | You ran `python3`; use `python3.11`. |
| Gradle or `jlink` fails | `JAVA_HOME` is not JDK 21; set it as in step 2. |
| `Install Python 3.13` | Run `uv python install 3.13`. |
| The new APK will not install over the old one | It was signed with a different key. Build with `--keystore` pointing to your original key. |
| Android: loading waits for minutes (for example at 20% or 60%) or shows "Failed to connect", but works in airplane mode | A VPN, proxy or "network accelerator" app was intercepting the game's requests to its own server on the phone. Builds from 2026-10-03 on send those requests directly; rebuild, or turn the app off while playing. |
| "Port 8080 is already used by another app on this device…" (or 8003, 3000) | Another app holds one of the game's local ports. Close or uninstall it, or build with `--port-offset 30000` (or the web builder's experimental port offset) and keep using that offset for updates. ⋮ → **Check Lunar Tear** shows whether the game can reach its server. |
| Android: black screen after the logo when reopening the game from Recent apps (for example after an update) | The game was opened without its server. Builds from 2026-10-04 on go through the launcher, which starts the server first; with older builds, open the app from its icon. |
| Anything else | ⋮ → **Export Lunar Tear log** saves a ZIP of the Lunar Tear log (kept between sessions, up to about 10 MB) with the device model and OS version. Attach it to your report. On Android it is also at `Android/data/<package>/files/logs/` (`adb pull` works without root). |
| Android 17: importing a `.7z` fails with `open /proc/self/fd/…: permission denied` | Fixed in builds from 2026-10-03 on; rebuild, or choose an extracted folder instead. |

More detail: [Android setup guide](docs/BUILD.md).

## Pinned upstream projects

All five are Git submodules fixed to the tested commits. Both platforms build from these exact versions.

| Project | Pinned commit |
| --- | --- |
| [Lunar Tear (JP/EN fork)](https://github.com/lovelyzy7/lunar-tear-jp_en) | `2b912f553fdb0` |
| [Lunar Scripts](https://gitlab.com/walter-sparrow-group/lunar-scripts) | `942dced617ea` |
| [Lunar Scripts (JP)](https://github.com/lovelyzy7/lunar-scripts-jp) | `b84faf515fd94` |
| [Lunar Base (bilingual fork)](https://github.com/lovelyzy7/lunar-base) | `4211ecc06310e` |
| [Master-data patcher](https://github.com/NavHobbyDev/lunar-tear-masterdata-patcher) | `9b6cd167b51d` |

Full pins: [upstream.lock.json](upstream.lock.json). Credits: [third-party notes](android/THIRD-PARTY.md).

## Status

Android 9+ on ARM64. Offline opening gameplay, touch movement, content patching, save restoration and the Archive were tested on an Android 16 emulator; folder import with progress, save import and 120 fps play were tested on a Samsung Galaxy Z Fold, including a build from the web builder. Full campaign coverage is still pending. Missions, summon details and the Arena (a full battle and its rewards) were tested on the Android emulator. See [validation](docs/VALIDATION.md).


What changed, day by day: [CHANGELOG.md](CHANGELOG.md).
