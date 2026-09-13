# Use the IDE

```bash
# 1. language + examples
git clone https://github.com/sera5m/vulcan-lang
# 2. this editor (copy vulcan_ide.py / vulcan_run.py / examples from your working tree if not on main yet)
git clone https://github.com/sera5m/vulcan-ide

cd vulcan-ide
PYTHONPATH=../vulcan-lang:. python3 vulcan_ide.py
```

Target **This PC** → Run:
1. `rsvm` on PATH (C++ BASE VM) if it succeeds
2. else `vulcan_run.py` so print / sin / fn / latex still work

Target **Watch** → USB `<<VUL` frame.

**Graphs** plots `@sig_gen_graph_preview` fns.

Default buffer:
```
print("hello from vulcan");
print(1 + 2 * 3);
print(sin(90));   # 32767 on LUT
```

## Watch web console (function generator + scope)

On the ESP32-S3 firmware, after Wi-Fi: open `http://<watch-ip>/` (or join AP `OIRIA-vulcan` / `vulcanvulcan`).
Paste or drop a `.vul`, or use the Wave / Scope tabs. See SIGGEN.md.
Target **Watch** in the IDE later will POST here; for now copy the script or use the browser.

```
native("wave", 1, 1000, 50, 4, 80);   // square 1 kHz GPIO 4
native("adc", 1);                    // scope millivolts
```
