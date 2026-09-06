This IDE’s VM backend is **vulcan-lang BASE** (`cpp_vm` → `rsvm`).

```bash
cmake -S ../vulcan-lang/cpp_vm -B ../vulcan-lang/cpp_vm/build -DOIRIA_ROOT=/path/to/OIRIA_OS_espIDF
cmake --build ../vulcan-lang/cpp_vm/build
export PATH="$PATH:$PWD/../vulcan-lang/cpp_vm/build"
python3 vulcan_ide.py
```

Run on This PC executes `rsvm file.vul` — the same C++ interpreter as the watch, desktop host only.
