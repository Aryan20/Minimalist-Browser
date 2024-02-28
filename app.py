import sys
import gi
import threading
gi.require_version('Gtk', '4.0')
gi.require_version('WebKit', '6.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, WebKit, Gio, GLib

import requests
from bs4 import BeautifulSoup 

from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key = "sk-no-key-required"
)

class MyApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        # Create a Builder
        builder = Gtk.Builder()
        builder.add_from_file("web_sidebar.ui")

        self.tab_view = builder.get_object("tab_view")
        self.button_new_tab = builder.get_object("button_new_tab")
        self.overview = builder.get_object("overview")
        self.button_overview = builder.get_object("button_overview")
        self.aiResponseList = builder.get_object("aiResponseList")

        self.aiEntry = builder.get_object("aiEntry")
        self.aiProgressBar = builder.get_object("aiProgressBar")

        self.initialiseAI()

        self.aiEntry.connect("activate", self.openaiCreate)
        self.overview.connect("create-tab", lambda _: self.addPage())
        self.button_overview.connect("clicked", lambda _: self.overview.set_open(True))
        self.button_new_tab.connect("clicked", lambda _: self.addPage())

        self.addPage()

        self.createAction('about', self.onAboutAction)

        self.win = builder.get_object("main_window")
        self.win.set_application(self)
        self.win.present()

    def loadWebPage(self, entry, webview):
        url = entry.get_text()
        scheme = GLib.Uri.peek_scheme(url)
        if not scheme:
            url = f"http://{url}"
        webview.load_uri(url)

    # Page load request initiated.
    # Elements such as entry and progress bar among others should be updated.
    def loadChanged(self, webview, event, entry, backButton, forwardButton, tabPage):
        tabPage.set_loading(True)
        entry.set_text(webview.get_uri())
        entry.set_progress_fraction(webview.get_estimated_load_progress())
        forwardButton.set_sensitive(webview.can_go_forward())
        backButton.set_sensitive(webview.can_go_back())
        if(webview.get_estimated_load_progress() >= 1):
            entry.set_progress_fraction(0)
            tabPage.set_loading(False)

    def reloadPage(self, event, webview):
        webview.reload()

    # Creates a new page composed of webview, searchbar, webview buttons, etc...
    def addPage(self):
        box = Gtk.Box()
        box.set_orientation(Gtk.Orientation.VERTICAL)

        tabPage = self.tab_view.append(box)
        tabPage.set_title("New Page")
        tabPage.set_live_thumbnail(True)

        searchBarEntry = Gtk.Entry()
        searchBarEntry.set_placeholder_text('Enter the URL here.')
        searchBarEntry.grab_focus()
        searchBarEntry.set_hexpand(True)

        webview = WebKit.WebView.new()
        webview.set_vexpand(True)

        reloadButton = Gtk.Button()
        reloadButton.set_icon_name("view-refresh-symbolic")
        reloadButton.connect("clicked", self.reloadPage, webview)
        reloadButton.set_has_frame(False)

        backButton = Gtk.Button()
        backButton.set_icon_name("go-previous-symbolic")
        backButton.connect("clicked", self.goBack, webview)
        backButton.set_has_frame(False)

        forwardButton = Gtk.Button()
        forwardButton.set_icon_name("go-next-symbolic")
        forwardButton.connect("clicked", self.goForward, webview)
        forwardButton.set_has_frame(False)

        inspectorButton = Gtk.Button()
        inspectorButton.set_icon_name("window-new-symbolic")
        inspectorButton.connect("clicked", self.loadInspector, webview)
        inspectorButton.set_has_frame(False)

        sendToAIButton = Gtk.Button()
        sendToAIButton.set_icon_name("document-send-symbolic")
        sendToAIButton.connect("clicked", self.sendToAI, webview)
        sendToAIButton.set_has_frame(False)

        zoomInButton = Gtk.Button()
        zoomInButton.set_icon_name("zoom-in-symbolic")
        zoomInButton.set_has_frame(False)

        zoomOutButton = Gtk.Button()
        zoomOutButton.set_icon_name("zoom-out-symbolic")
        zoomOutButton.set_has_frame(False)

        zoomInButton.connect("clicked", self.zoomIn, webview, zoomOutButton)
        zoomOutButton.connect("clicked", self.zoomOut, webview, zoomInButton)

        forwardButton.set_sensitive(False)
        backButton.set_sensitive(False)

        actionBox = Gtk.Box()
        actionBox.set_orientation(Gtk.Orientation.HORIZONTAL)
        actionBox.set_spacing(5)
        actionBox.set_margin_top(5)
        actionBox.set_margin_start(5)
        actionBox.set_margin_end(5)
        actionBox.set_margin_bottom(7)

        searchBarEntry.connect('activate', self.loadWebPage, webview)
        webview.connect('load-changed', self.loadChanged, searchBarEntry, backButton, forwardButton, tabPage)
        webview.connect('notify::title', lambda webview, event: tabPage.set_title(webview.get_title()))
        # webview.connect('notify::favicon', lambda webview, event: tabPage.set_icon(webview.get_favicon()))
  
        actionBox.append(backButton)
        actionBox.append(forwardButton)
        actionBox.append(searchBarEntry)
        actionBox.append(reloadButton)
        actionBox.append(inspectorButton)
        actionBox.append(sendToAIButton)
        actionBox.append(zoomInButton)
        actionBox.append(zoomOutButton)

        box.append(actionBox)
        box.append(webview)

        self.webKitModify(webview)
        
        return tabPage

    def zoomIn(self, zoomInButton, webview, zoomOutButton):
        zoomLevel = webview.get_zoom_level() + webview.get_zoom_level() * 0.2 + 0.1
        if zoomLevel >= 5.0:
            zoomInButton.set_sensitive(False)
        zoomOutButton.set_sensitive(True)
        webview.set_zoom_level(zoomLevel)

    def zoomOut(self, zoomOutButton, webview, zoomInButton):
        zoomLevel = webview.get_zoom_level() - webview.get_zoom_level() * 0.2 - 0.1
        if zoomLevel <= 0.2:
            zoomOutButton.set_sensitive(False)
        zoomInButton.set_sensitive(True)
        webview.set_zoom_level(zoomLevel)

    # Enables developer settings so that inspector window can be shown
    def webKitModify(self, webview):
        settings = webview.get_settings()
        modifiedSettings = WebKit.Settings.set_enable_developer_extras(settings, True)
        webview.set_settings(settings)

    # Shows / Hides the inspector window
    def loadInspector(self, event, webview):
        """
        Callback for the inspectorButton.
        Shows / Hides the inspector window
        """
        inspector = webview.get_inspector()
        if(inspector.is_attached()):
            inspector.close()
        else:
            inspector.show()

    def goBack(self, event, webview):
        """Callback for the backButton"""
        webview.go_back()
    
    def goForward(self, event, webview):
        """Callback for the forwardButton"""
        webview.go_forward()
    
    # Creates the about section window
    def onAboutAction(self, widget, _):
        """Callback for the app.about action."""
        about = Adw.AboutWindow(transient_for=self.props.active_window,
                                application_name='Minimalist Browser',
                                application_icon='security-medium-symbolic',
                                developer_name='Aryan Kaushik',
                                version='0.1.0',
                                developers=['Aryan Kaushik'],
                                website='www.aryank.in',
                                copyright='MIT © 2024 Aryan Kaushik')
        about.present()

    def createAction(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)

    def openaiCreate(self, entry):
        prompt = entry.get_text()
        entry.set_text("")
        self.prompt = prompt
        self.responseReceived = False
        self.messages.append({"role": "user", "content": prompt})
        self.aiResponseDisplay(prompt, "User ->")
        thread = threading.Thread(target=self.llamaIO)
        thread.start()

    def llamaIO(self):
        response = client.chat.completions.create(
            model="LLaMA_CPP",
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in self.messages
            ]
        )
        self.responseReceived = True
        response = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": response})
        self.aiResponseDisplay(response, "Assistant ->")
    
    def aiResponseDisplay(self, message, role):
        # Show / Hide the progress bar based on current state of bot.
        self.aiProgressBar.set_visible(not self.responseReceived)
        self.pulseProgress()

        frame = Gtk.Frame()
        responseBox = Gtk.Box()
        responseLabel = Gtk.Label()

        frame.set_label(role)
        frame.set_margin_end(3)
        frame.set_margin_start(3)

        responseLabel.set_margin_top(10)
        responseLabel.set_margin_bottom(5)
        responseLabel.set_margin_start(5)
        responseLabel.set_margin_end(5)
        
        responseLabel.set_label(message)
        responseLabel.set_wrap(True)

        responseBox.append(responseLabel)
        frame.set_child(responseBox)

        # Display the message by AI and User.
        self.aiResponseList.prepend(frame)

    def pulseProgress(self):
        def onPulse():
            if self.responseReceived:
                self.aiProgressBar.set_fraction(0)
                return False

            self.aiProgressBar.pulse()
            return True
        
        pulse_period = 500
        GLib.timeout_add(pulse_period, onPulse)

    # Scrapes the sent website URL and send it to AI with a custom prompt.
    def sendToAI(self, event, webview):
        content = BeautifulSoup(requests.get(webview.get_uri()).content, 'html.parser')
        text_content = ''
        for tag in content.find_all(['h1', 'h2', 'h3', 'p', 'span', 'a']):
            text_content += tag.get_text() + '\n'
        self.messages = [{"role": "system", "content": "You are LLaMa, an AI assistant. Your top priority is achieving user fulfillment via helping them with their requests based on a given page not owned by you"}]
        self.messages.append({"role": "system", "content": "The page to answer based on will be given next. The actors here are the site owners."})
        self.messages.append({"role": "system", "content": text_content.strip()})

    def initialiseAI(self):
        self.messages = [{"role": "system", "content": "You are Minimalist AI, an AI assistant based on LLaMa. Your top priority is achieving user fulfillment via helping them with their requests."}]
        self.responseReceived = True


app = MyApp(application_id="in.aryank.MinimalistBrowser")
app.run(sys.argv)