from anvil import *

from ._anvil_designer import InviteRowTemplate
from ... import state, ui


class InviteRow(InviteRowTemplate):
    """A walk invite on Discover: the walk (link), when, how far, who from; I'm in / Can't make it raise
    x-invite(wid=..., accept=...)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        w, d = self.item, self.dom_nodes
        state.href(d["link"], "#walk/%s" % w["id"])
        state.text(d["link"], "%s %s" % (ui.vibe_of(w.get("vibe"))[1], w.get("title")))
        state.text(d["sub"], "%s · %s · from %s" % (ui.fmt_when(w.get("start")), ui.km(w.get("distance_km")),
                                                  (w.get("host") or {}).get("name", "")))

    @handle("yes_button", "click")
    def yes_button_click(self, **event_args):
        self.parent.raise_event("x-invite", wid=self.item["id"], accept=True)

    @handle("no_button", "click")
    def no_button_click(self, **event_args):
        self.parent.raise_event("x-invite", wid=self.item["id"], accept=False)
