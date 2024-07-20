import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, GLib
import sqlite3
from datetime import datetime

def check_db_exists():
    data_dir = GLib.get_user_data_dir()
    dirpath = [data_dir, 'minimalistbrowser']
    dirname = Gio.File.new_build_filenamev(dirpath)
    filename = Gio.File.new_build_filenamev(dirpath + ['history.db'])
    if(dirname.query_exists()):
        if(filename.query_exists()):
            return True
    else:
        Gio.File.make_directory(dirname, None)
    Gio.File.create(filename, Gio.FileCreateFlags.PRIVATE, None)
    create_first_connection(filename.get_path())

def create_action_button(icon, **kwargs):
    button = Gtk.Button()
    button.set_icon_name(icon)
    if len(kwargs) > 0:
        button.set_has_frame(kwargs["frame"])
    else:
        button.set_has_frame(False)
    button.set_hexpand(False)
    button.set_vexpand(False)
    button.set_halign(Gtk.Align.CENTER)
    button.set_valign(Gtk.Align.CENTER)
    return button

def create_first_connection(path):
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    # cursor.execute("CREATE TABLE hosts ("
    #             "id INTEGER PRIMARY KEY,"
    #             "url LONGVARCAR,"
    #             "title LONGVARCAR,"
    #             "visit_count INTEGER DEFAULT 0 NOT NULL,"
    #             "zoom_level REAL DEFAULT 0.0)")
    # cursor.execute("CREATE TABLE visits ("
    #             "id INTEGER PRIMARY KEY,"
    #             "url INTEGER NOT NULL REFERENCES urls(id) ON DELETE CASCADE,"
    #             "visit_time INTEGER NOT NULL,"
    #             "visit_type INTEGER NOT NULL,"
    #             "referring_visit INTEGER)")
    cursor.execute("CREATE TABLE urls ("
                "id INTEGER PRIMARY KEY,"
                "url LONGVARCAR,"
                "title LONGVARCAR,"
                "last_visit_time INTEGER)")

def create_connection():
    data_dir = GLib.get_user_data_dir()
    dirpath = [data_dir, 'minimalistbrowser']
    filename = Gio.File.new_build_filenamev(dirpath + ['history.db'])
    connection = sqlite3.connect(filename.get_path())
    cursor = connection.cursor()
    return [connection, cursor]

def execute_statement(statement):
    con_cur = create_connection()
    cursor = con_cur[1]
    cursor.execute(statement)
    terminate_connection(con_cur)

def execute_search(statement):
    con_cur = create_connection()
    cursor = con_cur[1]
    cursor.execute(statement)
    rows = cursor.fetchall()
    terminate_connection(con_cur)
    return rows

def terminate_connection(connection):
    connection = connection[0]
    connection.commit()
    connection.close()

def format_date_display(timestamp):
    current_utc = datetime.utcnow()

    history_datetime = datetime.utcfromtimestamp(timestamp)
    if current_utc.year == history_datetime.year:
        if current_utc.month == history_datetime.month:
            formatted_time = history_datetime.strftime('%a %H:%M')
        else:
            formatted_time = history_datetime.strftime('%d %b %H:%M')
    else:
        formatted_time = history_datetime.strftime('%d %b %Y %H:%M')
        
        
    return formatted_time

def current_timestamp():
    return int(datetime.utcnow().timestamp())
