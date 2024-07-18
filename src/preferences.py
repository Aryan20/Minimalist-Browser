import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib

class Preferences(Adw.PreferencesDialog):
    def __init__(self, **kwargs):
        super().__init__()
        self.settings = Gio.Settings(schema_id="in.aryank.MinimalistBrowser")
        self.create_page()

    def create_page(self):
        prefPage1 = Adw.PreferencesPage()
        prefPage1.add(self.build_search_engine_group())
        prefPage1.add(self.build_homepage_group())
        self.add(prefPage1)
        self.present()

    def build_search_engine_group(self):
        search_engine_group = Adw.PreferencesGroup()
        search_engine_group.set_title("Search Engine")

        duckduckgo_row = Adw.ActionRow()
        duckduckgo_row.set_title("DuckDuckGo")
        self.duckduckgo_radio = Gtk.CheckButton()
        duckduckgo_row.add_prefix(self.duckduckgo_radio)

        google_row = Adw.ActionRow()
        google_row.set_title("Google")
        self.google_row_radio = Gtk.CheckButton()
        google_row.add_prefix(self.google_row_radio)

        custom_engine_row = Adw.ActionRow()
        custom_engine_row.set_title("Custom Search Engine")
        custom_engine_row_radio = Gtk.CheckButton()
        custom_engine_row.add_prefix(custom_engine_row_radio)

        search_engine_entry = Gtk.Entry()
        search_engine_entry.set_hexpand(True)
        search_engine_entry.set_valign(Gtk.Align.CENTER)
        search_engine_entry.connect("activate", self.custom_search_engine_cb)
        search_engine_entry.set_placeholder_text("Enter Custom Engine URL with {url} in place of query")
        custom_engine_row.add_suffix(search_engine_entry)

        self.google_row_radio.set_group(self.duckduckgo_radio)
        custom_engine_row_radio.set_group(self.google_row_radio)
        self.duckduckgo_radio.connect("toggled", lambda _: self.change_engine_cb())
        self.google_row_radio.connect("toggled", lambda _: self.change_engine_cb())

        self.duckduckgo_radio.set_active(self.settings.get_boolean('search-engine-duck'))
        self.google_row_radio.set_active(self.settings.get_boolean('search-engine-google'))
        if(self.settings.get_boolean('search-engine-custom')):
            custom_engine_row_radio.set_active(True)
            search_engine_entry.set_text(self.settings.get_string('search-engine'))

        search_engine_group.add(duckduckgo_row)
        search_engine_group.add(google_row)
        search_engine_group.add(custom_engine_row)

        return search_engine_group

    def change_engine_cb(self):
        self.settings.set_boolean('search-engine-custom', False)
        self.settings.set_boolean('search-engine-duck', False)
        self.settings.set_boolean('search-engine-google', False)
        if(self.google_row_radio.get_active()):
            self.settings.set_string('search-engine', "https://www.google.com/search?q={url}")
            self.settings.set_boolean('search-engine-google', True)
        elif(self.duckduckgo_radio.get_active()):
            self.settings.set_string('search-engine', "https://www.duckduckgo.com/?q={url}")
            self.settings.set_boolean('search-engine-duck', True)
            

    def custom_search_engine_cb(self, entry):
        self.settings.set_boolean('search-engine-duck', False)
        self.settings.set_boolean('search-engine-google', False)
        self.settings.set_boolean('search-engine-custom', True)

        self.settings.set_string('search-engine', entry.get_text())

    def build_homepage_group(self):
        homepage_group = Adw.PreferencesGroup()
        homepage_group.set_title("Home Page")

        defaultRow = Adw.ActionRow()
        defaultRow.set_title("Blank Page (Default)")
        self.default_row_radio = Gtk.CheckButton()
        defaultRow.add_prefix(self.default_row_radio)

        custom_homepage_row = Adw.ActionRow()
        custom_homepage_row.set_title("Custom Home Page")
        custom_homepage_row_radio = Gtk.CheckButton()
        custom_homepage_row.add_prefix(custom_homepage_row_radio)

        homepage_entry = Gtk.Entry()
        homepage_entry.set_hexpand(True)
        homepage_entry.set_valign(Gtk.Align.CENTER)
        homepage_entry.set_text(self.settings.get_string('custom-homepage-url'))
        homepage_entry.connect("activate", self.custom_homepage_cb)
        homepage_entry.set_placeholder_text("Enter Custom Homepage URL")
        custom_homepage_row.add_suffix(homepage_entry)

        custom_homepage_row_radio.set_group(self.default_row_radio)
        self.default_row_radio.set_active(not self.settings.get_boolean('custom-homepage'))
        custom_homepage_row_radio.set_active(self.settings.get_boolean('custom-homepage'))
        self.default_row_radio.connect("toggled", lambda _: self.change_homepage_cb())
        custom_homepage_row_radio.connect("toggled", lambda _: self.change_homepage_cb())

        homepage_group.add(defaultRow)
        homepage_group.add(custom_homepage_row)
        return homepage_group

    def change_homepage_cb(self):
        if(self.default_row_radio.get_active()):
            self.settings.set_boolean('custom-homepage', False)
        else:
            self.settings.set_boolean('custom-homepage', True)

    def custom_homepage_cb(self, entry):
        self.settings.set_boolean('custom-homepage', True)
        self.settings.set_string('custom-homepage-url', entry.get_text())
