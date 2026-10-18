> **iOS 已移除。** 下面关于 iPhone / iPad 的记录是历史；`ios/` 目录、IPA 打包与
> iOS 脚本都已删除。本项目只支持 Android，不再生成或接受 IPA。
>
> **iOS removed.** The iPhone/iPad records below are kept as history; `ios/`,
> IPA packaging and the iOS scripts are gone. This fork builds Android only.

# Validation

## Cancel, stamped scripts, source racing and a vendored runtime — 2026-10-18

- **Stop**: the button appears during a build; clicking it hid the progress,
  re-enabled BUILD and logged 已取消构建。 A full build afterwards took 29 s and
  produced `51b4cd22…282676`.
- **Stamped scripts**: `index.html` loads `app.js?b=1e40cb84e121` and that file
  creates `worker.js?b=1e40cb84e121`, so a new index can never pair with an old
  script.
- **Source**: a finished build shows 来源 本站 in the card; the log printed
  `Speed: site 6 ms` and `Speed: proxy no answer` (the dev site's release url is
  a +dev tag), and the site won.
- **Vendored Python**: `site/pyodide/` holds `pyodide.js`, `pyodide.asm.wasm`
  (8.6 MB), `python_stdlib.zip` (2.4 MB), the lock and the three wheels; the site
  grew from 26 MB to 38 MB and the worker logs a 127.0.0.1 runtime host.
- **Checks**: `ruff check web scripts android/tools` passes (74 findings fixed or
  configured away); `tests/browser/encoding_scan.py` reports 0 problems in 319
  tracked files; `tests/browser/build_test.py` replaces the Windows-only driver.

## The 00 groups, the proxy default and the Mod Menu bundle — 2026-10-18

- **No rule through the controls**: each choice is a `.group` whose border comes
  after its control row; at 390px the picker, the chip and the download button sit
  inside group 1 and the rule falls below them (screenshot
  `.build/source-00c.png`), with no line touching a button.
- **The default follows the time zone**: a fresh profile with
  `Emulation.setTimezoneOverride(Asia/Shanghai)` opens on option 2 with
  `https://gh-proxy.com/` filled in; with `Europe/Berlin` it opens on option 0
  with an empty field. Both download links followed the choice
  (`…/bundles/android.zip` vs `https://gh-proxy.com/https://github.com/…/android.zip`).
- **The Mod Menu through a proxy**: a proxy build logged
  下载 MOD 菜单…… 100% → MOD 菜单（1 MB）用时 0.0 秒 → MOD 菜单来自
  http://…/rel/modmenu.zip and produced the same APK as a direct build
  (`fce79190…a56de`). Pointed at a dead proxy, both bundles fell back to the site
  (代理不可用，改为从本站下载……) and the build still finished.
- **The watchdog waits longer**: a loaded machine took 175 s for one build without
  tripping it (the limit is 180 s of silence).

## The proxy digest, matched to the release asset — 2026-10-18

- **One launcher, one digest**: `build_site.py --launcher-zip` copies the
  release's `android.zip` (`2ea3156f…`) into the site, so `mirrors.json` publishes
  the asset's own SHA-256. A build through `https://gh-proxy.com/` and a build
  from the site produced the same APK (`64360096…`), and the local-file mode the
  same again.
- **The published site is a minute**: with `--launcher-zip` the Pages job skips
  the ten-minute APK build; a push still runs it as a check.
- **Deterministic zips**: `android_bundle` and the Mod Menu payload are written
  with a fixed timestamp (`STAMP`), so rebuilding from the same APK gives the
  same `android.zip`.

## Launcher sources, the phone bar and the repository name — 2026-10-18

- **Three launcher sources, measured in one page**: with the default selected,
  both the local picker and the proxy field are disabled; choosing *local*
  enables only the picker, and the chip reads `android.zip · 25 MB`; choosing
  *proxy* disables the picker and shows the resolved url in the hint. Each mode
  built the same APK — `51b4cd22…282676` — in 11 s, once from the local file
  (`Using the local launcher bundle (25 MB)`) and once through a CORS proxy
  (`the launcher came from http://…/bundles/android.zip`).
- **The phone bar**: at 390px the header is 98px in two rows — title 52px
  (17px `BUNKER`, 10px version) with the language button 44×44 at the right, and
  four 98px cells of 44px with 1px separators (screenshot `.build/nav-390.png`).
  At 768px it stays on one line (`.build/nav-768.png`). No wrapping, nothing
  below 44px.
- **Progress past 100%** came from a compressed body: jsDelivr's wasm is
  `Content-Length: 2667808` with `Content-Encoding: br` while the reader sees
  ~8.25 MB, i.e. 309%. Compressed responses now log megabytes
  (`正在下载 Python 运行时…… 12 MB`).
- **The release's `android.zip`** is uploaded by `release.yml` and is the target
  a proxy fetches; `mirrors.json` carries its url as `github`.

## The Mod Menu step, the finished chips and the signing progress — 2026-10-18

- **Seven chips on a phone**: 3 + 3 + one full-width 签名与校验 (measured at 390px:
  106px cells at x=30/142/254, rows at y=455/487, the last 330px wide at y=519;
  screenshot `.build/chips-7-390.png`). The skipped file check is struck through.
- **The Mod Menu has its own step**: with the box ticked the phone build logged
  MOD 菜单内容：3 dex, 1 library. → 正在写入 MOD 菜单…… → dex 1/3（1 KB）……
  … → libniermenu.so（1 MB）……, and finished with all seven chips filled; without
  the box the chip is `skipped` (`done,done,done,done,done,skipped,done`).
- **"Done" fills the last chip**: `setStage(7, 100)` marks every chip done; the
  phone showed `done,skipped,done,done,done,done,done` and no outlined chip.
