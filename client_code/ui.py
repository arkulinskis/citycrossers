"""UI toolkit: constants, HTML builders, formatting, server calls, small widgets."""
import math
import datetime

import anvil
import anvil.js
import anvil.server
import anvil.tz
from anvil import HtmlTemplate, TextBox, TextArea, DropDown, DatePicker, CheckBox, Notification, alert, confirm

# ------------------------------------------------------------------ constants

KINDS = {
  'start': ('🚩', 'Meeting point'), 'cafe': ('☕', 'Coffee stop'), 'food': ('🥐', 'Food stop'),
  'treat': ('🍦', 'Treat stop'), 'park': ('🌳', 'Park'), 'view': ('👀', 'Viewpoint'),
  'rest': ('🪑', 'Rest stop'), 'water': ('🚰', 'Water refill'), 'culture': ('🏛️', 'Culture spot'),
  'finish': ('🏁', 'Finish line'),
}
PLACE_KINDS = ['cafe', 'food', 'treat', 'park', 'view', 'rest', 'water', 'culture']
BREAK_MIN = {'start': 0, 'cafe': 25, 'food': 40, 'treat': 15, 'park': 10, 'view': 10,
             'rest': 10, 'water': 5, 'culture': 20, 'finish': 0}
PACES = {'stroll': ('🐢', 'Stroll', '~3.6 km/h', 3.6), 'steady': ('🚶', 'Steady', '~4.5 km/h', 4.5),
         'brisk': ('⚡', 'Brisk', '~5.4 km/h', 5.4)}
VIBES = [
  ('pastry', '🥐', 'Pastry pilgrimage', 'grad-peach'),
  ('sunrise', '🌅', 'Sunrise stride', 'grad-sun'),
  ('parks', '🌳', 'Park hopper', 'grad-mint'),
  ('urban', '🏙️', 'Urban explorer', 'grad-sky'),
  ('river', '🌊', 'Riverside ramble', 'grad-sea'),
  ('food', '🍜', 'Food crawl', 'grad-berry'),
  ('night', '🌙', 'Night walk', 'grad-night'),
  ('history', '🏛️', 'History hunt', 'grad-sand'),
]
VIBE = {v[0]: v for v in VIBES}
INTERESTS = ["Coffee", "Bakeries", "Parks", "Rivers & canals", "Architecture", "History", "Street art", "Markets",
             "Photography", "Birdwatching", "Sunrise", "Night walks", "Dogs", "Picnics", "Podcasts", "Languages"]
WALK_TAGS = ["Beginner friendly", "Dog friendly", "Step-free", "Bakeries", "Coffee", "Parks", "History",
             "Rivers & canals", "Markets", "Photography", "Sunrise", "Night walks", "Picnics", "Quiet chat",
             "Language exchange"]
SNACK_STYLES = ["Pastry first", "Savory all day", "Coffee is a food group", "I pack my own", "Whatever's closest"]
SKILLS = ["🧭 Great navigator", "🥐 Snack scout", "⏱️ Pace keeper", "💬 Great company",
          "🛟 Safety-minded", "📸 Photo taker", "🗺️ Local legend", "🌅 Early riser"]
MOODS = ['🥰', '😄', '🙂', '😌', '🥵', '🥐', '🌅', '🤯', '😴']
LEVELS = [(0, "Stroller", "🚶"), (100, "Wanderer", "🥾"), (300, "Rambler", "🌿"), (700, "Pathfinder", "🧭"),
          (1500, "Trailblazer", "🔥"), (3000, "City Crosser", "🏙️")]
STREET_FACTOR = 1.25
DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

FAIL = object()


# ------------------------------------------------------------------ html basics

def esc(s):
  if s is None:
    return ''
  return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
          .replace('"', '&quot;').replace("'", '&#39;'))


def dom(component):
  return anvil.js.get_dom_node(component)


