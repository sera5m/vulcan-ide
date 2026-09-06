from __future__ import annotations
import os, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
LANG_URL = "https://github.com/sera5m/vulcan-lang"

def lang_dir() -> Path:
    env = os.environ.get("VULCAN_LANG")
    if env:
        return Path(env)
    for c in (HERE / "third_party" / "vulcan-lang", HERE.parent / "vulcan-lang", Path.home() / "vulcan-lang"):
        if (c / "vulcan_run.py").exists() or (c / "cpp_vm").exists():
            return c
    return HERE / "third_party" / "vulcan-lang"

def ensure_lang() -> Path:
    d = lang_dir()
    if (d / "vulcan_run.py").exists() or (d / "cpp_vm" / "CMakeLists.txt").exists():
        s = str(d)
        if s not in sys.path:
            sys.path.insert(0, s)
        os.environ["VULCAN_LANG"] = s
        return d
    d.parent.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(["git", "clone", "--depth", "1", LANG_URL, str(d)])
    s = str(d)
    if s not in sys.path:
        sys.path.insert(0, s)
    os.environ["VULCAN_LANG"] = s
    return d
