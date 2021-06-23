import gi
import os

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

from includes.screen_panel import ScreenPanel


def create_panel(*args):
    return SystemPanel(*args)


class SystemPanel(ScreenPanel):
    def initialize(self, panel_name):
        _ = self.lang.gettext

        grid = self._gtk.HomogeneousGrid()
        grid.set_row_homogeneous(False)

        fr_language = self._gtk.ButtonImage('fr-lang',"\n".join(_('French Language').split(' ')))
        fr_language.connect("clicked", self.fr_language)

        en_language = self._gtk.ButtonImage('en-lang', "\n".join(_('English Language').split(' ')))
        en_language.connect("clicked", self.en_language)

        grid.attach(fr_language, 0, 0, 1, 1)
        grid.attach(en_language, 1, 0, 1, 1)

        self.content.add(grid)

    def fr_language(self, widget):
        self._screen.show_popup_message("This function is to be implemented in a future version.")

    def en_language(self, widget):
        self._screen.show_popup_message("This function is to be implemented in a future version.")