def add_cls(component, *names):
  node = dom(component)
  for n in names:
    for c in (n or '').split():
      node.classList.add(c)
  return component


def H(markup='', actions=None, classes=None):
  """An HtmlTemplate with delegated click actions: <button data-act="x" data-arg="y">."""
  h = HtmlTemplate(html=markup)
  if classes:
    add_cls(h, classes)
  if actions:
    bind(h, actions)
  return h


def bind(h, actions):
  node = dom(h)

  def handler(e):
    el = e.target.closest('[data-act]')
    if el is None or not node.contains(el):
      return
    fn = actions.get(el.getAttribute('data-act'))
    if fn is None:
      return
    e.stopPropagation()
    if el.tagName == 'A' and not el.getAttribute('href'):
      e.preventDefault()
    arg = el.getAttribute('data-arg')
    fn(arg)

  node.addEventListener('click', handler)
  return h


def on_click(component, fn):
  """Make a whole component clickable (ignores clicks on inner buttons/inputs)."""
  node = dom(component)
  node.classList.add('cc-clickable')

  def handler(e):
    if e.target.closest('button, a, input, textarea, select, [data-act]'):
      return
    fn()

  node.addEventListener('click', handler)
  return component


def slot(name, classes=''):
  return f'<div anvil-slot="{name}" class="{classes}"></div>'


def pill(text, color='', raw=False):
  return f'<span class="cc-pill {color}">{text if raw else esc(text)}</span>'


def btn(text, act, arg=None, kind='', raw=False, extra=''):
  a = f' data-arg="{esc(arg)}"' if arg is not None else ''
  return f'<button type="button" class="cc-btn {kind}" data-act="{act}"{a} {extra}>{text if raw else esc(text)}</button>'


def empty(emoji, title, text='', button=''):
  return (f'<div class="cc-empty"><span class="big">{emoji}</span><h3>{esc(title)}</h3>'
          f'<p class="muted">{esc(text)}</p>{button}</div>')


# ------------------------------------------------------------------ formatting

def local(d):
  if d is None:
    return None
  try:
    if isinstance(d, datetime.datetime) and d.tzinfo is not None:
      return d.astimezone(anvil.tz.tzlocal())
  except Exception:
    pass
  return d


def now_local():
  return datetime.datetime.now(anvil.tz.tzlocal())


def fmt_time(d):
  d = local(d)
  return f"{d.hour:02d}:{d.minute:02d}" if d else ''


def fmt_date(d, year=False):
  if d is None:
    return ''
  d = local(d)
  s = f"{DAYS[d.weekday()]} {d.day} {MONTHS[d.month - 1]}"
  if year:
    s += f" {d.year}"
  return s


def fmt_when(d):
  if d is None:
    return 'Date TBC'
  return f"{fmt_date(d)} · {fmt_time(d)}"


def days_until(d):
  if d is None:
    return None
  d = local(d)
  try:
    today = now_local().date()
    return (d.date() - today).days
  except Exception:
    return None


def fmt_rel(d):
  n = days_until(d)
  if n is None:
    return ''
  if n == 0:
    return 'Today'
  if n == 1:
    return 'Tomorrow'
  if n == -1:
    return 'Yesterday'
  if 1 < n < 7:
    return f'In {n} days'
  if n < 0:
    return f'{-n} days ago'
  if n < 14:
    return 'Next week'
  return f'In {n // 7} weeks'


def ago(d):
  if d is None:
    return ''
  try:
    secs = (now_local() - local(d)).total_seconds()
  except Exception:
    return ''
  if secs < 60:
    return 'just now'
  if secs < 3600:
    return f'{int(secs // 60)}m ago'
  if secs < 86400:
    return f'{int(secs // 3600)}h ago'
  if secs < 86400 * 7:
    return f'{int(secs // 86400)}d ago'
  return fmt_date(d)


def fmt_dur(minutes):
  minutes = int(minutes or 0)
  h, m = minutes // 60, minutes % 60
  if h and m:
    return f"{h}h {m:02d}m"
  return f"{h}h" if h else f"{m}m"


