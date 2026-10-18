# Changelog

What changed in Bunker, newest first. Each day lists its changes by area.
Commit ids are in brackets. Each release's heading sits above the dated
sections it contains; its notes run down to the previous release.

## 1.2.1 (2026-10-18)

The web builder is quicker to start, survives a slow or blocked CDN, and says
which release your APK is before you build. The Mod Menu checkbox works again.

- **The Mod Menu could not be built in the browser at all**: `menu_payload()` took
  a `ZipFile.read` and called it after the `with` block had closed the archive —
  `ValueError: Attempt to use ZIP archive that was already closed`. Only the site
  passes a zip (the command line passes the folder), so every browser build with
  the checkbox failed after downloading the launcher. It now reads inside the
  block, and a regression test builds the payload as a zip (`test_menu`, 13 tests).
- **Filling in the two files on a phone looked scattered**: the label held a fixed
  column, the description wrapped around it and the file chip fell to a third
  line. On a phone each file is now three rows — label, description, then the
  file chip beside the button — with a long file name cut with an ellipsis; the
  button says *change* once a file is there. The `01 Your files` block is a grid
  below 520px and unchanged on a desktop.
- **The page can name the release**: picking an APK computes its SHA-256 (about
  one second for 254 MB on a phone) and shows `✓ 日服 · JP` or `✓ 全球服 · EN`
  under the description, or `✗ not the original 3.7.1` when the bytes are not one
  of the two releases. The table behind it (`regions.json`) is generated from
  `android/tools/region.py`, the same digests the build checks.
- **The English page showed Chinese**: the base string was "The original 3.7.1
  ARM64 game APK (日服 or 全球服)." It is now "(JP or global)", with 日服/全球服
  in the Chinese dictionary, and the failure hints say "JP or global" too. A
  `notranslate` meta stops Chrome from translating the English page into Chinese
  ("JP or global" used to arrive as 日本版或全球版).
- **Two minutes of waiting before anything happened**: the step chips had no
  *load runtime* step, so a build lit "check files" while Pyodide was still
  booting, and ticking *skip the file check* changed nothing on screen. There are
  now six chips; the skipped check is struck through, and the runtime and the
  25 MB launcher start loading as soon as a file is picked.
- **The runtime and the launcher are kept on the device**: a service worker
  caches `bundles/`, `py/` and Pyodide (about 35 MB) under the release's build
  stamp, so a second build reads them from disk, and a new release drops the old
  cache instead of mixing versions. Chrome kills a worker whose Python has died,
  so a failed build now gets a fresh worker rather than "Pyodide already fatally
  failed".
- **A blocked CDN stopped a build**: Pyodide now comes from whichever of
  jsDelivr's three endpoints (`cdn`, `fastly`, `gcore`) answers first, and the
  launcher has a mirror slot (`build_site.py --mirror`, or the `BUNDLE_MIRROR`
  repository variable). Every bundle is hashed against `mirrors.json` (generated
  when the site is built) and bytes that do not match are refused, so a mirror
  cannot put code into the APK. A mirror needs a CORS header; GitHub's release
  downloads do not send one, so a release asset cannot be the second source.
- **Picking the master data on a phone opened the photo picker**, where a
  `.bin.e` cannot be chosen at all. The input asks for `application/octet-stream`
  so the system file browser opens instead.
- The APK's SHA-256 is computed after the finished file is handed to the page,
  so the card and the download no longer wait for it.

## 1.2.0 (2026-10-18)

The browser builds 日服 by itself, on a phone too; the panel and the Archive are
easier to scan; the two Mod Menu repositories are checked against each other.

- **The top of every page was too tall**: the bar and nav together took 87px of a
  phone screen before any content (`main` started at 131px). They are now 65px on
  desktop and 71px on a phone, with the same 44px targets; the narrow bar keeps
  only `POD PROGRAMS`, so the page title stops wrapping to two lines.
- **Two installs looked identical**: an `EN` / `JP` tag now sits next to the
  launcher title, in the Pod Programs bar and in the Archive bar (JP red). The
  Android side reads `assets/lunar/build.json` (`Region.java`) and hands it to
  both web apps; the desktop panel can set `LUNAR_BUILD_REGION`.
- **A 日服 build still read English story text**: the Archive hard-coded
  `assetbundle/text/en` and `voice/en`. It now takes the language from the region
  (`ja` for JP, `en` otherwise), records it in the index signature and rebuilds
  automatically — `FORMAT` 17 → 18.
- `archive/schedule.py` formatted dates with `%-d`, which only glibc understands:
  building the index on Windows (and in the browser builder) crashed.
- **A 日服 APK could only be built on the command line**: the web builder refused
  it, because the JP patcher rewrites smali. Those steps only serve Facebook
  login and the SQUARE ENIX BRIDGE account transfer, which no offline build uses.
  The in-place assembler now patches the JP library, its metadata and the
  `network_config` asset (API host **and** port), drops the dead Adjust/Firebase
  providers, and leaves the smali alone — so the browser and a CI runner can
  build JP. Verified on a phone: a fresh anonymous account reaches the story, and
  the Mod Menu's JP payload works. `scripts/build.py` keeps the full apktool
  route for anyone who wants the social login redirects.
- **The browser is now the only route for 日服**: the page ships the JP patcher
  (`upstream/lunar-scripts-jp/android/patch_apk_jp.py` was missing from
  `web/build_site.py`), so selecting the 日服 APK builds a working JP APK with no
  tools and no GitHub account.
