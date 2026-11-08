from anvil import *

from ._anvil_designer import SafetyPledgeTemplate
from ... import state


class SafetyPledge(SafetyPledgeTemplate):
    """The safety pledge: six promises to tick, then accept_safety_pledge (+10 pts). Closes with True when taken."""

    def __init__(self, **properties):
        super().__init__(**properties)

    @handle("yes_button", "click")
    def yes_button_click(self, **event_args):
        for i in range(1, 7):
            if not state.loose(self.dom_nodes)["c%d" % i].checked:
                state.toast("Tick every promise to continue. They're short, we promise.", "warning")
                return
        res = state.call("accept_safety_pledge")
        if res is not state.FAIL:
            state.set_me(res)
            state.toast("Pledge taken. +10 pts 🛟")
            self.raise_event("x-close-alert", value=True)

    @handle("no_button", "click")
    def no_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=False)
