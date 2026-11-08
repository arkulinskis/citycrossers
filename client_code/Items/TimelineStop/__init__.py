from anvil import *

from ._anvil_designer import TimelineStopTemplate
from ... import state, ui


class TimelineStop(TimelineStopTemplate):
    """A stop in a walk's timeline: the walk there (km, minutes), the stop's kind, arrival time, km in, break,
    partner deal and rating; a stop that is a map place opens it (x-place(pid=...)).
    item = {stop, leg (km or None), leg_min, eta, km_in}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it, d = self.item, self.dom_nodes
        s = it["stop"]
        if it.get("leg") is not None:
            state.text(d["leg"], "🚶 %.1f km · ~%s" % (it["leg"], ui.fmt_dur(it.get("leg_min"))))
        state.show(d["leg"], it.get("leg") is not None)
        emo, kname = ui.kind(s.get("kind"))
        d["bubble"].className = "bubble " + (s.get("kind") or "")
        state.text(d["bubble"], emo)
        linked = bool(s.get("place_id"))
        state.text(d["link"], s.get("name"))
        state.text(d["name"], s.get("name"))
        state.show(d["link"], linked)
        state.show(d["name"], not linked)
        deals = s.get("deals") or []
        state.text(d["deal"], ui.deal_tag(deals[0]) if deals else "")
        state.show(d["deal"], bool(deals))
        state.text(d["rating"], "★ %s" % s["rating"] if s.get("rating") else "")
        state.show(d["rating"], bool(s.get("rating")))
        eta = it.get("eta") or ""
        km_in = " · %.1f km in" % it["km_in"] if it.get("km_in") else ""
        state.text(d["eta"], "%s%s%s" % (eta + " · " if eta else "", kname, km_in))
        brk = s.get("break_min")
        state.text(d["brk"], "%s min break" % brk if brk else "")
        state.show(d["brk"], bool(brk))
        state.text(d["note"], s.get("note"))
        state.show(d["note"], bool(s.get("note")))

    def place_click(self, event):
        event.preventDefault()
        self.parent.raise_event("x-place", pid=self.item["stop"].get("place_id"))