- **A wrong file now says so**: the page checks the APK's and the master data's
  SHA-256 against the 3.7.1 releases the patch offsets come from, shows which
  step is running (five stages and a bar), names the failure and what to do
  about it, and on success shows the version, region, Mod Menu, size and
  SHA-256 of the APK it just built. Advanced options can skip the check for a
  split APK exported from an installed copy.
- **The build no longer holds the game in memory twice**: the patched library is
  streamed from its work file into the APK (the 120 MB `libil2cpp.so` is not a
  Python object any more), each patched entry is freed as soon as it is written,
  and the finished APK is handed to the page as a Blob built in the worker, so
  the page never holds a second 300 MB copy.
- **The cloud build route is gone**: `build-apk.yml`, `scripts/fetch_input.py`
  and the private assets repository were removed. Visitors supply their own
  APKs, so nothing game-related is published, and one route is easier to keep
  honest than two.
- **A phone builds 日服 on its own**: the same page in the phone's Chrome, with
  the files chosen in the system picker, produced an APK with the identical
  SHA-256 as the desktop build (296,237,450 B, `51b4cd22…`) in 44 s. No OPFS
  staging or chunked output was needed for a 12 GB device.
- **Chrome translated the Chinese page into Chinese**: the builder declared
  `lang="en"` while displaying Chinese, so the phone offered a translation and
  mangled the text (「几分钟」 became 「三十」). The page now sets `lang` from the
  language on screen.
- **The two Mod Menu repositories are checked against each other**:
  `scripts/check_menu_parity.py` compares every file of both menu modules and
  the menu's feature catalog (the same entries, labels and ranges, minus the
  device build's removed server hot-switch), pinning the pair in
  `menu.lock.json`. `scripts/menu_parity.allow` lists the four files that may
  differ, each with its reason. The first run found uncommitted work in both
  checkouts — the font-size setting did not cover every control, a refresh
  could leave the settings page open, and one `setScaledTextSize` call sat
  outside its `if` — which is now committed in both repositories
  (`bunker-modmenu` 19bde45, original 722ad23).
- **Status page tiles**: the ten Pod Programs links were one run-on paragraph
  (nothing styled their `tool-grid` class). They are now tiles — name over
  description with a chevron, four across on a desktop and one per row on a
  phone — and `Choose the player` gained its Chinese label.
- **Archive home tiles**: the seven sections were inline text that ran together
  on a phone. They are now the same kind of tile, and the page's search box and
  build stamp are translated (`搜索剧情文本与记录`, `索引构建于 …`).

- **Profile / Mission / Quest editors were broken on the phone**: their services
  still called the desktop grant executable, whose path the device config never
  defines, so every save ended in `Internal Server Error`. They now go through the
  same native bridge as the item/costume/weapon editors; Tutorial Prep, which used
  its own helper names, was patched the same way.
- **Account Info inputs were unusably narrow**: the row kept its fixed desktop
  column inside a phone viewport (`grid-template-columns` in the page's own style
  beat the mobile breakpoint), leaving a ~50px box. Phone layout is now one column
  with a full-width field and a 44px save button; on desktop the field grows with
  the panel instead of stopping at 260px. `.op-input` also referenced two variables
  that never existed, so the boxes had no fill or border.
- **The ◐ theme button did nothing**: it set `data-theme` while the stylesheet had
  no dark rules. Added the dark palette (tokens, row rules, rarity colours).
