from anvil import *

from ._anvil_designer import ReviewTemplate
from ... import state


class Review(ReviewTemplate):
    """Write (or edit) a review of a place or of a walk's stop: stars, headline, text, a private note to future me,
    "I'd come back", public or not. save_review; closes with True when saved."""

    def __init__(self, place_name="", place_id=None, stop_id=None, walk_id=None, existing=None, **properties):
        super().__init__(**properties)
        ex = existing or {}
        self.ids = {"place_id": place_id, "stop_id": stop_id, "walk_id": walk_id, "review_id": ex.get("id")}
        self.title.text = "⭐ Review %s" % place_name
        state.heading(self.title, 2)
        self.stars.value = ex.get("rating") or 0
        self.title_box.text = ex.get("title") or ""
        self.body_box.text = ex.get("body") or ""
        self.future_box.text = ex.get("future_note") or ""
        self.again_box.checked = ex.get("would_return", True) if existing else True
        self.public_box.checked = bool(ex.get("is_public") if existing else (state.me() or {}).get("journal_public_default"))

    @handle("yes_button", "click")
    def yes_button_click(self, **event_args):
        if not self.stars.value:
            state.toast("Tap the stars to rate it.", "warning")
            return
        data = dict(self.ids, rating=self.stars.value, title=self.title_box.text, body=self.body_box.text,
                    future_note=self.future_box.text, would_return=self.again_box.checked,
                    is_public=self.public_box.checked)
        res = state.call("save_review", data)
        if res is not state.FAIL:
            state.toast(res["message"])
            self.raise_event("x-close-alert", value=True)

    @handle("no_button", "click")
    def no_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=False)