- **准备运行时 has details**: 正在下载 Python 运行时…… 7%…, 正在下载 Python 标准库…,
  正在下载 Python 组件……, 正在加载构建脚本（14 个文件）……, Python 已就绪。
- **Signing reports progress**: 正在签名 10%… … 100% on a desktop build, and
  正在写入压缩包目录…… before the central directory; the APK is still
  `51b4cd22…282676` (`fce79190…a56de` with the menu).

## A stalled download, the chip grid and one-pass signing — 2026-10-18

- **A source that goes quiet no longer hangs the build**: a test server that
  sends 1 MB and then stops shows `no data for 20 s after 1 MB`, one retry, then
  the second source finishing the build; before this the same case sat at 31%
  indefinitely. A 90-second silence, a worker exception, or a frozen tab now
  shows 构建卡住了 and re-enables the button.
- **The chips on the phone**: measured at 392 CSS px, six chips in a 3×2 grid
  (106px each, 6px gaps), the bar 9px below, no overlap; screenshots
  `.build/phone-chips4.png` (all done) and `.build/chips-390.png` (done / skipped
  / on). A skipped check is struck through.
- **Signing is one pass**: `apk_sign.sign_and_digest` returns the file's SHA-256
  from the signing read; the same build is byte-identical to the recorded
  `51b4cd22…282676`, so the digest is right and the second 296 MB read is gone.
  On the phone the card appeared at 58.6 s with signing 55.5→58.6 s.
- **The build stamp is on every same-origin download**: `py/*?b=<stamp>`; without
  it a rebuilt dev site ran the previous `apk_sign.py` and failed with
  `AttributeError: module 'apk_sign' has no attribute 'sign_and_digest'`.
- **The log is Chinese on a Chinese page**: `正在下载启动器…… 42%`,
  `lib/arm64-v8a/libil2cpp.so（120 MB）……`, `正在用公开的 Bunker 密钥签名……`,
  `APK 已签名，可以安装。`, `完成。` — seen on the phone.
- **Encoding**: every tracked text file is UTF-8 without a BOM and without
  mojibake (319 files scanned); `webbuild.py` and `scripts/build.py` set UTF-8 on
  their console streams.

## The web builder's phone layout, checksum hint and caching — 2026-10-18

- **01 Your files on the device**: at 392 CSS px each file is three rows (label,
  description, chip beside the button), the chip clips a long name with an
  ellipsis and the button reads 更换 once a file is there; at 520px the same grid
  holds, at 521px and above the desktop row is unchanged, and no width from 360
  to 1280 scrolls sideways.
- **The page names the release it was given**: the 日服 APK shows `✓ 日服 · JP`,
  the 全球服 APK `✓ 全球服 · EN`, a 3.7.1-sized file with other bytes
  `✗ 不是原版 3.7.1（SHA-256 不匹配）`. On the phone the digest of the 254 MB APK
  takes about a second and is cached per file.
- **The Mod Menu checkbox builds again**: the same page with the box ticked
  produced a 283 MB APK, `built-menu: 已包含`, SHA-256 `fce79190…a56de`; the
  unticked build is `51b4cd22…282676`, the same file as before these changes.
- **The runtime starts while files are being chosen**: a phone build was 26.9 s
  when the runtime and launcher were already warm, and 57 s cold after the
  release stamp replaced the cache; on the second build the launcher line reads
  `the launcher (25 MB) in 0.1 s (cached)`. Desktop builds are 14–16 s. Every
  build produced `51b4cd22…282676`.
- **Chips say what is skipped**: with *skip the file check* ticked the chips end
  as `done,skipped,done,done,done,on`, and the first chip is 准备运行时 rather
  than 校验文件.
