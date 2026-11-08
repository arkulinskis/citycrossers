from anvil import *

from ._anvil_designer import OptionTemplate
from ... import state


class Option(OptionTemplate):
    """A big choice button: pace, who's coming, a walk to invite someone to (class "cc-option": title + line under it),
    or a vibe tile (class "cc-vibe grad-x": emoji + name). item = {key, title, sub?, emoji?, on, cls?}.
    A click raises x-pick(key=...) on the RepeatingPanel."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it, d = self.item, self.dom_nodes
        b = d["btn"]
        b.className = it.get("cls", "cc-option") + (" on" if it.get("on") else "")
        b.setAttribute("aria-pressed", "true" if it.get("on") else "false")
        b.setAttribute("data-key", str(it["key"]))
        state.text(d["emoji"], it.get("emoji"))
        state.show(d["emoji"], bool(it.get("emoji")))
        state.text(d["title"], it.get("title"))
        state.text(d["sub"], it.get("sub"))
        state.show(d["sub"], bool(it.get("sub")))

    def btn_click(self, event):
        self.parent.raise_event("x-pick", key=self.item["key"])
