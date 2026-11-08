import datetime

from anvil import *

from ._anvil_designer import AdminDealRowTemplate
from ... import state, ui


class AdminDealRow(AdminDealRowTemplate):
    """A partner deal in the admin list: headline, place, %, code, end date, Live / Paused / Expired; Edit, Pause or
    Activate, ✕. item = a deal from admin_overview; buttons raise x-deal(action=..., did=...)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        x, d = self.item, self.dom_nodes
        p = x.get("place") or {}
        state.text(d["title"], x.get("title"))
        state.text(d["desc"], (x.get("description") or "")[:80])
        state.text(d["place"], "%s %s" % (ui.emoji(p.get("kind")), p.get("name", "?")))
        state.text(d["pct"], "%s%%" % x["percent"] if x.get("percent") else "—")
        state.text(d["code"], x.get("code"))
        state.show(d["code"], bool(x.get("code")))
        state.show(d["nocode"], not x.get("code"))
        state.text(d["until"], ui.fmt_date(x["valid_until"], True) if x.get("valid_until") else "No end")
        expired = bool(x.get("valid_until") and x["valid_until"] < datetime.date.today())
        status, color = ("Expired", "") if expired else (("Live", "green") if x.get("active") else ("Paused", ""))
        d["status"].className = "cc-pill " + color
        state.text(d["status"], status)
        self.toggle_button.text = "Pause" if x.get("active") else "Activate"
        state.set_control_attr(self.delete_button, "aria-label", "Delete deal %s" % x.get("title"))

    def _raise(self, action):
        self.parent.raise_event("x-deal", action=action, did=self.item["id"])

    @handle("edit_button", "click")
    def edit_button_click(self, **event_args):
        self._raise("edit")

    @handle("toggle_button", "click")
    def toggle_button_click(self, **event_args):
        self._raise("toggle")

    @handle("delete_button", "click")
    def delete_button_click(self, **event_args):
        self._raise("delete")
