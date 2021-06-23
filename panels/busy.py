import logging

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

from includes.screen_panel import ScreenPanel


def create_panel(*args):
    return BusyPanel(*args)


class BusyPanel(ScreenPanel):
    def __init__(self, screen, title):
        super().__init__(screen, title, False)

    def initialize(self, panel_name):
        _ = self.lang.gettext

        info = Gtk.Box()
        info.set_vexpand(True)
        info.set_hexpand(True)
        info.set_halign(Gtk.Align.CENTER)

        self.labels['system_busy'] = Gtk.Label("Please wait for robot to complete it's action!")
        self.labels['system_busy'].get_style_context().add_class("init-info")

        info.add(self.labels['system_busy'])

        self.content.add(info)