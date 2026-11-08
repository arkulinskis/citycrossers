from anvil import *

from ._anvil_designer import NotifRowTemplate
from ... import avatar, state, ui

ICONS = {'invite': '💌', 'request': '🙋', 'join': '🎉', 'accepted': '✅', 'declined': '🙅', 'left': '👋',
         'friend_request': '👋', 'friend': '🤝', 'endorse': '🏅', 'stop': '🗳️', 'complete': '🏁', 'cancelled': '😢',
         'level': '⭐', 'deal': '🏷️', 'report': '🚩', 'verified': '✔️', 'walk': '🥾'}


class NotifRow(NotifRowTemplate):
    """A notification: who (avatar) or what (icon), the message, when; links to what it is about; unread ones are
    white with an orange dot. item = a notification from get_notifications."""

    def __init__(self, **properties):
        super().__init__(**properties)
        n, d = self.item, self.dom_nodes
        state.href(d["link"], "#" + n["link"] if n.get("link") else "#notifications")
        state.cls(d["link"], "unread", not n.get("read"))
        state.show(d["unread"], not n.get("read"))
        ico = ICONS.get(n.get("kind"), "🔔")
        who = n.get("from_user")
        if who:
            avatar.paint(d["av"], who, 42)
        state.show(d["av"], bool(who))
        state.text(d["ico"], ico)
        state.show(d["ico"], not who)
        state.text(d["msg"], n.get("message"))
        state.text(d["when"], "%s %s" % (ico, ui.ago(n.get("created"))))
