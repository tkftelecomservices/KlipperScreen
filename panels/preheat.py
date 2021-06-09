import gi
import logging

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

from includes.screen_panel import ScreenPanel


def create_panel(*args):
    return PreheatPanel(*args)


class PreheatPanel(ScreenPanel):
    active_heaters = []

    def initialize(self, panel_name):
        _ = self.lang.gettext
        self.preheat_options = self._screen._config.get_preheat_options()
        logging.debug("Preheat options: %s" % self.preheat_options)

        grid = self._gtk.HomogeneousGrid()

        eq_grid = Gtk.Grid()
        eq_grid.set_hexpand(True)
        eq_grid.set_vexpand(True)

        image = self._gtk.Image("ace+.png", None, 4, 3)

        eq_grid.attach(image, 0, 1, 1, 1)
        eq_grid.attach(image, 1, 1, 1, 1)
        eq_grid.attach(image, 2, 1, 1, 1)

        grid.attach(eq_grid, 0, 0, 1, 1)
        self.content.add(grid)

        self._screen.add_subscription(panel_name)

    def activate(self):
        return
        # for x in self._printer.get_tools():
        #     if x not in self.active_heaters:
        #         self.select_heater(None, x)
        #
        # for h in self._printer.get_heaters():
        #     if h not in self.active_heaters:
        #         self.select_heater(None, h)

    def process_update(self, action, data):
        if action != "notify_status_update":
            return

        # for x in self._printer.get_tools():
        #     self.update_temp(x,
        #         self._printer.get_dev_stat(x,"temperature"),
        #         self._printer.get_dev_stat(x,"target")
        #     )
        # for h in self._printer.get_heaters():
        #     self.update_temp(h,
        #         self._printer.get_dev_stat(h,"temperature"),
        #         self._printer.get_dev_stat(h,"target"),
        #         None if h == "heater_bed" else " ".join(h.split(" ")[1:])
        #     )
