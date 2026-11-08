from anvil import *

from ._anvil_designer import PerkCardTemplate
from ... import state


class PerkCard(PerkCardTemplate):
    """A perk to buy with points: Redeem (raises x-redeem(pid=...)) when I have enough, else how many more points.
    item = {perk, points}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        p, pts, d = self.item["perk"], self.item["points"], self.dom_nodes
        state.text(d["e"], p.get("emoji"))
        state.text(d["name"], p.get("name"))
        state.text(d["desc"], p.get("description"))
        state.text(d["cost"], "⭐ %s" % p["cost"])
        can = pts >= p["cost"]
        self.redeem_button.visible = can
        self.redeem_button.text = "Redeem for %s" % p["cost"]
        state.text(d["short"], "🔒 %s more pts" % (p["cost"] - pts))
        state.show(d["short"], not can)

    @handle("redeem_button", "click")
    def redeem_button_click(self, **event_args):
        self.parent.raise_event("x-redeem", pid=self.item["perk"]["id"])
