from anvil import *

from ._anvil_designer import PickWalkTemplate
from ... import state, ui


class PickWalk(PickWalkTemplate):
    """Invite someone (from their profile) to one of my upcoming walks: pick it, invite_to_walk.
    Closes with True once invited."""

    def __init__(self, person=None, walks=None, **properties):
        super().__init__(**properties)
        self.person = person or {}
        self.title.text = "💌 Invite %s" % self.person.get("name", "")
        state.heading(self.title, 2)
        self.walks_panel.items = [{
            "key": w["id"], "title": "%s %s" % (ui.vibe_of(w.get("vibe"))[1], w["title"]),
            "sub": "%s · %s · %s/%s going" % (ui.fmt_when(w.get("start")), ui.km(w.get("distance_km")),
                                             w.get("going", 0), w.get("max_walkers", 0)), "on": False}
            for w in (walks or [])]
        self.walks_panel.add_event_handler("x-pick", self._pick)

    def _pick(self, key=None, **event_args):
        n = state.call("invite_to_walk", key, [self.person["id"]])
        if n is state.FAIL:
            return
        first = self.person.get("name", "").split(" ")[0]
        state.toast("Invite sent to %s 💌" % first if n else "They're already on that walk (or invited).",
                    "ok" if n else "info")
        self.raise_event("x-close-alert", value=True)

    @handle("no_button", "click")
    def no_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=None)