- **A mirror is used, and a wrong mirror is refused**: with the same-origin
  bundle removed, the build fetched it from a second origin, logged
  `the launcher came from http://…/bundles/android.zip` and finished; pointed at
  a copy with one byte flipped, it stopped with 站点文件校验失败
  (*The launcher does not match the site's checksum*). A mirror needs a CORS
  header — GitHub's release downloads do not send one.
- **The cache is per release**: 29–35 entries under `bunker-<version>-<stamp>`,
  the Pyodide host chosen on the first visit is reused on the next (the wasm is
  matched in the cache before the latency race), and a rebuilt site (a new
  stamp) installs a new worker and drops the old cache.
- **The master picker on Android**: without an `accept` type Chrome opened the
  photo picker, where `20240404193219.bin.e` cannot be selected; with
  `application/octet-stream` the system file browser opens and both files were
  picked that way, then built.

## 日服 (JP) builds, the region badge and the Archive's language — 2026-10-18

- **Nav compression, measured on the device**: the bar and nav went from 48+39px
  to 36+29px on desktop and from 56+43px to 52+35px on a phone, so `main` starts
  at 97px instead of 131px; the narrow bar keeps only `POD PROGRAMS` and the
  page-level text, so the title stays on one line. `check_ui.py` over 15 pages ×
  3 widths reports 0 problems, and every nav target stays at 44px or wider.
- **Region badge**: on the 全球服 install the launcher shows `地堡 [EN]` and the
  Pod Programs bar `POD PROGRAMS [EN]`; on the 日服 install both read `JP`, in
  dark red. The launcher reads `assets/lunar/build.json`, the web apps get the
  region as a `lunar_region` cookie, and the About dialog names the release.
- **Archive language**: a 日服 build's index was rebuilt from `text/ja` and shows
  Japanese chapter titles (`一章: 風砂の章『荒野の三人』`) and Japanese side-story
  previews. The 全球服 build still builds from `text/en`, and both indices carry
  the language in their signature, so the first start after an update rebuilds
  once (`FORMAT` 17 → 18). Measured on the phone: about 20 s for 20 GB of assets.
- **A 日服 APK without any smali patch boots and plays**: a clean APK patched
  only through the library, metadata and `network_config` (no Facebook SDK,
  CustomTab, WebDialog, UniWebView or AuthHost changes) started, accepted the
  Terms of Service, signed in and entered the Cage. The local server created a
  complete second account for it (all `user_*` tables, 42 tutorials, 819
  missions), so the first-run path does not need the web login page. What the
  smali adds is Facebook login and the SQUARE ENIX BRIDGE transfer.
- **The web builder now builds 日服 too**: `web/webbuild.py --apk …game-jp.apk`
  produced a signed APK with the JP Mod Menu payload; it installed over the
  existing 日服 build, kept its data and booted with the menu.
- **The browser builds 日服, on a phone too**: desktop Chrome (headless) and the
  phone's own Chrome each built the same 日服 APK from the original APK and
  master data — 296,237,450 B, SHA-256 `51b4cd22…282676` on both, in 20 s and
  44 s. The desktop download was installed over the existing 日服 build, kept
  its data, showed `JP`, and both web apps ran; the phone's build had the same
  hash, so it is the same file.
- **The page refuses the wrong file**: pointing the master-data input at another
  file stopped the build at the check with 「主数据不是原版文件」 and where to get
  the right one, instead of failing later inside the patcher.
- **Chrome translated the Chinese page into Chinese**: the builder's markup said
  `lang="en"` while the page showed Chinese, so Android Chrome offered to
  translate it and rewrote 「几分钟」 into 「三十」. The page now sets
  `lang` from the chosen language, and the phone no longer offers to translate.
- A first phone attempt that filled the file inputs through DevTools (而不是
  文件选择器) failed with `FileReaderSync … readAsArrayBuffer`, because Chrome on
  Android cannot read a path set that way; the page names that case instead of
  showing a bare traceback. Choosing the files in the picker works.
- `archive/schedule.py` no longer uses `%-d` in `strftime`, which crashed index
  builds on Windows and in the browser.

## Arena against computer players — 2026-10-08

- The Arena had no server at all: the nine PvP calls, the defense deck,
  weekly rewards and the three Arena tables. Opponents are a per-season
  ladder of 5,000 computer players with playable costumes and their paired
  weapons, raised to a share of the player's deck (more for those with more
  points). Values from the game: 100 battle points, 1 back every 180 s, 10 a
  battle, 5 a refresh; grades and win, weekly grade and weekly rank rewards
  from the Arena tables. Season 202038 is in force (Bunker's patched seasons
  all run to 2030; the one that started last).
- `internal/pvp` tests with the patched master data and the emulator's save:
  the ladder is the same each start and ranks the player; a battle costs
  battle points that come back on time; opponent decks stay within the
  game's level limits; a win raises points and rank and pays the grade's win
  reward, a loss lowers them; 12 hours away gives 8 defense battles; a new
  week records last week's result and its rewards are due once.
- `mobile/pvp_test.go` runs every Arena call over gRPC on the on-device
  server: top data, matching list and refresh, battle start and finish with
  the reward in the diff, ranking with the player in place, season result,
  attack and defense logs, weekly reward claim, computer player profiles and
  the Arena info on the player's profile, and the Arena tables in the user data.
- Emulator, on a copy of the save with quest 61 marked cleared (the real
  save is restored afterwards): the Arena opened (season 037, rank 4934), the
  opponent screen listed three computer players, a battle played to the end
  and won (rank 4934 → 4574, 0 → 100 points, a coin and materials), and
  History showed it.
- Two client details found on the way: the opponent screen hangs without an
  Arena deck, so the first visit copies quest deck 1 to Arena deck 1 (also the
  defense deck); and battle loading stops on a null weapon awaken ability
  (`CalculatorDataBattleDeckForPvp.SetWeaponAwakenInfo`), found with a
  temporary hook on il2cpp's null-reference raise, so it is always sent, empty.

## Missions, rewards and summon rates — 2026-10-07

- Inventory against the 3.7.1 client: client and server define the same 40
  services and 174 calls; 28 had no handler. This adds missions, the mission
  pass, the daily quest set reward, multi-skip, costume level bonus
  confirmation, story choices, labyrinth season rewards, unread pop-ups,
  Portal Cage drops and the friend actions (which succeed with no friends
  offline). Arena (PvP, since added) and the Apple account calls remain unhandled.
- Mission rules: `scripts/gen_mission_rules.py` reads the 6,436 missions'
  English names; 5,635 get a rule. Most of the rest are Arena missions, named
  Mythic Slab boards and subjugation bosses, and missions with conditions the
  names only hint at.
- `internal/missions` tests on the emulator's save with the patched master
  data: the first request backfilled 53 missions (main quest and chapter
  clears, favourite character, logins), a quest clear counted for the daily
  quest mission, all 56 cleared missions paid their rewards, the state
  survived a reload, and the next day reset the daily missions. A check of the
  backfilled list removed a fallback that cleared "conditional" quest missions.
- `mobile/missions_test.go` runs the on-device server with the same save over
  gRPC: mission progress and rewards arrive in the response diffs; bulk skip,
  the daily set reward (once a day), level bonus confirmation, story choices,
  `GetUnreadPop`, `GetDropItem` and the friend actions answer; the user data carries the new
  tables; the game's Rates page shows the rates saved in Pod Programs.
- `internal/gacha` tests: the defaults equal Lunar Tear's table, the settings
  file is read and validated, 20,000 draws land within 1 point of the set ★4
  rate and featured share, and the 10-draw guarantee follows the setting.
- Emulator (Android 16): the APK started, logged in through the new
  interceptor without errors, and Pod Programs > Summon rates saved a preset
  to `saves/gacha_rates.json`. The in-game Missions menu was not reached: the
  emulator's save is at the start of the story.

