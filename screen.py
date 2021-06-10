#!/usr/bin/python

import argparse
import gi
import gettext
import importlib
import logging
import os
import subprocess

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from jinja2 import Environment, Template

from includes import functions
from includes.KlippyWebsocket import KlippyWebsocket
from includes.Rest import Rest
from includes.KlippyGtk import KlippyGtk
from includes.printer import Printer

from includes.config import KlipperScreenConfig

logging.getLogger('matplotlib').setLevel(logging.WARNING)

klipperscreendir = os.getcwd()


class RmsScreen(Gtk.Window):
    """ Class for creating a screen for Klipper via HDMI """
    _cur_panels = []
    bed_temp_label = None
    connecting = False
    connected_printer = None
    currentPanel = None
    files = None
    filename = ""
    keyboard = None
    keyboard_height = 200
    last_update = {}
    load_panel = {}
    number_tools = 1
    panels = {}
    popup_message = None
    printer = None
    printer_select_callbacks = []
    subscriptions = []
    shutdown = True
    _ws = None
    screen_timeout = None
    screen_saver_timeout = 60


    def __init__(self, args, version):
        self.version = version

        configfile = os.path.normpath(os.path.expanduser(args.configfile))

        self.lang = gettext.translation('KlipperScreen', localedir='includes/locales', fallback=True)
        self._config = KlipperScreenConfig(configfile, self.lang, self)

        logging.debug("OS Language: %s" % os.getenv('LANG'))

        _ = self.lang.gettext

        Gtk.Window.__init__(self)
        self.width = self._config.get_main_config().getint("width", Gdk.Screen.get_width(Gdk.Screen.get_default()))
        self.height = self._config.get_main_config().getint("height", Gdk.Screen.get_height(Gdk.Screen.get_default()))
        self.set_default_size(self.width, self.height)
        self.set_resizable(False)
        logging.info("Screen resolution: %sx%s" % (self.width, self.height))

        self.gtk = KlippyGtk(self.width, self.height)
        self.init_style()

        self.printer_initializing(_("Initializing"))
        self.set_screenblanking_timeout()

        self.screen_timeout = GLib.timeout_add(1000, self.check_screensaver)

        self.connect("button_press_event", self.disable_screensaver)

        # Move mouse to 0,0
        os.system("/usr/bin/xdotool mousemove 0 0")
        # Change cursor to blank
        if self._config.get_main_config().getboolean("show_cursor", fallback=False):
            self.get_window().set_cursor(Gdk.Cursor(Gdk.CursorType.ARROW))
        else:
            self.get_window().set_cursor(Gdk.Cursor(Gdk.CursorType.BLANK_CURSOR))

        self.api_client = Rest(
            {
                "on_message": self._api_callback,
                "on_error": self._api_callback_error
            },
            self._config.host
        )

        self.connect_printer("RMS")

    def disable_screensaver(self, dummy1, dummy2):
        if "screensaver" in self._cur_panels:
            self._menu_go_home()

    def check_screensaver(self):

        timeout = int(subprocess.getoutput("xprintidle"))
        timeout = int(timeout / 1000)

        logging.debug("$$$$$$$ counter:" + str(timeout))

        if timeout > self.screen_saver_timeout and "screensaver" not in self._cur_panels:
            logging.info("### Creating screensaver panel")
            self.show_panel("screensaver", "screensaver", "Screen Saver", 1, False)

        return True

    def connect_printer(self, name):
        _ = self.lang.gettext

        if self.connected_printer == name:
            while len(self.printer_select_callbacks) > 0:
                i = self.printer_select_callbacks.pop(0)
                i()
            return

        self.printer_select_callbacks = []

        if self._ws is not None:
            self._ws.close()
        self.connecting = True

        logging.info("Connecting to printer: %s" % name)

        self.printer = Printer()

        self._remove_all_panels()
        panels = list(self.panels)
        if len(self.subscriptions) > 0:
            self.subscriptions = []
        for panel in panels:
            del self.panels[panel]
        self.printer_initializing(_("Connecting to %s") % name)

        self.printer.set_callbacks({
            "idle": self.state_idle,
            "halted": self.state_halted,
            "disconnected": self.state_disconnected,
            "busy": self.state_busy,
            #"error": self.state_error,
            #"paused": self.state_paused,
            #"printing": self.state_printing,
            #"ready": self.state_ready,
            #"startup": self.state_startup,
            #"shutdown": self.state_shutdown
        })

        self._ws = KlippyWebsocket(self,
            {
                "on_connect": self.init_printer,
                "on_message": self._websocket_callback,
                "on_close": self.printer_initializing
            },
            self._config.host
        )
        self._ws.initial_connect()
        self.connecting = False

        self.connected_printer = name
        logging.debug("Connected to printer: %s" % name)

    def _load_panel(self, panel, *args):
        if panel not in self.load_panel:
            logging.debug("Loading panel: %s" % panel)
            panel_path = os.path.join(os.path.dirname(__file__), 'panels', "%s.py" % panel)
            logging.info("Panel path: %s" % panel_path)
            if not os.path.exists(panel_path):
                msg = f"Panel {panel} does not exist"
                logging.info(msg)
                raise Exception(msg)

            module = importlib.import_module("panels.%s" % panel)
            if not hasattr(module, "create_panel"):
                msg = f"Cannot locate create_panel function for {panel}"
                logging.info(msg)
                raise Exception(msg)
            # This wil load callback
            self.load_panel[panel] = getattr(module, "create_panel")

        try:
            # Call create_panel
            return self.load_panel[panel](*args)
        except Exception:
            msg = f"Unable to create panel {panel}"
            logging.exception(msg)
            raise Exception(msg)

    def show_panel(self, panel_name, type, title, remove=None, pop=True, **kwargs):
        if panel_name not in self.panels:
            self.panels[panel_name] = self._load_panel(type, self, title)

            try:
                if kwargs != {}:
                    self.panels[panel_name].initialize(panel_name, **kwargs)
                else:
                    self.panels[panel_name].initialize(panel_name)
            except:
                del self.panels[panel_name]
                logging.exception("Unable to load panel %s" % type)
                self.show_error_modal("Unable to load panel %s" % type)
                return

            if hasattr(self.panels[panel_name],"process_update"):
                self.panels[panel_name].process_update("notify_status_update", self.printer.get_data())

        try:
            if remove == 2:
                self._remove_all_panels()
            elif remove == 1:
                self._remove_current_panel(pop)

            logging.debug("Attaching panel %s" % panel_name)

            self.add(self.panels[panel_name].get())
            self.show_all()

            #if hasattr(self.panels[panel_name],"process_update"):
                #self.panels[panel_name].process_update("notify_status_update", self.printer.get_updates())
            if hasattr(self.panels[panel_name],"activate"):
                self.panels[panel_name].activate()
                self.show_all()
        except:
            logging.exception("Error attaching panel")

        self._cur_panels.append(panel_name)
        logging.debug("Current panel hierarchy: %s", str(self._cur_panels))

    def show_popup_message(self, message):
        if self.popup_message != None:
            self.close_popup_message()

        box = Gtk.Box()
        box.get_style_context().add_class("message_popup")
        box.set_size_request(self.width, self.gtk.get_header_size())
        label = Gtk.Label()
        if "must home axis first" in message.lower():
            message = "Must home all axis first."
        label.set_text(message)

        close = Gtk.Button.new_with_label("X")
        close.set_can_focus(False)
        close.props.relief = Gtk.ReliefStyle.NONE
        close.connect("clicked", self.close_popup_message)

        box.pack_start(label, True, True, 0)
        box.pack_end(close, False, False, 0)
        box.set_halign(Gtk.Align.CENTER)

        cur_panel = self.panels[self._cur_panels[-1]]
        for i in ['back','estop','home']:
            if i in cur_panel.control:
                cur_panel.control[i].set_sensitive(False)
        cur_panel.get().put(box, 0,0)

        self.show_all()
        self.popup_message = box

        GLib.timeout_add(10000, self.close_popup_message)

        return False

    def close_popup_message(self, widget=None):
        if self.popup_message == None:
            return

        cur_panel = self.panels[self._cur_panels[-1]]
        for i in ['back','estop','home']:
            if i in cur_panel.control:
                cur_panel.control[i].set_sensitive(True)
        cur_panel.get().remove(self.popup_message)
        self.popup_message = None
        self.show_all()

    def show_error_modal(self, err):
        _ = self.lang.gettext
        logging.exception("Showing error modal: %s", err)

        buttons = [
            {"name":_("Go Back"),"response": Gtk.ResponseType.CANCEL}
        ]

        label = Gtk.Label()
        label.set_markup(("%s \n\n" % err) +
            _("Check /tmp/KlipperScreen.log for more information.\nPlease submit an issue on GitHub for help."))
        label.set_hexpand(True)
        label.set_halign(Gtk.Align.CENTER)
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)

        dialog = self.gtk.Dialog(self,  buttons, label, self.error_modal_response)

    def error_modal_response(self, widget, response_id):
        widget.destroy()

    def init_style(self):
        style_provider = Gtk.CssProvider()


        css = open(klipperscreendir + "/styles/style.css")
        css_data = css.read()
        css.close()
        css_data = css_data.replace("KS_FONT_SIZE",str(self.gtk.get_font_size()))

        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css_data.encode())

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


    def _go_to_submenu(self, widget, name):
        logging.info("#### Go to submenu " + str(name))
        #self._remove_current_panel(False)

        # Find current menu item
        panels = list(self._cur_panels)
        if "main_panel" in self._cur_panels:
            menu = "__main"
        elif "splash_screen" in self._cur_panels:
            menu = "__splashscreen"
        else:
            menu = "__print"

        logging.info("#### Menu " + str(menu))
        disname = self._config.get_menu_name(menu, name)
        menuitems = self._config.get_menu_items(menu, name)
        if len(menuitems) == 0:
            logging.info("No items in menu, returning.")
            return

        self.show_panel(self._cur_panels[-1] + '_' + name, "menu", disname, 1, False, display_name=disname,
            items=menuitems)

    def _remove_all_panels(self):
        while len(self._cur_panels) > 0:
            self._remove_current_panel(True, False)
        self.show_all()

    def _remove_current_panel(self, pop=True, show=True):
        if len(self._cur_panels) > 0:
            self.remove(self.panels[self._cur_panels[-1]].get())
            if pop == True:
                self._cur_panels.pop()
                if len(self._cur_panels) > 0:
                    self.add(self.panels[self._cur_panels[-1]].get())
                    if hasattr(self.panels[self._cur_panels[-1]], "process_update"):
                        self.panels[self._cur_panels[-1]].process_update("notify_status_update", None)
                    if show:
                        self.show_all()

    def _menu_go_back (self, widget=None):
        logging.info("#### Menu go back")
        #self.remove_keyboard()
        self._remove_current_panel()

    def _menu_go_home(self):
        logging.info("#### Menu go home")
        #self.remove_keyboard()
        while len(self._cur_panels) > 1:
            self._remove_current_panel()

    def add_subscription (self, panel_name):
        add = True
        for sub in self.subscriptions:
            if sub == panel_name:
                return

        self.subscriptions.append(panel_name)

    def remove_subscription (self, panel_name):
        for i in range(len(self.subscriptions)):
            if self.subscriptions[i] == panel_name:
                self.subscriptions.pop(i)
                return

    def set_screenblanking_timeout(self):
        # Disable screen blanking
        os.system("xset -display :0 s off")
        os.system("xset -display :0 s noblank")
        os.system("xset -display :0 -dpms")

    def state_busy(self):
        self.show_panel('busy_screen', "busy", "Robot is busy", 2)

    def state_disconnected(self):
        if "printer_select" in self._cur_panels:
            self.printer_select_callbacks = [self.state_disconnected]
            return

        _ = self.lang.gettext
        logging.debug("### Going to disconnected")
        self.printer_initializing(_("Robot has disconnected"))

    def state_error(self):
        if "printer_select" in self._cur_panels:
            self.printer_select_callbacks = [self.state_error]
            return

        _ = self.lang.gettext
        msg = self.printer.get_stat("webhooks","state_message")
        if "FIRMWARE_RESTART" in msg:
            self.printer_initializing(
                _("Klipper has encountered an error.\nIssue a FIRMWARE_RESTART to attempt fixing the issue.")
            )
        elif "micro-controller" in msg:
            self.printer_initializing(
                _("Klipper has encountered an error with the micro-controller.\nPlease recompile and flash.")
            )
        else:
            self.printer_initializing(
                _("Klipper has encountered an error.")
            )

    def state_paused(self):
        if "job_status" not in self._cur_panels:
            self.printer_printing()

    def state_printing(self):
        if "printer_select" in self._cur_panels:
            self.printer_select_callbacks = [self.state_printing]
            return

        if "job_status" not in self._cur_panels:
            self.printer_printing()

    def state_ready(self):
        if "printer_select" in self._cur_panels:
            self.printer_select_callbacks = [self.state_ready]
            return

        # Do not return to main menu if completing a job, timeouts/user input will return
        if "job_status" in self._cur_panels or "main_menu" in self._cur_panels:
            return
        self.printer_ready()
    
    def state_idle(self):
        # if "printer_select" in self._cur_panels:
        #     self.printer_select_callbacks = [self.state_ready]
        #     return

        # # Do not return to main menu if completing a job, timeouts/user input will return
        # if "job_status" in self._cur_panels or "main_menu" in self._cur_panels:
        #     return
        self.printer_ready()

    def state_halted(self):
        # if "printer_select" in self._cur_panels:
        #     self.printer_select_callbacks = [self.state_ready]
        #     return

        self.printer_halted()

    def state_startup(self):
        if "printer_select" in self._cur_panels:
            self.printer_select_callbacks = [self.state_startup]
            return

        _ = self.lang.gettext
        self.printer_initializing(_("Klipper is attempting to start"))

    def state_shutdown(self):
        if "printer_select" in self._cur_panels:
            self.printer_select_callbacks = [self.state_shutdown]
            return

        _ = self.lang.gettext
        self.printer_initializing(_("Klipper has shutdown"))

    def _websocket_callback(self, data):
        _ = self.lang.gettext

        if self.connecting == True:
            return

        self.printer.process_update(dict(data))

        if "state" in data:
            if "status" in data['state']:
                logging.debug(data['state']['status'])
                self.printer.change_state(data['state']['status'])

        if self._cur_panels[-1] in self.subscriptions:
            self.panels[self._cur_panels[-1]].process_update("notify_status_update", data)

        # if action == "notify_klippy_disconnected":
        #     logging.debug("Received notify_klippy_disconnected")
        #     self.printer.change_state("disconnected")
        #     return
        # elif action == "notify_klippy_ready":
        #     self.printer.change_state("ready")
        # elif action == "notify_status_update" and self.printer.get_state() != "shutdown":
        #
        # elif action == "notify_filelist_changed":
        #     logging.debug("Filelist changed: %s", json.dumps(data,indent=2))
        #     #self.files.add_file()
        # elif action == "notify_metadata_update":
        #     self.files.request_metadata(data['filename'])
        # elif action == "notify_power_changed":
        #     logging.debug("Power status changed: %s", data)
        #     self.printer.process_power_update(data)
        # elif self.printer.get_state() not in ["error","shutdown"] and action == "notify_gcode_response":
        #     if "Klipper state: Shutdown" in data:
        #         logging.debug("Shutdown in gcode response, changing state to shutdown")
        #         self.printer.change_state("shutdown")
        #
        #     if not (data.startswith("B:") and
        #         re.search(r'B:[0-9\.]+\s/[0-9\.]+\sT[0-9]+:[0-9\.]+', data)):
        #         if data.startswith("!! "):
        #             self.show_popup_message(data[3:])
        #         logging.debug(json.dumps([action, data], indent=2))


    def _confirm_send_action(self, widget, text, method, params={}):
        _ = self.lang.gettext

        buttons = [
            {"name":_("Continue"), "response": Gtk.ResponseType.OK},
            {"name":_("Cancel"),"response": Gtk.ResponseType.CANCEL}
        ]

        try:
            env = Environment(extensions=["jinja2.ext.i18n"])
            env.install_gettext_translations(self.lang)
            j2_temp = env.from_string(text)
            text = j2_temp.render()
        except:
            logging.debug("Error parsing jinja for confirm_send_action")

        label = Gtk.Label()
        label.set_markup(text)
        label.set_hexpand(True)
        label.set_halign(Gtk.Align.CENTER)
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)

        dialog = self.gtk.Dialog(self, buttons, label, self._confirm_send_action_response,  method, params)

    def _confirm_send_action_response(self, widget, response_id, method, params):
        if response_id == Gtk.ResponseType.OK:
            self._send_action(widget, method, params)

        widget.destroy()

    def _send_action(self, widget, method, params):
        self.api_client.async_send_gcode(params['script'])

    def printer_initializing(self, text=None):
        self.shutdown = True
        self.close_popup_message()
        self.show_panel('splash_screen',"splash_screen", "Splash Screen", 2)
        if text != None:
            self.panels['splash_screen'].update_text(text)
            self.panels['splash_screen'].show_restart_buttons()

    def init_printer(self):
        _ = self.lang.gettext

        # on connection of websocket, do we want to get some extra robot info?

    def printer_ready(self):
        _ = self.lang.gettext
        self.close_popup_message()
        # Force update to printer webhooks state in case the update is missed due to websocket subscribe not yet sent
        #self.printer.process_update({"webhooks":{"state":"ready","state_message": "Printer is ready"}})
        self.show_panel('main_panel', "main_menu", _("Home"), 2, items=self._config.get_menu_items("__main"))

    def printer_halted(self):
        logging.debug("printer_halted")

        _ = self.lang.gettext
        self.close_popup_message()
        self.show_panel('halted_panel', "halted", _("Halted"), 2)

    def _api_callback(self, result):
        _ = self.lang.gettext

        logging.debug(result)

    def _api_callback_error(self, msg):
        _ = self.lang.gettext

        self.show_popup_message(msg)
        logging.debug(msg)


def main():

    version = functions.get_software_version()
    parser = argparse.ArgumentParser(description="KlipperScreen - A GUI for Klipper")
    parser.add_argument(
        "-c","--configfile", default="~/KlipperScreen.conf", metavar='<configfile>',
        help="Location of KlipperScreen configuration file"
    )
    parser.add_argument(
        "-l","--logfile", default="/tmp/KlipperScreen.log", metavar='<logfile>',
        help="Location of KlipperScreen logfile output"
    )
    args = parser.parse_args()

    functions.setup_logging(
        os.path.normpath(os.path.expanduser(args.logfile)),
        version
    )

    logging.info("RmsScreen version: %s" % version)

    win = RmsScreen(args, version)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    try:
        main()
    except:
        logging.exception("Fatal error in main loop")