def km(v):
  v = v or 0
  return f"{v:.1f} km" if v < 100 else f"{int(v)} km"


def stars(n):
  n = int(round(n or 0))
  return '★' * n + '☆' * (5 - n)


# ------------------------------------------------------------------ geo (mirrors server)

def haversine(a, b):
  r = 6371.0
  p1, p2 = math.radians(a['lat']), math.radians(b['lat'])
  dp = math.radians(b['lat'] - a['lat'])
  dl = math.radians(b['lng'] - a['lng'])
  h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
  return 2 * r * math.asin(math.sqrt(h))


def route_stats(stops, pace):
  dist = 0.0
  legs = []
  for a, b in zip(stops, stops[1:]):
    d = haversine(a, b) * STREET_FACTOR
    legs.append(d)
    dist += d
  speed = PACES.get(pace, PACES['steady'])[3]
  breaks = [BREAK_MIN.get(s.get('kind'), 0) for s in stops]
  walking = dist / speed * 60
  return {'km': round(dist, 1), 'minutes': int(round(walking + sum(breaks))),
          'walk_min': int(round(walking)), 'breaks': len([b for b in breaks if b]),
          'break_min': sum(breaks), 'legs': legs, 'speed': speed}


def level_for(points):
  idx = 0
  for i, (th, _n, _e) in enumerate(LEVELS):
    if (points or 0) >= th:
      idx = i
  return LEVELS[idx]


# ------------------------------------------------------------------ people & walks html

def media_url(m):
  if m is None:
    return None
  try:
    return m.url
  except Exception:
    return None


def avatar(card, size=40):
  if not card:
    return ''
  url = media_url(card.get('avatar'))
  style = f"width:{size}px;height:{size}px;font-size:{max(11, int(size * 0.38))}px;background-color:{esc(card.get('avatar_color') or '#17A673')};"
  if url:
    style += f"background-image:url('{esc(url)}');"
    return f'<span class="cc-av" style="{style}" title="{esc(card.get("name"))}"></span>'
  return f'<span class="cc-av" style="{style}" title="{esc(card.get("name"))}">{esc(card.get("initials") or "?")}</span>'


def avatar_stack(cards, size=34, limit=5):
  cards = [c for c in cards if c and c.get('id')]
  out = ''.join(avatar(c, size) for c in cards[:limit])
  if len(cards) > limit:
    out += f'<span class="cc-av cc-av-more" style="width:{size}px;height:{size}px">+{len(cards) - limit}</span>'
  return f'<span class="cc-av-stack">{out}</span>'


def person(card, sub=None, size=44, link=True):
  if not card:
    return ''
  name = esc(card.get('name'))
  ver = ' <span class="cc-verified" title="Verified">✔</span>' if card.get('verified') else ''
  lvl = card.get('level') or {}
  sub = sub if sub is not None else esc(card.get('headline') or f"{lvl.get('emoji', '')} {lvl.get('name', '')}")
  nm = f'<a class="name" href="#u/{card["id"]}">{name}</a>' if link and card.get('id') else f'<span class="name">{name}</span>'
  return f'<div class="cc-person">{avatar(card, size)}<div class="who">{nm}{ver}<div class="sub">{sub}</div></div></div>'


def level_pill(card):
  lvl = (card or {}).get('level') or {}
  return pill(f"{lvl.get('emoji', '🚶')} {lvl.get('name', 'Stroller')}", 'sun')


def vibe_of(key):
  return VIBE.get(key) or VIBE['urban']


def strip(stops, limit=8):
  if not stops:
    return ''
  items = stops if len(stops) <= limit else stops[:limit - 1] + [stops[-1]]
  parts = []
  for i, s in enumerate(items):
    k = s.get('kind') or 'rest'
    if i:
      parts.append('<span class="seg"></span>')
    parts.append(f'<span class="dot {k}" title="{esc(s.get("name"))}">{KINDS.get(k, ("📍",))[0]}</span>')
  return f'<div class="cc-strip">{"".join(parts)}</div>'