## Display settings and Game Mode — 2026-10-06

- Galaxy Fold (Android 16, 120 Hz): at 60 fps characters walked at 7.4 m/s
  instead of 3.7: ActorController.FixedUpdate runs once per rendered frame
  while the physics step stays 1/30 s. With the physics step following the
  frame time, walking measured 3.7-3.8 m/s at 60 and 30 fps alike; battles
  (30 x frame time per frame) kept their speed. Steady 120 fps at 1080p; at
  the screen's own 2448x1848 the GPU limits it to about 52.
- iPad Pro (M4): the same through the IL2CPP API (LunarDisplay.m),
  116-120 frames/s at Screen maximum and 1080p; walking and battles normal.
- Web builder (live site after the merge): the Android APK built in Chrome
  carries libbunkerdisplay.so, the Display page and appCategory="game";
  installed with the public key, it imported the game files, played, and
  switched frame rate and resolution from Pod Programs.
- Summon crash (2026-10-07): above 30 fps the summon reveal crashed on the
  Fold, the iPad and the emulator, always at the same address. Bisected on the
  emulator (host GPU): frame rate alone and frame rate with the physics step
  were fine over three 10x summons each; frame rate with the fractional
  battle step crashed. Battles now get one whole step each 1/30 s and none on
  the frames between (BattleGame.Update skips a zero step); three 10x summons
  at Screen maximum no longer crash.

## The Archive — 2026-10-05

- Phase 0 on the real Android dump: revision 0 holds 6,633 English text
  bundles, 270 MP4 movies in `resources/`, ASTC textures (stills, art,
  icons), Vorbis-in-FSB5 audio clips (24k English voice lines, 524 music
  tracks) and Unity 2019.4 meshes and animations. Octo's header mask covers
  the first 256 bytes including the version byte; lunar-scripts'
  `decrypt_assetbundle.py` masks one byte too many by default, which breaks
  bundles whose data starts inside the header. Text bundles were unaffected.
- `android/tools/test_archive.py` (8 tests) passed, including a full index
  build from the real dump: 0 of 6,633 bundles failed, 4,666 scenes and
  23,638 story lines in about 4 seconds on a PC, and every page answered.
  All 144,911 text entries render with balanced italics.
- Android 16 emulator (x86_64 with ARM translation), APK built with
  `scripts/build.py` in WSL: the Archive section sits below Pod Programs and
  stays off until game files are ready. With a reduced dump (English text,
  catalog, three movies), the Archive built its index on the device, listed
  Season 1 with chapter titles, paged scenes, showed the weapon stories,
  searched lines, played a movie streamed from its own server, and followed
  dark mode. Opening the Archive from adb is refused (not exported).
- Same emulator with a 64 GB data partition: the real 15 GB `.7z` imported
  20.91 GB in about 20 minutes. The Archive rebuilt its index on the device
  in under 30 seconds and listed all 145 movies with their Library titles.
  Deploy then reached the game's title screen.
- Characters and Gallery: textures decode in the Go library
  (`server/mobile/unityasset`: Octo mask, UnityFS, serialized files read by
  their type trees, Texture2D and a Go port of texture2ddecoder's ASTC
  decoder). Go tests compare eight real textures (ASTC 5x5, 6x6 and 8x8,
  102x102 to 2048x2048) with texture2ddecoder's output: every byte matches.
  On the emulator the Archive listed 35 characters and 284 costumes with
  portraits, showed a costume's 2048x2048 art trimmed to the figure with its
  story, and the gallery's stills, all decoded on the device. Decoded images
  are kept as PNGs under the Archive's folder.
- Voices and music: Unity's FSB5 Vorbis is rebuilt as Ogg in the Go library
  (`unityasset/audio.go`). FMOD strips the Vorbis setup header and keeps its
  CRC32; the dump uses three, regenerated once with libvorbis 1.3.7 and
  checked against those CRCs (`vorbis_setups.go`). Go tests rebuild six real
  clips (music, story and character voices) and match python-fsb5's output
  packet for packet with the same granule positions; ffmpeg decodes the
  files without errors at the right length. 21,396 of 23,638 story lines
  have an English voice. On the emulator "Play scene" read a scene line by
  line (Android reported the app playing 44.1 kHz mono and moved to the next
  line), a soundtrack part played in stereo with loop and seek, and a
  character's profile line played.
- 3D viewer: the Go library writes a costume as glTF (`unityasset/model.go`:
  the skeleton, every enabled skinned mesh with its weights and bind poses,
  and each material's colour texture, mirrored into glTF's right-handed
  space) and a Mecanim clip as three.js clip JSON (`animation.go`: streamed
  Hermite keys, dense and constant curves, bones named through the Avatar's
  path table, root motion kept in place). Go tests convert all 323 costumes
  that have a skeleton without a failure (3 variants have no linked
  materials and show untextured) and check a run cycle: unit rotations,
  finite values, moving legs. three.js r160 is bundled (MIT) so it works
  offline. On the PC the costume rendered textured in its rest pose and with
  the idle and run motions. On the emulator the first build drew it white:
  three.js fetches embedded textures from blob: URLs and the page policy
  blocked fetch(); reproduced on the PC with the same policy, fixed with
  connect-src blob: (now set by the Archive itself and covered by a test).
