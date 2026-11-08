from anvil import *

from ._anvil_designer import PersonRowTemplate
from ... import state


class PersonRow(PersonRowTemplate):
    """A walker in a list (the crew, join requests, the waitlist, crew to endorse, requests I sent).
    item = {card, sub?, size?, side?: (text, action, roles), under?: [(text, action, roles), ...] (at most two),
    profile?: show a Profile link under, note?: their message, divider?: dashed line above}.
    Buttons raise x-act(action=..., uid=card id)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it, d = self.item, self.dom_nodes
        card = it["card"]
        self.person.show(card, sub=it.get("sub"), size=it.get("size", 38))
        state.cls(d["row"], "divided", bool(it.get("divider")))
        side = it.get("side")
        self.b1.visible = bool(side)
        if side:
            self.b1.text, self._a1, self.b1.role = side[0], side[1], side[2]
        under = list(it.get("under") or [])
        for b, attr in ((self.b2, "_a2"), (self.b3, "_a3")):
            spec = under.pop(0) if under else None
            b.visible = bool(spec)
            if spec:
                b.text, b.role = spec[0], spec[2]
                setattr(self, attr, spec[1])
        self.profile_link.visible = bool(it.get("profile"))
        state.set_attr(self.profile_link, "href", "#u/%s" % card.get("id"))
        state.show(d["under"], bool(it.get("under")) or bool(it.get("profile")))
        note = it.get("note")
        state.text(d["note"], "“%s”" % note if note else "")
        state.show(d["note"], bool(note))

    def _raise(self, action):
        self.parent.raise_event("x-act", action=action, uid=self.item["card"].get("id"))

    @handle("b1", "click")
    def b1_click(self, **event_args):
        self._raise(getattr(self, "_a1", ""))

    @handle("b2", "click")
    def b2_click(self, **event_args):
        self._raise(getattr(self, "_a2", ""))

    @handle("b3", "click")
    def b3_click(self, **event_args):
        self._raise(getattr(self, "_a3", ""))
