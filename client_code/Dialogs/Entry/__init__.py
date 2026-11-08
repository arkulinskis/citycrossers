import datetime

from anvil import *

from ._anvil_designer import EntryTemplate
from ... import state, ui


class Entry(EntryTemplate):
    """A journey entry (new, about a walk, or an edit): mood, title, date, km, story, a photo, public or not.
    save_entry; closes with True when saved."""

    def __init__(self, existing=None, walk=None, **properties):
        super().__init__(**properties)
        ex = existing or {}
        self.ex, self.walk = ex, walk or {}
        self.title.text = "📔 %s" % ("Edit entry" if existing else "New journey entry")
        state.heading(self.title, 2)
        self.mood_chips.setup(ui.MOODS, selected=ex.get("mood") or "🙂", multi=False)
        self.title_box.text = ex.get("title") or ("Walking “%s”" % walk["title"] if walk else "")
        self.body_box.text = ex.get("body") or ""
        self.date_picker.date = ex.get("date") or datetime.date.today()
        km = ex.get("km") if ex.get("km") is not None else (walk.get("distance_km") if walk else None)
        self.km_box.text = state.loose(km)
        self.public_box.checked = bool(ex.get("is_public") if existing else (state.me() or {}).get("journal_public_default"))

    @handle("yes_button", "click")
    def yes_button_click(self, **event_args):
        data = {"id": self.ex.get("id"), "mood": self.mood_chips.value, "title": self.title_box.text,
                "body": self.body_box.text, "entry_date": self.date_picker.date, "km": self.km_box.text,
                "is_public": self.public_box.checked, "walk_id": self.walk.get("id") or self.ex.get("walk_id")}
        if self.photo_loader.file is not None:
            data["photo"] = self.photo_loader.file
        res = state.call("save_entry", data)
        if res is not state.FAIL:
            state.toast(res["message"])
            self.raise_event("x-close-alert", value=True)

    @handle("no_button", "click")
    def no_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=False)
