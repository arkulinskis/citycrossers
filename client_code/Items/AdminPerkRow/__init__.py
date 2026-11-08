from anvil import *

from ._anvil_designer import AdminPerkRowTemplate
from ... import state


class AdminPerkRow(AdminPerkRowTemplate):
    """A perk in the catalog for admins (cost, on/off); Edit raises x-perk(pid=...)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        p, d = self.item, self.dom_nodes
        state.text(d["name"], "%s %s" % (p.get("emoji") or "", p.get("name")))
        state.text(d["desc"], p.get("description"))
        state.text(d["cost"], "⭐ %s" % p.get("cost"))
        d["status"].className = "cc-pill " + ("green" if p.get("active") else "")
        state.text(d["status"], "Active" if p.get("active") else "Off")
        state.set_control_attr(self.edit_button, "aria-label", "Edit %s" % p.get("name"))

    @handle("edit_button", "click")
    def edit_button_click(self, **event_args):
        self.parent.raise_event("x-perk", pid=self.item["id"])
