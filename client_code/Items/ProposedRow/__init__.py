from anvil import *

from ._anvil_designer import ProposedRowTemplate
from ... import state, ui


class ProposedRow(ProposedRowTemplate):
    """A stop someone suggested for a walk: who suggested it, 👍 votes (walkers going can vote), ✓ Add (host) and
    ✕ (host or the suggester). item = {stop, can_vote, is_host, mine}; raises x-proposed(action=..., sid=...)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it, d = self.item, self.dom_nodes
        s = it["stop"]
        by = s.get("proposed_by") or {}
        state.text(d["e"], ui.emoji(s.get("kind")))
        state.text(d["name"], s.get("name"))
        state.text(d["sub"], "suggested by %s%s" % (by.get("name", "someone"), (" · " + s["note"]) if s.get("note") else ""))
        self.vote_button.visible = bool(it.get("can_vote"))
        self.vote_button.text = "👍 %s" % s.get("votes", 0)
        self.vote_button.role = ["cc-btn", "sm"] if s.get("voted") else ["cc-btn", "ghost", "sm"]
        state.set_control_attr(self.vote_button, "aria-pressed", "true" if s.get("voted") else "false")
        state.set_control_attr(self.vote_button, "aria-label", "Vote for %s (%s votes)" % (s.get("name"), s.get("votes", 0)))
        state.text(d["votes"], "👍 %s" % s.get("votes", 0))
        state.show(d["votes"], not it.get("can_vote"))
        self.accept_button.visible = bool(it.get("is_host"))
        self.remove_button.visible = bool(it.get("is_host") or it.get("mine"))
        state.set_control_attr(self.remove_button, "aria-label", "Remove %s" % s.get("name"))

    def _raise(self, action):
        self.parent.raise_event("x-proposed", action=action, sid=self.item["stop"]["id"])

    @handle("vote_button", "click")
    def vote_button_click(self, **event_args):
        self._raise("vote")

    @handle("accept_button", "click")
    def accept_button_click(self, **event_args):
        self._raise("accept")

    @handle("remove_button", "click")
    def remove_button_click(self, **event_args):
        self._raise("remove")