- Audit of every page and conversion: a crawl of every link from the home
  page opened 7,951 pages without an error, then checked their text for
  template leftovers, escaped game markup and "1 lines". Every file the pages
  link to was converted by the Go library: 7,368 images, 21,921 sounds, 282
  models and 22,503 motions, all without a failure. Fixed on the way: story
  previews and search results showed raw `<i>`/`<align>` tags and cut words
  in half; "Rest pose" scattered multi-mesh costumes (three.js posed each
  skin from its own stale bind matrices; the saved pose is restored
  instead), and costumes with only battle motions opened in that pose; four
  costumes ship without an Avatar, so their motions now take bone paths
  from the skeleton (matching the Avatar's exactly where both exist); each
  costume listed every other costume's signature moves; three library
  backdrops are ETC2 (decoder ported from texture2ddecoder, every pixel
  matches); two costumes have no full art and show their large card;
  `bgm_delay_settings` was listed as a track; the viewer linked costumes
  without a model; "Save PNG" and the 3D snapshot did nothing in WebView and
  now open the system save dialog; tapping a second voice line quickly
  stopped both; uppercase `<I>`, a stray `</I.` and "<3" in game text were
  mishandled. `test_archive.py` (10 tests) and the Go tests pass. On the
  emulator: 2P's Mock Machine renders whole in its battle idle and rest
  pose, a snapshot and a still saved to Downloads as PNGs, and Noelle's
  Dissenting Weapon (no Avatar) played its motions.
- Speakers and chapters: the main story's event maps (`eventmap/main`, read
  by the Go library's `scenario.go`) list the lines each map plays, the actor
  each is attached to and any speaker shown instead; Go reads the same 6,751
  map lines as UnityPy. Names are the game's own actor names. 5,562 of the
  7,909 main-story scene lines are named: those the maps name, and lines with
  the same voice code in the same scene, or in the season when that code is
  at least 90% one actor. Narration, title cards and the unnamed girl stay
  unlabelled, as do event, character and side scenes, which the game narrates
  without speakers (one voice code per scene). The maps are named by quest
  map number (season, route, chapter order), which regroups the main story
  into the game's chapters with their own names: both Season 2 routes, the
  intermissions and Season 1's Interval Prologue; the two Season 2 endings,
  played by both routes' finales, sit in the first route's. The other
  stories are named the same way: the event maps in `character`,
  `endcontents`, `limitcontents`, `marathon` and `side` name the text files
  they read, and their quest map numbers lead through the event quests to
  the Character Quest's character (shared by that character's Dark Memories
  and Recollections of Dusk), the Record event's title, or the side story's
  character. All 112 story groups are named; the battle prompts every side
  map shares are "Other scenes". The Library's 535 summaries are filed the
  same way: the main story's under each season's chapter names (titled by
  quest where the game titles them), the events' by Record name (their key
  number is the event chapter's SortOrder; all 45 checked against the
  scenes they quote), and the Character Quests', Recollections of Dusk' and
  Dark Memories' by character.
- Weapons: 639 of the 640 weapon folders convert to glTF with the costume
  code (the last, wp003001, has no mesh or art); 52 variants carry only a
  prefab whose mesh sits in a sibling's skeleton bundle, found in their
  series (wp005528 draws wp005505's) or, for 19, in another series of the
  same type. All 1,280 weapon art images decode. Records show each weapon's
  art and open it in the 3D viewer, standing up and framed whole; the two
  "Defective" weapons are listed too. The viewer now frames any model by its
  whole bounding sphere in the narrower view angle and zooms out to four
  times that.
- Movies: the Library's categories are the seasons (the game labels the
  first two "2020" and "2021" and leaves the third unnamed) plus the
  title-screen movies; each season now also lists its story scenes, named
  by chapter from their codes (mm + season, route, chapter, part), and the
  English-voice cut plays where there is one. The 108 dated clips the game's
  announcements played are grouped by the year they ran and titled by their
  caption, preferring a line that names a character. 180 movies are listed
  (35 exist only in Korean or Japanese cuts and were hidden before); 8 with
  no announcement or caption are "Other clips".
- Music: the game has no track titles (each event map's _bgm string is the
  same leftover default), but every map names the track it starts
  (_bgms: track and stem, bgm_1071_2), and the battle tables name theirs.
  Each track is filed where it is first heard (a season's chapter, a
  character's stories, a Record event, a side story, or battle) with the
  other places; 312 of the 352 tracks are placed, 40 never play anywhere
  and are "Other". Track 9999 is 8 s of silence (3.9 KB of Vorbis) that
  maps play to stop the music, and is left out. Not checked on iOS or a
  physical phone.
- Gallery names: stills are filed by main-story chapter (still_main_ +
  season, route, chapter id, number), event scenes by Record event (the
  2d/ev folder's code is the event's) and part, and Library art by the
  summary it sits beside (bg + the summary key's numbers; 396 of 535
  summaries have one and now show it), report, Lost Archive, movie or
  record. Photos have no names in the data and are numbered.
- Companions, Memoirs, Debris: all 53 companions show their art,
  description and 3D model with motions; 144 Memoirs are listed by series
  with their art; 181 of 182 Debris show their picture.
- Other models: the Characters tab lists Mama and the cast (ma), story
  characters (np, pc, pe, sp, um) and enemies (mt) by family: 10, 248
  and 230 models (110 enemy looks borrow their family's skeleton; mt042001
  has none and is left out). An enemy is named by the game's own name for
  its model (costume.name.mt…, 148 looks: Beast Type, Puppet Type, Sea
  Creature Type…), else by the boss names of the quests it fights in
  (quest -> scenes -> battle groups -> NPC deck -> boss-type member ->
  costume skeleton and variation). Event puppets are never marked boss; a
  boss name with no marked boss goes to the look fought in every such quest
  and seldom elsewhere (Birthday Puppet is mt002046). Looks still unnamed
  take their family's name and element (variation 1xx-5xx is Fire, Wind,
  Water, Light, Dark in all 99 named looks). 9 enemy looks stay numbered
  and one family (mt043, whose boss name is the garbled "%ol13##") is
  unnamed. The cast's names come from actor.object.name (by actor object
  and by m_actor's name id: the um models are "Box"); 36 story families,
  mostly silent extras and props, have no English name anywhere ("-" or
  absent, and never a speaker) and are listed last under Unnamed. Garbled
  names (■ blocks, "&f33") are skipped.
  Enemy looks drew their textures from the family's first look, so the
  model code now loads those too (mt008101). The story characters (pc, pe,
  sp, um and one ma) came out untextured: their shader keeps the colour map
  in _BaseMap, not _MainTex; pc009001's hair leaves the slot empty and takes
  the texture named for the part (t_pc009001_hair_aaaa). All 542 cast,
  enemy and companion models now convert textured except two enemy eyes
  that use another family's face texture (mt019 -> mt007001) and the Cursed
  Gods' grey placeholder material. The pc textures are greyscale in the
  game files, so those figures show in grey. The props (oa) are left out.
  mt043001 is modelled 85 units tall (a costume is about 2) and its idle
  motion holds it 60 units up: the viewer's clip planes and floor now
  follow the model's size, and once a motion has faded in the model is
  framed again if it has left the view (checked on the emulator).
  Character voice lines keep their numbered labels: the outgame voice
  files have no subtitles in the dump.
