import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib
from datetime import datetime
from .utils import *

def add_url(title, url):
    statement = "INSERT INTO urls (url, title, last_visit_time) VALUES ('{}', '{}', {})".format(url, title, int(datetime.utcnow().timestamp()))
    execute_insert(statement)