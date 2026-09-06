"""Pull BASE (vulcan-lang) like an SDK. The IDE does not *be* the language."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LANG_URL = "https://github.com/sera5m/vulcan-lang"
OIRIA_URL = "https://github.com/sera5m/OIRIA_OS_espIDF"


def lang_dir() -> Path:
    env = os.environ.get("VULCAN_LANG")
    if env:
        return Path(env)
    for c in (
        HERE / "third_party" / "vulcan-lang",
        HERE.parent / "vulcan-lang",
        Path.home() / "vulcan-lang",
    ):
        if (c / "vulcan_run.py").exists() or (c / "cpp_vm").exists():
            return c
    return HERE / "third_party" / "vulcan-lang"


def ensure_lang() -> Path:
    d = lang_dir()
    if (d / "vulcan_run.py").exists() or (d / "cpp_vm" / "CMakeLists.txt").exists():
        _on_path(d)
        return d
    d.parent.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(["git", "clone", "--depth", "1", LANG_URL, str(d)])
    _on_path(d)
    return d


def _on_path(d: Path):
    s = str(d)
    if s not in sys.path:
        sys.path.insert(0, s)
    os.environ["VULCAN_LANG"] = s


def build_pc_vm(lang: Path, oiria: Path | None = None) -> Path | None:
    """Compile the PC interpreter (rsvm) from BASE + watch sources."""
    cpp = lang / "cpp_vm"
    build = cpp / "build"
    exe = build / ("rsvm.exe" if os.name == "nt" else "rsvm")
    if exe.exists():
        return exe
    root = oiria
    if root is None:
        cand = lang.parent / "OIRIA_OS_espIDF"
        if (cand / "os_code" / "core" / "rs_vm" / "vm" / "rs_vm.cpp").exists():
            root = cand
    if root is None:
        return None
    build.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(
        ["cmake", "-S", str(cpp), "-B", str(build), f"-DOIRIA_ROOT={root}"]
    )
    subprocess.check_call(["cmake", "--build", str(build)])
    return exe if exe.exists() else None
