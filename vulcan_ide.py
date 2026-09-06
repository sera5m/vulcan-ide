#!/usr/bin/env python3
"""Vulcan IDE — file browse, export, line numbers, BASE VM."""
from __future__ import annotations

import os
import sys
import glob
import shutil
import threading
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
try:
    from bootstrap import ensure_lang
    ensure_lang()
except Exception:
    pass

if sys.platform.startswith("linux") and "GDK_BACKEND" not in os.environ:
    os.environ["GDK_BACKEND"] = "wayland"

try:
    import gi
    gi.require_version("Gtk", "4.0")
    from gi.repository import Gtk, GLib, Gio, Pango
except Exception as e:
    sys.stderr.write(
        "Need GTK4 + PyGObject.\n"
        "  sudo pacman -S python-gobject gtk4 python-pyserial python-matplotlib\n"
        "%s\n" % e
    )
    sys.exit(1)

try:
    import serial
    from serial.tools import list_ports
except Exception:
    serial = None
    list_ports = None

DEFAULT = """print("hello from vulcan");
print(1 + 2 * 3);
print(sin(90));
include "examples/basic.vul";
"""
VUL_EXTS = {".vul", ".bvul"}


def ports():
    found = []
    if list_ports:
        found = [p.device for p in list_ports.comports()]
    if not found:
        found = sorted(glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*"))
    return found or ["/dev/ttyACM0"]


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="dev.oiria.VulcanIde",
                         flags=Gio.ApplicationFlags.HANDLES_OPEN)
        self.win = None
        self.editor = None
        self.gutter = None
        self.log = None
        self.status = None
        self.target = None
        self.port = None
        self.ser = None
        self.file_list = None
        self.dir_label = None
        self.path = None
        self.workdir = HERE / "examples" if (HERE / "examples").is_dir() else Path.cwd()

    def do_activate(self):
        if self.win:
            self.win.present()
            return
        self.win = Gtk.ApplicationWindow(application=self, title="Vulcan IDE")
        self.win.set_default_size(1100, 720)
        root = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

        rail = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        rail.set_margin_start(8)
        rail.set_margin_end(6)
        rail.set_margin_top(8)
        rail.set_size_request(180, -1)
        run = Gtk.Button(label="Run")
        run.add_css_class("suggested-action")
        run.connect("clicked", self._run)
        exp = Gtk.Button(label="Export")
        exp.connect("clicked", self._export)
        sav = Gtk.Button(label="Save")
        sav.connect("clicked", self._save)
        op = Gtk.Button(label="Open")
        op.connect("clicked", self._open)
        self.target = Gtk.DropDown.new_from_strings(["This PC", "Watch"])
        self.port = Gtk.DropDown.new_from_strings(ports())
        conn = Gtk.Button(label="Connect")
        conn.connect("clicked", self._connect)
        self.status = Gtk.Label(label="This PC", xalign=0, wrap=True)
        for w in (run, op, sav, exp, Gtk.Label(label="Target", xalign=0),
                  self.target, Gtk.Label(label="Port", xalign=0), self.port, conn, self.status):
            rail.append(w)
        self.dir_label = Gtk.Label(xalign=0, wrap=True)
        self.dir_label.add_css_class("dim-label")
        folder = Gtk.Button(label="Folder")
        folder.connect("clicked", self._pick_folder)
        rail.append(folder)
        rail.append(self.dir_label)
        self.file_list = Gtk.ListBox()
        self.file_list.connect("row-activated", self._on_file)
        scf = Gtk.ScrolledWindow()
        scf.set_vexpand(True)
        scf.set_child(self.file_list)
        rail.append(scf)
        root.append(rail)

        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        col.set_hexpand(True)
        edit_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.gutter = Gtk.TextView(editable=False, monospace=True, can_focus=False)
        self.gutter.add_css_class("dim-label")
        self.gutter.set_size_request(44, -1)
        self.editor = Gtk.TextView(monospace=True)
        self.editor.set_wrap_mode(Gtk.WrapMode.NONE)
        self.editor.set_left_margin(6)
        self.editor.set_monospace(True)
        self.editor.get_buffer().set_text(DEFAULT)
        self.editor.get_buffer().connect("changed", lambda *_: self._renumber())
        sc_g = Gtk.ScrolledWindow()
        sc_g.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sc_g.set_child(self.gutter)
        sc_e = Gtk.ScrolledWindow()
        sc_e.set_vexpand(True)
        sc_e.set_hexpand(True)
        sc_e.set_child(self.editor)
        # share vertical adjustment so gutter scrolls with editor
        def bind(*_):
            sc_g.set_vadjustment(sc_e.get_vadjustment())
        GLib.idle_add(bind)
        edit_row.append(sc_g)
        edit_row.append(sc_e)
        col.append(edit_row)
        self.log = Gtk.TextView(editable=False, monospace=True)
        lg = Gtk.ScrolledWindow()
        lg.set_min_content_height(150)
        lg.set_child(self.log)
        col.append(lg)
        root.append(col)

        self.win.set_child(root)
        self.win.present()
        self._renumber()
        self._refresh_files()
        self._say("Run: rsvm if on PATH, else vulcan_run (includes, arrays, native, @memory_hard).\n")

    def _text(self):
        b = self.editor.get_buffer()
        return b.get_text(b.get_start_iter(), b.get_end_iter(), False)

    def _say(self, s):
        self.log.get_buffer().insert(self.log.get_buffer().get_end_iter(), s)

    def _renumber(self):
        n = self._text().count("\n") + 1
        self.gutter.get_buffer().set_text("\n".join("%4d" % i for i in range(1, n + 1)))

    def _refresh_files(self):
        while True:
            row = self.file_list.get_row_at_index(0)
            if not row:
                break
            self.file_list.remove(row)
        self.dir_label.set_text(str(self.workdir))
        if not self.workdir.is_dir():
            return
        for p in sorted(self.workdir.iterdir()):
            if p.suffix.lower() in VUL_EXTS or p.suffix.lower() in {".md", ".txt"}:
                lab = Gtk.Label(label=p.name, xalign=0)
                lab.path = str(p)
                self.file_list.append(lab)

    def _on_file(self, _lb, row):
        child = row.get_child()
        path = getattr(child, "path", None)
        if path:
            self.editor.get_buffer().set_text(Path(path).read_text(encoding="utf-8"))
            self.path = path
            self._renumber()

    def _pick_folder(self, *_):
        dlg = Gtk.FileDialog(title="Project folder")
        def done(d, res):
            try:
                f = d.select_folder_finish(res)
                self.workdir = Path(f.get_path())
                self._refresh_files()
            except Exception:
                pass
        dlg.select_folder(self.win, None, done)

    def _open(self, *_):
        dlg = Gtk.FileDialog(title="Open")
        def done(d, res):
            try:
                f = d.open_finish(res)
                p = Path(f.get_path())
                self.workdir = p.parent
                self.path = str(p)
                self.editor.get_buffer().set_text(p.read_text(encoding="utf-8"))
                self._refresh_files()
                self._renumber()
            except Exception:
                pass
        dlg.open(self.win, None, done)

    def _save(self, *_):
        if not self.path:
            self._export()
            return
        Path(self.path).write_text(self._text(), encoding="utf-8")
        self._say("saved %s\n" % self.path)

    def _export(self, *_):
        dlg = Gtk.FileDialog(title="Export .vul")
        def done(d, res):
            try:
                f = d.save_finish(res)
                p = Path(f.get_path())
                if p.suffix == "":
                    p = p.with_suffix(".vul")
                p.write_text(self._text(), encoding="utf-8")
                self.path = str(p)
                self._say("exported %s\n" % p)
            except Exception as e:
                self._say("export: %s\n" % e)
        dlg.save(self.win, None, done)

    def _run(self, *_):
        src = self._text()
        if self.target.get_selected() == 1:
            self._watch(src)
            return

        def work():
            rsvm = shutil.which("rsvm")
            if rsvm:
                import tempfile
                f = tempfile.NamedTemporaryFile("w", suffix=".vul", delete=False)
                f.write(src)
                f.close()
                pr = subprocess.run([rsvm, f.name], capture_output=True, text=True)
                out = (pr.stdout or "") + (pr.stderr or "")
                if pr.returncode == 0:
                    GLib.idle_add(self._say, "[rsvm]\n" + out + "\n")
                    return
                GLib.idle_add(self._say, "[rsvm failed]\n" + out + "\n")
            try:
                from vulcan_run import run_source, RunError
                out = run_source(src, self.path)
                GLib.idle_add(self._say, "[run]\n" + out + "\n")
            except Exception as e:
                GLib.idle_add(self._say, "[err] %s\n" % e)

        threading.Thread(target=work, daemon=True).start()

    def _connect(self, *_):
        if serial is None:
            self._say("install python-pyserial\n")
            return
        name = self.port.get_selected_item()
        dev = name.get_string() if name else "/dev/ttyACM0"
        try:
            if self.ser:
                self.ser.close()
            self.ser = serial.Serial(dev, 115200, timeout=0.05)
            self.status.set_text("connected " + dev)
            self._say("connected %s\n" % dev)
        except Exception as e:
            self._say(str(e) + "\n")

    def _watch(self, src):
        if not self.ser:
            self._say("Connect first\n")
            return
        self.ser.write(("clear\n<<VUL\n" + src.strip() + "\nVUL>>\n").encode())
        self._say("sent to watch\n")


if __name__ == "__main__":
    App().run(sys.argv)
