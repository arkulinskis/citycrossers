from anvil import *

from ._anvil_designer import AvatarLinkTemplate
from ... import avatar, state


class AvatarLink(AvatarLinkTemplate):
    """A walker's avatar linking to their profile (mutual connections). item = a user card."""

    def __init__(self, **properties):
        super().__init__(**properties)
        m, d = self.item, self.dom_nodes
        state.href(d["link"], "#u/%s" % m["id"])
        d["link"].setAttribute("aria-label", m.get("name") or "A walker")
        avatar.paint(d["av"], m, 36)
