from ._anvil_designer import PeopleTemplate
from anvil import *

from .. import ui, state
from ..ui import esc


def person_card(p, actions_html):
  top = p.get('top_endorsement')
  pace = ui.PACES.get(p.get('pace'), ui.PACES['steady'])
  match = ui.pill(f"{p['match']}% match", 'dark') if p.get('match') else ''
  return f'''
  <div class="cc-person-card">
    <div class="banner {ui.VIBES[hash(p["id"]) % len(ui.VIBES)][3]}"></div>
    {ui.avatar(p, 76)}
    <div class="inner">
      <h4><a href="#u/{p["id"]}" style="color:inherit">{esc(p["name"])}</a>{' <span class="cc-verified">✔</span>' if p.get("verified") else ''}</h4>
      <div class="headline">{esc(p.get("headline") or "New walker, say hi!")}</div>
      <div class="cc-pills">{match}{ui.level_pill(p)}{ui.pill(pace[0] + " " + pace[1])}</div>
      <div class="small muted">{ui.km(p.get("km_total"))} · {p.get("walks_count", 0)} walks{(" · " + esc(p["city"])) if p.get("city") else ""}</div>
      {ui.pill(top["skill"] + " ×" + str(top["count"]), "violet") if top else ""}
      <div class="actions">{actions_html}</div>
    </div>
  </div>'''


class People(PeopleTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.search_box = ui.textbox('Search walkers by name, city or headline…')
    self.search_box.add_event_handler('pressed_enter', lambda **e: self.search())
    self.results = None
    ui.bind(self, {'connect': self.connect, 'accept': lambda a: self.respond(a, True),
                   'reject': lambda a: self.respond(a, False), 'remove': self.remove, 'search': lambda a: self.search(),
                   'clear': self.clear_search})
    self.load()

  def load(self):
    d = ui.call('people_page')
    self.data = d if d is not ui.FAIL else {'friends': [], 'incoming': [], 'outgoing': [], 'suggestions': []}
    self.render()

  def render(self):
    d = self.data
    sections = ''
    if self.results is not None:
      cards = ''
      for p in self.results:
        rel = p.get('relationship')
        if rel == 'friends':
          act = '<span class="cc-pill green">✓ Connected</span>'
        elif rel == 'pending_out':
          act = '<span class="cc-pill sun">⏳ Requested</span>'
        elif rel == 'pending_in':
          act = ui.btn('✓ Accept', 'accept', p['id'], 'sm')
        else:
          act = ui.btn('👋 Connect', 'connect', p['id'], 'sm')
        cards += person_card(p, f'<a class="cc-btn ghost sm" href="#u/{p["id"]}">View</a>{act}')
      sections += f'''<div class="cc-section-title"><h2>🔎 Results</h2>{ui.btn("Clear", "clear", kind="ghost sm")}</div>
        {('<div class="cc-grid cards">' + cards + '</div>') if cards else ui.empty("🔎", "Nobody found", "Try another name or city.")}'''
    if d['incoming']:
      cards = ''.join(person_card(p, ui.btn('Ignore', 'reject', p['id'], 'ghost sm') + ui.btn('✓ Accept', 'accept', p['id'], 'sm'))
                      for p in d['incoming'])
      sections += f'<div class="cc-section-title"><h2>👋 Want to walk with you</h2></div><div class="cc-grid cards">{cards}</div>'
    if d['friends']:
      cards = ''.join(person_card(p, f'<a class="cc-btn ghost sm" href="#u/{p["id"]}">Profile</a>'
                                     f'<a class="cc-btn sm orange" href="#plan">Plan a walk</a>') for p in d['friends'])
      sections += f'<div class="cc-section-title"><h2>🤝 Your crew <span class="muted" style="font-size:1rem">({len(d["friends"])})</span></h2></div><div class="cc-grid cards">{cards}</div>'
    else:
      sections += ('<div class="cc-section-title"><h2>🤝 Your crew</h2></div>' +
                   ui.empty('🫂', 'No connections yet', "Connect with walkers below, or walk with someone first. Everyone's a stranger until km 3."))
    if d['suggestions']:
      cards = ''.join(person_card(p, f'<a class="cc-btn ghost sm" href="#u/{p["id"]}">View</a>' + ui.btn('👋 Connect', 'connect', p['id'], 'sm'))
                      for p in d['suggestions'])
      sections += f'<div class="cc-section-title"><h2>✨ Walkers you might click with</h2><span class="small muted">Ranked by pace, distance &amp; interests</span></div><div class="cc-grid cards">{cards}</div>'
    if d['outgoing']:
      sections += '<div class="cc-section-title"><h3>⏳ Requests you sent</h3></div><div class="cc-row">' + ''.join(
        f'<div class="cc-card flat" style="padding:10px 14px">{ui.person(p, sub="Waiting…", size=34)}</div>' for p in d['outgoing']) + '</div>'
    self.clear()
    self.html = f'''
    <div class="cc-page">
      <h1 style="margin:0">People 👋</h1>
      <p class="muted" style="margin:4px 0 18px">The best walks are with people you haven't met yet. Connect, then invite them along.</p>
      <div class="cc-card" style="display:flex;gap:10px;align-items:center;padding:12px">
        <div style="flex:1">{ui.slot("search")}</div>{ui.btn("Search", "search")}
      </div>
      {sections}
    </div>'''
    self.add_component(self.search_box, slot='search')

  def search(self):
    text = (self.search_box.text or '').strip()
    if len(text) < 2:
      ui.toast("Type at least 2 letters.", 'warning')
      return
    res = ui.call('search_people', text)
    if res is not ui.FAIL:
      self.results = res
      self.render()

  def clear_search(self, _=None):
    self.results = None
    self.search_box.text = ''
    self.render()

  def connect(self, uid):
    res = ui.call('send_friend_request', uid)
    if res is not ui.FAIL:
      ui.toast("Connected! 🤝" if res == 'friends' else "Request sent 👋")
      if self.results:
        for p in self.results:
          if p['id'] == uid:
            p['relationship'] = res
      self.load()

  def respond(self, uid, accept):
    res = ui.call('respond_friend_request', uid, accept)
    if res is not ui.FAIL:
      ui.toast("You're connected! Time to plan a walk 🥾" if accept else "Request ignored", 'success' if accept else 'info')
      self.load()

  def remove(self, uid):
    if ui.ask("Remove this connection?", yes="Remove") and ui.call('remove_friend', uid) is not ui.FAIL:
      self.load()
