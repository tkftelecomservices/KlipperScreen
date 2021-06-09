import logging
import random

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

from ks_includes.screen_panel import ScreenPanel


def create_panel(*args):
    return ScreenSaverPanel(*args)


class ScreenSaverPanel(ScreenPanel):
    image = None
    fixed = None
    change_position_timeout = None

    def initialize(self, panel_name):
        _ = self.lang.gettext

        self.fixed = Gtk.Fixed()
        self.fixed.set_size_request(self._screen.width, self._screen.height)

        logging.debug("width: " + str(self._screen.width))

        self.image = self._gtk.Image("tkfts.svg", None, 8, 4)
        self.fixed.put(self.image, (self._screen.width-515)/2, (self._screen.height-85)/2)
        self.layout = self.fixed

        self.change_position_timeout = GLib.timeout_add(5000, self.update_position)

    def update_position(self):
        self.fixed.move(self.image, random.randrange(1, (self._screen.width - 515), 50), random.randrange(1, (self._screen.height-85), 50))

        return True
