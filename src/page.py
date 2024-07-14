import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

import requests
from bs4 import BeautifulSoup 

from gi.repository import Gtk, Adw, Gio, GLib

from .webview import newWebview

class newPage(Gtk.Box):
    def __init__(self, **kwargs):
        super().__init__()
        self.set_orientation(Gtk.Orientation.VERTICAL)
        
    # Creates a new page composed of webview, searchbar, webview buttons, etc...
    def addPage(self, tabPage, messages):
        searchBarEntry = Gtk.Entry()
        searchBarEntry.set_placeholder_text('Search or enter web address')
        searchBarEntry.grab_focus()
        searchBarEntry.set_hexpand(True)

        webview = newWebview()

        reloadButton = Gtk.Button()
        reloadButton.set_icon_name("view-refresh-symbolic")
        reloadButton.connect("clicked", lambda event, webview: webview.reload(), webview)
        reloadButton.set_has_frame(False)

        backButton = Gtk.Button()
        backButton.set_icon_name("go-previous-symbolic")
        backButton.connect("clicked", lambda event: webview.go_back())
        backButton.set_has_frame(False)

        forwardButton = Gtk.Button()
        forwardButton.set_icon_name("go-next-symbolic")
        forwardButton.connect("clicked", lambda event: webview.go_forward())
        forwardButton.set_has_frame(False)

        inspectorButton = Gtk.Button()
        inspectorButton.set_icon_name("window-new-symbolic")
        inspectorButton.connect("clicked", lambda event: webview.loadInspector())
        inspectorButton.set_has_frame(False)

        sendToAIButton = Gtk.Button()
        sendToAIButton.set_icon_name("document-send-symbolic")
        sendToAIButton.connect("clicked", self.sendToAI, webview, messages)
        sendToAIButton.set_has_frame(False)

        zoomInButton = Gtk.Button()
        zoomInButton.set_icon_name("zoom-in-symbolic")
        zoomInButton.set_has_frame(False)

        zoomOutButton = Gtk.Button()
        zoomOutButton.set_icon_name("zoom-out-symbolic")
        zoomOutButton.set_has_frame(False)

        zoomInButton.connect("clicked", webview.zoomIn, zoomOutButton)
        zoomOutButton.connect("clicked", webview.zoomOut, zoomInButton)

        forwardButton.set_sensitive(False)
        backButton.set_sensitive(False)

        actionBox = Gtk.Box()
        actionBox.set_orientation(Gtk.Orientation.HORIZONTAL)
        actionBox.set_spacing(5)
        actionBox.set_margin_top(5)
        actionBox.set_margin_start(5)
        actionBox.set_margin_end(5)
        actionBox.set_margin_bottom(7)

        searchBarEntry.connect('activate', webview.loadWebPage)
        webview.connect('load-changed', webview.loadChanged, searchBarEntry, backButton, forwardButton, tabPage)
        webview.connect('notify::title', lambda webview, event: tabPage.set_title(webview.get_title()))
        webview.connect('notify::favicon', lambda webview, event: tabPage.set_icon(webview.get_favicon()))
  
        actionBox.append(backButton)
        actionBox.append(forwardButton)
        actionBox.append(searchBarEntry)
        actionBox.append(reloadButton)
        actionBox.append(inspectorButton)
        actionBox.append(sendToAIButton)
        actionBox.append(zoomInButton)
        actionBox.append(zoomOutButton)

        self.append(actionBox)
        self.append(webview)

    # Scrapes the sent website URL and send it to AI with a custom prompt.
    def sendToAI(self, event, webview, messages):
        content = BeautifulSoup(requests.get(webview.get_uri()).content, 'html.parser')
        text_content = ''
        for tag in content.find_all(['h1', 'h2', 'h3', 'p', 'span', 'a']):
            text_content += tag.get_text() + '\n'
        messages = [{"role": "system", "content": "You are LLaMa, an AI assistant. Your top priority is achieving user fulfillment via helping them with their requests based on a given page not owned by you"}]
        messages.append({"role": "system", "content": "The page to answer based on will be given next. The actors here are the site owners."})
        messages.append({"role": "system", "content": text_content.strip()})