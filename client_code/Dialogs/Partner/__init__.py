from anvil import *

from ._anvil_designer import PartnerTemplate


class Partner(PartnerTemplate):
    """"Become a partner stop": how cafés get a deal badge on the map (from the landing page)."""

    def __init__(self, **properties):
        super().__init__(**properties)

    @handle("ok_button", "click")
    def ok_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=True)
