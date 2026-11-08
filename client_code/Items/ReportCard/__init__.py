from anvil import *

from ._anvil_designer import ReportCardTemplate
from ... import state, ui


class ReportCard(ReportCardTemplate):
    """A safety report for admins: the reason, who reported whom (or which walk), the details; Mark resolved /
    Re-open raises x-resolve(rid=...). item = a report from admin_overview."""

    def __init__(self, **properties):
        super().__init__(**properties)
        r, d = self.item, self.dom_nodes
        is_open = r.get("status") == "open"
        d["card"].className = "cc-card " + ("tint-berry" if is_open else "flat")
        state.text(d["reason"], "🚩 " + (r.get("reason") or ""))
        d["status"].className = "cc-pill " + ("orange" if is_open else "green")
        state.text(d["status"], r.get("status"))
        state.text(d["when"], ui.ago(r.get("created")))
        rep = r.get("reporter") or {}
        state.text(d["reporter"], rep.get("name", "someone"))
        state.href(d["reporter"], "#u/%s" % rep.get("id", ""))
        who = r.get("reported_user")
        self.who_part.visible = bool(who)
        self.profile_link.visible = bool(who)
        if who:
            self.who.show(who, size=36)
            state.set_attr(self.profile_link, "href", "#u/%s" % who["id"])
        walk = r.get("walk")
        state.show(d["walk_row"], bool(walk))
        if walk:
            state.text(d["walk"], walk.get("title"))
            state.href(d["walk"], "#walk/%s" % walk["id"])
        state.text(d["details"], r.get("details") or "No details given.")
        state.cls(d["details"], "muted", not r.get("details"))
        self.resolve_button.text = "Mark resolved" if is_open else "Re-open"
        self.resolve_button.role = ["cc-btn", "sm"] if is_open else ["cc-btn", "ghost", "sm"]

    @handle("resolve_button", "click")
    def resolve_button_click(self, **event_args):
        self.parent.raise_event("x-resolve", rid=self.item["id"])
