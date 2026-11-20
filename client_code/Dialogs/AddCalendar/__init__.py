from anvil import *

from ._anvil_designer import AddCalendarTemplate
from ... import calendar, state, ui


class AddCalendar(AddCalendarTemplate):
    """Add a walk to a calendar: download an .ics file (made in the browser) or open Google Calendar with the walk
    filled in. walk = the get_walk dict, url = its /w/<id> address. Closes with True."""

    def __init__(self, walk=None, url="", **properties):
        super().__init__(**properties)
        self.walk = walk or {}
        self.url = url
        state.text(self.dom_nodes["sub"], "“%s”, %s. Times follow your calendar's time zone." % (
            self.walk.get("title", ""), ui.fmt_when(self.walk.get("start"))))
        self.google_link.url = calendar.google_link(self.walk, url)

    @handle("ics_button", "click")
    def ics_button_click(self, **event_args):
        try:
            calendar.download(self.walk, self.url)
            state.toast("Calendar file saved. Open it to add the walk 📅")
        except Exception:
            state.toast("Couldn't make the calendar file on this device. Try Google Calendar instead.", "error")

    @handle("close_button", "click")
    def close_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=True)
