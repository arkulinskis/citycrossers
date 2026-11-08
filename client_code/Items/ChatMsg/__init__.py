from anvil import *

from ._anvil_designer import ChatMsgTemplate
from ... import avatar, state, ui


class ChatMsg(ChatMsgTemplate):
    """A message in a walk's group chat (mine on the right, in green). item = {user, body, created, mine}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        m, d = self.item, self.dom_nodes
        u = m.get("user") or {}
        state.cls(d["msg"], "mine", bool(m.get("mine")))
        avatar.paint(d["av"], u, 30)
        state.text(d["who"], "%s · %s" % (u.get("name", ""), ui.ago(m.get("created"))))
        state.text(d["body"], m.get("body"))
