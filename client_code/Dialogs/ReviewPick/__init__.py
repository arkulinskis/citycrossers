from anvil import *

from ._anvil_designer import ReviewPickTemplate
from ... import state, ui


class ReviewPick(ReviewPickTemplate):
    """Pick any place from the map to review (my walks' stops first). Closes with the place id, or None."""

    def __init__(self, places=None, **properties):
        super().__init__(**properties)
        self.place_dd.items = [("%s %s" % (ui.emoji(p["kind"]), p["name"]), p["id"]) for p in (places or [])]

    @handle("yes_button", "click")
    def yes_button_click(self, **event_args):
        if not self.place_dd.selected_value:
            state.toast("Pick a place first.", "warning")
            return
        self.raise_event("x-close-alert", value=self.place_dd.selected_value)

    @handle("no_button", "click")
    def no_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=None)
