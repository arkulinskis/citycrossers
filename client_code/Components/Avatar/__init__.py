from anvil import *

from ._anvil_designer import AvatarTemplate
from ... import avatar


class Avatar(AvatarTemplate):
    """A walker's avatar (photo or initials). show(card, size=40) draws it; card = a user card from the server."""

    def __init__(self, **properties):
        super().__init__(**properties)

    def show(self, card, size=40):
        avatar.paint(self.dom_nodes["av"], card, size)
