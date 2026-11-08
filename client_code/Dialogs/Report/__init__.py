from anvil import *

from ._anvil_designer import ReportTemplate
from ... import state

REASONS = ["Made me feel unsafe", "Harassment or inappropriate behaviour", "Fake profile or spam",
           "Didn't follow walk safety rules", "Walk details are misleading", "Something else"]


class Report(ReportTemplate):
    """Report a walker or a walk to the team (confidential). Closes with True when sent."""

    def __init__(self, user_id=None, walk_id=None, who="", **properties):
        super().__init__(**properties)
        self.user_id, self.walk_id = user_id, walk_id
        self.title.text = "🚩 Report %s" % (who or "a problem")
        state.heading(self.title, 2)
        self.reason_dd.items = REASONS

    @handle("yes_button", "click")
    def yes_button_click(self, **event_args):
        if not self.reason_dd.selected_value:
            state.toast("Pick a reason.", "warning")
            return
        if state.call("report", user_id=self.user_id, walk_id=self.walk_id, reason=self.reason_dd.selected_value,
                      details=self.details_box.text) is not state.FAIL:
            state.toast("Thank you. Our team will review this quickly. 🛟")
            self.raise_event("x-close-alert", value=True)

    @handle("no_button", "click")
    def no_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=False)
