import sys
import gi
import threading

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib, Gdk

from openai import OpenAI
from .page import NewPage
from .preferences import Preferences

from .utils import *
from .history_manager import *

client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key = "sk-no-key-required"
)

class MinimalistbrowserApplication(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(application_id='in.aryank.MinimalistBrowser',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action('about', self.on_about_action_cb)
        self.create_action('preferences', self.on_preferences_action_cb)
        self.create_action('history', self.on_history_action_cb)
        self.settings = Gio.Settings(schema_id="in.aryank.MinimalistBrowser")

    def do_activate(self):
        # Create a Builder
        builder = Gtk.Builder()
        builder.add_from_resource("/in/aryank/MinimalistBrowser/web_sidebar.ui")

        self.tab_view = builder.get_object("tab_view")
        self.button_new_tab = builder.get_object("button_new_tab")
        self.overview = builder.get_object("overview")
        self.button_overview = builder.get_object("button_overview")
        self.ai_response_list = builder.get_object("ai_response_list")

        self.ai_entry = builder.get_object("ai_entry")
        self.ai_progress_bar = builder.get_object("ai_progress_bar")

        self.initialise_ai()

        self.ai_entry.connect("activate", self.openai_create_cb)
        self.overview.connect("create-tab", lambda _: self.add_page())
        self.button_overview.connect("clicked", lambda _: self.overview.set_open(True))
        self.button_new_tab.connect("clicked", lambda _: self.add_page())

        self.add_page()

        self.win = builder.get_object("main_window")
        self.win.set_application(self)
        self.win.present()
        check_db_exists()
    
    def add_page(self):
        page = NewPage()
        tab_page = self.tab_view.append(page)
        tab_page.set_title("New Page")
        tab_page.set_live_thumbnail(True)
        page.add_page(tab_page, self.messages)

    # Creates the about section window
    def on_about_action_cb(self, widget, _):
        """Callback for the app.about action."""
        about = Adw.AboutWindow(transient_for=self.props.active_window,
                                application_name='Minimalist Browser',
                                application_icon='in.aryank.MinimalistBrowser',
                                developer_name='Aryan Kaushik',
                                version='0.1.0',
                                developers=['Aryan Kaushik'],
                                website='www.aryank.in',
                                copyright='MIT © 2024 Aryan Kaushik')
        about.present()

    def on_preferences_action_cb(self, widget, _):
        preferences_dialog = Preferences()
        preferences_dialog.present()

    def on_history_action_cb(self, widget, _):
        builder = Gtk.Builder()
        builder.add_from_resource("/in/aryank/MinimalistBrowser/history_dialog.ui")
        list_box = builder.get_object("listbox")

        statement = "SELECT * from urls ORDER BY last_visit_time DESC"
        rows = execute_search(statement)
        if(len(rows) > 0):
            for row in rows:
                action_row = Adw.ActionRow()
                action_row.set_use_markup(False)
                action_row.set_title(row[2])
                action_row.set_subtitle(row[1])
                action_row.set_subtitle_lines(1)
                action_row.set_activatable(True)
                copy_button = create_action_button('edit-copy')
                copy_button.connect('clicked', self.copy_history_url_cb, action_row)
                action_row.add_suffix(copy_button)
                list_box.append(action_row)
            list_box.connect("row-activated", self.history_row_activated_cb)
        else:
            history_stack = builder.get_object("history_presentation_stack")
            status_page = builder.get_object("empty_history_message")
            history_stack.set_visible_child(status_page)
        dialog = builder.get_object("dialog")
        dialog.present()

    def history_row_activated_cb(self, listbox, actionrow): 
        page = NewPage()
        tab_page = self.tab_view.append(page)
        tab_page.set_live_thumbnail(True)
        page.add_page(tab_page, self.messages, url=actionrow.get_subtitle())

    def copy_history_url_cb(self, button, action_row):
        Gdk.Clipboard.set(
            Gdk.Display.get_clipboard(Gdk.Display.get_default()), 
            action_row.get_subtitle())

    def create_action(self, name, callback, shortcuts=None):
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

    def openai_create_cb(self, entry):
        prompt = entry.get_text()
        entry.set_text("")
        self.prompt = prompt
        self.ai_response_received = False
        self.messages.append({"role": "user", "content": prompt})
        self.ai_response_display(prompt, "User ->")
        thread = threading.Thread(target=self.llama_io)
        thread.start()

    def llama_io(self):
        response = client.chat.completions.create(
            model="LLaMA_CPP",
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in self.messages
            ]
        )
        self.ai_response_received = True
        response = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": response})
        self.ai_response_display(response, "Assistant ->")
    
    def ai_response_display(self, message, role):
        # Show / Hide the progress bar based on current state of bot.
        self.ai_progress_bar.set_visible(not self.ai_response_received)
        self.pulse_progress()

        # Display the message by AI and User.
        self.ai_response_list.prepend(AiMessageFrame(role=role, message=message))

    def pulse_progress(self):
        def on_pulse():
            if self.ai_response_received:
                self.ai_progress_bar.set_fraction(0)
                return False

            self.ai_progress_bar.pulse()
            return True
        
        pulse_period = 500
        GLib.timeout_add(pulse_period, on_pulse)

    def initialise_ai(self):
        self.messages = [{"role": "system", "content": "You are Minimalist AI, an AI assistant based on LLaMa. Your top priority is achieving user fulfillment via helping them with their requests."}]
        self.ai_response_received = True

class AiMessageFrame(Gtk.Frame):
    def __init__(self, **kwargs):
        super().__init__()
        response_box = Gtk.Box()
        response_label = Gtk.Label()

        self.set_label(kwargs["role"])
        self.set_margin_end(3)
        self.set_margin_start(3)

        response_label.set_margin_top(10)
        response_label.set_margin_bottom(5)
        response_label.set_margin_start(5)
        response_label.set_margin_end(5)
        
        response_label.set_label(kwargs["message"])
        response_label.set_wrap(True)

        response_box.append(response_label)
        self.set_child(response_box)


def main(version):
    """The application's entry point."""
    app = MinimalistbrowserApplication()
    return app.run(sys.argv)