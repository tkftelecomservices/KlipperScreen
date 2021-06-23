from pprint import pprint

import gi
import logging

gi.require_version("Gtk", "3.0")
from gi.repository import  Gdk, GLib
from jsonmerge import Merger

class Robot:
    data = {}

    DISCONNECTED = "disconnected"

    MEASURING = "measuring"

    state_callbacks = {
        "disconnected": None,
        "idle": None,
        "halted": None,
        "busy": None,
        "measuring": None,
        # "error": None,
        # "paused": None,
        # "printing": None,
        # "ready": None,
        # "startup": None,
        # "shutdown": None
    }

    def __init__(self):
        self.state = self.DISCONNECTED

        self.data = {
            'state': {'upTime': 0},
            'move': {
                'axes': [
                    {'homed': False},
                    {'homed': False},
                    {'homed': False}
                ]
            }
        }

        schema = {
            "type": "object",
            "properties": {
                "boards": {
                    "mergeStrategy": "arrayMergeByIndex",
                },
                "move": {
                    "type": "object",
                    "properties": {
                        "axes": {
                            "mergeStrategy": "arrayMergeByIndex",
                        }
                    }
                }
            },
            "additionalProperties": False
        }

        self.merger = Merger(schema)

    def merge(self, a, b, path=None):
        "merges b into a"
        if path is None: path = []
        for key in b:
            if key in a:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    self.merge(a[key], b[key], path + [str(key)])
                else:
                    # update value
                    a[key] = b[key]
            else:
                # create value
                a[key] = b[key]
        return a

    def process_update(self, data):

        self.data = self.merger.merge(self.data, data)

        if "state" in data:
            if "status" in data['state']:
                state = data['state']['status']

                if self.data['state']['currentTool'] == 0:
                    state = self.MEASURING

                self.change_state(state)

    def evaluate_state(self):
        state = self.state

        if not self.data['move']['axes'][0]['homed'] or not self.data['move']['axes'][1]['homed'] or not self.data['move']['axes'][2]['homed']:
            return "not homed"

        return state

    #     wh_state = self.data['webhooks']['state'].lower() # possible values: startup, ready, shutdown, error
    #     idle_state = self.data['idle_timeout']['state'].lower() # possible values: Idle, printing, ready
    #     print_state = self.data['print_stats']['state'].lower() # possible values: complete, paused, printing, standby
    #
    #     if wh_state == "ready":
    #         new_state = "ready"
    #         if print_state == "paused":
    #             new_state = "paused"
    #         elif idle_state == "printing":
    #             if print_state == "complete":
    #                 new_state = "ready"
    #             elif print_state != "printing": # Not printing a file, toolhead moving
    #                 new_state = "busy"
    #             else:
    #                 new_state = "printing"
    #
    #         if new_state != "busy":
    #             self.change_state(new_state)
    #     else:
    #         self.change_state(wh_state)

    # def process_power_update(self, data):
    #     if data['device'] in self.power_devices:
    #         self.power_devices[data['device']]['status'] = data['status']

    def change_state(self, state):
        if state == self.state or state not in list(self.state_callbacks):
            return

        logging.debug("Changing state from '%s' to '%s'" % (self.state, state))
        self.state = state
        if self.state_callbacks[state] is not None:
            logging.debug("Adding callback for state: %s" % state)
            Gdk.threads_add_idle(
                GLib.PRIORITY_HIGH_IDLE,
                self.state_callbacks[state]
            )

    def get_data(self):
        return self.data

    def get_stat(self, stat, substat = None):
        if stat not in self.data:
            return None
        if substat != None:
            if substat in self.data[stat]:
                return self.data[stat][substat]
            return None
        return self.data[stat]

    def get_state(self):
        return self.state

    def set_callbacks(self, callbacks):
        for name, cb in callbacks.items():
            if name in list(self.state_callbacks):
                self.state_callbacks[name] = cb