import logging

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

from includes.screen_panel import ScreenPanel


def create_panel(*args):
    return MeasuringPanel(*args)


class MeasuringPanel(ScreenPanel):
    def __init__(self, screen, title):
        super().__init__(screen, title, False)

    def initialize(self, panel_name):
        _ = self.lang.gettext

        info = Gtk.Box()
        info.set_vexpand(True)
        info.set_hexpand(True)
        info.set_halign(Gtk.Align.CENTER)

        self.labels['busy_icon'] = self._gtk.ButtonImage("measuring", None, None, 4, 4)
        self.labels['system_busy'] = Gtk.Label(_("Robot is performing a measurement."), "header")

        self.labels['busy_info'] = Gtk.Label(_("You can stop this operation using the Control software."))

        info.add(self.labels['busy_icon'])
        info.add(self.labels['system_busy'])

        self.content.add(info)