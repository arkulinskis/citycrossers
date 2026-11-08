from anvil import *

from ._anvil_designer import BadgeTileTemplate
from ... import state


class BadgeTile(BadgeTileTemplate):
    """A badge on a profile (earned, or a faded "how to earn it"). item = {emoji, name, how, earned}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        b, d = self.item, self.dom_nodes
        state.cls(d["tile"], "locked", not b.get("earned"))
        d["tile"].setAttribute("title", b.get("how") or "")
        state.text(d["e"], b.get("emoji"))
        state.text(d["name"], b.get("name"))
        state.show(d["locked"], not b.get("earned"))
        state.text(d["how"], b.get("how"))
