# Changelog

What changed in Bunker, newest first. Each day lists its changes by area.
Commit ids are in brackets. Each release's heading sits above the dated
sections it contains; its notes run down to the previous release.

## 1.4.10 (2026-11-02)

The save starts the moment a build finishes, before a phone reclaims the
hundreds of megabytes the page is holding.

## 2026-11-02 (after 1.4.9)

### Web builder
- The download starts automatically when the build completes. A finished APK
  is hundreds of megabytes held by the page, and on a phone that memory is
  reclaimed within minutes: a save started late died halfway, the installer
  found a pending download and reported the package as corrupt. The link, the
  share sheet and the size check remain for a retry. [app.js]

## 1.4.9 (2026-11-02)

The page labels every product with the game's release and this project's
version after it: 3.7.1-{1.4.9}.

## 2026-11-02 (after 1.4.8)

### Web builder
- The version shown in the header and in the result panel's VERSION row is the
  game's release followed by this project's version from version.json, e.g.
  3.7.1-{1.4.9}; the tail is the variable one. [app.js]

## 1.4.8 (2026-11-02)

The build can hand the finished APK to the share sheet, which reaches the
installer or a file manager without the download manager at all — the chain
that stalls in Incognito and on some phones.

## 2026-11-02 (after 1.4.7)

### Web builder
- The result panel gains "Share / send to…": the finished APK goes to the
  Android share sheet (save to files, or straight to the installer), a second
  delivery channel beside the download. Builds made in Incognito, where the
  download manager is the weakest link, no longer depend on it alone. [app.js]
  [index.html]

## 1.4.7 (2026-11-02)

A finished APK now reaches the phone: the download runs as a sized response
the download manager can complete, and the page can check the saved file.

## 2026-11-02 (after 1.4.6)

### Web builder
- The finished APK is delivered through the service worker as a response with
  a length instead of a page-held Blob link. The Blob link died halfway on
  phones and left a pending download item, which the installer reported as a
  corrupt package ("There was a problem parsing the package (11)") although
  the build itself was fine. [sw.js] [app.js]
- The result panel offers "Verify the downloaded file": pick the saved APK
  back and the page compares its size with the product's, so an interrupted
  download says "incomplete — download again" instead of "corrupt". [app.js]
  [index.html]

## 1.4.6 (2026-11-01)

The web builder explains why a file is not the original and warns what
happens if one is built anyway.

## 2026-11-01 (after 1.4.5)

### Web builder
- The file check matches by SHA-256 and, when a file is not any original
  release, shows its size and digest next to the originals' instead of
  rejecting it on size alone without saying why. [app.js]
- Forcing a build with bytes from a different build now warns that the patch
  offsets land in the wrong places and the finished APK may be corrupt and
  refuse to install. [app.js]

## 1.4.5 (2026-11-01)

Pod Programs opens with cleaner navigation that is always in reach: five
buttons with sliding entry strips and a merged event manager. The game's
special button glyphs render again.

## 2026-11-01 (after 1.4.4)

### Pod Programs
- Navigation: five always-visible buttons (Status, Players, Edit, Tools,
  Manage) replace the dropdowns; each opens a sliding strip of boxed
  entries, one strip at a time and none until asked. Manage carries the
  merged Event Manager and Settings entries. [2aa1574] [e6f9a8a]
- The Event Manager page lists the schedule of events, shops, gacha and
  quests. [9eff325]
- The panel's grid stays tidy at every screen width, and the Archive's
  stylesheet no longer overrides the panel's. [ea6bcae] [40208d6]
- Dropdown option rows draw with an opaque background again. [b88ffa2]

### Fonts
- The font payloads carry the original glyph outlines again, so the battle
  AUTO and speed buttons and other special characters no longer show empty
  boxes. [b989186]

## 1.4.4 (2026-10-31)

Flying Mama plays at its normal speed above 30 fps, and the Dark Memory
chapter summon no longer leaves the game stuck before Dark Memories open.

## 2026-10-31 (after 1.4.3)

### Display (Android)
- Flying Mama plays at its normal speed with a frame rate above 30 chosen in
  Display. The minigame counts frames, so at 60 fps the stage scrolled and
  Mama fell twice as fast against the same clock; its logic now runs 30 times
  a second, and taps still count on every frame. [7869f1e]

### Summons
- The Dark Memory chapter summon appears once Dark Memories open (clearing
  the last quest of Season 1, Chapter 14). Before that, its To Quests opened
  an empty screen that the game could not leave. [c0554ce]

### Tools
- The Android tools tests run as a folder again: the two scripts that need
  private game files are skipped there. [13d48c5]

