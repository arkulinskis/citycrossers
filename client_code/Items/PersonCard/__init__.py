from anvil import *

from ._anvil_designer import PersonCardTemplate
from ... import state, ui


class PersonCard(PersonCardTemplate):
    """A walker card (Discover's "Walkers to meet", the People page). item = {p, mode}:
    "suggest" (View + Connect, shared interests), "search" (View + Connected / Requested / Accept / Connect by
    relationship), "incoming" (Ignore + Accept), "friend" (View + Plan a walk).
    Buttons raise x-person(action="connect" | "accept" | "reject", uid=...)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        p, mode, d = self.item["p"], self.item.get("mode", "suggest"), self.dom_nodes
        d["banner"].className = "banner " + ui.banner_of(p["id"])
        self.av.show(p, 76)
        state.text(d["name"], p.get("name"))
        state.href(d["name"], "#u/%s" % p["id"])
        state.show(d["ver"], bool(p.get("verified")))
        state.text(d["headline"], p.get("headline") or "New walker, say hi!")
        pace = ui.pace_of(p.get("pace"))
        lvl = p.get("level") or {}
        pills = []
        if p.get("match"):
            pills.append({"text": "%s%% match" % p["match"], "color": "dark"})
        pills.append({"text": "%s %s" % (lvl.get("emoji", "🚶"), lvl.get("name", "Stroller")), "color": "sun"})
        pills.append({"text": "%s %s" % (pace[0], pace[1])})
        self.pills_panel.items = pills
        if mode == "suggest":
            stats = "%s walked · %s walks · %s people met" % (ui.km(p.get("km_total")), p.get("walks_count", 0),
                                                              p.get("people_met", 0))
        else:
            stats = "%s · %s walks%s" % (ui.km(p.get("km_total")), p.get("walks_count", 0),
                                         (" · " + p["city"]) if p.get("city") else "")
        state.text(d["stats"], stats)
        extra = []
        top = p.get("top_endorsement")
        if top:
            extra.append({"text": "%s ×%s" % (top["skill"], top["count"]), "color": "violet"})
        if mode == "suggest":
            extra += [{"text": s, "color": "green"} for s in (p.get("shared") or [])[:3]]
        self.extra_panel.items = extra
        state.set_attr(self.view_link, "href", "#u/%s" % p["id"])
        rel = p.get("relationship")
        self.view_link.visible = mode != "incoming"
        self.plan_link.visible = mode == "friend"
        self.connected_pill.visible = mode == "search" and rel == "friends"
        self.requested_pill.visible = mode == "search" and rel == "pending_out"
        self.ignore_button.visible = mode == "incoming"
        self.accept_button.visible = mode == "incoming" or (mode == "search" and rel == "pending_in")
        self.connect_button.visible = mode == "suggest" or (mode == "search" and rel not in ("friends", "pending_out", "pending_in"))

    def _raise(self, action):
        self.parent.raise_event("x-person", action=action, uid=self.item["p"]["id"])

    @handle("connect_button", "click")
    def connect_button_click(self, **event_args):
        self._raise("connect")

    @handle("accept_button", "click")
    def accept_button_click(self, **event_args):
        self._raise("accept")

    @handle("ignore_button", "click")
    def ignore_button_click(self, **event_args):
        self._raise("reject")