- Web builder (Edge-based pane on Windows, local test server, site assembled
  by web/build_site.py from this branch's launcher APK): the Android APK built
  in the browser in under a minute. Against the command-line build, the
  launcher's native libraries, all 20 Chaquopy assets (the Archive's Python
  among them) and the launcher dex holding the Archive are byte-identical, and
  the patched master data decodes to the same 607 tables. The rest differs as
  designed (the command line rebuilds resources and dex with apktool; the web
  builder edits the original in place). The APK verifies with the Bunker
  public key; re-signed with the local key it updated the emulator in place,
  reached the game's title screen, and its Archive showed a textured cast model
  in 3D and the Memoirs with their art.

## Signed web APKs and the download fix — 2026-10-04

- `android/tools/test_apk_sign.py` passed: an APK signed by `apk_sign.py`
  (APK Signature Scheme v2, public key in `web/signing`) verifies with
  `apksigner`, and a signed APK is refused a second signature.
- Download failure found and fixed: the page's `<main>` and the BUILD button
  both had `id="build"`, so the build handler was attached to the whole page
  section. Clicking the download link revoked the finished APK's link and
  started another build; Chrome reported the download as a network failure.
  The section is now `id="terminal"` and the page has no duplicate ids.
- The site was assembled as CI does and run in Chrome with real clicks: BUILD
  enabled once both files were chosen, the build ran once, and the download
  link saved `bunker.apk` (304,320,690 bytes) without starting another build.
  It verifies with `apksigner` (v2, Bunker public key).
- On the emulator, the downloaded APK was refused over a copy signed with a
  different key (`INSTALL_FAILED_UPDATE_INCOMPATIBLE`), as documented. After
  uninstalling, it installed and opened the Bunker. A separately assembled APK
  signed with the same public key then installed over it as an update
  (first-install time kept) and opened with its server running.

## Pod Programs editors on the device, dark theme — 2026-10-17

- Rooted Xiaomi (Android 16, 2520x1080) with the built APK installed over the
  game's signature. Verified through the app's own WebView (Chrome DevTools over
  `adb forward`): the Profile page's Account Info row measured 321px wide by 44px
  tall at a 392px viewport (it was ~50px wide before), SAVE took a
  `profile-editor` snapshot and reported "已保存 1 个字段，用时 0.04s", Tutorial
  Prep wrote a `tutorial-prep` snapshot, and the mission/quest endpoints answered
  with their own validation errors instead of `Internal Server Error`.
- The ◐ button now switches the panel: body background `rgb(207,199,176)` ->
  `rgb(27,26,23)`, panels to `rgb(35,33,25)`. `check_ui.py --theme light` and
  `--theme dark` both report 0 problems across 14 pages x 3 widths.

## Web builder redesign and rename to Bunker — 2026-10-04

- The site was assembled as CI does (`web/build_site.py` with a fresh Android
  launcher, iOS framework and Python bundle) and both builds were run in Chrome
  against the real game files. Android produced `bunker.apk`: all 5,003 entries
  match `android/tools/assemble_apk.py` exactly except the patched master data,
  whose compression differs between Pyodide and native libraries; all 607 of its
  tables decode identically. iOS produced `bunker.ipa` with the current launcher
  framework, Pod Programs code and templates. Each build ran once even when the
  button was pressed twice, with no console errors. The command-line build now
  writes `artifacts/bunker.apk` / `artifacts/bunker.ipa`.

## Bunker and Pod Programs redesign, choosing players — 2026-10-04

- The launcher (Bunker) and Pod Programs use the NieR:Automata terminal look on
  Android and iOS, light or dark by the system or ⋮ → Display. Checked on the
  Android 17 emulator, the Galaxy Z Fold, the iPad and the iOS simulator smoke test.
- Every Pod Programs action was exercised on the emulator: create and restore a
  save backup; apply a content preset, restore the previous master data, export
  it and load an original; grant gems, an important item, a costume, a weapon
  and a memoir set; run an Upgrade Manager action. Fixed on the way: the
  content patcher no longer breaks on a half-written state file (writes are now
  atomic), unowned karma slots say "locked", and karma pickers fit a phone.
- Use this player: `android/tools/test_players.py` (6 tests) covers swapping,
  switching back, a device that has not signed in, and New player. On the
  emulator and iPad the game then signed in as the chosen player. New player
  needs the server to register a device ID it does not know
  (`patches/lunar-tear-new-player.patch`); on the emulator, iPad and Fold the
  game then asked for a name and started a new player, and switching back
  restored the original.

## Persistent server log and export — 2026-10-04

