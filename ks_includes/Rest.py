import requests
import logging
import threading
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib


class Rest(threading.Thread):
    def __init__(self, callback, ip, port=80):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self._callback = callback
        self._thread = None

    def send_gcode(self, code):
        # url = "http://%s:%s/%s" % (self.ip, self.port, method)
        url = "http://10.0.0.2/machine/code"
        logging.debug("Sending request to %s, gcode: %s" % (url, code))

        try:
            r = requests.post(url, code, headers={})
        except:
            logging.error("Error sending api request")
            return

        if r.status_code != 200:
            logging.error("API Request failed")

    def async_send_gcode(self, code=""):
        def run(code, callback):
            # url = "http://%s:%s/%s" % (self.ip, self.port, method)
            url = "http://10.0.0.2/machine/code"
            logging.debug("Sending async request to %s, gcode: %s" % (url, code))

            try:
                r = requests.post(url, code, headers={})
            except:
                Gdk.threads_add_idle(
                    GLib.PRIORITY_HIGH_IDLE,
                    callback['on_error'],
                    "Error sending api request"
                )
                return

            if r.status_code != 200:
                Gdk.threads_add_idle(
                    GLib.PRIORITY_HIGH_IDLE,
                    callback['on_error'],
                    "Wrong status code received"
                )
            else:
                Gdk.threads_add_idle(
                    GLib.PRIORITY_HIGH_IDLE,
                    callback['on_message'],
                    r.text
                )

        if self._thread is not None and self._thread.isAlive():
            Gdk.threads_add_idle(
                GLib.PRIORITY_HIGH_IDLE,
                self._callback['on_error'],
                "Api thread is locked"
            )
            return

        self._thread = threading.Thread(target=run, args=(code, self._callback))
        self._thread.daemon = True
        try:
            self._thread.start()
        except Exception:
            logging.debug("Error starting api thread")
