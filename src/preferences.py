import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib

class preferences(Adw.PreferencesDialog):
    def __init__(self, **kwargs):
        super().__init__()
        self.settings = Gio.Settings(schema_id="in.aryank.MinimalistBrowser")
        self.createPage()

    def createPage(self):
        prefPage1 = Adw.PreferencesPage()

        searchEngineGroup = Adw.PreferencesGroup()
        searchEngineGroup.set_title("Search Engine")

        duckDuckGoRow = Adw.ActionRow()
        duckDuckGoRow.set_title("DuckDuckGo")
        self.duckDuckGoRowRadio = Gtk.CheckButton()
        duckDuckGoRow.add_prefix(self.duckDuckGoRowRadio)

        googleRow = Adw.ActionRow()
        googleRow.set_title("Google")
        self.googleRowRadio = Gtk.CheckButton()
        googleRow.add_prefix(self.googleRowRadio)

        customEngineRow = Adw.ActionRow()
        customEngineRow.set_title("Custom Search Engine")
        customEngineRowRadio = Gtk.CheckButton()
        customEngineRow.add_prefix(customEngineRowRadio)

        searchEngineEntry = Gtk.Entry()
        searchEngineEntry.set_hexpand(True)
        searchEngineEntry.set_valign(Gtk.Align.CENTER)
        searchEngineEntry.connect("activate", self.customSearchEngine)
        customEngineRow.add_suffix(searchEngineEntry)

        self.googleRowRadio.set_group(self.duckDuckGoRowRadio)
        customEngineRowRadio.set_group(self.googleRowRadio)
        self.duckDuckGoRowRadio.connect("toggled", lambda _: self.changeEngine())
        self.googleRowRadio.connect("toggled", lambda _: self.changeEngine())

        self.duckDuckGoRowRadio.set_active(self.settings.get_boolean('search-engine-duck'))
        self.googleRowRadio.set_active(self.settings.get_boolean('search-engine-google'))
        if(self.settings.get_boolean('search-engine-custom')):
            customEngineRowRadio.set_active(True)
            searchEngineEntry.set_text(self.settings.get_string('search-engine'))

        searchEngineGroup.add(duckDuckGoRow)
        searchEngineGroup.add(googleRow)
        searchEngineGroup.add(customEngineRow)
        prefPage1.add(searchEngineGroup)
        self.add(prefPage1)
        self.present()

    def changeEngine(self):
        self.settings.set_boolean('search-engine-custom', False)
        self.settings.set_boolean('search-engine-duck', False)
        self.settings.set_boolean('search-engine-google', False)
        if(self.googleRowRadio.get_active()):
            self.settings.set_string('search-engine', "https://www.google.com/search?q={url}")
            self.settings.set_boolean('search-engine-google', True)
        elif(self.duckDuckGoRowRadio.get_active()):
            self.settings.set_string('search-engine', "https://www.duckduckgo.com/?q={url}")
            self.settings.set_boolean('search-engine-duck', True)
            

    def customSearchEngine(self, entry):
        self.settings.set_boolean('search-engine-duck', False)
        self.settings.set_boolean('search-engine-google', False)
        self.settings.set_boolean('search-engine-custom', True)

        self.settings.set_string('search-engine', entry.get_text())