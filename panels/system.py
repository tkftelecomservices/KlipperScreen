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

        ks_restart = self._gtk.ButtonImage('reboot',"\n".join(_('Restart Screen').split(' ')))
        ks_restart.connect("clicked", self.restart_screen)

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        info.set_vexpand(True)

        self.labels['loadavg'] = Gtk.Label("temp")
        self.update_system_load()

        self.system_timeout = GLib.timeout_add(1000, self.update_system_load)

        self.labels['klipper_version'] = Gtk.Label(_("Klipper Version") +
            (": %s" % 500))
        self.labels['klipper_version'].set_margin_top(15)

        self.labels['ks_version'] = Gtk.Label(_("KlipperScreen Version") + (": %s" % self._screen.version))
        self.labels['ks_version'].set_margin_top(15)

        stream = os.popen('hostname -I')
        ip = stream.read()

        self.labels['network_ip'] = Gtk.Label(_("Network Ip") + ": %s" % ip)
        self.labels['network_ip'].set_margin_top(15)

        info.add(self.labels['loadavg'])
        info.add(self.labels['klipper_version'])
        info.add(self.labels['ks_version'])
        info.add(self.labels['network_ip'])

        grid.attach(info, 0, 0, 5, 2)
        grid.attach(ks_restart, 2, 2, 1, 1)

        self.content.add(grid)

    def update_system_load(self):
        _ = self.lang.gettext
        lavg = os.getloadavg()
        self.labels['loadavg'].set_text(
            _("Load Average") + (": %.2f %.2f %.2f" % (lavg[0], lavg[1], lavg[2]))
        )
        return True

    def restart_screen(self, widget):
        os.system("sudo systemctl restart KlipperScreen")