- Go tests: the log file keeps lines across restarts (one "log opened" marker
  per session), rotates to `server.log.1` at 5 MB, and the export ZIP holds both
  files and `info.txt`, also when written over a longer file through a descriptor.
- Galaxy Z Fold (Android 17): after an update and a restart, `server.log` in
  `Android/data/<package>/files/logs/` held both sessions and `adb pull` read it
  without root. ⋮ → **Export server log** saved a ZIP through the system picker
  with `server.log` and `info.txt` (package, Android version, model, port offset).
- iOS simulator smoke test: the server log is saved in `Documents/logs`. The
  log folder is set when the server starts, not while the app loads, because
  calling Go that early delayed the launcher. The smoke test also found that
  builds without `LunarPortOffset` reset a test offset to 0; the offset is now
  set only when the build has one. Export on iOS uses the same Go code as
  Android and is covered by the Go tests; the share sheet itself was not
  exercised on a device.

## Server checks, port conflicts and port offset — 2026-10-04

- Another device showed a black screen after the logo. Reproduced on an
  Android 17 emulator by holding port 8080 with another process: the old build
  showed the raw "address already in use" error with the server card still
  "Ready", and the game opened directly sat on a black screen. Now the server
  checks itself after starting (game, assets and accounts ports, and that this
  server answers), the launcher names the busy port and shows "Not running",
  and a game opened directly goes to the launcher instead. Same results on the
  Fold. Go tests cover the check, including another program on a port.
- Port offset (scripts/build.py --port-offset, and the web builder's
  experimental option): with port 8080 held, an offset build first still failed
  ("Failed to connect"). Unity extracts the game's code data to
  Android/data/…/files/il2cpp on first launch and re-extracts only when the
  Unity version changes, so every update had kept running the first install's
  copy, including its addresses. The game process now deletes that copy after
  each install or update, and drops the cached asset list when the offset
  changes. Afterwards the web-built and command-line offset builds reached
  player registration on 38003/38080/33000 with 8080 held, and switching back
  to a default build re-extracted the copy and played normally, also on the
  Fold.

## Game reopened without its server — 2026-10-04

- On the Fold, after an update the game was reopened from Recent apps. Updating
  ends the server process, and Recent apps opens the game directly rather than
  through the launcher, so the game waited on a black screen after the logo;
  the server log ended with "Server stopped".
- Fix: the provider in the game's process checks that the server answers when
  the game opens, and otherwise replaces the game with the launcher, which
  starts the server and the game. On the Fold, after installing (server
  stopped) and opening the game directly, the launcher took over, the server
  was listening within about 2 seconds and the game reached its title screen
  without any taps.

## Proxy stall and Android 17 archive import — 2026-10-03

- Report: on a OnePlus 13, entering the game sat at 20% for minutes unless
  the phone was in airplane mode. Reproduced on an Android 17 emulator with
  Google Play services and the full game files, with an HTTP proxy set that
  cannot reach the phone's loopback (as a VPN or accelerator app would be):
  loading stopped at 60% and showed "Failed to connect. Retrying." for over
  three minutes, while the game's asset requests to 127.0.0.1:8080 and its
  Facebook SDK requests to 127.0.0.1:3000 arrived at the proxy and were retried
  every 10 seconds (Octo's stall timeout). Without the proxy the same game
  loaded in about 20 seconds.
- Fix: a provider created in the game's process at start installs a proxy
  selector that sends loopback addresses directly and keeps the phone's proxy
  for everything else, and reinstalls it when Android replaces it. With the
  same proxy, the fixed build loaded to player registration in about 12
  seconds and no loopback request reached the proxy. Checked for both the
  command-line build and the web builder's APK.
- Android 17 refused to reopen a picked archive through /proc/self/fd
  ("permission denied"). The import now reads the descriptor Android opened,
  with positioned reads shared by the unpacking workers. A Go test imports an
  archive whose file was deleted after opening. On the Android 17 emulator the
  real 15 GB .7z imported 20.91 GB in about 11 minutes, with the progress bar
  following the real progress.

## Archive import and use in place — 2026-10-03

- Go tests: a .7z of the dump unpacks only revision 0 and decompresses only
  the archive blocks that hold it; a .zip unpacks only revision 0; unsafe
  paths, other formats and archives without a catalog are refused; cancel
  works. The real 15 GB Android .7z unpacked on a Mac to 201,073 files that
  match the prepared folder by name and size (3,002 also compared by hash).
- iOS Simulator smoke test, all cases passing, including: .7z and .zip import,
  moving a folder already inside the app's Documents, refusing a bad one and
  putting it back, and use in place (linked, survives relaunch, refuses to
  start without the folder, and a later copy removes only the link). Run on
  offset ports while another service used port 3000.
- iPad Pro 11-inch (M4): the real 14.9 GB iOS .7z, imported by the app,
  unpacked 20.96 GB in about 6½ minutes; the archive was removed and the game
  started.
- iPad, use in place: a copy of the game files in On My iPad (outside NieR)
  was chosen with Game files › Change › Extracted folder: use in place. NieR's
  revisions/0 became a link and its own copy was removed. After a cold
  relaunch the saved bookmark reopened the folder, the game reached its title
  screen and loaded into the 3D world from the linked files.
- Samsung Galaxy Z Fold: use in place on an extracted folder in Download, with
  All files access, linked the files without copying (the old 21 GB copy was
  freed) and opened Tools. Importing the real 15 GB Android .7z afterwards
  unpacked 20.91 GB in about 15 minutes, and the linked folder's 201,073 files
  were left intact. The first builds' progress bar showed 100% early:
  the time-left estimate was built from a partial total read while the archive was still being listed (12.7 of
  20.9 GB on a Mac). Totals are now published once the listing is complete.

## iOS — 2026-10-03

- The combined repository still generates the same 291 Android sources
  byte for byte, and its Android build passed with the same signing key.
- The iOS build applied all 4 address patches, 11 sign-in framework patches
  and 13 game-code patches from the pinned lunar-scripts IPA patcher, injected
  the launcher, and signed for a development team. Go server tests passed.
- iOS Simulator (stand-in app, real launcher and server): setup screen, bundled
  master data, server start, sign-in page, save creation, restart with the
  same auth key, folder import, invalid-folder rejection and split-archive
  import with long paths all passed.
- iPad Pro 11-inch (M4), iPadOS 26.6.2, development-signed IPA: the launcher
  showed the setup screen without files. The 20.9 GB iOS assets were copied as
  11 archive pieces over USB and unpacked by the app in under two minutes.
  The embedded server started on the device. The game reached its title screen,
  accepted the terms, registered a new player, downloaded 19 MB from the
  device itself, and played the opening story.
- Remote control from the Mac (screenshots, taps and typing) worked through
  the UI-test helper.

- Tools in the iOS Simulator, with the real launcher framework and a copy of
  the iPad save: all 13 editor actions succeeded with a valid backup each,
  restoring a backup worked, the save passed SQLite's integrity check, and
  the server restarted on the edited save. The "All content" preset produced
  a master file identical to the same patch run on the Mac.
- Tools on the iPad: the three-finger gesture opened the launcher, ⋮ › Tools
  stopped the server and opened the editors on the iPadTest save. Granting
  50,000 free gems wrote `user_gem.free_gem = 50000`; "All content" applied;
  Close showed the restart screen, Close game ended the app, and the game
  reopened on the edited save and patched master data.

- Import progress: the Fold imported the 20.9 GB folder with a progress bar
  in the app and its notification; the 11:50 estimate of 15 minutes finished
  at about 12:06. The iOS Simulator showed the same bar for a 20.9 GB folder.
- Save import (Go tests, iOS Simulator, Fold): an iPad export imported on the
  Fold loaded in the game as the Fold's player (the server log shows the
  Fold's own game ID signing in to the imported player, with no new player
  registered). Re-importing the Fold's original export restored it exactly
  (identical database dump and sign-in key). Bad backups are refused without
  changing the save.

