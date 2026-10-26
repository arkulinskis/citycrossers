from ._anvil_designer import MapPageTemplate
from anvil import *
import anvil.js

from .. import ui, state, dialogs
from ..ui import esc
from ..mapkit import MapView

FILTERS = [('all', '✨ Everything'), ('deals', '🏷️ Deals'), ('walks', '🚩 Walks')] + \
          [(k, ui.KINDS[k][0] + ' ' + ui.KINDS[k][1]) for k in ui.PLACE_KINDS]


class MapPage(MapPageTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.filter = 'all'
    self.picking = False
    data = ui.call('map_data')
    self.data = data if data is not ui.FAIL else {'places': [], 'walks': []}
    self.mv = MapView(height='min(64vh, 620px)', on_click=self.map_clicked, scroll_zoom=True)
    ui.bind(self, {'filter': self.set_filter, 'locate': lambda a: self.mv.locate(), 'propose': self.toggle_pick,
                   'place': lambda a: self.open_place(a), 'walk': lambda a: state.go('walk/' + a)})
    self.render()

  def render(self):
    places = self.data['places']
    deals = [p for p in places if p['deals']]
    chips = ''.join(f'<button class="cc-chip {"on" if k == self.filter else ""}" data-act="filter" data-arg="{k}">{esc(l)}</button>'
                    for k, l in FILTERS)
    deal_cards = ''
    for p in deals:
      for d in p['deals']:
        tag = f'{d["percent"]}% OFF' if d.get('percent') else 'DEAL'
        deal_cards += f'''<div class="cc-card cc-clickable" data-act="place" data-arg="{p["id"]}" style="padding:16px">
          <div class="cc-row between"><span class="cc-deal-tag">{tag}</span><span class="small muted">{ui.KINDS.get(p["kind"], ("📍",))[0]} {esc(p["name"])}</span></div>
          <h4 style="margin:10px 0 2px">{esc(d["title"])}</h4><div class="small muted">{esc(d["description"])}</div></div>'''
    if not deal_cards:
      deal_cards = ui.empty('🏷️', 'No partner deals yet', 'Admins can add deals for places from the Admin page.')
    walks = ''.join(f'''<div class="cc-row cc-clickable" data-act="walk" data-arg="{w["id"]}" style="gap:12px;padding:10px;border-radius:14px;flex-wrap:nowrap">
        <span class="{ui.vibe_of(w["vibe"])[3]}" style="border-radius:14px;width:46px;height:46px;display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0">{ui.vibe_of(w["vibe"])[1]}</span>
        <span style="min-width:0"><b style="display:block">{esc(w["title"])}</b><span class="small muted">{esc(ui.fmt_when(w["start"]))} · {ui.km(w["distance_km"])} · {w["going"]}/{w["max_walkers"]} going</span></span></div>'''
                    for w in sorted(self.data['walks'], key=lambda w: w['start'])[:8]) or '<p class="muted">No upcoming walks on the map yet.</p>'
    self.clear()
    self.html = f'''
    <div class="cc-page">
      <div class="cc-row between" style="margin-bottom:16px;align-items:flex-end">
        <div><h1 style="margin:0">The snack map 🗺️</h1>
          <p class="muted" style="margin:4px 0 0">Every good stop, pinned by walkers. Tap a pin for reviews, deals and walks.</p></div>
        <div class="cc-row">
          <button class="cc-btn ghost" data-act="locate">📍 Near me</button>
          <button class="cc-btn orange js-propose" data-act="propose">➕ Propose a place</button>
        </div>
      </div>
      <div class="cc-map-wrap">
        <div class="cc-map-tools js-filters">{chips}</div>
        {ui.slot("map")}
      </div>
      <div class="cc-map-legend">
        <span>☕🥐🍦 food &amp; drink</span><span>🌳 parks</span><span>👀 viewpoints</span><span>🪑 rest</span><span>🚰 water</span>
        <span>🏛️ culture</span><span><b style="color:#FF7A3D">%</b> partner deal</span><span>🚩 walk starts</span>
        <span class="cc-spacer"></span><span>{len(places)} places · {len(self.data["walks"])} upcoming walks</span>
      </div>
      <div class="cc-grid two" style="margin-top:28px">
        <div><div class="cc-section-title" style="margin-top:0"><h2>🏷️ Partner deals</h2></div>
          <div class="cc-grid cards-sm">{deal_cards}</div></div>
        <div><div class="cc-section-title" style="margin-top:0"><h2>🚩 Walks starting soon</h2></div>
          <div class="cc-card" style="padding:8px">{walks}</div></div>
      </div>
    </div>'''
    self.add_component(self.mv.component, slot='map')
    self.draw()

  def draw(self):
    self.mv.clear('places')
    self.mv.clear('walks')
    shown = []
    f = self.filter
    if f in ('all', 'walks'):
      for w in self.data['walks']:
        el = self.mv.popup_el(f'''<h4>{ui.vibe_of(w["vibe"])[1]} {esc(w["title"])}</h4>
          <div class="small muted">{esc(ui.fmt_when(w["start"]))}<br>{ui.km(w["distance_km"])} · {w["going"]}/{w["max_walkers"]} going</div>
          <button class="cc-btn sm" data-act="walk" data-arg="{w["id"]}">See the walk</button>''',
                              actions={'walk': lambda a: state.go('walk/' + a)})
        self.mv.add_marker(w['lat'], w['lng'], '🚩', 'walk', popup=el, layer='walks', tooltip=w['title'])
        shown.append(w)
    if f != 'walks':
      for p in self.data['places']:
        if f == 'deals' and not p['deals']:
          continue
        if f not in ('all', 'deals') and p['kind'] != f:
          continue
        emo, kind_name = ui.KINDS.get(p['kind'], ('📍', 'Spot'))
        deal = p['deals'][0] if p['deals'] else None
        deal_html = (f'<div style="margin-top:6px"><span class="cc-deal-tag">{(str(deal["percent"]) + "% OFF") if deal.get("percent") else "DEAL"}</span> '
                     f'<b class="small">{esc(deal["title"])}</b></div>') if deal else ''
        rating = f'<span class="cc-rating">{ui.stars(p["avg_rating"])}</span> <span class="tiny muted">({p["review_count"]})</span>' if p['review_count'] else '<span class="tiny muted">No reviews yet</span>'
        el = self.mv.popup_el(f'''<h4>{emo} {esc(p["name"])}</h4><div class="tiny muted">{esc(kind_name)}</div>
          <div>{rating}</div><div class="small" style="margin-top:4px">{esc(p["description"][:120])}</div>{deal_html}
          <div class="cc-row" style="gap:6px"><button class="cc-btn sm" data-act="place" data-arg="{p["id"]}">Reviews &amp; more</button>
          <button class="cc-btn sm ghost" data-act="plan" data-arg="{p["id"]}">Start here</button></div>''',
                              actions={'place': self.open_place, 'plan': lambda a: state.go('plan/from/' + a)})
        self.mv.add_marker(p['lat'], p['lng'], emo, p['kind'], popup=el, deal=bool(deal), layer='places', tooltip=p['name'])
        shown.append(p)
    if shown and not getattr(self, '_fitted', False):
      self._fitted = True
      self.mv.fit(shown, padding=30, max_zoom=14)

  def set_filter(self, f):
    self.filter = f
    chips = ui.dom(self).querySelectorAll('.js-filters .cc-chip')
    for i in range(chips.length):
      c = chips.item(i)
      if c.getAttribute('data-arg') == f:
        c.classList.add('on')
      else:
        c.classList.remove('on')
    self.draw()

  def toggle_pick(self, _=None):
    self.picking = not self.picking
    self.mv.set_picking(self.picking)
    b = ui.dom(self).querySelector('.js-propose')
    b.textContent = '✖ Cancel' if self.picking else '➕ Propose a place'
    if self.picking:
      ui.toast("Click the map where the place is 👇", 'info')

  def map_clicked(self, lat, lng):
    if not self.picking:
      return
    self.toggle_pick()
    res = dialogs.place_form('Propose a place', 'Share a stop worth stopping for. Other walkers can review it and add it to routes.',
                             lat=lat, lng=lng, ask_desc=True, button='Put it on the map (+3 pts)')
    if not res:
      return
    place = ui.call('add_place', res)
    if place is ui.FAIL:
      return
    ui.toast(f"{place['name']} is on the map! +3 pts 📍")
    self.data['places'].append(place)
    self.draw()
    state.refresh_me()

  def open_place(self, pid):
    dialogs.place_details(pid)
