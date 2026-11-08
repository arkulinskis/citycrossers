from anvil import *
from anvil.js import window

from ._anvil_designer import AvatarStackTemplate
from ... import avatar, state


class AvatarStack(AvatarStackTemplate):
    """Overlapping avatars (a drawing, not a list of controls): show(cards, size=34, limit=5)."""

    def __init__(self, **properties):
        super().__init__(**properties)

    def show(self, cards, size=34, limit=5):
        box = self.dom_nodes["stack"]
        box.textContent = ""
        cards = [c for c in (cards or []) if c and c.get("id")]
        for c in cards[:limit]:
            el = window.document.createElement("span")
            avatar.paint(el, c, size)
            box.appendChild(el)
        if len(cards) > limit:
            more = state.loose(window.document.createElement("span"))
            more.className = "cc-av cc-av-more"
            more.style.width = more.style.height = "%dpx" % size
            more.textContent = "+%d" % (len(cards) - limit)
            box.appendChild(more)