- Web builder (Chrome on macOS, local test server): the Android APK built in
  18 s and matched the command-line build entry for entry (master data decodes
  to identical tables); signed with the existing key, it updated the Fold and
  played offline in airplane mode. The same APK built by
  `android/tools/assemble_apk.py` on the command line also opened Tools offline. The iOS IPA built in
  37 s with the same files as the command-line build; signed and installed on
  the iPad, it kept the game files and save, reached the title screen and
  opened Tools.

- Raw dump import: none of the four pinned projects reads revisions other than
  0 (the server serves revision 0 for every request; lunar-base only scans for
  text bundles, which only revision 0 has). On the Fold, choosing a raw-dump
  layout (revisions/0 with the real files, plus catalog-only revisions 1-3)
  copied 20.91 GB, revision 0 only, and the game then loaded into a battle. The
  iOS Simulator check imports a raw-dump folder and a split archive of one,
  copies only revision 0, and refuses a dump that points at another revision.

Not yet verified on iOS: airplane-mode play, Safari sign-in for an existing
account, sustained play and battles, iPhone, and the folder picker with a
20 GB folder.

## Android — 2026-09-20

## Repository build

- All four submodules are fixed to the commits in `upstream.lock.json`.
- Preparing these pins plus the Android overlays and patches reproduced all
  291 generated source files byte-for-byte from the tested integration.
- The new repository's complete build passed: protobuf generation, Go tests
  with real master data, ARM64 native build, Gradle build and Android lint.
- The combined APK passed signature verification and 16 KB ZIP alignment.
  Its checksum is written locally to `artifacts/SHA256SUMS` on every build.
- Editor integration checks also passed against this repository's generated
  sources, using isolated copies of the private save and master data.
- Five synthetic asset-copy checks passed, including preservation of existing
  files, rejection of cross-revision dumps and cleanup after a failed copy.

## Runtime checks on the same integration sources

These checks were performed before the sources were reorganized into this
repository; the newly packaged APK has not had another full emulator playthrough.

- Android 16 ARM64 emulator, airplane mode and no default network: player setup,
  opening story and touch-controlled movement passed. A cold restart rebuilt the
  game's download cache from the phone's embedded server and retained the save.
- All three server listeners belonged to the app and bound only to loopback.
  Playing required no desktop server. SQLite save integrity passed.
- Tools opened in portrait and landscape. Applying the Story preset, granting
  one free gem and restoring its automatic snapshot passed through the Android
  UI and native bridge; the gem balance changed 0 → 1 → 0.
- Host integration checks exercised every editor page and writes for inventory,
  costumes, weapons, companions, upgrades, karma, slabs, debris and memoirs.
  Session checks, inventory overflow rejection without partial writes, oldest
  retained snapshot restoration and master-data rollback passed.
- Native Android instrumentation passed master loading, SQLite, server health,
  stop/restart and backup preparation. A small folder import through Android's
  document picker passed and automatically opened the game.
- Android 17 with 16 KB kernel pages passed native server checks and game title
  startup. The original game's libraries use Android's page-size compatibility
  loader; full gameplay was checked on Android 16 with 4 KB pages.

## Still unverified

- Physical Samsung Fold behavior, folding/resizing, sustained performance,
  battery use and Samsung background-process management.
- Full campaign and battle coverage.
- Full-size import through a physical phone's document picker. The 20.9 GB
  emulator test used development access to seed files into app storage; normal
  app operation does not require root.
- Physical-phone Tools document import/export. Internal game-save snapshots can
  be restored, but importing the separately exported save ZIP is not implemented.

Private game files, saved games, screenshots and runtime logs remain outside Git.
