import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango

from includes.screen_panel import ScreenPanel


def create_panel(*args):
    return SplashScreenPanel(*args)


class SplashScreenPanel(ScreenPanel):
    box = None

    def __init__(self, screen, title, back=True):
        super().__init__(screen, title, back)

        self.layout = Gtk.Layout()
        self.layout.set_size(self._screen.width, self._screen.height)

    def initialize(self, panel_name):
        _ = self.lang.gettext

        image = self._gtk.Image("ace+.png", None, 4, 3)

        self.labels['text'] = Gtk.Label(_("Initializing system..."))
        self.labels['text'].set_line_wrap(True)
        self.labels['text'].set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.labels['text'].set_halign(Gtk.Align.CENTER)

        self.labels['actions'] = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.labels['actions'].set_hexpand(True)
        self.labels['actions'].set_vexpand(False)
        self.labels['actions'].set_halign(Gtk.Align.END)
        self.labels['actions'].set_margin_end(20)

        main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        main.pack_start(image, True, True, 10)
        main.pack_end(self.labels['actions'], False, False, 10)
        main.pack_end(self.labels['text'], True, True, 10)

        box = Gtk.VBox()
        box.add(main)
        box.set_size_request(self._screen.width, self._screen.height)

        self.layout.put(box, 0, 0)

    def update_text(self, text):
        self.labels['text'].set_text(text)
        self.clear_action_bar()

    def clear_action_bar(self):
        for child in self.labels['actions'].get_children():
            self.labels['actions'].remove(child)

    def show_restart_buttons(self):
        _ = self.lang.gettext

        self.labels['menu'] = self._gtk.ButtonImage("control",_("Menu"),"color4")
        self.labels['menu'].connect("clicked", self._screen._go_to_submenu, "")
        # self.labels['restart'] = self._gtk.ButtonImage("reboot",_("Restart"),"color1")
        # self.labels['restart'].connect("clicked", self.restart)

        self.clear_action_bar()

        # self.labels['actions'].add(self.labels['restart'])
        self.labels['actions'].add(self.labels['menu'])
        self.labels['actions'].show_all()

    def restart(self, widget):
        self._screen._ws.klippy.restart()
