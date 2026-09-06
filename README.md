# vulcan-ide

Desktop editor + PC interpreter. First run clones [vulcan-lang](https://github.com/sera5m/vulcan-lang).

```bash
sudo pacman -S python-gobject gtk4 python-pyserial python-matplotlib
git clone https://github.com/sera5m/vulcan-ide
cd vulcan-ide
python3 vulcan_ide.py
```

- Folder / file list, Open, Save, Export
- Line numbers; errors print `line N:`
- Run: `rsvm` if on PATH, else `vulcan_run.py`
- Language: include, C arrays, `@memory_hard`, `native` / `py`