STATUS_PILLS = {
  'going': ('✓ Going', 'green'), 'requested': ('⏳ Requested', 'sun'), 'invited': ('💌 Invited', 'berry'),
  'waitlist': ('🕒 Waitlist', 'sky'), 'declined': ('Declined', ''), 'left': ('Left', ''),
}


def walk_card(w, extra=''):
  v = vibe_of(w.get('vibe'))
  pace = PACES.get(w.get('pace'), PACES['steady'])
  status = ''
  if w.get('status') == 'completed':
    status = pill('🏁 Completed', 'dark')
  elif w.get('status') == 'cancelled':
    status = pill('Cancelled', 'dark')
  elif w.get('is_host'):
    status = pill('⭐ Hosting', 'dark')
  elif w.get('my_status') in STATUS_PILLS:
    t, c = STATUS_PILLS[w['my_status']]
    status = pill(t, c)
  vis = '🌍 Public' if w.get('visibility') == 'public' else '👯 Friends'
  host = w.get('host') or {}
  return f'''
  <div class="cc-walk-card">
    <div class="cover {v[3]}">
      <span class="status">{status}</span>
      <span class="emo">{v[1]}</span>
      <span class="when">{esc(fmt_rel(w.get("start")))}<br><span style="font-weight:600">{esc(fmt_when(w.get("start")))}</span></span>
    </div>
    <div class="body">
      <h4>{esc(w.get("title"))}</h4>
      <div class="facts"><span>📏 {km(w.get("distance_km"))}</span><span>⏱️ {fmt_dur(w.get("duration_min"))}</span>
        <span>{pace[0]} {pace[1]}</span><span>{vis}</span></div>
      {strip(w.get("stops") or [])}
      <div class="foot">
        <div class="cc-row" style="gap:8px">{avatar(host, 28)}<span class="small muted">by {esc(host.get("name", "someone"))}</span></div>
        <span class="small" style="font-weight:700">{w.get("going", 0)}/{w.get("max_walkers", 0)} going</span>
      </div>
      {extra}
    </div>
  </div>'''


def walk_cards_grid(walks, page_go, extra_fn=None, classes='cc-grid cards'):
  """Grid of clickable walk cards. Returns an HtmlTemplate."""
  html = '<div class="' + classes + '">'
  for w in walks:
    extra = extra_fn(w) if extra_fn else ''
    html += f'<div data-act="open" data-arg="{w["id"]}" class="cc-clickable" style="border-radius:20px">{walk_card(w, extra)}</div>'
  html += '</div>'
  return H(html, actions={'open': lambda wid: page_go('walk/' + wid)})


# ------------------------------------------------------------------ inputs

def textbox(placeholder='', text='', type='text'):
  if type == 'number':
    return TextBox(placeholder=placeholder, text=text if text not in (None, '') else None, type='number',
                   spacing_above='none', spacing_below='none')
  return TextBox(placeholder=placeholder, text=text or '', type=type, spacing_above='none', spacing_below='none')


def textarea(placeholder='', text='', height=110):
  return TextArea(placeholder=placeholder, text=text or '', height=height, spacing_above='none', spacing_below='none')


def dropdown(items, value=None, placeholder=None):
  d = DropDown(items=items, spacing_above='none', spacing_below='none')
  if placeholder:
    d.include_placeholder = True
    d.placeholder = placeholder
  if value is not None:
    try:
      d.selected_value = value
    except Exception:
      pass
  return d


def checkbox(text, checked=False):
  return CheckBox(text=text, checked=bool(checked), spacing_above='none', spacing_below='none')


def field(label, name, hint=''):
  h = f'<div class="hint">{esc(hint)}</div>' if hint else ''
  return f'<div class="cc-field"><label>{esc(label)}</label><div anvil-slot="{name}"></div>{h}</div>'


