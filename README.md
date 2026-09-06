# vulcan-ide

GTK4 Vulcan editor. **Depends on** [vulcan-lang](https://github.com/sera5m/vulcan-lang) (BASE + desktop VM).

Does **not** depend on the watch firmware. USB to a watch is optional I/O.

```
vulcan-lang (BASE + desktop VM)
        ^
        |
   vulcan-ide     this repo
```

```bash
git clone https://github.com/sera5m/vulcan-lang
git clone https://github.com/sera5m/vulcan-ide
cd vulcan-ide
git submodule update --init   # third_party/vulcan-lang
PYTHONPATH=third_party/vulcan-lang:. python3 vulcan_ide.py
```

Linux: `python-gobject gtk4 python-pyserial python-matplotlib`
