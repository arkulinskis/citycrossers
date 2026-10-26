from ._anvil_designer import MyWalksTemplate
from anvil import *

from .. import ui, state
from ..ui import esc

TABS = [('upcoming', '🗓️ Going'), ('hosting', '⭐ Hosting'), ('invites', '💌 Invites'),
        ('pending', '⏳ Pending'), ('past', '🏁 Past walks')]


class MyWalks(MyWalksTemplate):
  def __init__(self, tab=None, **properties):
    self.init_components(**properties)
    data = ui.call('my_walks')
    self.data = data if data is not ui.FAIL else {k: [] for k, _ in TABS}
    if tab not in dict(TABS):
      tab = 'upcoming' if self.data['upcoming'] or not self.data['hosting'] else 'hosting'
      if self.data['invites']:
        tab = 'invites'
    self.tab = tab
    ui.bind(self, {'tab': self.set_tab})
    self.render()

  def set_tab(self, tab):
    self.tab = tab
    self.render()

  def render(self):
    d = self.data
    tabs = ''.join(f'<button class="{"on" if k == self.tab else ""}" data-act="tab" data-arg="{k}">{label}'
                   f'{"<span class=cnt>" + str(len(d[k])) + "</span>" if d[k] and k != "past" else ""}</button>'
                   for k, label in TABS)
    walks = d[self.tab]
    total_km = sum((w.get('distance_km') or 0) for w in d['past'])
    empties = {
      'upcoming': ('🥾', "No walks lined up", "Swipe through Discover to find your next crew.",
                   '<a class="cc-btn" href="#discover">Find a walk</a>'),
      'hosting': ('⭐', "You're not hosting anything", "Hosting earns +25 pts per walk, and you choose the snacks.",
                  '<a class="cc-btn orange" href="#plan">Plan a walk</a>'),
      'invites': ('💌', "No invites right now", "Connect with more walkers and the invites will roll in.",
                  '<a class="cc-btn ghost" href="#people">Find people</a>'),
      'pending': ('⏳', "Nothing pending", "Requests you've sent and waitlists you're on will show here.", ''),
      'past': ('🏁', "No finished walks yet", "Your first one is going to be great.", ''),
    }

    def extra(w):
      if w.get('needs_completion'):
        return '<div class="cc-alert" style="margin:6px 0 0;padding:8px 10px"><span>🏁</span><span class="small"><b>Did it happen?</b> Mark it complete to award points.</span></div>'
      if w.get('requests'):
        return f'<div class="cc-alert orange" style="margin:6px 0 0;padding:8px 10px"><span>🙋</span><span class="small"><b>{w["requests"]} request{"s" if w["requests"] != 1 else ""}</b> waiting for you</span></div>'
      return ''

    self.clear()
    self.html = f'''
    <div class="cc-page">
      <div class="cc-row between" style="align-items:flex-end;margin-bottom:18px">
        <div><h1 style="margin:0">My walks 🥾</h1>
        <p class="muted" style="margin:4px 0 0">{len(d["past"])} walks done · {ui.km(total_km)} together with your crews</p></div>
        <a class="cc-btn orange" href="#plan">➕ Plan a walk</a>
      </div>
      <div class="cc-tabs" style="margin-bottom:20px">{tabs}</div>
      {ui.slot("list")}
    </div>'''
    if walks:
      self.add_component(ui.walk_cards_grid(walks, state.go, extra_fn=extra), slot='list')
    else:
      e = empties[self.tab]
      self.add_component(ui.H(ui.empty(*e)), slot='list')
