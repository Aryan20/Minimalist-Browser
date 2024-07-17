import gi
import re

gi.require_version('Gtk', '4.0')
gi.require_version('WebKit', '6.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, WebKit, Gio, GLib

class newWebview(WebKit.WebView):
    # Enables developer settings so that inspector window can be shown
    def __init__(self, **kwargs):
        super().__init__()
        settings = self.get_settings()
        modifiedSettings = WebKit.Settings.set_enable_developer_extras(settings, True)
        self.set_settings(settings)
        self.set_vexpand(True)
        self.connect('load-failed', self.errorPrint)

    # Shows / Hides the inspector window
    def loadInspector(self):
        """
        Callback for the inspectorButton.
        Shows / Hides the inspector window
        """
        inspector = self.get_inspector()
        if(inspector.is_attached()):
            inspector.close()
        else:
            inspector.show()

    def zoomIn(self, zoomInButton, zoomOutButton):
        zoomLevel = self.get_zoom_level() + self.get_zoom_level() * 0.2 + 0.1
        if zoomLevel >= 5.0:
            zoomInButton.set_sensitive(False)
        zoomOutButton.set_sensitive(True)
        self.set_zoom_level(zoomLevel)

    def zoomOut(self, zoomOutButton, zoomInButton):
        zoomLevel = self.get_zoom_level() - self.get_zoom_level() * 0.2 - 0.1
        if zoomLevel <= 0.2:
            zoomOutButton.set_sensitive(False)
        zoomInButton.set_sensitive(True)
        self.set_zoom_level(zoomLevel)

    def loadWebPageEntryCallback(self, entry):
        url = entry.get_text()
        self.loadWebPage(url)

    def loadWebPage(self, url):
        settings = Gio.Settings(schema_id="in.aryank.MinimalistBrowser")
        regex = r"^(www\.)?[\w-]+\.[\w.]+[\w-]*$"
        scheme = GLib.Uri.peek_scheme(url)
        if not scheme:
            if re.match(regex, url):
                url = f"http://{url}"
                self.load_uri(url)
            else:
                self.load_uri(settings.get_string('search-engine').format(url=url))
        else:
            self.load_uri(url)

    # Page load request initiated.
    # Elements such as entry and progress bar among others should be updated.
    def loadChanged(self, webview, event, entry, backButton, forwardButton, tabPage):
        tabPage.set_loading(True)
        entry.set_text(self.get_uri())
        entry.set_progress_fraction(self.get_estimated_load_progress())
        forwardButton.set_sensitive(self.can_go_forward())
        backButton.set_sensitive(self.can_go_back())
        if(self.get_estimated_load_progress() >= 1):
            entry.set_progress_fraction(0)
            tabPage.set_loading(False)

    def loadHomePage(self):
        settings = Gio.Settings(schema_id="in.aryank.MinimalistBrowser")
        if(settings.get_boolean('custom-homepage')):
            self.loadWebPage(settings.get_string('custom-homepage-url'))

    def printPage(self):
        WebKit.PrintOperation.run_dialog(WebKit.PrintOperation.new(self))

    def errorPrint(self, webview, event, url, error):
        print(error.code)
        print(error.message)
        if(error.code == 1 or error.code == 0):
            self.load_alternate_html('<style>body{background-color: #242424; color:white; padding: 10px; padding-top: 30px;} h1 {text-align: center;} div{margin: auto; max-width: 550px;} p {font-size: 14;}</style><div><h1>Unable to display this website</h1>' + f'<p>The site at {url} seems to be unavailable.</p><p>It may be temporarily inaccessible or moved to a new address. You may wish to verify that your internet connection is working correctly.<p></div>', url)
        elif(error.code == 2):
            self.load_alternate_html('<style>body{background-color: #242424; color:white; padding: 10px; padding-top: 30px;} div{margin: auto; max-width: 550px;} p {font-size: 14;}</style><div><h1 style="color:coral;text-align:center;">This Connection is Not Secure</h1>' + f'<p>This does not look like the real {url}. Attackers might be trying to steal or alter information going to or from this site.<p></div>', url)