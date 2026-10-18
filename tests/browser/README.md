# Browser build checks

These drive the built site in a real Chrome. They are not in CI: the build needs
a real 3.7.1 game APK (254 MB) and its master data, which the repository does
not carry, so run them before a release.

```
python3 web/build_site.py --companion-apk android/app/build/outputs/apk/debug/app-debug.apk
python3 -m http.server -d .build/site 8914 &
python3 tests/browser/build_test.py --base http://127.0.0.1:8914/ \
    --game /path/game-jp.apk --master /path/20240404193219.bin.e [--menu] [--skip] [--mobile]
```

`build_test.py` prints the build log, the step chips and the result card, and
fails the process when the page shows a failure. It needs `websocket-client`
(`pip install websocket-client`) and Chrome (or `CHROME` in the environment).

`encoding_scan.py` checks every tracked text file for a BOM, a broken UTF-8
sequence or mojibake; it is quick enough to run any time.