- **Windows builds silently dropped the Mod Menu** in the browser builder: payload
  names were compared with `\` against `/` keys. `prepare.py` had the matching
  line-ending/encoding bug, which made every patch fail to apply on a fresh tree.
- `check_ui.py --theme light|dark` measures either palette.
- The profile page's back link printed two arrows (← ← All users).

The Special Gift Roulette now pays gems, and both rate tables moved to the panel.

- **Special Gift Roulette** (Global client only): a spin pays free gems instead of
  materials — 10, 30, 50, 100 or 3000 with Lunar Tear's weighting (60/25/10/4.7/0.3),
  at most six spins a day. The video ad is skipped by answering the ad SDK's
  rewarded/closed events, so the wheel plays offline. The wheel's amounts are fixed:
  the client only animates those five.
- **Rates page** (`/rates` in Lunar Base, Pod Programs > Rates on the device)
  replaces the old Summon rates page: summon odds on one card, the roulette's
  chances on the other. Both write `gacha_rates.json` / `roulette_rates.json` next
  to the save, which the server polls, so a save applies to the next summon or spin
  with no restart; Reset restores Lunar Tear's values. The page validates the same
  rules the server does and flags a broken file.
- The rates tables and roulette logic now live in **lunar-tear-jp_en** itself
  (`internal/gacha/rates.go`, `roulette.go`), so a standalone Lunar Tear server
  reads the same files the panel edits. Bunker keeps only the pages that need its
  Archive.

## 1.1.1 (2026-10-17)

The update channel belongs to this fork.

- The launcher checks **this** repository's releases for updates and opens this
  fork's web builder, not the upstream author's. A fork that kept the upstream
  URLs would have offered the original Bunker (no 日服, no Chinese, no menu) as
  an update.
- About now credits the original project and links here.

## 1.1.0 (2026-10-17)

日服 and 全球服 from one app, Chinese first, and an optional Mod Menu.


### Mod Menu in the browser, and the web builder page

- The web builder can add the Mod Menu: **进阶选项 :: MOD 菜单**. The game's
  launcher entry points at a prebuilt subclass (`tools/menu/MenuShim.java`)
  that starts the menu and then the game, so the browser needs no dex compiler;
  the menu's dex files and `libniermenu.so` are appended the same way the
  launcher's own are. The CLI `--mod-menu` path is unchanged.
- The menu is a floating window: the first launch asks for **Display over other
  apps**. If it cannot start, the game starts anyway (the shim catches it and
  writes `files/menushim.log`).
- `scripts/make_menu_payload.py` rebuilds `web/modmenu/` (shim dex + both
  releases' menu dex and library) from a bunker-modmenu checkout.
- Web builder fixes: the page stopped translating and the language button was
  blank because attribute originals were kept in `dataset` with a `:` key,
  which throws; the toggle label is now set before translating, so it can never
  be blank, and 中/EN round-trips restore every string and attribute.
- The page's links (GUIDE, TROUBLESHOOTING, SOURCE, the guide sentence and the
  footer) point at this fork's README sections instead of the upstream repo.
- Narrow screens keep the toggle readable; the header, frames and labels shrink
  below 720 px.

### Mod Menu (optional)

- The menu now lives in its own repository,
  [bunker-modmenu](https://github.com/lovelyzy7/bunker-modmenu), with one
  workspace per release. Bunker injects it with `--mod-menu` (or
  `--mod-menu-root` / `$BUNKER_MODMENU` for a checkout elsewhere) and re-signs
  the result with the build's own key, so launcher updates keep working.
- **The server hot-switch is gone** from the menu: the address book, the libc
  `connect()` hook, automatic failover, "remember last choice", the
  `auth_host.txt` writer and menu entries 7-16. The server is always on the same
  device, so switching could only break the link.
- Kept: damage and defense multipliers, skill no-cooldown, God mode, forced hit,
  BigHunt cap lift, and the BigHunt protection that disables the HP patches
  there (they froze the wave-end animation).
- `scripts/test_menu.py` covers finding the checkout, per-release workspaces,
  stripping old signatures and picking the SDK build-tools.
- Verified on Windows with the real 日服 APK: the injector merged the menu's
  classes into `classes5.dex`, added `libniermenu.so` (no hot-switch strings,
  features present), and the result verifies under Bunker's own certificate.

### Android only: iOS support removed

- The iPhone/iPad build is gone: `ios/` (launcher framework, IPA packaging,
  simulator helpers), `docs/IOS.md`, the iOS jobs in both workflows, and the
  iOS branches in `scripts/build.py`, `web/webbuild.py`, `web/worker.js`,
  `web/build_site.py`, `web/index.html`, `scripts/release_assets.py` and
  `android/tools/region.py`. `scripts/build.py` takes `--apk` and nothing else.
- The web builder offers no platform choice and says so; An IPA is refused with
  the reason instead of being built.
- README, `docs/BUILD.md` and the release notes state that this fork builds
  Android only; `docs/VALIDATION.md` keeps its iPhone/iPad records as history
  with a note at the top.

### 中文为主 (Chinese first)

- **Pod Programs** (the save editors) is Chinese by default. `base.html` now
  loads lunar-base's i18n and Bunker's own phrase table, hides the page for the
  first paint unless English was chosen, and keeps a 中文/EN toggle. 310 phrases
  and 32 patterns cover the nav, home grid, content patcher, display, summon
  rates, save data, players and every editor; game data names are never touched.
- **The Android launcher** speaks Chinese: a new `Text.java` holds 224 entries
  and `Text.of()` (Chinese by default, the English original when the language is
  en, unchanged for strings it does not know). Every user-visible string in the
  launcher, service notifications, updater, file import and the Archive window
  goes through it, while state keys, preferences and file names stay English.
- **The web builder page** is Chinese by default with a 中文/EN toggle, including
  the log lines and the download button.
- **The Archive** is Chinese by default with a toggle: 83 phrases and plural/
  season patterns over its own pages, with character, costume, track and line
  names left as the game has them.
- iPhone and iPad are not translated yet: the iOS launcher needs Xcode to
  verify, and there is no JP client for iOS.

### Regions (日服 / 全球服)

- `scripts/build.py` reads the APK's package name and builds for that release:
  `com.square_enix.android_googleplay.nierspjp` (日服) goes through
  lunar-scripts-jp, `…nierspww` (全球服) through lunar-scripts as before.
  `--region en|jp` overrides the detection and is refused when it contradicts
  the files.
- The 日服 client patch rewrites smali, so JP builds need apktool: the web
  builder reports that and points at the command line. The iOS build stays
  EN only, and a JP IPA is refused with the reason.
- The local-reachability patch no longer uses a fixed address. It locates the
  `UnityEngine.Application::get_internetReachability` wrapper through the name
  string that only that wrapper computes, which finds it in both releases
  (0x4910D4C EN, 0x4883AB0 JP) and still refuses an unknown library. It is
  idempotent, so rebuilding over an already patched library works.
- The build records its region (`assets/lunar/build.json` and the
  `org.veritr1x.bunker.REGION` manifest entry), and an update keeps the region
  of the build it replaces, so a JP build never turns into an EN one.
- Verified end to end on Windows with both retail APKs: decode, client patch,
  reachability, master data, merge, zipalign, sign (v3) and verify.

### Upstream

- Lunar Tear is now the JP/EN fork (`lovelyzy7/lunar-tear-jp_en`, pinned
  `2b912f553fdb0`), which serves both the JP (3.7.1) and the EN client from
  one instance, adds the JP transfer pages, and fixes the octo
  master-data and maintenance answers.
- Lunar Base is now the bilingual fork (`lovelyzy7/lunar-base`, pinned
  `4211ecc06310e`), which adds a 中文/EN toggle on every page, one-click
  admin setup, and further editors.
- Added Lunar Scripts (JP) (`lovelyzy7/lunar-scripts-jp`, pinned
  `b84faf515fd94`) for the JP client patch pipeline.
- All seven server patches were re-based onto the fork and the full Go test
  suite passes. The fork's Individualpop/Pvp stubs give way to Bunker's
  implementations, the premium draw keeps the original five-tier rates
  (Pod Programs remains the way to change them), and the grant shim runs
  in-process with the fork's added actions (quests, tutorials).

### Web console (Pod Programs)

- The bundled Python now ships `itsdangerous` and treats `bcrypt` as
  optional: on device it is absent, game-account and admin password login
  answer "bad credentials", and everything else works. On a host venv the
  fork's full login works as before.
- `android_runtime.py` adapts to the fork's renamed server-control service
  and its `BackupInfo` restore result.

## 1.0.1 (2026-10-15)

Summon fixes and smoother updates.

### Summons
- Step-up summons cost what their step pages in the game say: the amount at
  each step, which steps are free, and whether only paid gems count. The
  prices were read from all 429 step pages; 33 of the 43 step-up summons had
  been charged a made-up 2,000 / free / 3,000 / free / 5,000 paid gems (for
  example Resolute Dress, now 3,000 / 1,500 / 3,000 / 1,500 / 3,000 gems).
  [579fb8d]
- The Summon buttons answer after swiping the banner list. Above 30 fps the
  list could stop a fraction short of its banner far down the list and keep
  counting as moving, so taps were ignored. [5c35088]

### Updates
- Network problems read as plain messages, Cancel shows only while the
  download can still be cancelled, and Lunar Tear starts again when an install
  is refused. A web-builder publish by hand builds the latest release.
  [4166ae0]

## 1.0.0 (2026-10-15)

The first release. Bunker now has a version, shown in the launcher's About,
the Lunar Tear log and the web builder, and from this version on it can
update itself: see Updates below and "Updating" in the README. Everything
before this date is part of 1.0.0 too.

## 2026-10-15

### Updates
- Every build knows its version: `1.0.0` for a release, `1.0.0+dev.<commit>`
  for any other build. About, the exported log, the server log and the web
  builder show it. [8ad1095, 01c86e0]
- When the launcher opens and the device is online, it looks for a newer
  release and offers it (⋮ › Check for updates turns this off). Android
  rebuilds the app on the phone from Bunker's new files and the game files
  already in it, and Android asks to confirm the install; only builds signed
  with the public Bunker key can do this. iPhone and iPad build
  `Bunker-<version>.ipa` in Files and open the share sheet for SideStore,
  AltStore or a Mac. A damaged download, too little space or a refused
  install leave the app as it was. [6e7d8d3, b431cf7, aa9ebe8, e41af44, 8a020c9]
- Before a new version first updates a save, it copies it to Pod Programs'
  snapshots as "Before update" (the newest three are kept). An older Bunker
  refuses a save that a newer one has updated, instead of damaging it, and
  won't import one either. [1389a05, 1ebe33d, 8a020c9]
- Releases come from version tags: a workflow checks the tag, builds Bunker's
  own bundles (no game files), creates the GitHub Release with these notes
  and `update.json`, and publishes the web builder. Pushes to main only
  build. Release notes use whole lines, not the file's wrapping. [626f533, 0929939]

### Summons
- Fixed the crash after summoning (often on Summon Again, a few minutes
  after starting the game), on Android and iOS. The game's text builder
  makes its buffer only twice as big when text doesn't fit, so a long
  text (the summon confirmation's "Available for purchase until") ran past
  its end and damaged another game text; the game then crashed while
  freeing unused assets. Long texts now always fit. [0f82f23]

### Chapter summons
- A chapter summon appears in Summons only once its chapter's quest is
  cleared, as in the original game. The game never reads the server's lock
  flag and shows every summon it is sent as open, so all of them were listed;
  drawing one still locked was refused, and the game fell back to the title
  screen. [8673c63]

### Upgrades
- Glorious Success Rate Up campaigns raise the chance of a glorious success
  when upgrading characters and weapons, as their names say, using the
  game's own formula (+20 to +80 per thousand on the usual 10%). The server
  had read them as a small experience bonus (2 to 8%) and left the chance
  alone. The server log notes each roll and its chance. [da50bb5, 120704a]

### Step-up summons
- Multi-step summons move on and show every step. The game builds the
  summon screen from one summon per step and shows the one for the step
  you're on; the server sent only step 1, so from step 2 the screen came up
  empty. A summon not drawn yet also stayed on step 1 after the first draw.
  Only the current step can be drawn. [fcb1f1e]
- Each summon has as many steps as the game has step pages for it (3 to 5;
  most had been given 5, one 7, showing blank steps). New Year's Luck of
  the Draw costs what its pages say: 3,000, free, 2,000, free, 5,000 paid
  gems; other step prices are still chosen here. A save past a summon's
  last step starts again at step 1. [fcb1f1e]

### Fortune draws
- The New Year and anniversary fortune draws (omikuji) now open with the
  Original calendar, on their original dates (seven, starting between weeks 23 and
  134). With everything open they stay closed, as before. [d7eb4dd]
- A draw shows one of its fortunes at random (5 to 22 for each draw, from
  the game files); the server had sent the draw's own number, which has no
  result screen. The fortunes carry no items: the game data doesn't say
  which. [d7eb4dd]

## 2026-10-14

### Server: missing game rules
- Event login bonuses: with the Original calendar, every dated login bonus
  card open that day (over a hundred in the game data, for events and
  anniversaries) takes one stamp a day beside the everyday card, its reward
  going to the gift box. A new calendar loop starts the cards again (it
  had also reset the everyday card's id). Not with everything open, where
  the patched data keeps every card open.
- Weapon Evolve keeps each ability's level; a new slot starts at 1.
- Exploration pays by the score's grade (six in the game data): 5 to 30
  stamina and its reward draws (1, or 11 on hard), each gold or a costume or
  weapon experience material, larger with the grade. The amounts are chosen
  here; the game data has the grades, draw counts and ticket costs. Playing
  with tickets needs enough of them.
- Labyrinth seasons move on: opening a labyrinth in a new season pays the
  last season's reward for the furthest stage (the game plays it as the reach
  reward) and starts the climb again: its quests and stage clear rewards
  reset; accumulation rewards stay. It no longer showed every milestone.
- Item shop: an early restock costs the gems the game shows (10, 30, 50 ...
  500 by refresh of the day); the count starts at 1 each day (the game failed
  pricing a refresh at 0). The 17 items are the whole lineup in the game data.
- Beginner and comeback campaigns: a new player who has cleared the first
  quest gets 7 days of the beginner campaigns; a login after 28 to 30 days
  away starts the comeback ones (7 or 14 days). Their quest and enhance
  campaigns now apply, and the game is sent both tables.
- Arena battle point items (4001-4005 and the recovery shop refill) restore
  battle points.
- Chapter summons are real boxes: each chapter's box holds the materials its
  quests drop (10 of each common, 6 uncommon, 3 rare, 1 of the rarest, its
  targets), drawn without putting them back; it refills on the 1st of the
  month (as the game says) and can be reset once the targets are drawn. The
  Featured Items panel shows the rarest with their counts, and the details
  page lists the box. The box contents are chosen here (not in the game data).
- Enhancing a costume or weapon can be a great success (10%, half again the
  experience; chosen here), with the game's animation.
- The Summon button shows its "free" badge while a free daily summon is
  unused.
- Limited-time offers (the Limited shop's 34 packs) open for their original
  sale periods (the cell's term, or the shop's dates), which follow the
  Original calendar; what opened them for a player is not in the game data.
  Each can be bought once while open (other packs still restock). [8d6485d]
- Tests drive handlers with the original game data (BUNKER_TEST_MASTER).
  [94343e5]

### Special Gift Roulette
The menu's roulette (Global only) gave free gems after a video ad, up to 6
spins a day. No ad can be shown any more, so the button did nothing, and the
server answered a spin with a summon item.
- A spin now pays free gems: 10 (60%), 30 (25%), 50 (10%), 100 (4.7%) or
  3,000 (0.3%). The wheel shows 15 slices, but the rates were never
  published; players saw mostly 10s and very rarely the 3,000, so the draw is
  weighted.
- The video is skipped: when the game asks ironSource for it, the "rewarded"
  event comes at once and "closed" on the next frame, as the SDK sent them.
  Android replaces IronSource.showRewardedVideo; iOS, which can't change the
  game's code, points the ad agent's entry at the same function.
- Emulator: six spins with the result dialog, gems added, the counter down to
  the reset countdown. [5450aee]
- iOS: the SDK there keeps its listeners in underscore-named fields and
  delivers "closed" with UnitySendMessage (Android's event dispatcher doesn't
  run on iOS), so the patch does the same. Pod Programs > Summon rates sets
  the roulette's chances (roulette_rates.json beside the save, read on the
  next spin; they must add up to 100%; Default brings back the ones above).
  Fold and iPad: spins play the wheel and pay. [fcd818b]

### Storage: links survive an iOS update
iOS gives an app a new data folder path when the app is updated, and the
cache's symbolic links held absolute paths: after an update they all pointed
nowhere, so the game downloaded those files again on every start (19 MB and
170 MB on the iPad) and could not save them through the broken links. The
roulette's own art failed to load the same way.
- Symbolic links now use relative paths. At start, links that are absolute or
  broken are pointed at the server's copy again; a broken link is removed
  before a file is served.
- iPad: 110,765 links repaired (188 MB) in about 4 minutes on the first start;
  after the next update, which moved the folder again, all links still
  worked and nothing was downloaded. [fcd818b]

### Original calendar: opens with the launch summons
The first summons opened 20 hours into the launch week (28 July 2021, 22:00
UTC), and the game hangs on a summon page with none open: a calendar started
in those first hours showed an empty summon screen and got stuck there.
- A loop now opens once the launch summons are open, moving the clock on by
  a whole day when needed (the daily reset keeps its hour); a new loop does
  the same.
- Calendars already started move on at the next Deploy or Pod Programs
  visit. [52cca2b]

### Names
- Big Hunt is called Subjugation Battles, as in the game: in the Archive's
  Schedule, Pod Programs' calendar and patcher, and this changelog. [5a02b2d]

### Storage: game files stored once
The game keeps its own copy of every file it downloads from the in-app
server, so played content took up space twice. Each cached file is now a
link to the server's copy.
- Files already in the cache are linked when the server starts, new
  downloads a few seconds after the game saves them. A file is linked only
  when its bytes match the server's copy.
- Hard links are used where the system allows them. Android refuses hard
  links to apps, and iOS refuses them to game files used in place from
  another folder; there the cached file becomes a symbolic link instead,
  for files of 4 KB or more (a smaller file takes no more space than its
  link).
- The game rewrites cache files in place, so the link is removed before a
  file is sent again; a new download can never change the server's copy.
- Emulator: the 9,811 files already cached (1.3 GB) were linked in 12
  seconds; a full Download Data run then cached 126,975 files (15 GB) while
  storage grew by about 1 GB, the game's own index files and the links.
  iPad: 5,271 cached files linked, 636 MB saved. [e774947]

### Android: Deploy starting the game
- Deploy failed to start the game most times on a Galaxy Fold: Android
  stopped the game's process because it took over 10 seconds to start. The
  check for empty cached files followed each cached file's link to the game
  files on shared storage; it now reads the links themselves and stops after
  3 seconds. [81b68ec]

### iOS: start-up after a full download
- The game no longer gets stopped by iOS while starting once its data is
  fully downloaded. The check for empty cached files read each of the 100,000+
  cached files one by one, past iOS's 20-second launch limit; it now reads
  them in bulk and stops after 4 seconds. [07e7627]
- Linking a new download no longer reads every cache folder: each asset
  request took about 0.2 s, now well under a millisecond, so Download Data
  runs at full speed again. [30d4235]

### Archive: Schedule
A new section lists the live service's dated content from the original
master data, in UTC. [f6fd958]
- **Timeline:** what started each month, linked to its entry.
- **Summons:** banner art, runs, shards, pity and leftover conversion, and
  each shard exchange's items (costumes link to their pages). Summons without
  a banner, or with only placeholder rows, take their shard exchange's dates,
  as on the server.
- **Events, shops, home banners and the rest:** event quests by difficulty,
  shop items with prices and limits, every home banner, login bonuses, Arena
  seasons, Subjugation Battles, mission passes, campaigns and fortune draws.
- **No date in the game data:** about 150 rows carry a placeholder date
  (mostly 19 Aug–16 Sep 2099) instead of their real dates. They are listed
  apart, with whether their art and title are in the English files and
  whether the same target ran on a dated row, not as "never ran".
- **Names:** 62 summons whose title exists only in their banner art are named
  from the art; Pod Programs' schedule uses the same names. 13 have no English
  title or art.
- The Schedule is worked out while the index is built, so it opens at once.

## 2026-10-13

### Pod Programs: Original calendar
Content › Schedule can replay the live service from global launch (28 July
2021) instead of keeping everything open. [36e881f, f8051fe, 921b5b3, 356d2d1]
- **Game data:** events, summons, shops, seasons, missions, login bonuses,
  campaigns and item terms move forward by whole weeks to start at the current
  week. The main story, character lists, collections and the character viewer
  count as already released.
- **Moving ahead:** Next update, Next week, or Jump to a week or an update,
  with a preview of what opens, what is still paid and what is skipped. The
  calendar only moves forward, in whole days.
- **Speed:** real time, 2×, 3.5× or 7×, one week at a time at the daily reset.
- **Loops:** a loop is 144 weeks. The next loop's game data is built ahead,
  and the server starts it when a loop ends.
- **Server:** an Arena season's final rank reward is paid after it ends. Event
  items leave the inventory when their term ends. A new loop resets event
  quests, event missions, exchange shop purchases, the mission pass, login
  bonuses, Labyrinth seasons, Subjugation Battle records and limited summon
  progress. Subjugation Battles follow the game clock while the server runs.
  [356d2d1]
- **Speed** is saved with a Save speed button, so scrolling can't change it.

### Summons
- NieR:Automata Crossover Vol. 2 (launch and rerun) is offered and gives
  Vol. 1's Shard (Automata); the server used to skip it. [8ddce67]
- Leftover shards become Medals once, at the medal's conversion date; the
  summon screen shows the conversion once. Before, ended summons added the
  shards a second time. [77c1b59, c9b4c25]
- The ticket draw takes the Premium Summon Ticket (item 1002), not Gold.
  [77c1b59]
- Each summon's pity ceiling comes from its medal (50, 100, 150 or 200).
- Summons with a placeholder 2099 row (50, 58) are listed once and open.
- With the calendar, featured items match catalog terms on original dates.
- The shard conversion popup is sent until the next game start; the game
  only shows it when Summons is opened, not when returning to it. [c9b4c25]
- Multi-step summons are one summon each, with 7, 5 or 3 steps from the game
  text (5 when unknown).
- Summons that start together get their own featured items: those their
  exchange shop also sells (e.g. Drakengard 3 rerun, FFXIV Resurrected).
- Chapter summons moved to ids 2100000+ (saved box progress moves with
  them), so "Mama's Dream" banners no longer open chapter 1 and 2 summons.
- 19 summons without a medal row get theirs from a matching exchange shop
  (Festive Dress, YoRHa Stage Play, Fortune's Dress, Blessed Dress, DQX,
  Yuletide and more).
- FFXIV (159) and Monthly Featured (414) reruns run on their shop's dates.
- Special summons follow their titles: free summons give one free 10-pull a
  day, "★★★★ guaranteed" ones a single 10-pull with a ★4 for 3000 gems, and
  "paid only" ones take paid gems. Bonus and newcomer summons are left out.
  [c83dcc1]
- Every draw carries a medal bonus, even an empty one; free summons hung
  without it. A draw option that is used up is switched off, so the game
  can't send a draw the server refuses (that restarted the game). [65dfca7]
- Summons with shards but no banner row are offered from their exchange
  shop's opening to two days before the shards convert: 106 weekly
  summons, 22 paid multi-step summons, Fortune's Dress and Blessed Dress.
  Pod Programs names them after their shards (e.g. "Weekly Summons B").
  Five without art are left out. [5d37688]
- Known issue: on the Android 16 emulator the game can crash (libil2cpp
  0x257da0c) during the first few summons after starting. A 6 October
  build without Bunker's display or server changes crashes the same way;
  the Galaxy Fold doesn't.

### Story events
- Chapter 6-4 (Levania's memory): the player could walk past Mama's lines and
  fall off the right edge of the map. The game misses a player who walks
  through an event's zone while a speech balloon fades out; that zone now
  still counts. Applies on Android and iOS at every frame rate, the game's own
  30 fps included. Chapter 6-7's tree still falls across the chasm. [4b4f8f8,
  2e71e34]

### Server: behaving like the original game
Checked against the game's master data and the 3.7.1 client. [2aa0757]
- **Gifts:** claiming a gift now grants it; login bonus rewards were lost
  before. Expired gifts are dropped and reported. A gift over its storage
  limit stays in the box. Login gifts say "Earned from login bonus". The gift
  box filters and pages work, and history shows the newest 100.
- **Login bonus:** one stamp per day.
- **Duplicates:** duplicate costumes and companions from any source give their
  exchange items. Enhanced costumes and companions arrive at their proper level.
  Companions 49–51 and 53 below level 50 are raised to 50.
- **Summons:** a failed payment cancels the draw. Each chapter summon uses its
  own chapter ticket. The summon medal limit comes from master data.
- **Costumes:** level bonus stats and karma results now apply in battle.
- **Quests:**
  - Quest missions are judged from how the battle went and the deck used. They
    clear only on a win and pay when they clear.
  - Event, extra and Subjugation Battle first clears no longer lose their
    rewards after a story replay.
  - A lost or retired quest is marked "challenged", which unlocks quests that
    need it.
  - Quest bonus drops and key-item drop effects apply.
  - Recollections of Dusk locks the costumes and weapons used in a run.
  - Hidden stories and Lost Archives wait for the quests that unlock them.
  - Skips are refused without enough tickets or stamina.
- **Subjugation Battles:** pay only the highest score tier reached. Damage
  counts across all waves, and a crashed run no longer carries into the next.
- **Missions:** bosses defeated, Subjugation Battle knockdowns, reports, Arena
  play, wins, streaks and rank, library, ability level, exploration score and
  concert taps now count. 6,284 of 6,436 missions have rules.
- **Friends:** the Arena's computer players can be added as friends and sent
  support, so "Send a friend support" and "complete all dailies" can clear.
- **Profile:** shows the last deck used and its real total force.
- **Other:** exploring keeps natural stamina recovery. Visiting a cage ornament
  no longer marks its reward received.
- **Reliability:** an error in one request no longer stops the server. Database
  settings apply to every connection, and saves can't overwrite each other.

### Server: more of the original game
- **Daily reset:** days now start at 00:00 GMT-8, all year, as the game's own
  "Resets at 00:00 (PST)" says. Weeks start Monday 00:00 GMT-8. Saves made
  before move across without losing the week's Subjugation Battle and Arena
  results, and without a second daily reward on the day of the switch.
- **Daily quests:** quests that can be cleared a set number of times a day
  start over each day.
- **Stamina:** levelling up no longer lowers stamina that is above the maximum.
- **Shop:** limited stock refills each day, week or month, as the game data
  says, and a sold-out item can't be bought.
- **Storage limits:** items past the limit (999 weapons or memoirs, 99,999
  materials) go to the gift box, labelled as the game labels them. Summons,
  quests, missions and the shop all do this, and the shop shows its "sent to
  gift box" notice.
- **Debris** rewards are granted; they were dropped before.
- **Character viewer:** a field's unlock notice shows once, not on every visit.
- **Mama's summon banner** shows the latest chapter you've unlocked.
- **Missions:** 66 more missions count (6,350 of 6,436), including:
  - the Collection missions for sets of costumes;
  - event missions for a named weapon or costume;
  - "Update your profile comment" and the New Year missions.

  Event missions on Hard and EX Hard quests now match their quests.
- **Friends:** computer players each have their own level and total force.
- **Profile:** play history shows its 29 counts. The Cage's pedometer shows the
  distance walked.

### Server: fixes
- A new player's first load stopped at 60%. Two karma tables were sent as
  null; every table is now sent as a list. [ac566d3]

### iOS device tools
- `device.py hold` keeps a finger on the walking stick. The test controller
  runs under Xcode 27. [a937c20]

## 2026-10-10

### Docs
- README: summon details, server fixes, and where missions and the Arena were
  tested. [b74def2]

## 2026-10-08

### Server
- Arena against computer players: ladder, battles, points, rewards, defense
  battles and weekly results. [cb4988d]

## 2026-10-07

### Server
- Missions:
  - Daily, challenge, special and mission pass missions progress and pay their
    rewards.
  - Mission pass points and levels.
  - Progress already in a save counts once.
  - Rules come from the missions' names. [4683eba]
- Missing handlers added: the daily quest set reward, skipping several quests
  at once, costume level bonus confirmation, story choices, labyrinth season
  rewards, unread pop-ups and Portal Cage drops. [4683eba]
- Pod Programs → Summon rates sets the summon rates, which the game's Rates page
  shows. [4683eba]
- The summon Details page shows the banner's costs, exchange and item rates.
  [926046b]
- Friend actions are answered offline instead of failing. [b1d6100]
- A daily login counts for missions. Empty cached assets are dropped at game
  start, on Android and iOS. [108ec0a, 01660dc]

### Display
- Battles step in whole 30 Hz steps above 30 fps, fixing a crash in the summon
  reveal. [ecf7393]

### Archive
- Every costume is named. 10H's story variant is filed with her. Placeholder
  stills and blend layers are dropped. [2c4b9ac]
- Movies open full screen. The Archive is added to the iOS launcher. [be752ba]

### Launcher and docs
- About shows Bunker, its creator and credits. [0c34541]
- README: Archive and Display screenshots. [c9bb5d8]

## 2026-10-06

### Display
- Pod Programs → Display sets the frame rate (30, 60, 90, 120 or the screen's
  maximum) and resolution (1080p, 1440p or the screen's own). Walking and
  battles keep their 30 fps speed. [f81a3e9, da80e25]
- The same on iPhone and iPad, and Game Mode on both platforms. [1af9015]

### Archive
- Main-story lines show who says them, and chapters use the game's names.
  [fafe305]
- Stories are named by character or event; Library summaries are filed as the
  game files them. [f86dc2f, cf847b5]
- Weapons with art and 3D models; companions, memoirs, cast and enemies in 3D;
  a named gallery. [9fbc19c, 70a5056, 6c0d44f]
- Movies filed by season, title screen and announcement. The soundtrack is
  filed where each track is first heard, with every place it plays. [ef48d7a,
  b006fd2, ccc0fcd]
- Viewer fixes for very large models, and story characters' textures.
  [61ba3f8, 9ec5d22, b4b9c2a, 14f08b0]

### Docs
- README features section; display validation on the Fold, the iPad and the web
  build. [9a6b667, 52842c8, 4eaaf9c, e62b91d]

## 2026-10-05

### Archive
- A read-only Archive beside the game, with the story, records, movies and
  search. [fe481a0]
- Characters, costumes and a gallery, with textures decoded on the phone.
  [c524454]
- Voice lines and music, played on the phone. [cafcb97]
- A 3D viewer with costumes and character motions. [b0cc4bc]
- A full audit of every page and conversion, with the problems it found fixed.
  [187482b, 65baa4d]

### Web builder and launcher
- Web-built APKs are signed with a public Bunker key, and the download is fixed.
  [a37b411, a399acb]
- Internal identifiers renamed to org.veritr1x.bunker; existing installs update
  normally. [ffbb2f3]
- Mac: a Bunker menu with ⌘B opens the launcher. [a2ac31a]
- Pod Programs uses the launcher's colours. [c134238]

## 2026-10-04

### Launcher
- The game starts its server when reopened directly from Recent apps. [4c03fbb]
- Server self-checks, clear errors when another app holds a port, and an
  optional port offset. [1d9e1d8]
- Launcher and Pod Programs redesigned. The server log is kept between sessions.
  You can choose or start a player. [9a6db6a]
- Renamed to Bunker; the builds are now bunker.apk and bunker.ipa. [467a5eb]

### Docs
- README screenshots and a shorter description. [f2e727b, c7bd61f]

## 2026-10-03

### Platforms
- iPhone and iPad build: the server runs inside the game, offline. [d1045c2]
- Android:
  - Import shows progress with time left. [7372bbd]
  - Save backup import. [7372bbd]
  - The APK builds without apktool. [5f45d19]
  - The game keeps its own name, NieR. [1cf9aa8]
- Android 17: picked archives import correctly. [21f59cb]
- Android: the game reaches its own server even with VPN and proxy apps.
  [ea7b7b9]
- iOS: the launcher redraws after an import at launch. [0937b41]

### Game files
- The extracted resource dump can be imported directly, copying only revision
  0. [cdb901d, f126c53]
- Its .7z or .zip can be imported directly, or a folder used in place.
  [26858a8]
- Archive progress fixed; the iOS chooser matches Android. [328a1d0, 91d45fe]

### Web builder
- An in-browser builder, published by GitHub Actions. Your files are never
  uploaded. [37d74af, 9c70834]

### Docs
- Step-by-step build from a fresh clone; renamed outputs and repository URL.
  [24cd9ab, 7cfd8f0, 8cc3745, 7cd67f4, f6e7c95]

## 2026-09-20

- Android all-in-one launcher with pinned upstream projects. [649aab4]
