from anvil import *

from ._anvil_designer import LevelTileTemplate
from ... import state


class LevelTile(LevelTileTemplate):
    """One of the six levels on the Perks hero (mine is lit). item = {emoji, name, at, on}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it, d = self.item, self.dom_nodes
        state.cls(d["tile"], "on", bool(it.get("on")))
        if it.get("on"):
            d["tile"].setAttribute("aria-current", "true")
        state.text(d["e"], it["emoji"])
        state.text(d["name"], it["name"])
        state.text(d["pts"], it["at"])
