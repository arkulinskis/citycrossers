from anvil import *

from ._anvil_designer import SafetyTemplate
from ... import dialogs, router, state


class Safety(SafetyTemplate):
    """#safety: the safety guide (before you join, before you set off, on the walk, weather, guidelines, if something
    goes wrong). Visitors see it too (public=True: no header, a way back to the landing page); members get the
    safety pledge if they haven't taken it."""

    def __init__(self, public=False, **properties):
        super().__init__(**properties)
        pledged = bool((state.me() or {}).get('safety_pledge')) and not public
        self.back_link.visible = public
        self.public_foot.visible = public
        self.public_cta.visible = public
        self.pledged_cta.visible = pledged
        self.pledge_cta.visible = not public and not pledged

    @handle('pledge_button', 'click')
    def pledge_button_click(self, **event_args):
        if dialogs.safety_pledge():
            router.go('discover')