class Chips(object):
  """Multi- or single-select chip picker."""

  def __init__(self, options, selected=None, multi=True, color='', limit=None, on_change=None):
    self.options = [(o, o) if not isinstance(o, (list, tuple)) else (o[0], o[1]) for o in options]
    self.multi = multi
    self.color = color
    self.limit = limit
    self.on_change = on_change
    if multi:
      self.selected = list(selected or [])
    else:
      self.selected = [selected] if selected is not None else []
    self.component = H('', actions={'chip': self._toggle})
    self._render()

  def _render(self):
    out = '<div class="cc-chips">'
    for i, (val, label) in enumerate(self.options):
      on = 'on ' + self.color if val in self.selected else ''
      out += f'<button type="button" class="cc-chip {on}" data-act="chip" data-arg="{i}">{esc(label)}</button>'
    self.component.html = out + '</div>'

  def _toggle(self, idx):
    val = self.options[int(idx)][0]
    if self.multi:
      if val in self.selected:
        self.selected.remove(val)
      else:
        if self.limit and len(self.selected) >= self.limit:
          toast(f"Pick up to {self.limit}.", 'warning')
          return
        self.selected.append(val)
    else:
      self.selected = [val]
    self._render()
    if self.on_change:
      self.on_change(self.value)

  @property
  def value(self):
    return list(self.selected) if self.multi else (self.selected[0] if self.selected else None)


class Stars(object):
  def __init__(self, value=0):
    self.value = int(value or 0)
    self.component = H('', actions={'star': self._set})
    self._render()

  def _render(self):
    out = '<div class="cc-stars">'
    for i in range(1, 6):
      out += f'<button type="button" class="{"on" if i <= self.value else ""}" data-act="star" data-arg="{i}" aria-label="{i} stars">⭐</button>'
    self.component.html = out + '</div>'

  def _set(self, v):
    self.value = int(v)
    self._render()


# ------------------------------------------------------------------ feedback

def toast(msg, style='success', timeout=3.5):
  try:
    Notification(msg, style=style, timeout=timeout).show()
  except Exception:
    print(msg)


def confetti(emojis=None):
  try:
    if emojis:
      anvil.js.window.cc.confetti(emojis)
    else:
      anvil.js.window.cc.confetti()
  except Exception:
    pass


def copy_text(text):
  try:
    return bool(anvil.js.window.cc.copy(text))
  except Exception:
    return False


def modal(content, title=None, large=True, buttons=None, dismissible=True):
  return alert(content=content, title=title, large=large, buttons=buttons or [], dismissible=dismissible)


def close_modal(component, value=None):
  component.raise_event('x-close-alert', value=value)


def ask(text, title=None, yes='Yes', no='Cancel'):
  return confirm(text, title=title, buttons=[(no, False), (yes, True)])


def call(fn_name, *args, **kwargs):
  """Server call with friendly errors. Returns FAIL on error.
  If the server asks for the safety pledge, show it and retry once."""
  quiet = kwargs.pop('_quiet', False)
  try:
    if quiet:
      return anvil.server.call_s(fn_name, *args, **kwargs)
    return anvil.server.call(fn_name, *args, **kwargs)
  except Exception as e:
    msg = str(e)
    if 'SAFETY_PLEDGE_REQUIRED' in msg:
      from . import dialogs
      if dialogs.safety_pledge():
        return call(fn_name, *args, **kwargs)
      return FAIL
    if 'Please sign in' in msg or 'logged in' in msg.lower():
      from . import state
      state.go('landing')
      return FAIL
    for prefix in ('Exception: ', 'anvil.server.InternalError: '):
      if msg.startswith(prefix):
        msg = msg[len(prefix):]
    if not quiet:
      toast(msg or "Something went wrong. Try again?", 'danger', 5)
    return FAIL
