from anvil import *

from ._anvil_designer import PersonTemplate
from ... import avatar, state


class Person(PersonTemplate):
    """A walker in one line: avatar, name (links to #u/<id>), ✔ when verified, and a sub-line (their headline or
    level unless sub is given). show(card, sub=None, size=44, link=True)."""

    def __init__(self, **properties):
        super().__init__(**properties)

    def show(self, card, sub=None, size=44, link=True):
        card = card or {}
        d = self.dom_nodes
        avatar.paint(d["av"], card, size)
        linked = bool(link and card.get("id"))
        state.text(d["link"], card.get("name"))
        state.text(d["plain"], card.get("name"))
        if linked:
            d["link"].setAttribute("href", "#u/%s" % card["id"])
        state.show(d["link"], linked)
        state.show(d["plain"], not linked)
        state.show(d["ver"], bool(card.get("verified")))
        if sub is None:
            lvl = card.get("level") or {}
            sub = card.get("headline") or ("%s %s" % (lvl.get("emoji", ""), lvl.get("name", ""))).strip()
        state.text(d["sub"], sub)
        state.show(d["sub"], bool(sub))
