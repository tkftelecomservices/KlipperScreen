#!/usr/bin/python

import gi
import threading
import json
import websocket
import logging

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib


class Websocket(threading.Thread):
    _req_id = 0
    connected = False
    timeout = None

    def __init__(self, screen, callback, host):
        threading.Thread.__init__(self)
        self._screen = screen
        self._callback = callback
        self.closing = False

        self._url = "%s" % (host)

    def initial_connect(self):
        # Enable a timeout so that way if moonraker is not running, it will attempt to reconnect
        if self.timeout == None:
            self.timeout = GLib.timeout_add(500, self.reconnect)

    def connect (self):
        #self.ws_url = "ws://%s/websocket?token=%s" % (self._url, token)
        self.ws_url = "ws://10.0.0.2/machine"
        self.ws = websocket.WebSocketApp(self.ws_url,
            on_message  = lambda ws,msg:    self.on_message(ws, msg),
            on_error    = lambda ws,msg:    self.on_error(ws, msg),
            on_close    = lambda ws:        self.on_close(ws),
            on_open     = lambda ws:        self.on_open(ws)
        )

        self._wst = threading.Thread(target=self.ws.run_forever)
        self._wst.daemon = True
        try:
            self._wst.start()
        except Exception:
            logging.debug("Error starting web socket")

    def close(self):
        self.closing = True
        self.ws.close()

    def is_connected(self):
        return self.connected

    def on_message(self, ws, message):
        response = json.loads(message)

        # logging.debug(response)

        Gdk.threads_add_idle(
            GLib.PRIORITY_HIGH_IDLE,
            self._callback['on_message'],
            response
        )

        self.ws.send("OK")

    def on_open(self, ws):
        logging.info("Websocket Open")
        logging.info("Self.connected = %s" % self.is_connected())
        self.connected = True
        self.timeout = None
        if "on_connect" in self._callback:
            Gdk.threads_add_idle(
                GLib.PRIORITY_HIGH_IDLE,
                self._callback['on_connect']
            )

    def on_close(self, ws):

        if self.closing:
            logging.debug("Closing websocket")
            self.ws.stop()
            return

        if not self.is_connected():
            # no need to update interface
            logging.debug("Unable to connect")
        else:
            logging.info("Websocket Closed")
            self.connected = False

            if "on_close" in self._callback:
                Gdk.threads_add_idle(
                    GLib.PRIORITY_HIGH_IDLE,
                    self._callback['on_close'],
                    "Lost connection to RMS"
                )

        # Re-connect
        self.timeout = GLib.timeout_add(500, self.reconnect)

    def reconnect(self):
        logging.debug("Attempting to reconnect")
        if self.is_connected():
            logging.debug("Already connected")
            return False

        self.connect()
        return False

    def on_error(self, ws, error):
        logging.warning("Websocket error: %s" % error)