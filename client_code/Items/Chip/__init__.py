from anvil import *

from ._anvil_designer import ChipTemplate
from ... import state


class Chip(ChipTemplate):
    """One choice in a row: a filter chip, a tab (inside .cc-tabs), a tag or skill to pick.
    item = {key, label, on, cls?, count?}: cls is the button's class ("cc-chip" by default, "" for tabs, "cc-chip orange"
    for the orange "on" colour). A click raises x-pick(key=...) on the RepeatingPanel; the page or Components/Chips
    redraws the row."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it, d = self.item, self.dom_nodes
        b = d["btn"]
        b.className = it.get("cls", "cc-chip") + (" on" if it.get("on") else "")
        b.setAttribute("aria-pressed", "true" if it.get("on") else "false")
        b.setAttribute("data-key", str(it["key"]))
        state.text(d["label"], it["label"])
        n = it.get("count")
        state.text(d["cnt"], n)
        state.show(d["cnt"], bool(n))

    def btn_click(self, event):
        self.parent.raise_event("x-pick", key=self.item["key"])
