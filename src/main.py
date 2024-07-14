import sys
import gi
import threading

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib

from openai import OpenAI
from.page import newPage
from.preferences import preferences

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
        self.settings = Gio.Settings(schema_id="in.aryank.MinimalistBrowser")

    def do_activate(self):
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

        self.win = builder.get_object("main_window")
        self.win.set_application(self)
        self.win.present()
    
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