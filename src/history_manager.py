import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib
from .utils import *

def add_url(title, url):
    statement = "INSERT INTO urls (url, title, last_visit_time) VALUES ('{}', '{}', {})".format(url, title, current_timestamp())
    execute_statement(statement)

class HistoryClearAlert(Adw.AlertDialog):
    def __init__(self, **kwargs):
        super().__init__()
        self.set_heading("Clear Browsing History?")
        self.set_body("All links will be permanently deleted. Happy privacy ;)")
        self.add_response("0", "Cancel")
        self.add_response("1", "Clear")

        self.set_close_response("0")
        self.set_default_response("1")

        self.connect("response", self.response_cb)

    def response_cb(self, dialog, response):
        if response == "1":
            statement = "DELETE FROM urls;"
            execute_statement(statement)
