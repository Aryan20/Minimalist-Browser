import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

import requests
from bs4 import BeautifulSoup 

from gi.repository import Gtk, Adw, Gio, GLib

from .webview import NewWebView
from .utils import create_action_button

class NewPage(Gtk.Box):
    def __init__(self, **kwargs):
        super().__init__()
        self.set_orientation(Gtk.Orientation.VERTICAL)
        
    # Creates a new page composed of webview, searchbar, webview buttons, etc...
    def add_page(self, tab_page, messages, **kwargs):
        search_bar_entry = Gtk.Entry()
        search_bar_entry.set_placeholder_text('Search or enter web address')
        search_bar_entry.grab_focus()
        search_bar_entry.set_hexpand(True)

        webview = NewWebView()

        reloadButton = create_action_button("view-refresh-symbolic")
        reloadButton.connect("clicked", lambda event, webview: webview.reload(), webview)
        back_button = create_action_button("go-previous-symbolic")
        back_button.connect("clicked", lambda event: webview.go_back())
        forward_button = create_action_button("go-next-symbolic")
        forward_button.connect("clicked", lambda event: webview.go_forward())
        inspector_button = create_action_button("window-new-symbolic")
        inspector_button.connect("clicked", lambda event: webview.load_inspector_cb())
        send_to_ai_button = create_action_button("document-send-symbolic")
        send_to_ai_button.connect("clicked", self.send_page_content_to_ai, webview, messages)
        print_page_button = create_action_button("document-print")
        print_page_button.connect("clicked", lambda event: webview.print_page_cb())
        zoom_in_button = create_action_button("zoom-in-symbolic")
        zoom_out_button = create_action_button("zoom-out-symbolic")
        zoom_in_button.connect("clicked", webview.zoom_in, zoom_out_button)
        zoom_out_button.connect("clicked", webview.zoom_out, zoom_in_button)

        forward_button.set_sensitive(False)
        back_button.set_sensitive(False)

        action_box = Gtk.Box()
        action_box.set_orientation(Gtk.Orientation.HORIZONTAL)
        action_box.set_spacing(5)
        action_box.set_margin_top(5)
        action_box.set_margin_start(5)
        action_box.set_margin_end(5)
        action_box.set_margin_bottom(7)

        search_bar_entry.connect('activate', webview.load_webpage_entry_cb)
        webview.connect('load-changed', webview.load_changed_cb, search_bar_entry, back_button, forward_button, tab_page)
        webview.connect('notify::title', lambda webview, event: tab_page.set_title(webview.get_title()))
        webview.connect('notify::favicon', lambda webview, event: tab_page.set_icon(webview.get_favicon()))
  
        action_box.append(back_button)
        action_box.append(forward_button)
        action_box.append(search_bar_entry)
        action_box.append(reloadButton)
        action_box.append(inspector_button)
        action_box.append(send_to_ai_button)
        action_box.append(print_page_button)
        action_box.append(zoom_in_button)
        action_box.append(zoom_out_button)

        self.append(action_box)
        self.append(webview)
        if(len(kwargs) > 0 and kwargs['url']):
            webview.load_uri(kwargs['url'])
        else:
            webview.load_home_page()

    # Scrapes the sent website URL and send it to AI with a custom prompt.
    def send_page_content_to_ai(self, event, webview, messages):
        content = BeautifulSoup(requests.get(webview.get_uri()).content, 'html.parser')
        text_content = ''
        for tag in content.find_all(['h1', 'h2', 'h3', 'p', 'span', 'a']):
            text_content += tag.get_text() + '\n'
        messages = [{"role": "system", "content": "You are LLaMa, an AI assistant. Your top priority is achieving user fulfillment via helping them with their requests based on a given page not owned by you"}]
        messages.append({"role": "system", "content": "The page to answer based on will be given next. The actors here are the site owners."})
        messages.append({"role": "system", "content": text_content.strip()})