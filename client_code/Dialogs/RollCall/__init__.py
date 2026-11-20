from anvil import *

from ._anvil_designer import RollCallTemplate
from ... import state


class RollCall(RollCallTemplate):
    """The host's roll call when a walk is marked complete: the crew going (not the host), each ticked "Here".
    Tapping a walker marks them missed (and back). Closes with the ids of the walkers who missed it ([] = everyone
    came), or None when cancelled. crew = user cards from get_walk."""

    def __init__(self, crew=None, **properties):
        super().__init__(**properties)
        self.crew = crew or []
        self.missed = set()
        self.crew_panel.add_event_handler("x-act", self._toggle)
        self.render()

    def render(self):
        rows = []
        for c in self.crew:
            out = c.get("id") in self.missed
            rows.append({"card": c, "size": 34, "sub": "Missed this one" if out else "Here",
                         "side": ("✕ Missed", "toggle", ["cc-btn", "danger", "sm"]) if out
                         else ("✓ Here", "toggle", ["cc-btn", "soft", "sm"])})
        self.crew_panel.items = rows
        n_out = len(self.missed)
        state.text(self.dom_nodes["count"], "%d here · %d missed" % (len(self.crew) - n_out, n_out))

    def _toggle(self, action=None, uid=None, **event_args):
        if uid in self.missed:
            self.missed.discard(uid)
        else:
            self.missed.add(uid)
        self.render()

    @handle("yes_button", "click")
    def yes_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=list(self.missed))

    @handle("no_button", "click")
    def no_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=None)
