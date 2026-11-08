from anvil import *

from ._anvil_designer import EndorseRowTemplate
from ... import state


class EndorseRow(EndorseRowTemplate):
    """An endorsement on a profile: the skill and how many walkers gave it; "+ Endorse" / "✓ Endorsed" when I may
    endorse this person. item = {e, can}; the button raises x-endorse(skill=...)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        e, d = self.item["e"], self.dom_nodes
        state.cls(d["row"], "mine", bool(e.get("mine")))
        state.text(d["skill"], e.get("skill"))
        state.text(d["count"], e.get("count", 0))
        state.show(d["btn"], bool(self.item.get("can")))
        state.text(d["btn"], "✓ Endorsed" if e.get("mine") else "+ Endorse")
        d["btn"].setAttribute("aria-label", "%s: %s" % ("Remove endorsement" if e.get("mine") else "Endorse", e.get("skill")))

    def btn_click(self, event):
        self.parent.raise_event("x-endorse", skill=self.item["e"]["skill"])
