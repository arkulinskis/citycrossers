from anvil import *

from ._anvil_designer import PillTemplate
from ... import state


class Pill(PillTemplate):
    """A small rounded label (tags, interests, shared interests). item = {text, color?} or a plain string;
    color = green, orange, sun, sky, berry, violet, dark or outline."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it = self.item if isinstance(self.item, dict) else {"text": self.item}
        el = self.dom_nodes["pill"]
        el.className = "cc-pill " + (it.get("color") or "")
        state.text(el, it.get("text"))
