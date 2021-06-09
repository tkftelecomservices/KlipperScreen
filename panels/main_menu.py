import gi
import logging

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
from panels.menu import MenuPanel


def create_panel(*args):
    return MainPanel(*args)


class MainPanel(MenuPanel):
    def __init__(self, screen, title, back=False):
        super().__init__(screen, title, False)

    def initialize(self, panel_name, items):
        print("### Making MainMenu")

        grid = self._gtk.HomogeneousGrid()
        grid.set_hexpand(True)
        grid.set_vexpand(True)

        # Create Extruders and bed icons
        eq_grid = Gtk.Grid()
        eq_grid.set_hexpand(True)
        eq_grid.set_vexpand(True)

        self.heaters = []

        self.labels[1] = self._gtk.ButtonImage("extruder-" + str(1), self._gtk.formatTemperatureString(0, 0))
        self.heaters.append(1)

        # self._screen.printer.data['state']['upTime']

        self.labels[2] = self._gtk.ButtonImage("bed", self._gtk.formatTemperatureString(0, 0))
        self.heaters.append(2)

        self.labels[3] = self._gtk.ButtonImage("heat-up", "name")
        self.heaters.append(3)

        i = 0
        cols = 3 if len(self.heaters) > 4 else (1 if len(self.heaters) <= 2 else 2)
        for h in self.heaters:
            eq_grid.attach(self.labels[h], i % cols, int(i / cols), 1, 1)
            i += 1

        self.items = items
        self.create_menu_items()

        self.grid = Gtk.Grid()
        self.grid.set_row_homogeneous(True)
        self.grid.set_column_homogeneous(True)

        grid.attach(eq_grid, 0, 0, 1, 1)
        grid.attach(self.arrangeMenuItems(self.items, 2, True), 1, 0, 1, 1)

        self.grid = grid

        self.content.add(self.grid)
        self.layout.show_all()

        self._screen.add_subscription(panel_name)

    def activate(self):
        return

    def process_update(self, action, data):
        if action != "notify_status_update":
            return

        self.labels[1].set_label(self._gtk.formatTemperatureString(self._screen.printer.data['state']['upTime'], 77))
        self.labels[3].set_label(self._screen.printer.data['state']['status'])

        return
