#!/usr/bin/env python3
"""Vulcan IDE — GTK4 editor. Pulls vulcan-lang BASE, runs PC VM."""
from __future__ import annotations
import os, sys, glob, shutil, threading, subprocess
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
    from gi.repository import Gtk, GLib, Gio
except Exception as e:
    sys.stderr.write("Need GTK4 + PyGObject.\n  sudo pacman -S python-gobject gtk4 python-pyserial python-matplotlib\n%s\n" % e)
    sys.exit(1)
try:
    import serial
    from serial.tools import list_ports
except Exception:
    serial = None
    list_ports = None
DEFAULT = 'print("hello from vulcan");\nprint(1 + 2 * 3);\nprint(sin(90));\n'
def ports():
    found = []
    if list_ports:
        found = [p.device for p in list_ports.comports()]
    if not found:
        found = sorted(glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*"))
    return found or ["/dev/ttyACM0"]
class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="dev.oiria.VulcanIde")
        self.win = self.editor = self.log = self.status = None
        self.target = self.port = self.ser = None
    def do_activate(self):
        if self.win:
            self.win.present(); return
        self.win = Gtk.ApplicationWindow(application=self, title="Vulcan IDE")
        self.win.set_default_size(980, 680)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        for m in ("start", "end", "top", "bottom"):
            getattr(box, "set_margin_" + m)(8)
        bar = Gtk.Box(spacing=6)
        run = Gtk.Button(label="Run")
        run.add_css_class("suggested-action")
        run.connect("clicked", self._run)
        self.target = Gtk.DropDown.new_from_strings(["This PC", "Watch"])
        self.port = Gtk.DropDown.new_from_strings(ports())
        conn = Gtk.Button(label="Connect")
        conn.connect("clicked", self._connect)
        self.status = Gtk.Label(label="This PC", xalign=0)
        for w in (run, Gtk.Label(label="Target"), self.target, Gtk.Label(label="Port"), self.port, conn, self.status):
            bar.append(w)
        box.append(bar)
        self.editor = Gtk.TextView(monospace=True)
        self.editor.get_buffer().set_text(DEFAULT)
        sc = Gtk.ScrolledWindow(); sc.set_vexpand(True); sc.set_child(self.editor); box.append(sc)
        self.log = Gtk.TextView(editable=False, monospace=True)
        lg = Gtk.ScrolledWindow(); lg.set_min_content_height(140); lg.set_child(self.log); box.append(lg)
        self.win.set_child(box); self.win.present()
        self._say("BASE: vulcan-lang. Run uses rsvm or python.\n")
    def _text(self):
        b = self.editor.get_buffer()
        return b.get_text(b.get_start_iter(), b.get_end_iter(), False)
    def _say(self, s):
        self.log.get_buffer().insert(self.log.get_buffer().get_end_iter(), s)
    def _run(self, *_):
        src = self._text()
        if self.target.get_selected() == 1:
            self._watch(src); return
        def work():
            rsvm = shutil.which("rsvm")
            if rsvm:
                import tempfile
                f = tempfile.NamedTemporaryFile("w", suffix=".vul", delete=False)
                f.write(src); f.close()
                pr = subprocess.run([rsvm, f.name], capture_output=True, text=True)
                out = (pr.stdout or "") + (pr.stderr or "")
                if pr.returncode == 0:
                    GLib.idle_add(self._say, "[rsvm]\n" + out + "\n"); return
                GLib.idle_add(self._say, "[rsvm failed] " + out + "\n")
            try:
                from vulcan_run import run_source
                GLib.idle_add(self._say, "[run]\n" + run_source(src) + "\n")
            except Exception as e:
                GLib.idle_add(self._say, "[err] %s\n" % e)
        threading.Thread(target=work, daemon=True).start()
    def _connect(self, *_):
        if serial is None:
            self._say("install python-pyserial\n"); return
        name = self.port.get_selected_item()
        dev = name.get_string() if name else "/dev/ttyACM0"
        try:
            if self.ser: self.ser.close()
            self.ser = serial.Serial(dev, 115200, timeout=0.05)
            self.status.set_text("connected " + dev)
            self._say("connected %s\n" % dev)
        except Exception as e:
            self._say(str(e) + "\n")
    def _watch(self, src):
        if not self.ser:
            self._say("Connect first\n"); return
        self.ser.write(("clear\n<<VUL\n" + src.strip() + "\nVUL>>\n").encode())
        self._say("sent to watch\n")
if __name__ == "__main__":
    App().run(sys.argv)