## 1.4.1 (2026-10-29)

Bunker reads better on tablets and in landscape: Pod Programs shows every
tab and full names, notices keep a readable column, and the Archive's
stories fill the screen. The guides show their pictures (notice pack 3).

## 2026-10-29 (after 1.4.0)

### Display
- On tablets and in landscape, every Pod Programs tab shows (on two rows
  when they don't fit), and long costume, weapon and upgrade names wrap
  instead of being cut off. [03e995b]
- Notices and summon details keep their text in a readable column on wide
  screens. [03e995b]
- In the Archive, weapon stories, records, companion and costume texts
  reflow to the screen instead of keeping the game's narrow line breaks;
  lists, reports and the like keep their own breaks. [a8c9870]

### Anecdotes
- The sub-quest guides and the Anecdotes' How to Play pages show their
  pictures, from notice pack 3. [f2b976b] [9af79be]
- The completed sheet's story marks every panel's word, also where the
  story uses a longer form of it ("nightmares", "wished"). [b0a3a65]

## 1.4.0 (2026-10-29)

The Anecdotes are playable again on the game's own panel mission page, the
Library lists their stories, and notice pack 2 brings more of the official
notices back. With the Original calendar, the Abyss Towers and the Anecdotes
rerun on their own schedules, and many summons run as long as their notices
say.

## 2026-10-29

### Calendar
- With the Original calendar, the Abyss Towers rerun on their own schedule:
  each tower opens for each of its runs (both Fivefold Unveilings included)
  and closes between them, with the floors that run had (20, then 30, 40
  and 50), and stays open for good from March 2023 as notice 1037 says.
  Before, a tower opened at its first run with all its floors and never
  closed. A tower's accumulation rewards are still claimed once. [ba0ccbe]
- With the Original calendar, every Anecdote run plays, not only the
  first (15 runs in all). [095eac0]
- Record: Seat of Shadow (Resurrected) ends on 2 December 2023 as its
  notices say, a day earlier than before. [9c8b65c]

### Anecdotes
- The Anecdotes are playable. Each of the eight has its two sheets of
  panels again (from guides and gameplay videos; 26 panels whose exact
  condition isn't recorded count the nearest thing). A run's panels count
  what the player does while it is open, a reached panel's reward goes to
  the gift box, and a finished sheet pays its own reward and unlocks its
  story in the Library. [c55ecc4] [cadd148]
- The sheets are the game's own page, restored from a preserved copy of the
  official web app in the notice pack: the panels over the hidden picture,
  each received panel opening onto its piece and word, and a finished sheet
  assembling its card beside its story. The words of every sheet come from
  gameplay videos. Mama's banners open the run that is on. [a32d3d7]
- Three panels paid an item that doesn't exist instead of a Premium Summon
  Ticket, a Skip Ticket or a Small Stamina Recovery. [a32d3d7]
- With the Original calendar, Library › Card Stories lists each Anecdote
  once, as the live game did. Before, it was listed once per run (Doll three
  times). [438f7a1]
- When a sub-quest type unlocks, its guide opens on the official page
  (Dark Memory and Recollections of Dusk; the other guides weren't
  preserved). Before, the page was blank. [dcaa007]

### Notices
- Notice pack 2: four notices that were missing, the later versions of
  "Known issues" (#4) and three more, no garbled characters, and 274 more
  images: banners and pictures from the Wayback Machine and gameplay videos
  (where a banner is lost, the official X account's poster for the notice),
  item icons rebuilt from the game's own art (and the event medal and
  ticket coins), and 22 thumbnails. It also carries the official web app
  the Anecdotes run on. [28608b6]
- Updates from 1.3.x get the new notices without the web app, which their
  launchers can't take; 1.4 and later updates take the whole pack.
  [e240558]

### Summons
- The Paid Only Unacquired ★★★★ Witch and Assassin summons now give a
  Witch (Saryu) or an Assassin (Akeha) the player lacks, any of them if the
  player has them all, and their details list them. Before, they could give
  any ★4 character. [9874b88]
- The Healer & Support ★★★★ Guaranteed summons have their lineup: their
  panels show its characters, their ★4s come from it, and their details
  list it, taken from the Healer & Support Summon Medal Exchange. Before,
  the panel had only the banner art. [9874b88]
- With the Original calendar, 29 summons run as long as their notices say.
  The game data dated them by their 3-day home banner, so they closed early,
  such as the Unacquired ★★★★ Assassin summon after 3 of its 13 days and
  the RoD Resonant Character summons. [05974bd]
- The Re[in]carnation Appreciation Gala's free summons (July to September
  2023) are back: seven free summons of 40 draws each, one a week, each
  giving ★4 characters of one costume series. The game data lacked them.
  [db8c595]
- The Story Completion festivals (February to April 2024) have all three
  volumes each, as their notices say; the game data had only the first.
  Each volume's ★4 characters are its own lineup (limited-time characters,
  or the series its art names), with the notices' 10% ★4 rate, as the
  Black Friday Karma Festival now has too. [5a3fe20]
- Guarantees that name a group of characters now give one of them: the
  RoD Resonant Character, Abyssal, Celebratory and Yuletide summons, the
  Season 1 summon (whose characters are now all it gives) and the
  limited-time character summons. Before, the guaranteed slot gave any ★4.
  The limited-time sets are a best guess, as no notice lists them.
  [c4cd7c6]

### Tests
- The real-save tests pass on any save and game data: the arena season
  and play history checks follow the save's own dates. [a2b6660]

## 2026-10-28

### Calendar
- With the Original calendar, a rerun event's medal exchange now opens with
  the event. The game data keeps only an event's last run, so events that
  reopen from an earlier run (26 of them, such as "Record: The Cage of
  Reincarnation" from July 2021) dropped medals for months before their
  exchange and the medal itself opened. The exchange, its offers and the
  medal now open when the event first does and stay until its last run
  ends. Reported in GitHub issue #5. [bcd55ab]
- With the Original calendar, the medals and tickets an event gives are
  valid while it runs. Like the exchanges, they kept the dates of the
  event's last run: silver and gold medals of events reopened from an
  earlier run were not valid yet, story events' summon tickets were valid
  in another year than the event, and three 2021 events dropped medals
  never valid. Every item an event gives is now valid from its first run
  to its last (100 medals and tickets). [3f0934d]
- With the Original calendar, a story event's summon stays open for every
  run of the event. Its 2023 reruns had no summon to spend their tickets
  in (chapters 300 and 301). [9b7624b]
- The Original calendar no longer replays 25 placeholder dates as runs:
  dates content carried in the game data before it was used, such as
  chapter 513's medal dated August 2021 for a November event, one-day
  quests and home-screen pop-ups that were parked on their own days, and
  a few tips and missions. A date range now counts only if the game data
  published during it had the content live. [db9374f]

## 1.3.1 (2026-10-30)

The web builder downloads its runtime sources as one small archive and
fetches only the game's own font payload, and a product built in the
browser installs again: the piecewise delivery copied the wrong bytes
from the runtime's shared buffer.

## 2026-10-30

### Web builder
- The "Prepare runtime" step fetches one sources archive instead of 40
  separate files. [e0293f9]
- The font payload is fetched per client at build time (jp or en only),
  not both up front; the service worker keeps it for later builds.
- Fixed: a build finished in the browser delivered an APK that Android
  rejected as corrupt. Each piece was copied from the whole runtime
  buffer instead of its own window; the on-disk product and its
  signatures were never affected.

## 1.3.5 (2026-10-27)

Chapter 4's "A Tool of the Master" can be finished on very wide Android
screens, the guerrilla quests' unlock follows the game's rules, and new
builds start with all content open and no ads.

## 2026-10-26

### Game client
- Guerrilla quests: the "Use 100 gems" unlock now takes the 100 gems.
  The first unlock each day stays free and comes back at the daily reset.
  Before, every unlock was free and the day's count never reset. With
  fewer than 100 gems the game's Unlock button does nothing; that is the
  game's own check. [087b373]
- With the Original calendar, the guerrilla quests' Force Unlock button
  appears when the unlock did in the live service, about six weeks into
  each loop. Before, the game showed it from the start, offering an unlock
  "for 0m" that opened nothing; it is now hidden until then, and the
  server takes no gems for it either. [1319534, ccda6e3]
- Android, story rooms: on screens wider than 19.5:9 (2.4:1 phones with
  "Full screen, around the camera") the camera now goes all the way to the
  room's edge, where the invisible walls are. Before, it stopped short, the
  wall stopped the player the same distance short, and a story trigger near
  the edge could not be reached (chapter 4, "A Tool of the Master").
  [b0b1121]

### Game data
- New builds (APK and the web page) start with the game data Pod
  Programs makes when nothing is picked: content stays open until 31
  December 2099, which the server treats as never ending, and the menu's
  ad banners, the home screen's news cut-ins and the login popup are hidden.
  Before, a fresh install was open only to 2030 and showed the ads until
  Pod Programs patched it. Installed apps keep their current game data.
  [0b195b6]

### Web builder
- The Android build needs much less memory: about 1.2 GB in Chrome instead
  of 2 GB. The game library is patched where it lies, and the APK is signed
  as it is written and passed to the page in pieces. The APK is the same as
  before. [4205647]

### Development
- The unit tests now run on every push to main, not only at release.
  [9588b6e]

## 1.3.1 (2026-10-25)

On Android more of the game's tracking stays off.

## 2026-10-25

### Privacy
- On Android, more of the game's tracking stays off: Unity Analytics,
  Crashlytics, Facebook events, Adjust and ironSource no longer start, and
  the advertising-ID permission and Adjust's install tracker are removed
  from the app. New builds get this at once; an existing install gets it
  from its second in-app update after this one, because each update runs
  the tools already installed. See docs/PRIVACY.md. Contributed by
  nathangerday (PR #3). [962eb57, 6ba7d42]

## 1.3.0 (2026-10-25)

Bunker now runs on Windows, with keyboard controls. The music comes back
after you leave the game, and campaign badges no longer show a jumbled
number.

## 2026-10-25

### Windows
- New: `Bunker-<version>.exe` plays the Android build on a Windows PC, in
  Google's Android Emulator. The first time, it downloads the emulator
  from Google, sets up a phone, installs your APK and copies the game
  files in from the `.7z`. Each step shows on screen, and it asks for any
  file it can't find. See docs/WINDOWS.md. [550840e]
- Keyboard controls: WASD or the arrow keys move, and Ctrl+B opens the
  Bunker. [7cb3539]
- Release notes end with a Downloads list that says what `Bunker.exe`
  is for and which files you don't need. The Windows guide now says
  gameplay was tested: the field with the keyboard, and the music after a
  pause. [0934243]

### Web builder
- After an Android build, a separate paragraph explains how to play the
  APK on Windows with `Bunker.exe`. [0764eb1]

### Game client
- Music no longer stops for good after you leave the game. Before, after
  opening the Bunker, the home screen or another app, the game stayed
  silent until it was restarted. Now the music comes back about a second
  after you return. [03f176e]
- Campaign badges (such as half stamina on EX Character Quests) no longer
  show a jumbled number: campaigns left open end in 2099, 26,000 days away,
  too long for the badge. Remaining times now stop at "999d".
  [d7b1ed6]

### Docs
- The README, guides, changelog and on-screen messages use shorter,
  plainer sentences. Facts, commands and button names are unchanged.
  [c6639f3]


## 1.2.8 (2026-10-18)

The vendored Python runtime was missing one file, so every build still fell back
to the CDN.

- **`pyodide.asm.js` was not copied into `site/pyodide/`**: Pyodide loads that
  glue file next to the wasm, so the first attempt failed with
  "The script at 鈥?pyodide.asm.js failed to load" and the builder quietly used
  jsDelivr 鈥?the dependency 1.2.7 set out to remove. It is copied now, and a
  local build loads the runtime from the page's own host.

## 1.2.7 (2026-10-18)

A build can be stopped, the log can be copied and filtered, the launcher comes
from whichever of site and proxy is faster, and Python ships with the site
instead of a CDN.

- **Stop a build**: a STOP button appears while one runs. It ends the build at
  once by terminating the worker 鈥?Python's long calls cannot be interrupted
  from JavaScript 鈥?and the next build reloads the runtime from the cache.
  Measured: cancel after 3 s, then a full build in 29 s.
- **The log does more than scroll**: COPY LOG copies it, ONLY ERRORS hides the
  rest, the result card gains a SOURCE row (this site / the local file / the
  GitHub proxy), and the three switches (skip check, Mod Menu, port offset)
  survive a reload.
- **One page can no longer mix releases**: the build stamp is part of the script
  urls (`app.js?b=鈥, `worker.js?b=鈥), so a fresh index.html never runs the
  previous release's app.js 鈥?the state seen on a phone right after a deploy.
- **The faster of site and proxy wins**: with a proxy chosen, the site, that
  proxy and the other known proxy are timed with 64 KB before the download, the
  quickest fetches it, and the others cover a failure. Two public proxies answer
  with a CORS header (`gh-proxy.com`, `gh-proxy.org`); the seven others tried do
  not, so a page cannot use them.
- **Python ships with the site**: `build_site.py` copies Pyodide into
  `site/pyodide/` (13 MB), the worker loads it from there first, and the jsDelivr
  endpoints remain as fallbacks ordered by a 64 KB transfer rather than a HEAD
  ping.
- **Checks that were skipped now run**: the apksigner round-trip
  (`test_apk_sign.py`) runs in the Android job of both workflows, `ruff` reports
  style problems in the release check (non-blocking), and the browser build
  driver moved to `tests/browser/` with real arguments instead of Windows paths.
- **Encoding**: `build_site.py` writes UTF-8 explicitly 鈥?on Windows the default
  cp936 could not even hold the 鈻?in the build button, and the stamping step
  failed on it.

## 1.2.6 (2026-10-18)

Mainland China starts on the GitHub proxy, the Mod Menu bundle can be fetched
and downloaded the same way, and the 00 block no longer draws a rule through its
own controls.

- **A rule crossed the file picker**: the separator under each choice was drawn
  on the choice, so the row belonging to it (the picker, the proxy field) sat
  against the line. Each choice is now a group whose rule comes after its
  controls.
- **The downloads are buttons**: 鈥淒ownload the launcher bundle (25 MB)鈥?and
  鈥淒ownload the Mod Menu bundle (0.8 MB)鈥?are boxed, follow the chosen source
  (through the proxy when one is set), and stay readable when their row is grey.
- **Mainland China gets the proxy on the first visit**: the page reads the time
  zone 鈥?Asia/Shanghai and the other mainland zones preselect option 2 with
  https://gh-proxy.com/ filled in, everywhere else option 0. The choice is
  remembered from then on.
- **The Mod Menu can come through the proxy as well**: the release now carries
  `modmenu.zip`, `mirrors.json` names its url, and a proxy build fetches it with
  the same digest check; if the proxy fails, both bundles fall back to this site.
- **The watchdog waits three minutes**, not 90 seconds: a phone (or a busy
  machine) can spend a minute in one patch step, and a false 鈥渟tuck鈥?is worse
  than a late one.

## 1.2.5 (2026-10-18)

The site serves exactly the launcher bundle the release carries, so the new
GitHub-proxy source can be checked against the same digest.

- **A proxy download was refused**: the release's `android.zip` and the site's
  bundle were built from two separate APK builds, so they differed byte for byte
  and the page stopped with "does not match the site's checksum". The site now
  downloads the release's `android.zip` and serves it unchanged, so a proxy
  build and a normal build produce the same APK (`64360096鈥, measured).
- **Publishing is a minute, not ten**: the Pages job no longer compiles an APK
  (the release already did); it fetches the release asset and assembles the
  site. A push still builds the APK to prove it compiles.
- **The bundles are reproducible**: the zips `build_site.py` writes carry a
  fixed timestamp, so the same inputs give the same bytes.

## 1.2.4 (2026-10-18)

A new 00 section decides where the 25 MB launcher comes from 鈥?this site, a file
you already have, or a GitHub proxy 鈥?and the phone's top bar became a proper bar.

- **Choosing the launcher source**: 00 鍑嗗杩愯鏃?offers three exclusive options.
  *This site* is the default and works as before (downloaded once, then kept on
  the device). *A local launcher bundle* takes an `android.zip` from the device
  and downloads nothing at all. *A GitHub download proxy* takes a base such as
  `https://ghproxy.net/`, a full url, or a template containing `{url}`, and
  fetches the release's `android.zip` through it. Choosing one greys out the
  other, and the build button stays disabled until the chosen source is usable
  (a file picked, a valid url). Whatever arrives is hashed against
  `mirrors.json` first, so a proxy cannot put different bytes into the APK.
- **The release carries the launcher**: `android.zip`, the same bundle the site
  serves, is attached to every release 鈥?that is what a proxy fetches. A page
  cannot download a release asset directly (GitHub sends no CORS header).
- **Progress past 100%**: jsDelivr serves the Python wasm with
  `Content-Encoding: br`, so `Content-Length` is the compressed size while the
  reader counts decompressed bytes, and the runtime download showed 309%. A
  compressed response now reports megabytes instead of a percentage.
- **The phone's top bar**: the five links wrapped 4+1 and the language button
  dropped onto a row of its own under BUILD, next to a three-line title. It is
  now two rows 鈥?identity (17px name, 10px version, language button) and four
  equal action cells with separators, 44px tall 鈥?while the desktop bar keeps
  its single line.
- **The repository is `bunker` now**: the site moved to
  https://lovelyzy7.github.io/bunker/ and every link in the page, the app's
  About dialog, its update check and the documentation follows. GitHub does not
  redirect Pages, so the old address stops working; the installed app updates
  through the API, which does redirect.

## 1.2.3 (2026-10-18)

Every step the build takes is on screen now, the Mod Menu included, and the
long waits say what they are waiting for.

- **The Mod Menu had no step of its own**: the chips went from 鎵撳寘 APK straight
  to 绛惧悕涓庢牎楠?while the menu's dex files and library were being written. A
  鍐欏叆 MOD 鑿滃崟 chip now sits between them, with the details in the log
  (dex 1/3锛? KB锛夆€? libniermenu.so锛? MB锛夆€?. When the menu is not ticked the chip
  is struck through, like a skipped file check. On a phone the seven chips are
  3 + 3, with the last one spanning the row.
- **The last chip never turned green**: completion jumped to one short of the
  end of the list, so 绛惧悕涓庢牎楠?stayed outlined on "Done". It now passes the last
  step, and every chip is filled.
- **鍑嗗杩愯鏃?was silent during its two big downloads**: it now reports the
  Python runtime and standard library with a percentage, the packages, the
  builder sources and "Python ready".
- **Signing a 300 MB APK was a silent wait**: the signing read reports every 10%
  (姝ｅ湪绛惧悕 60%鈥?, and the archive's central directory gets its own line.

## 1.2.2 (2026-10-18)

A build can no longer hang on a stalled download, the six step chips are two
even rows on a phone with a gap above the bar, and the last step reads the
300 MB APK once instead of twice.

- **A build could stop at a percentage and never move**: the launcher download
  had a 30 s abort, but aborting a fetch does not settle a pending `read()` when
  the connection has already stalled 鈥?the build then waited forever at 31%.
  The read is now raced against a timer (20 s without data), the same source is
  retried once, and then the next source is tried; a test that serves 1 MB and
  then goes quiet shows the retry and the fallback finishing the build.
- **A dead worker left the button disabled for good**: the page now reports a
  failure when nothing comes back for 90 seconds, when the worker itself throws,
  or when the browser froze the tab (back/forward cache) mid-build, and starts a
  fresh worker for the next try.
- **The step chips and the progress bar touched, and wrapped 4+2**: below 520px
  they are a 3脳2 grid of equal widths with the bar 9px below the last row, so
  nothing overlaps and the labels line up.
- **The last step read the whole APK twice**: signing streamed the file to build
  the v2 digest and the page hashed it again for the SHA-256. `apk_sign` now
  returns the file digest from the same pass, so the card shows it at once and
  300 MB is not read a second time.
- **A Python file from an older build could be used**: the worker wrote `py/*`
  from the service worker's cache, which is keyed by the release but not by the
  build, so a rebuilt site could run the previous `apk_sign.py`
  (`AttributeError: module 'apk_sign' has no attribute 'sign_and_digest'`). Every
  same-origin download now carries the site's build stamp.
- **The build log was English on a Chinese page**: the lines the build prints are
  translated (姝ｅ湪涓嬭浇鍚姩鍣? 姝ｅ湪鏀瑰啓涓绘暟鎹? 姝ｅ湪鎵撳寘 APK, 姝ｅ湪绛惧悕鈥?, including
  why a download failed (20 绉掓病鏈夋敹鍒版暟鎹紙宸叉敹 1 MB锛?.
- **Windows consoles mangled or refused the output**: `webbuild.py` and
  `scripts/build.py` switch stdout to UTF-8, so 鏃ユ湇 (JP) and 鉁?print instead of
  raising `UnicodeEncodeError` or showing mojibake.
- The bundle cache no longer stores a partial body, and the reader no longer
  waits for the disk write before the download starts.

## 1.2.1 (2026-10-18)

The web builder is quicker to start, survives a slow or blocked CDN, and says
which release your APK is before you build. The Mod Menu checkbox works again.

- **The Mod Menu could not be built in the browser at all**: `menu_payload()` took
  a `ZipFile.read` and called it after the `with` block had closed the archive 鈥?
  `ValueError: Attempt to use ZIP archive that was already closed`. Only the site
  passes a zip (the command line passes the folder), so every browser build with
  the checkbox failed after downloading the launcher. It now reads inside the
  block, and a regression test builds the payload as a zip (`test_menu`, 13 tests).
- **Filling in the two files on a phone looked scattered**: the label held a fixed
  column, the description wrapped around it and the file chip fell to a third
  line. On a phone each file is now three rows 鈥?label, description, then the
  file chip beside the button 鈥?with a long file name cut with an ellipsis; the
  button says *change* once a file is there. The `01 Your files` block is a grid
  below 520px and unchanged on a desktop.
- **The page can name the release**: picking an APK computes its SHA-256 (about
  one second for 254 MB on a phone) and shows `鉁?鏃ユ湇 路 JP` or `鉁?鍏ㄧ悆鏈?路 EN`
  under the description, or `鉁?not the original 3.7.1` when the bytes are not one
  of the two releases. The table behind it (`regions.json`) is generated from
  `android/tools/region.py`, the same digests the build checks.
- **The English page showed Chinese**: the base string was "The original 3.7.1
  ARM64 game APK (鏃ユ湇 or 鍏ㄧ悆鏈?." It is now "(JP or global)", with 鏃ユ湇/鍏ㄧ悆鏈?
  in the Chinese dictionary, and the failure hints say "JP or global" too. A
  `notranslate` meta stops Chrome from translating the English page into Chinese
  ("JP or global" used to arrive as 鏃ユ湰鐗堟垨鍏ㄧ悆鐗?.
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

The browser builds 鏃ユ湇 by itself, on a phone too; the panel and the Archive are
easier to scan; the two Mod Menu repositories are checked against each other.

- **The top of every page was too tall**: the bar and nav together took 87px of a
  phone screen before any content (`main` started at 131px). They are now 65px on
  desktop and 71px on a phone, with the same 44px targets; the narrow bar keeps
  only `POD PROGRAMS`, so the page title stops wrapping to two lines.
- **Two installs looked identical**: an `EN` / `JP` tag now sits next to the
  launcher title, in the Pod Programs bar and in the Archive bar (JP red). The
  Android side reads `assets/lunar/build.json` (`Region.java`) and hands it to
  both web apps; the desktop panel can set `LUNAR_BUILD_REGION`.
- **A 鏃ユ湇 build still read English story text**: the Archive hard-coded
  `assetbundle/text/en` and `voice/en`. It now takes the language from the region
  (`ja` for JP, `en` otherwise), records it in the index signature and rebuilds
  automatically 鈥?`FORMAT` 17 鈫?18.
- `archive/schedule.py` formatted dates with `%-d`, which only glibc understands:
  building the index on Windows (and in the browser builder) crashed.
- **A 鏃ユ湇 APK could only be built on the command line**: the web builder refused
  it, because the JP patcher rewrites smali. Those steps only serve Facebook
  login and the SQUARE ENIX BRIDGE account transfer, which no offline build uses.
  The in-place assembler now patches the JP library, its metadata and the
  `network_config` asset (API host **and** port), drops the dead Adjust/Firebase
  providers, and leaves the smali alone 鈥?so the browser and a CI runner can
  build JP. Verified on a phone: a fresh anonymous account reaches the story, and
  the Mod Menu's JP payload works. `scripts/build.py` keeps the full apktool
  route for anyone who wants the social login redirects.
- **The browser is now the only route for 鏃ユ湇**: the page ships the JP patcher
  (`upstream/lunar-scripts-jp/android/patch_apk_jp.py` was missing from
  `web/build_site.py`), so selecting the 鏃ユ湇 APK builds a working JP APK with no
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
- **A phone builds 鏃ユ湇 on its own**: the same page in the phone's Chrome, with
  the files chosen in the system picker, produced an APK with the identical
  SHA-256 as the desktop build (296,237,450 B, `51b4cd22鈥) in 44 s. No OPFS
  staging or chunked output was needed for a 12 GB device.
- **Chrome translated the Chinese page into Chinese**: the builder declared
  `lang="en"` while displaying Chinese, so the phone offered a translation and
  mangled the text (銆屽嚑鍒嗛挓銆?became 銆屼笁鍗併€?. The page now sets `lang` from the
  language on screen.
- **The two Mod Menu repositories are checked against each other**:
  `scripts/check_menu_parity.py` compares every file of both menu modules and
  the menu's feature catalog (the same entries, labels and ranges, minus the
  device build's removed server hot-switch), pinning the pair in
  `menu.lock.json`. `scripts/menu_parity.allow` lists the four files that may
  differ, each with its reason. The first run found uncommitted work in both
  checkouts 鈥?the font-size setting did not cover every control, a refresh
  could leave the settings page open, and one `setScaledTextSize` call sat
  outside its `if` 鈥?which is now committed in both repositories
  (`bunker-modmenu` 19bde45, original 722ad23).
- **Status page tiles**: the ten Pod Programs links were one run-on paragraph
  (nothing styled their `tool-grid` class). They are now tiles 鈥?name over
  description with a chevron, four across on a desktop and one per row on a
  phone 鈥?and `Choose the player` gained its Chinese label.
- **Archive home tiles**: the seven sections were inline text that ran together
  on a phone. They are now the same kind of tile, and the page's search box and
  build stamp are translated (`鎼滅储鍓ф儏鏂囨湰涓庤褰昤, `绱㈠紩鏋勫缓浜?鈥).

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
- **The 鈼?theme button did nothing**: it set `data-theme` while the stylesheet had
  no dark rules. Added the dark palette (tokens, row rules, rarity colours).
- **Windows builds silently dropped the Mod Menu** in the browser builder: payload
  names were compared with `\` against `/` keys. `prepare.py` had the matching
  line-ending/encoding bug, which made every patch fail to apply on a fresh tree.
- `check_ui.py --theme light|dark` measures either palette.
- The profile page's back link printed two arrows (鈫?鈫?All users).

The Special Gift Roulette now pays gems, and both rate tables moved to the panel.

- **Special Gift Roulette** (Global client only): a spin pays free gems instead of
  materials 鈥?10, 30, 50, 100 or 3000 with Lunar Tear's weighting (60/25/10/4.7/0.3),
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
  URLs would have offered the original Bunker (no 鏃ユ湇, no Chinese, no menu) as
  an update.
- About now credits the original project and links here.

## 1.1.0 (2026-10-17)

鏃ユ湇 and 鍏ㄧ悆鏈?from one app, Chinese first, and an optional Mod Menu.


### Mod Menu in the browser, and the web builder page

- The web builder can add the Mod Menu: **杩涢樁閫夐」 :: MOD 鑿滃崟**. The game's
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
  be blank, and 涓?EN round-trips restore every string and attribute.
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
- Verified on Windows with the real 鏃ユ湇 APK: the injector merged the menu's
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

### 涓枃涓轰富 (Chinese first)

- **Pod Programs** (the save editors) is Chinese by default. `base.html` now
  loads lunar-base's i18n and Bunker's own phrase table, hides the page for the
  first paint unless English was chosen, and keeps a 涓枃/EN toggle. 310 phrases
  and 32 patterns cover the nav, home grid, content patcher, display, summon
  rates, save data, players and every editor; game data names are never touched.
- **The Android launcher** speaks Chinese: a new `Text.java` holds 224 entries
  and `Text.of()` (Chinese by default, the English original when the language is
  en, unchanged for strings it does not know). Every user-visible string in the
  launcher, service notifications, updater, file import and the Archive window
  goes through it, while state keys, preferences and file names stay English.
- **The web builder page** is Chinese by default with a 涓枃/EN toggle, including
  the log lines and the download button.
- **The Archive** is Chinese by default with a toggle: 83 phrases and plural/
  season patterns over its own pages, with character, costume, track and line
  names left as the game has them.
- iPhone and iPad are not translated yet: the iOS launcher needs Xcode to
  verify, and there is no JP client for iOS.

### Regions (鏃ユ湇 / 鍏ㄧ悆鏈?

- `scripts/build.py` reads the APK's package name and builds for that release:
  `com.square_enix.android_googleplay.nierspjp` (鏃ユ湇) goes through
  lunar-scripts-jp, `鈥ierspww` (鍏ㄧ悆鏈? through lunar-scripts as before.
  `--region en|jp` overrides the detection and is refused when it contradicts
  the files.
- The 鏃ユ湇 client patch rewrites smali, so JP builds need apktool: the web
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
  `4211ecc06310e`), which adds a 涓枃/EN toggle on every page, one-click
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
  release and offers it (鈰?鈥?Check for updates turns this off). Android
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
  (mostly 19 Aug鈥?6 Sep 2099) instead of their real dates. They are listed
  apart, with whether their art and title are in the English files and
  whether the same target ran on a dated row, not as "never ran".
- **Names:** 62 summons whose title exists only in their banner art are named
  from the art; Pod Programs' schedule uses the same names. 13 have no English
  title or art.
- The Schedule is worked out while the index is built, so it opens at once.

## 2026-10-13

### Pod Programs: Original calendar
Content 鈥?Schedule can replay the live service from global launch (28 July
2021) instead of keeping everything open. [36e881f, f8051fe, 921b5b3, 356d2d1]
- **Game data:** events, summons, shops, seasons, missions, login bonuses,
  campaigns and item terms move forward by whole weeks to start at the current
  week. The main story, character lists, collections and the character viewer
  count as already released.
- **Moving ahead:** Next update, Next week, or Jump to a week or an update,
  with a preview of what opens, what is still paid and what is skipped. The
  calendar only moves forward, in whole days.
- **Speed:** real time, 2脳, 3.5脳 or 7脳, one week at a time at the daily reset.
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
  day, "鈽呪槄鈽呪槄 guaranteed" ones a single 10-pull with a 鈽? for 3000 gems, and
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
  Companions 49鈥?1 and 53 below level 50 are raised to 50.
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
- Pod Programs 鈫?Summon rates sets the summon rates, which the game's Rates page
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
- Pod Programs 鈫?Display sets the frame rate (30, 60, 90, 120 or the screen's
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
- Mac: a Bunker menu with 鈱楤 opens the launcher. [a2ac31a]
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
