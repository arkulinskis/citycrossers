from anvil import *

from ._anvil_designer import PromptTemplate
from ... import state


class Prompt(PromptTemplate):
    """A short question with a text box (the "say hi to the host" line when requesting a spot).
    Closes with the text ("" allowed), or False when cancelled."""

    def __init__(self, title="", sub="", placeholder="", yes="Send", **properties):
        super().__init__(**properties)
        self.title.text = title
        state.heading(self.title, 2)
        self.sub.text = sub
        self.text_box.placeholder = placeholder
        self.yes_button.text = yes

    @handle("yes_button", "click")
    def yes_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=self.text_box.text or "")

    @handle("no_button", "click")
    def no_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=False)

    @handle("", "show")
    def form_show(self, **event_args):
        self.text_box.focus()
