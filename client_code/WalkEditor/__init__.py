from ._anvil_designer import WalkEditorTemplate
from anvil import *
import anvil.js
import datetime

from .. import ui, state, dialogs
from ..ui import esc
from ..mapkit import MapView

STOP_KINDS = ['start', 'cafe', 'food', 'treat', 'park', 'view', 'rest', 'water', 'culture', 'finish']
SIZES = [2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30]


def next_saturday():
  today = datetime.date.today()
  days = (5 - today.weekday()) % 7 or 7
  d = today + datetime.timedelta(days=days)
  return datetime.datetime(d.year, d.month, d.day, 9, 30)


class WalkEditor(WalkEditorTemplate):
  def __init__(self, walk_id=None, start_place=None, **properties):
    self.init_components(**properties)
    self.walk_id = walk_id
    self.stops = []
    self.vibe = 'urban'
    self.pace = 'steady'
    self.visibility = 'friends'
    existing = None
    if walk_id:
      existing = ui.call('get_walk_for_edit', walk_id)
      if existing is ui.FAIL:
        self.html = '<div class="cc-page">' + ui.empty('🙈', "Can't edit this walk", "Only the host can change the plan.") + '</div>'
        return
    md = ui.call('map_data')
    self.places = md['places'] if md is not ui.FAIL else []
    friends = ui.call('my_friends')
    self.friends = friends if friends is not ui.FAIL else []

    # ---- inputs
    ex = existing or {}
    self.title = ui.textbox('e.g. Canal Crawl: Little Venice → Limehouse', text=ex.get('title'))
    self.desc = ui.textarea("What's the vibe? Where are the best stops? What should people bring?", text=ex.get('description'), height=110)
    self.when = DatePicker(date=ex.get('start') or next_saturday(), pick_time=True, format='%a %d %b %Y, %H:%M',
                           min_date=datetime.date.today(), spacing_above='none', spacing_below='none')
    self.size = ui.dropdown([(f"{n} walkers" + (" (incl. you)" if n == 2 else ""), n) for n in SIZES], value=ex.get('max_walkers') or 8)
    self.meeting = ui.textbox('e.g. By the blue café boat. Look for the green balloon!', text=ex.get('meeting_note'))
    self.approval = ui.checkbox('🙋 I approve requests before people join (recommended)', ex.get('approval_required', True))
    self.tags = ui.Chips(ui.WALK_TAGS, selected=ex.get('tags') or [], limit=6)
    invited = ex.get('invited_ids') or []
    self.invites = ui.Chips([(f['id'], f['name']) for f in self.friends], selected=invited) if self.friends else None
    self.vibe = ex.get('vibe') or 'urban'
    self.pace = ex.get('pace') or 'steady'
    self.visibility = ex.get('visibility') or 'friends'
    for s in ex.get('stops') or []:
      self.stops.append({'name': s['name'], 'kind': s['kind'], 'lat': s['lat'], 'lng': s['lng'],
                         'place_id': s.get('place_id'), 'note': s.get('note') or ''})

    # ---- dynamic bits
    self.vibe_view = ui.H('', actions={'vibe': self.set_vibe})
    self.pace_view = ui.H('', actions={'pace': self.set_pace})
    self.vis_view = ui.H('', actions={'vis': self.set_vis})
    self.stops_view = ui.H('', actions={'up': self.move_up, 'down': self.move_down, 'del': self.remove_stop,
                                        'edit': self.edit_stop, 'locate': lambda a: self.mv.locate()})
    self.mv = MapView(height='420px', on_click=self.map_clicked, scroll_zoom=True, classes='picking')
    ui.bind(self, {'save': self.save, 'cancel': lambda a: state.go('walk/' + walk_id if walk_id else 'discover')})

    if start_place and not self.stops:
      p = self._place(start_place)
      if p:
        self.stops.append({'name': p['name'], 'kind': 'start', 'lat': p['lat'], 'lng': p['lng'], 'place_id': p['id'], 'note': ''})
        self.mv.center = [p['lat'], p['lng']]
    self.render()

  def _place(self, pid):
    for p in self.places:
      if p['id'] == pid:
        return p
    return None

  # ------------------------------------------------------------ layout
  def render(self):
    editing = bool(self.walk_id)
    self.html = f'''
    <div class="cc-page">
      <div style="margin-bottom:18px">
        <h1 style="margin:0">{"✏️ Edit your walk" if editing else "🗺️ Plan a walk"}</h1>
        <p class="muted" style="margin:4px 0 0">{"Changes notify everyone who's going." if editing else
          "Pick a route, sprinkle in snack stops, and invite your crew. We'll handle the maths."}</p>
      </div>
      <div class="cc-grid halves" style="align-items:start">
        <div class="cc-stack">
          <div class="cc-card">
            <h3>1 · The basics</h3>
            {ui.field("Walk name", "title")}
            <div class="cc-field"><label>Vibe</label>{ui.slot("vibe")}</div>
            {ui.field("Description", "desc")}
            <div class="cc-field"><label>Tags <span class="muted small">(up to 6)</span></label>{ui.slot("tags")}</div>
          </div>
          <div class="cc-card">
            <h3>2 · When &amp; how fast</h3>
            <div class="cc-form-row">{ui.field("Start", "when")}{ui.field("Group size", "size")}</div>
            <div class="cc-field"><label>Pace</label>{ui.slot("pace")}</div>
            {ui.field("Meeting spot details (shown to people going)", "meeting", "Meet somewhere public and easy to find.")}
          </div>
          <div class="cc-card">
            <h3>4 · Who's coming?</h3>
            {ui.slot("vis")}
            <div style="margin-top:12px">{ui.slot("approval")}</div>
            <div class="cc-field" style="margin-top:14px"><label>💌 Invite connections</label>
              {ui.slot("invites") if self.friends else '<p class="small muted" style="margin:0">No connections yet. Open the walk to the public, or find walkers on the <a href="#people">People</a> page. You can also invite by email after creating it.</p>'}</div>
          </div>
        </div>
        <div class="cc-stack" style="position:sticky;top:84px">
          <div class="cc-card">
            <div class="cc-card-title"><h3>3 · The route</h3><button class="cc-btn ghost sm" data-act="locate" type="button">📍 Near me</button></div>
            <p class="small muted" style="margin-top:-6px">Click the map to drop stops, or tap an existing pin and choose “Add to route”.
              First stop is the meeting point, last is the finish line.</p>
            <div class="cc-map-wrap" style="margin-bottom:14px">{ui.slot("map")}</div>
            {ui.slot("stops")}
          </div>
        </div>
      </div>
      <div class="cc-card" style="margin-top:20px;display:flex;gap:12px;align-items:center;flex-wrap:wrap;position:sticky;bottom:12px;z-index:5;box-shadow:var(--shadow-lg)">
        <span class="small muted" style="flex:1;min-width:200px">🛟 Tip: public walks start somewhere busy, and you approve who joins.</span>
        <button class="cc-btn ghost" data-act="cancel" type="button">Cancel</button>
        <button class="cc-btn orange lg" data-act="save" type="button">{"Save changes" if editing else "Create walk &amp; notify friends 🎉"}</button>
      </div>
    </div>'''
    self.add_component(self.title, slot='title')
    self.add_component(self.vibe_view, slot='vibe')
    self.add_component(self.desc, slot='desc')
    self.add_component(self.tags.component, slot='tags')
    self.add_component(self.when, slot='when')
    self.add_component(self.size, slot='size')
    self.add_component(self.pace_view, slot='pace')
    self.add_component(self.meeting, slot='meeting')
    self.add_component(self.vis_view, slot='vis')
    self.add_component(self.approval, slot='approval')
    if self.invites:
      self.add_component(self.invites.component, slot='invites')
    self.add_component(self.mv.component, slot='map')
    self.add_component(self.stops_view, slot='stops')
    self.render_vibes()
    self.render_pace()
    self.render_vis()
    self.render_stops()
    self.draw_places()
    if self.stops:
      self.mv.fit(self.stops, max_zoom=15)

  # ------------------------------------------------------------ pickers
  def render_vibes(self):
    self.vibe_view.html = '<div class="cc-vibes">' + ''.join(
      f'<button type="button" class="cc-vibe {g} {"on" if k == self.vibe else ""}" data-act="vibe" data-arg="{k}"><span class="e">{e}</span>{esc(n)}</button>'
      for k, e, n, g in ui.VIBES) + '</div>'

  def set_vibe(self, k):
    self.vibe = k
    self.render_vibes()

  def render_pace(self):
    self.pace_view.html = '<div class="cc-options" style="grid-template-columns:repeat(3,1fr)">' + ''.join(
      f'<button type="button" class="cc-option {"on" if k == self.pace else ""}" data-act="pace" data-arg="{k}"><b>{v[0]} {v[1]}</b><span>{v[2]}</span></button>'
      for k, v in ui.PACES.items()) + '</div>'

  def set_pace(self, k):
    self.pace = k
    self.render_pace()
    self.render_stops()

  def render_vis(self):
    opts = [('friends', '👯 Friends only', 'Only people you invite and your connections can see it.'),
            ('public', '🌍 Open to the public', "Shows up in walkers' Discover decks. Great when your friends are busy.")]
    self.vis_view.html = '<div class="cc-options">' + ''.join(
      f'<button type="button" class="cc-option {"on" if k == self.visibility else ""}" data-act="vis" data-arg="{k}"><b>{t}</b><span>{esc(d)}</span></button>'
      for k, t, d in opts) + '</div>'
    self.approval.visible = self.visibility == 'public'

  def set_vis(self, k):
    self.visibility = k
    if k == 'public' and (self.size.selected_value or 8) < 3:
      self.size.selected_value = 6
    self.render_vis()

  # ------------------------------------------------------------ stops
  def render_stops(self):
    if not self.stops:
      self.stops_view.html = ('<div class="cc-empty" style="padding:18px"><span class="big">👆</span>'
                              '<b>Click the map to drop your meeting point.</b></div>')
      self.draw_route()
      return
    st = ui.route_stats(self.stops, self.pace)
    rows = ''
    for i, s in enumerate(self.stops):
      emo, kname = ui.KINDS.get(s['kind'], ('📍', 'Stop'))
      brk = ui.BREAK_MIN.get(s['kind'], 0)
      leg = f' · {st["legs"][i - 1]:.1f} km from last stop' if i > 0 else ''
      rows += f'''<div class="cc-stop-row"><span class="n">{i + 1}</span><span class="e">{emo}</span>
        <div class="t"><b>{esc(s["name"])}</b><span>{esc(kname)}{" · " + str(brk) + " min break" if brk else ""}{leg}</span></div>
        <div class="ctl"><button type="button" data-act="edit" data-arg="{i}" title="Edit">✏️</button>
          <button type="button" data-act="up" data-arg="{i}" title="Move up">↑</button>
          <button type="button" data-act="down" data-arg="{i}" title="Move down">↓</button>
          <button type="button" data-act="del" data-arg="{i}" title="Remove">✕</button></div></div>'''
    # The break manifesto: flag long stretches without a pause
    warn = ''
    run = 0.0
    longest = 0.0
    for i, leg in enumerate(st['legs']):
      run += leg
      longest = max(longest, run)
      if ui.BREAK_MIN.get(self.stops[i + 1]['kind'], 0) > 0:
        run = 0.0
    food = len([s for s in self.stops if s['kind'] in ('cafe', 'food', 'treat')])
    if longest > 6:
      warn += f'<div class="cc-alert orange" style="margin-top:10px"><span class="ico">⏸️</span><span>There\'s a {longest:.1f} km stretch without a break. The break manifesto suggests a pause every ~5 km.</span></div>'
    if len(self.stops) >= 2 and food == 0:
      warn += '<div class="cc-alert" style="margin-top:10px"><span class="ico">🥐</span><span>No food stop yet! Every CityCrossers walk deserves at least one.</span></div>'
    if len(self.stops) >= 2 and self.stops[-1]['kind'] != 'finish':
      warn += '<div class="cc-alert sky" style="margin-top:10px"><span class="ico">🏁</span><span>Tip: make the last stop a finish line (✏️ to edit) so people know where it ends.</span></div>'
    summary = f'''<div class="cc-route-sum" style="margin-top:12px">
      <div><b>{st["km"]}</b><span>km (approx.)</span></div>
      <div><b>{ui.fmt_dur(st["minutes"])}</b><span>total time</span></div>
      <div><b>{st["breaks"]}</b><span>breaks · {ui.fmt_dur(st["break_min"])}</span></div>
      <div class="note">{ui.PACES[self.pace][0]} {ui.fmt_dur(st["walk_min"])} walking at {ui.PACES[self.pace][2]} · distances follow streets roughly</div></div>'''
    self.stops_view.html = rows + summary + warn
    self.draw_route()

  def _insert(self, stop):
    if not self.stops:
      stop['kind'] = 'start'
      self.stops.append(stop)
    elif len(self.stops) == 1:
      if stop['kind'] in ('start',):
        stop['kind'] = 'finish'
      self.stops.append(stop)
    elif self.stops[-1]['kind'] == 'finish' and stop['kind'] != 'finish':
      self.stops.insert(len(self.stops) - 1, stop)
    else:
      self.stops.append(stop)
    self.render_stops()

  def map_clicked(self, lat, lng):
    n = len(self.stops)
    default = 'start' if n == 0 else ('finish' if n == 1 else 'cafe')
    title = 'Add the meeting point' if n == 0 else ('Add the finish line' if n == 1 else 'Add a stop')
    res = dialogs.place_form(title, 'Give it a name people will recognise.', lat=lat, lng=lng, kinds=STOP_KINDS,
                             default_kind=default, button='Add to route')
    if res:
      self._insert({'name': res['name'], 'kind': res['kind'], 'lat': lat, 'lng': lng, 'place_id': None, 'note': ''})

  def add_place(self, pid):
    p = self._place(pid)
    if not p:
      return
    if any(s.get('place_id') == pid for s in self.stops):
      ui.toast("That's already on your route.", 'info')
      return
    self._insert({'name': p['name'], 'kind': p['kind'], 'lat': p['lat'], 'lng': p['lng'], 'place_id': p['id'], 'note': ''})
    ui.toast(f"Added {p['name']} ✓")

  def edit_stop(self, i):
    i = int(i)
    s = self.stops[i]
    res = dialogs.place_form('Edit stop', '', lat=s['lat'], lng=s['lng'], kinds=STOP_KINDS, default_kind=s['kind'],
                             name=s['name'], button='Save')
    if res:
      s['name'], s['kind'] = res['name'], res['kind']
      self.render_stops()

  def move_up(self, i):
    i = int(i)
    if i > 0:
      self.stops[i - 1], self.stops[i] = self.stops[i], self.stops[i - 1]
      self.render_stops()

  def move_down(self, i):
    i = int(i)
    if i < len(self.stops) - 1:
      self.stops[i + 1], self.stops[i] = self.stops[i], self.stops[i + 1]
      self.render_stops()

  def remove_stop(self, i):
    self.stops.pop(int(i))
    self.render_stops()

  # ------------------------------------------------------------ map
  def draw_places(self):
    self.mv.clear('places')
    used = set(s.get('place_id') for s in self.stops)
    for p in self.places:
      if p['id'] in used:
        continue
      emo = ui.KINDS.get(p['kind'], ('📍',))[0]
      deal = p['deals'][0] if p['deals'] else None
      el = self.mv.popup_el(f'''<h4>{emo} {esc(p["name"])}</h4><div class="small muted">{esc(p["description"][:100])}</div>
        {('<div style="margin-top:6px"><span class="cc-deal-tag">DEAL</span> <b class="small">' + esc(deal["title"]) + '</b></div>') if deal else ''}
        <button class="cc-btn sm" data-act="add" data-arg="{p["id"]}">➕ Add to route</button>''', actions={'add': self.add_place})
      self.mv.add_marker(p['lat'], p['lng'], emo, p['kind'], popup=el, deal=bool(deal), layer='places', tooltip=p['name'])

  def draw_route(self):
    self.mv.clear('route')
    self.mv.route(self.stops, layer='route')
    for i, s in enumerate(self.stops):
      self.mv.add_marker(s['lat'], s['lng'], ui.KINDS.get(s['kind'], ('📍',))[0], s['kind'], number=i + 1,
                         layer='route', tooltip=s['name'])
    self.draw_places()

  # ------------------------------------------------------------ save
  def save(self, _=None):
    title = (self.title.text or '').strip()
    if len(title) < 3:
      ui.toast("Give your walk a name first.", 'warning')
      return
    if len(self.stops) < 2:
      ui.toast("Add at least a meeting point and a finish line on the map.", 'warning')
      return
    if not self.when.date:
      ui.toast("Pick a start date and time.", 'warning')
      return
    data = {
      'title': title, 'description': self.desc.text, 'start': self.when.date, 'pace': self.pace,
      'max_walkers': self.size.selected_value or 8, 'visibility': self.visibility, 'vibe': self.vibe,
      'tags': self.tags.value, 'approval_required': self.approval.checked if self.visibility == 'public' else True,
      'meeting_note': self.meeting.text, 'stops': self.stops,
      'invite_ids': self.invites.value if self.invites else [],
    }
    if self.walk_id:
      wid = ui.call('update_walk', self.walk_id, data)
      if wid is ui.FAIL:
        return
      ui.toast("Walk updated ✓")
    else:
      wid = ui.call('create_walk', data)
      if wid is ui.FAIL:
        return
      ui.confetti(['🥐', '☕', '🗺️', '🎉', '🥾'])
      ui.toast("Your walk is live! +10 pts 🎉")
    state.refresh_me()
    state.go('walk/' + wid)
