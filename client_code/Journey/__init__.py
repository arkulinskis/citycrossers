from ._anvil_designer import JourneyTemplate
from anvil import *

from .. import ui, state, dialogs
from ..ui import esc

FILTERS = [('all', '✨ Everything'), ('entry', '📔 Entries'), ('review', '⭐ Reviews'), ('walk', '🥾 Walks'),
           ('public', '🌍 Public')]


class Journey(JourneyTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.filter = 'all'
    ui.bind(self, {'filter': self.set_filter, 'new_entry': self.new_entry, 'new_review': self.new_review,
                   'edit_entry': self.edit_entry, 'del_entry': self.del_entry, 'edit_review': self.edit_review,
                   'del_review': self.del_review, 'toggle_review': self.toggle_review})
    self.load()

  def load(self):
    d = ui.call('journey')
    self.data = d if d is not ui.FAIL else {'items': [], 'stats': {}, 'public_default': False}
    self.render()

  def _find(self, kind, iid):
    for i in self.data['items']:
      if i['type'] == kind and i['id'] == iid:
        return i
    return None

  def render(self):
    st = self.data['stats']
    items = self.data['items']
    f = self.filter
    if f == 'public':
      shown = [i for i in items if i.get('is_public')]
    elif f != 'all':
      shown = [i for i in items if i['type'] == f]
    else:
      shown = items
    chips = ''.join(f'<button class="cc-chip {"on" if k == f else ""}" data-act="filter" data-arg="{k}">{l}</button>' for k, l in FILTERS)
    timeline = ''
    for i in shown:
      timeline += self.item_html(i)
    if not shown:
      timeline = ui.empty('📔', 'Your journey starts here',
                          'Write about a walk, review a place you loved, or leave a note for future you. '
                          'Finished walks appear here automatically.',
                          '<div class="cc-row" style="justify-content:center">' + ui.btn('📔 New entry', 'new_entry') +
                          ui.btn('⭐ Review a place', 'new_review', kind='orange') + '</div>')
    else:
      timeline = f'<div class="cc-journey">{timeline}</div>'
    self.clear()
    self.html = f'''
    <div class="cc-page narrow">
      <div class="cc-hello" style="margin-bottom:20px">
        <h1>My journey 📔</h1>
        <p style="margin:0;font-size:1.05rem">Your life, one walk at a time. Private by default. Share what you want people to know you love.</p>
        <div class="cc-stat-row">
          <div class="cc-stat"><b>{ui.km(st.get("km", 0))}</b><span>walked</span></div>
          <div class="cc-stat"><b>{st.get("walks", 0)}</b><span>walks</span></div>
          <div class="cc-stat"><b>{st.get("people", 0)}</b><span>people met</span></div>
          <div class="cc-stat"><b>{st.get("reviews", 0)}</b><span>places reviewed</span></div>
          <div class="cc-stat"><b>{st.get("entries", 0)}</b><span>entries</span></div>
        </div>
      </div>
      <div class="cc-row between" style="margin-bottom:16px">
        <div class="cc-chips">{chips}</div>
        <div class="cc-row">{ui.btn("📔 New entry", "new_entry")}{ui.btn("⭐ Review a place", "new_review", kind="orange")}</div>
      </div>
      {timeline}
    </div>'''

  def item_html(self, i):
    date = ui.fmt_date(i['date'], True) if i.get('date') else ''
    vis = ('<span class="cc-pill sky tiny">🌍 Public</span>' if i.get('is_public') else '<span class="cc-pill tiny">🔒 Private</span>')
    if i['type'] == 'entry':
      photo = ui.media_url(i.get('photo'))
      walk = f' · <a href="#walk/{i["walk_id"]}">{esc(i["walk_title"])}</a>' if i.get('walk_id') else ''
      return f'''<div class="cc-j-item entry"><span class="marker">{i["mood"]}</span><div class="cc-card">
        <div class="cc-row between"><span class="date">{esc(date)}{(" · " + ui.km(i["km"])) if i.get("km") else ""}{walk}</span>{vis}</div>
        <h3 style="margin:6px 0">{esc(i["title"])}</h3><p style="margin:0;white-space:pre-wrap">{esc(i["body"])}</p>
        {('<img class="cc-j-photo" src="' + esc(photo) + '" alt="">') if photo else ''}
        <div class="cc-row end" style="margin-top:10px">{ui.btn("Edit", "edit_entry", i["id"], "ghost sm")}{ui.btn("Delete", "del_entry", i["id"], "danger sm")}</div></div></div>'''
    if i['type'] == 'review':
      place = i.get('place') or {}
      emo = ui.KINDS.get(place.get('kind'), ('📍',))[0]
      future = f'<div class="cc-future">💌 Note to future me: {esc(i["future_note"])}</div>' if i.get('future_note') else ''
      toggle = ui.btn('Make private' if i.get('is_public') else 'Make public', 'toggle_review', i['id'], 'ghost sm')
      return f'''<div class="cc-j-item review"><span class="marker">⭐</span><div class="cc-card">
        <div class="cc-row between"><span class="date">{esc(date)} · review</span>{vis}</div>
        <div class="cc-row between" style="margin-top:6px"><h3 style="margin:0">{emo} {esc(place.get("name", "A place"))}</h3>
          <span class="cc-rating">{ui.stars(i["rating"])}</span></div>
        {('<b>' + esc(i["title"]) + '</b>') if i.get("title") else ''}<p style="margin:4px 0 0">{esc(i["body"])}</p>{future}
        {'<div class="tiny muted" style="margin-top:6px">💚 Would go back</div>' if i.get("would_return") else ''}
        <div class="cc-row end" style="margin-top:10px">{toggle}{ui.btn("Edit", "edit_review", i["id"], "ghost sm")}{ui.btn("Delete", "del_review", i["id"], "danger sm")}</div></div></div>'''
    v = ui.vibe_of(i.get('vibe'))
    host = i.get('host') or {}
    return f'''<div class="cc-j-item walk"><span class="marker">🥾</span><div class="cc-card {v[3]}" style="border:0">
      <span class="date" style="color:inherit;opacity:.75">{esc(date)} · walk completed</span>
      <h3 style="margin:6px 0"><a href="#walk/{i["id"]}" style="color:inherit">{v[1]} {esc(i["title"])}</a></h3>
      <div class="small">🏁 {ui.km(i.get("km"))} with {esc(host.get("name", "the crew"))}'s crew</div></div></div>'''

  def set_filter(self, f):
    self.filter = f
    self.render()

  def new_entry(self, _=None):
    if dialogs.entry():
      state.refresh_me()
      self.load()

  def new_review(self, _=None):
    if dialogs.review_any():
      state.refresh_me()
      self.load()

  def edit_entry(self, iid):
    i = self._find('entry', iid)
    if i and dialogs.entry(existing=i):
      self.load()

  def del_entry(self, iid):
    if ui.ask("Delete this entry? This can't be undone.", yes="Delete") and ui.call('delete_entry', iid) is not ui.FAIL:
      self.load()

  def edit_review(self, iid):
    i = self._find('review', iid)
    if i and dialogs.review((i.get('place') or {}).get('name', 'this place'), existing=i):
      self.load()

  def del_review(self, iid):
    if ui.ask("Delete this review?", yes="Delete") and ui.call('delete_review', iid) is not ui.FAIL:
      self.load()

  def toggle_review(self, iid):
    i = self._find('review', iid)
    if i and ui.call('set_review_public', iid, not i.get('is_public')) is not ui.FAIL:
      ui.toast("Review is now public 🌍" if not i.get('is_public') else "Review is now private 🔒")
      self.load()
