from anvil import *

from ._anvil_designer import NotificationsTemplate
from ... import state


class Notifications(NotificationsTemplate):
    """#notifications: everything that happened to me (invites, requests, endorsements, walk changes), newest first.
    Opening the page marks them read (the header's bell goes back to 0)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        items = state.call('get_notifications')
        items = items if items is not state.FAIL else []
        self.list_panel.items = items
        self.list_panel.visible = bool(items)
        self.empty_box.visible = not items
        if any(not n['read'] for n in items):
            state.call('mark_notifications_read', quiet=True)
            state.set_counts({'notifications': 0})
