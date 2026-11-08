from anvil import *

from ._anvil_designer import DealCardTemplate
from ... import state, ui


class DealCard(DealCardTemplate):
    """A partner deal. item = {deal, place, mode}: mode "map" (map page: opens the place), "perks" (orange, with the
    code and end date: opens the place) or "place" (inside the place dialog: flat, not clickable).
    A click raises x-place(pid=...)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it, d = self.item, self.dom_nodes
        deal, place, mode = it["deal"], it.get("place") or {}, it.get("mode", "map")
        card = d["card"]
        state.cls(card, "tint-orange", mode != "map")
        state.cls(card, "flat", mode == "place")
        self.clickable = mode != "place" and bool(place.get("id"))
        state.cls(card, "cc-clickable", self.clickable)
        if self.clickable:
            card.setAttribute("role", "button")
            card.setAttribute("tabindex", "0")
        state.text(d["tag"], ui.deal_tag(deal))
        state.text(d["place"], "%s %s" % (ui.emoji(place.get("kind")), place.get("name", "")) if place.get("name") else "")
        state.text(d["title"], deal.get("title"))
        state.text(d["desc"], deal.get("description"))
        code = deal.get("code") if mode != "map" else None
        state.text(d["code"], code)
        state.show(d["code_row"], bool(code))
        until = deal.get("valid_until") if mode == "perks" else None
        state.text(d["until"], "Until %s" % ui.fmt_date(until, True) if until else "")
        state.show(d["until"], bool(until))

    def card_click(self, event):
        if self.clickable:
            self.parent.raise_event("x-place", pid=(self.item.get("place") or {}).get("id"))

    def card_key(self, event):
        if event.key in ("Enter", " "):
            event.preventDefault()
            self.card_click(event)
