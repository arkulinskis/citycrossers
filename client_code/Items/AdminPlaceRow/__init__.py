from anvil import *

from ._anvil_designer import AdminPlaceRowTemplate
from ... import state, ui


class AdminPlaceRow(AdminPlaceRowTemplate):
    """A place on the map, for admins: kind, rating, deal badge; Verify, + Deal, ✕.
    item = {place, deal}; buttons raise x-place(action=..., pid=...)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        p, d = self.item["place"], self.dom_nodes
        emo, kname = ui.kind(p.get("kind"))
        state.text(d["name"], "%s %s" % (emo, p.get("name")))
        state.text(d["desc"], (p.get("description") or "")[:70])
        state.text(d["kind"], kname)
        state.text(d["rating"], "★ %s (%s)" % (p["avg_rating"], p["review_count"]) if p.get("review_count") else "—")
        state.text(d["deal"], "🏷️" if self.item.get("deal") else "")
        self.verify_button.text = "✔ Verified" if p.get("verified") else "Verify"
        self.verify_button.role = ["cc-btn", "soft" if p.get("verified") else "ghost", "sm"]
        state.set_control_attr(self.delete_button, "aria-label", "Delete %s" % p.get("name"))

    def _raise(self, action):
        self.parent.raise_event("x-place", action=action, pid=self.item["place"]["id"])

    @handle("verify_button", "click")
    def verify_button_click(self, **event_args):
        self._raise("verify")

    @handle("deal_button", "click")
    def deal_button_click(self, **event_args):
        self._raise("deal")

    @handle("delete_button", "click")
    def delete_button_click(self, **event_args):
        self._raise("delete")
