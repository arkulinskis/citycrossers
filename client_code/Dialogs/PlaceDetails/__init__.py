from anvil import *

from ._anvil_designer import PlaceDetailsTemplate
from ... import state, ui


class PlaceDetails(PlaceDetailsTemplate):
    """A place on the map: kind, rating, description, partner deals and public reviews. Closes with "review",
    "plan" (dialogs.place_details then opens the review or the planner) or None."""

    def __init__(self, place=None, **properties):
        super().__init__(**properties)
        p, d = place or {}, self.dom_nodes
        emo, kind_name = ui.kind(p.get("kind"))
        state.text(d["emoji"], emo)
        self.title.text = p.get("name", "") + ("  ✔" if p.get("verified") else "")
        state.heading(self.title, 2)
        state.text(d["kind"], kind_name)
        n = p.get("review_count") or 0
        state.text(d["rating"], ui.stars(p.get("avg_rating")) if n else "")
        state.text(d["count"], "(%d)" % n if n else "")
        state.text(d["desc"], p.get("description"))
        added = p.get("added_by")
        state.text(d["added"], "Added by %s" % added["name"] if added else "")
        state.show(d["added"], bool(added))
        deals = p.get("deals") or []
        self.deals_part.visible = bool(deals)
        self.deals_panel.items = [{"deal": x, "place": None, "mode": "place"} for x in deals]
        reviews = p.get("reviews") or []
        self.reviews_panel.items = [{"review": r, "mode": "place"} for r in reviews]
        self.no_reviews.visible = not reviews
        self.review_button.text = "✏️ Review again" if p.get("reviewed") else "⭐ Review"

    @handle("review_button", "click")
    def review_button_click(self, **event_args):
        self.raise_event("x-close-alert", value="review")

    @handle("plan_button", "click")
    def plan_button_click(self, **event_args):
        self.raise_event("x-close-alert", value="plan")

    @handle("close_button", "click")
    def close_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=None)
