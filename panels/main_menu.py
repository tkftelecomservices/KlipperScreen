import gi
import logging
import math

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from panels.menu import MenuPanel


def create_panel(*args):
    return MainPanel(*args)


class MainPanel(MenuPanel):
    def __init__(self, screen, title, back=False):
        super().__init__(screen, title, False)

    def initialize(self, panel_name, items):
        _ = self.lang.gettext

        # code for menu
        print("### Making MainMenu")

        self.items = items
        self.create_menu_items()

        self.grid = Gtk.Grid()
        self.grid.set_row_homogeneous(True)
        self.grid.set_column_homogeneous(True)

        # grid used for this page
        grid = self._gtk.HomogeneousGrid()
        grid.set_row_homogeneous(False)

        self.labels['button_grid'] = self._gtk.HomogeneousGrid()
        self.labels['button_grid'].set_vexpand(False)

        fi_box = Gtk.VBox(spacing=0)
        fi_box.set_hexpand(True)
        fi_box.set_vexpand(False)
        fi_box.set_halign(Gtk.Align.START)

        self.labels['status'] = Gtk.Label()
        self.labels['status'].set_halign(Gtk.Align.START)
        self.labels['status'].set_vexpand(False)
        self.labels['status'].get_style_context().add_class("printing-filename")


        heater_bed = self._gtk.Image("bed.svg", None, .6, .6)
        self.labels['heater_bed'] = Gtk.Label(label="MCU")
        self.labels['heater_bed'].get_style_context().add_class("printing-info")
        heater_bed_box = Gtk.Box(spacing=0)
        heater_bed_box.add(heater_bed)
        heater_bed_box.add(self.labels['heater_bed'])
        self.labels['temp_grid'] = heater_bed

        # Create time remaining items
        hourglass = self._gtk.Image("hourglass.svg", None, .6, .6)
        #self.labels['left'] = Gtk.Label(label=_("Left:"))
        #self.labels['left'].get_style_context().add_class("printing-info")
        #self.labels['time_left'] = Gtk.Label(label="0s")
        #self.labels['time_left'].get_style_context().add_class("printing-info")
        itl_box = Gtk.Box(spacing=0)
        itl_box.add(hourglass)
        #itl_box.add(self.labels['left'])
        #itl_box.add(self.labels['time_left'])
        self.labels['itl_box'] = itl_box

        # Create overall items
        clock = self._gtk.Image("clock.svg", None, .6, .6)
        self.labels['uptime'] = Gtk.Label(label=_("Uptime:"))
        self.labels['uptime'].get_style_context().add_class("printing-info")
        self.labels['duration'] = Gtk.Label(label="0s")
        self.labels['duration'].get_style_context().add_class("printing-info")
        it_box = Gtk.Box(spacing=0)
        it_box.add(clock)
        it_box.add(self.labels['uptime'])
        it_box.add(self.labels['duration'])
        self.labels['it_box'] = it_box

        position = self._gtk.Image("move.svg", None, .6, .6)
        self.labels['pos_x'] = Gtk.Label(label="X: 0")
        self.labels['pos_x'].get_style_context().add_class("printing-info")
        self.labels['pos_y'] = Gtk.Label(label="Y: 0")
        self.labels['pos_y'].get_style_context().add_class("printing-info")
        self.labels['pos_z'] = Gtk.Label(label="Z: 0")
        self.labels['pos_z'].get_style_context().add_class("printing-info")
        pos_box = Gtk.Box(spacing=0)
        posgrid = self._gtk.HomogeneousGrid()
        posgrid.set_hexpand(True)
        posgrid.attach(self.labels['pos_x'], 0, 0, 1, 1)
        posgrid.attach(self.labels['pos_y'], 1, 0, 1, 1)
        posgrid.attach(self.labels['pos_z'], 2, 0, 1, 1)
        pos_box.add(position)
        pos_box.add(posgrid)
        self.labels['pos_box'] = pos_box

        speed = self._gtk.Image("speed-step.svg", None, .6, .6)
        self.labels['speed'] = Gtk.Label(label="a")
        self.labels['speed'].get_style_context().add_class("printing-info")
        speed_box = Gtk.Box(spacing=0)
        speed_box.add(speed)
        speed_box.add(self.labels['speed'])
        extrusion = self._gtk.Image("extrude.svg", None, .6, .6)
        self.labels['extrusion'] = Gtk.Label(label="b")
        self.labels['extrusion'].get_style_context().add_class("printing-info")
        extrusion_box = Gtk.Box(spacing=0)
        extrusion_box.add(extrusion)
        extrusion_box.add(self.labels['extrusion'])
        fan = self._gtk.Image("fan.svg", None, .6, .6)
        self.labels['fan'] = Gtk.Label(label="c")
        self.labels['fan'].get_style_context().add_class("printing-info")
        fan_box = Gtk.Box(spacing=0)
        fan_box.add(fan)
        fan_box.add(self.labels['fan'])
        sfe_grid = self._gtk.HomogeneousGrid()
        sfe_grid.set_hexpand(True)
        sfe_grid.attach(speed_box, 0, 0, 1, 1)
        sfe_grid.attach(extrusion_box, 1, 0, 1, 1)
        sfe_grid.attach(fan_box, 2, 0, 1, 1)
        self.labels['sfe_grid'] = sfe_grid

        fi_box.add(self.labels['status'])  # , True, True, 0)
        fi_box.set_valign(Gtk.Align.CENTER)

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        info.props.valign = Gtk.Align.CENTER
        info.set_hexpand(True)
        info.set_vexpand(True)




        self.labels['i1_box'] = Gtk.HBox(spacing=0)
        self.labels['i1_box'].set_vexpand(True)
        self.labels['i1_box'].get_style_context().add_class("printing-info-box")
        self.labels['i1_box'].set_valign(Gtk.Align.CENTER)
        self.labels['i2_box'] = Gtk.VBox(spacing=0)
        self.labels['i2_box'].set_vexpand(True)
        self.labels['i2_box'].get_style_context().add_class("printing-info-box")
        self.labels['i2_box'].set_valign(Gtk.Align.CENTER)
        self.labels['info_grid'] = self._gtk.HomogeneousGrid()
        self.labels['info_grid'].attach(self.labels['i1_box'], 0, 0, 1, 1)
        self.labels['info_grid'].attach(self.labels['i2_box'], 1, 0, 1, 1)

        grid.attach(fi_box, 0, 0, 4, 1)
        grid.attach(self.labels['info_grid'], 0, 1, 4, 2)

        grid.attach(self.arrangeMenuItems(self.items, 4, True), 0, 3, 4, 1)

        # self.add_labels()
        #self.labels['i1_box'].add(self.labels['thumbnail'])
        self.labels['i2_box'].add(self.labels['temp_grid'])
        self.labels['i2_box'].add(self.labels['pos_box'])
        #self.labels['i2_box'].add(self.labels['sfe_grid'])
        self.labels['i2_box'].add(self.labels['it_box'])
        #self.labels['i2_box'].add(self.labels['itl_box'])

        self.content.add(grid)
        self.layout.show_all()

        self._screen.add_subscription(panel_name)

    def activate(self):
        return

    def on_draw(self, da, ctx):
        w = da.get_allocated_width()
        h = da.get_allocated_height()
        r = min(w, h) * .4

        ctx.set_source_rgb(0.6, 0.6, 0.6)
        ctx.set_line_width(self._gtk.get_font_size() * .75)
        ctx.translate(w / 2, h / 2)
        ctx.arc(0, 0, r, 0, 2 * math.pi)
        ctx.stroke()

        ctx.set_source_rgb(1, 0, 0)
        ctx.arc(0, 0, r, 3 / 2 * math.pi, 3 / 2 * math.pi + (0.6 * 2 * math.pi))
        ctx.stroke()

    def process_update(self, data):
        self.labels['status'].set_text("Status: %s" % self._screen.robot.evaluate_state())

        self.labels['pos_x'].set_text("X: %.2f" % (self._screen.robot.data['move']['axes'][0]['machinePosition']))
        self.labels['pos_y'].set_text("Y: %.2f" % (self._screen.robot.data['move']['axes'][1]['machinePosition']))
        self.labels['pos_z'].set_text("Z: %.2f" % (self._screen.robot.data['move']['axes'][2]['machinePosition']))

        #logging.debug(str(self._screen.printer.data['move']['axes'][0]))

        self.labels['heater_bed'].set_markup(
            "MCU: %.1f °C" % (self._screen.robot.data['boards'][0]['mcuTemp']['current'])
        )

        self.labels['duration'].set_text(str(self._gtk.formatTimeString(self._screen.robot.data['state']['upTime'])))

        #self.labels['progress_text'].set_text("%s%%" % (str(min(int(0.7 * 100), 100))))

        # self.labels[1].set_label(self._gtk.formatTemperatureString(self._screen.printer.data['state']['upTime'], 77))
        # self.labels[3].set_label(self._screen.printer.data['state']['status'])

        return
