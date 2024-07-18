import sys
import gi
import threading

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib, Gdk

from openai import OpenAI
from.page import newPage
from.preferences import preferences

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
        self.createAction('quit', lambda *_: self.quit(), ['<primary>q'])
        self.createAction('about', self.onAboutAction)
        self.createAction('preferences', self.onPreferencesAction)
        self.createAction('history', self.onHistoryAction)
        self.settings = Gio.Settings(schema_id="in.aryank.MinimalistBrowser")

    def do_activate(self):
        # Create a Builder
        builder = Gtk.Builder()
        builder.add_from_resource("/in/aryank/MinimalistBrowser/web_sidebar.ui")

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

        self.win = builder.get_object("main_window")
        self.win.set_application(self)
        self.win.present()
        check_db_exists()
    
    def addPage(self):
        page = newPage()
        tabPage = self.tab_view.append(page)
        tabPage.set_title("New Page")
        tabPage.set_live_thumbnail(True)
        page.addPage(tabPage, self.messages)

    # Creates the about section window
    def onAboutAction(self, widget, _):
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

    def onPreferencesAction(self, widget, _):
        preferencesDialog = preferences()
        preferencesDialog.present()

    def onHistoryAction(self, widget, _):
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
                copy_button = createActionButton('edit-copy')
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
        page = newPage()
        tabPage = self.tab_view.append(page)
        tabPage.set_live_thumbnail(True)
        page.addPage(tabPage, self.messages, url=actionrow.get_subtitle())

    def copy_history_url_cb(self, button, action_row):
        Gdk.Clipboard.set(
            Gdk.Display.get_clipboard(Gdk.Display.get_default()), 
            action_row.get_subtitle())

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

        # Display the message by AI and User.
        self.aiResponseList.prepend(aiMessageFrame(role=role, message=message))

    def pulseProgress(self):
        def onPulse():
            if self.responseReceived:
                self.aiProgressBar.set_fraction(0)
                return False

            self.aiProgressBar.pulse()
            return True
        
        pulse_period = 500
        GLib.timeout_add(pulse_period, onPulse)

    def initialiseAI(self):
        self.messages = [{"role": "system", "content": "You are Minimalist AI, an AI assistant based on LLaMa. Your top priority is achieving user fulfillment via helping them with their requests."}]
        self.responseReceived = True

class aiMessageFrame(Gtk.Frame):
    def __init__(self, **kwargs):
        super().__init__()
        responseBox = Gtk.Box()
        responseLabel = Gtk.Label()

        self.set_label(kwargs["role"])
        self.set_margin_end(3)
        self.set_margin_start(3)

        responseLabel.set_margin_top(10)
        responseLabel.set_margin_bottom(5)
        responseLabel.set_margin_start(5)
        responseLabel.set_margin_end(5)
        
        responseLabel.set_label(kwargs["message"])
        responseLabel.set_wrap(True)

        responseBox.append(responseLabel)
        self.set_child(responseBox)


def main(version):
    """The application's entry point."""
    app = MinimalistbrowserApplication()
    return app.run(sys.argv)