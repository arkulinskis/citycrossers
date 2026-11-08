from anvil import *

from ._anvil_designer import ReviewStopRowTemplate
from ... import state, ui


class ReviewStopRow(ReviewStopRowTemplate):
    """After a walk: one of its stops, with ⭐ Review (raises x-review(sid=...)) or ✓ Reviewed.
    item = {stop, done}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        s, d = self.item["stop"], self.dom_nodes
        state.text(d["name"], "%s %s" % (ui.emoji(s.get("kind")), s.get("name")))
        done = bool(self.item.get("done"))
        state.show(d["done"], done)
        self.review_button.visible = not done
        state.set_control_attr(self.review_button, "aria-label", "Review %s" % s.get("name"))

    @handle("review_button", "click")
    def review_button_click(self, **event_args):
        self.parent.raise_event("x-review", sid=self.item["stop"]["id"])
