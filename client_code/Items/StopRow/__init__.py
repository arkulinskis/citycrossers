from anvil import *

from ._anvil_designer import StopRowTemplate
from ... import state, ui


class StopRow(StopRowTemplate):
    """A stop on the route being planned: its number, kind, break and distance from the last stop, with
    edit / up / down / remove. item = {i, stop, leg}; buttons raise x-stop(action=..., i=...)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it, d = self.item, self.dom_nodes
        s, i = it["stop"], it["i"]
        emo, kname = ui.kind(s.get("kind"))
        brk = ui.BREAK_MIN.get(s.get("kind"), 0)
        state.text(d["n"], i + 1)
        state.text(d["e"], emo)
        state.text(d["name"], s.get("name"))
        sub = kname + (" · %d min break" % brk if brk else "")
        if it.get("leg") is not None:
            sub += " · %.1f km from last stop" % it["leg"]
        state.text(d["sub"], sub)
        name = s.get("name") or "stop"
        for key, label in (("edit", "Edit %s"), ("up", "Move %s up"), ("down", "Move %s down"), ("del", "Remove %s")):
            d[key].setAttribute("aria-label", label % name)

    def _raise(self, action):
        self.parent.raise_event("x-stop", action=action, i=self.item["i"])

    def edit_click(self, event):
        self._raise("edit")

    def up_click(self, event):
        self._raise("up")

    def down_click(self, event):
        self._raise("down")

    def del_click(self, event):
        self._raise("del")
