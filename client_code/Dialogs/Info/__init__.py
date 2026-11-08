from anvil import *

from ._anvil_designer import InfoTemplate
from ... import router, state


class Info(InfoTemplate):
    """A message with one button (dialogs.info): an emoji, a title, a line of text, an optional code (perk codes),
    a preformatted block (a walk plan to copy) and an optional link button (text, "address")."""

    def __init__(self, title="", text="", emoji="", code="", button="OK", link=None, pre="", **properties):
        super().__init__(**properties)
        d = self.dom_nodes
        state.text(d["emoji"], emoji)
        state.show(d["emoji"], bool(emoji))
        self.title.text = title
        state.heading(self.title, 2)
        state.text(d["text"], text)
        state.show(d["text"], bool(text))
        state.text(d["code"], code)
        state.show(d["code_row"], bool(code))
        state.text(d["pre"], pre)
        state.show(d["pre"], bool(pre))
        self.ok_button.text = button
        self.link = state.loose(link)
        self.link_button.visible = bool(link)
        if link:
            self.link_button.text = link[0]

    @handle("ok_button", "click")
    def ok_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=True)

    @handle("link_button", "click")
    def link_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=None)
        router.go(self.link[1])
