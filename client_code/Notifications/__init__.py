from ._anvil_designer import NotificationsTemplate
from anvil import *

from .. import ui, state
from ..ui import esc

ICONS = {'invite': '💌', 'request': '🙋', 'join': '🎉', 'accepted': '✅', 'declined': '🙅', 'left': '👋',
         'friend_request': '👋', 'friend': '🤝', 'endorse': '🏅', 'stop': '🗳️', 'complete': '🏁', 'cancelled': '😢',
         'level': '⭐', 'deal': '🏷️', 'report': '🚩', 'verified': '✔️', 'walk': '🥾'}


class Notifications(NotificationsTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    items = ui.call('get_notifications')
    items = items if items is not ui.FAIL else []
    rows = ''
    for n in items:
      who = n.get('from_user')
      ico = ui.avatar(who, 42) if who else f'<span class="ico">{ICONS.get(n["kind"], "🔔")}</span>'
      href = f'#{n["link"]}' if n.get('link') else '#notifications'
      rows += f'''<a class="cc-notif {"" if n["read"] else "unread"}" href="{esc(href)}">{ico}
        <span class="txt">{esc(n["message"])}<br><span class="when">{ICONS.get(n["kind"], "🔔")} {ui.ago(n["created"])}</span></span></a>'''
    if not rows:
      rows = ui.empty('🔔', 'All quiet', "Invites, requests and endorsements will show up here.")
    self.html = f'''
    <div class="cc-page narrow">
      <h1>🔔 Notifications</h1>
      <div class="cc-stack" style="margin-top:12px">{rows}</div>
    </div>'''
    if any(not n['read'] for n in items):
      ui.call('mark_notifications_read', _quiet=True)
      if state.main:
        state.main.update_counts(dict(state.counts, notifications=0))
