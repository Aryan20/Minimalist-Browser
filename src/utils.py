import sqlite3

from gi.repository import Gio, GLib

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

def execute_insert(statement):
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
