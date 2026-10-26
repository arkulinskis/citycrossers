"""Modal dialogs: auth, safety pledge, places/stops, reviews, journal, reports, invites."""
import datetime

import anvil
import anvil.users
import anvil.server
from anvil import TextBox, DatePicker, FileLoader

from . import ui, state
from .ui import esc


# ================================================================== auth

def auth(mode='signup'):
  box = _AuthBox(mode)
  return ui.modal(box.component, large=False)


class _AuthBox(object):
  def __init__(self, mode):
    self.mode = mode
    self.name = ui.textbox('First name or walking alias')
    self.email = ui.textbox('you@example.com', type='email')
    self.pw = TextBox(placeholder='Password (8+ characters)', hide_text=True, spacing_above='none', spacing_below='none')
    for tb in (self.name, self.email, self.pw):
      tb.add_event_handler('pressed_enter', lambda **e: self.submit())
    self.component = ui.H(f'''
      <div class="cc-auth">
        <div class="head"><img src="_/theme/logo.svg" alt="" style="width:64px;height:64px;display:block;margin:0 auto 6px">
          <h2 class="cc-modal-title t-title"></h2>
          <div class="cc-modal-sub t-sub"></div>
        </div>
        <div class="cc-error hidden"></div>
        <div class="f-name">{ui.field("What should walkers call you?", "name")}</div>
        {ui.field("Email", "email")}
        {ui.field("Password", "pw")}
        <button type="button" class="cc-btn block lg t-go" data-act="go"></button>
        <div class="switch">
          <span class="t-switch-text"></span> <button type="button" class="cc-link" data-act="switch"></button>
          <div class="f-forgot" style="margin-top:8px"><button type="button" class="cc-link" data-act="forgot">Forgot your password?</button></div>
        </div>
        <p class="tiny muted center" style="margin-top:14px">By joining you agree to walk kindly, follow our
          safety guidelines, and never leave anyone behind at a bakery.</p>
      </div>''', actions={'go': lambda a: self.submit(), 'switch': lambda a: self.set_mode(
        'login' if self.mode == 'signup' else 'signup'), 'forgot': lambda a: self.forgot()})
    self.component.add_component(self.name, slot='name')
    self.component.add_component(self.email, slot='email')
    self.component.add_component(self.pw, slot='pw')
    self.set_mode(mode)

  def _q(self, sel):
    return ui.dom(self.component).querySelector(sel)

  def set_mode(self, mode):
    self.mode = mode
    signup = mode == 'signup'
    self._q('.t-title').textContent = 'Join the walk' if signup else 'Welcome back'
    self._q('.t-sub').textContent = ('Free forever. Long walks, new people, snack stops guaranteed.' if signup
                                     else 'Your crew (and your snacks) missed you.')
    self._q('.t-go').textContent = 'Create my account' if signup else 'Log in'
    self._q('.t-switch-text').textContent = 'Already walking with us?' if signup else 'New here?'
    self._q('[data-act=switch]').textContent = 'Log in' if signup else 'Create an account'
    for sel, show in (('.f-name', signup), ('.f-forgot', not signup)):
      el = self._q(sel)
      if show:
        el.classList.remove('hidden')
      else:
        el.classList.add('hidden')
    self.error(None)

  def error(self, msg):
    el = self._q('.cc-error')
    if msg:
      el.textContent = msg
      el.classList.remove('hidden')
    else:
      el.classList.add('hidden')

  def submit(self):
    email = (self.email.text or '').strip()
    pw = self.pw.text or ''
    if '@' not in email:
      return self.error("Please enter a valid email address.")
    if len(pw) < 8:
      return self.error("Passwords need at least 8 characters.")
    try:
      if self.mode == 'signup':
        name = (self.name.text or '').strip()
        if len(name) < 2:
          return self.error("Tell us what to call you (2+ characters).")
        anvil.users.signup_with_email(email, pw, remember=True)
        anvil.server.call('update_me', {'display_name': name})
        state.after_login = state.after_login or 'welcome'
      else:
        anvil.users.login_with_email(email, pw, remember=True)
    except anvil.users.UserExists:
      self.set_mode('login')
      return self.error("You already have an account. Log in instead.")
    except Exception as e:
      return self.error(str(e).replace('anvil.users.', ''))
    ui.close_modal(self.component, True)

  def forgot(self):
    email = (self.email.text or '').strip()
    if '@' not in email:
      return self.error("Type your email above first, then click 'Forgot your password?'.")
    try:
      anvil.users.send_password_reset_email(email)
      ui.toast("If that email has an account, a reset link is on its way.")
    except Exception as e:
      self.error(str(e))


# ================================================================== safety pledge

PLEDGE = [
  ("📍", "I'll meet in public places", "Meeting points are busy, well-lit public spots. Never someone's home."),
  ("📲", "I'll tell someone my plans", "Share the walk link with a friend or family member before you go."),
  ("👀", "I'll trust my gut", "If something feels off, I can leave at any time, no explanation needed."),
  ("🤝", "I'll be a good walker", "Respect, consent and kindness. Zero tolerance for harassment."),
  ("💧", "I'll look after myself", "Water, snacks, comfy shoes, a charged phone. Know your limits."),
  ("🚩", "I'll report problems", "Reports go straight to our team and are kept confidential."),
]


def safety_pledge():
  items = ''.join(f'''<label class="cc-card flat" style="display:flex;gap:12px;align-items:flex-start;padding:12px 14px;margin-bottom:8px;cursor:pointer">
      <input type="checkbox" style="width:20px;height:20px;accent-color:#17A673;margin-top:3px;flex-shrink:0">
      <span><b>{e} {esc(t)}</b><br><span class="small muted">{esc(d)}</span></span></label>''' for e, t, d in PLEDGE)
  holder = {}

  def accept(_):
    boxes = ui.dom(holder['c']).querySelectorAll('input[type=checkbox]')
    for i in range(boxes.length):
      if not boxes.item(i).checked:
        ui.toast("Tick every promise to continue. They're short, we promise.", 'warning')
        return
    res = ui.call('accept_safety_pledge')
    if res is not ui.FAIL:
      state.set_me(res)
      ui.toast("Pledge taken. +10 pts 🛟")
      ui.close_modal(holder['c'], True)

  c = ui.H(f'''<div>
      <div class="cc-modal-title">🛟 The CityCrossers safety pledge</div>
      <div class="cc-modal-sub">Before your first walk with new people, a few promises. Takes 20 seconds, counts forever.</div>
      {items}
      <div class="cc-row end" style="margin-top:12px">
        <button type="button" class="cc-btn ghost" data-act="no">Not now</button>
        <button type="button" class="cc-btn" data-act="yes">I promise 🤝</button>
      </div></div>''', actions={'yes': accept, 'no': lambda a: ui.close_modal(holder['c'], False)})
  holder['c'] = c
  return bool(ui.modal(c, large=True))


# ================================================================== place / stop picker

def place_form(title, subtitle='', lat=None, lng=None, kinds=None, default_kind='cafe', with_map=False,
               context=None, ask_desc=False, name='', button='Add'):
  """Returns {'name','kind','lat','lng','description'} or None."""
  from .mapkit import MapView
  kinds = kinds or ui.PLACE_KINDS
  pick = {'lat': lat, 'lng': lng}
  name_tb = ui.textbox('e.g. Kettle & Crumb, or "the bench with the view"', text=name)
  desc_ta = ui.textarea('What makes it a good stop? (optional)', height=70)
  kind = ui.Chips([(k, ui.KINDS[k][0] + ' ' + ui.KINDS[k][1]) for k in kinds], selected=default_kind, multi=False)
  holder = {}
  mv = None

  def set_point(la, ln):
    pick['lat'], pick['lng'] = la, ln
    mv.clear('pick')
    mv.add_marker(la, ln, ui.KINDS.get(kind.value or 'rest', ('📍',))[0], kind.value or 'rest', layer='pick', draft=True)
    hint = ui.dom(holder['c']).querySelector('.pick-hint') if 'c' in holder else None
    if hint:
      hint.textContent = '📍 Spot picked. Click again to move it.'

  def save(_):
    nm = (name_tb.text or '').strip()
    if len(nm) < 2:
      ui.toast("Give it a name.", 'warning')
      return
    if pick['lat'] is None:
      ui.toast("Click the map to drop the pin.", 'warning')
      return
    ui.close_modal(holder['c'], {'name': nm, 'kind': kind.value or default_kind, 'lat': pick['lat'], 'lng': pick['lng'],
                                 'description': (desc_ta.text or '').strip()})

  map_html = ''
  if with_map:
    map_html = '<div class="cc-map-wrap" style="margin-bottom:14px">' + ui.slot('map') + '</div><p class="small muted pick-hint">👆 Click the map to drop a pin.</p>'
  c = ui.H(f'''<div>
      <div class="cc-modal-title">{esc(title)}</div>
      <div class="cc-modal-sub">{esc(subtitle)}</div>
      {map_html}
      {ui.field("Name", "name")}
      <div class="cc-field"><label>What kind of stop?</label>{ui.slot("kind")}</div>
      {ui.field("Description", "desc") if ask_desc else ""}
      <div class="cc-row end"><button type="button" class="cc-btn ghost" data-act="no">Cancel</button>
      <button type="button" class="cc-btn" data-act="yes">{esc(button)}</button></div></div>''',
           actions={'yes': save, 'no': lambda a: ui.close_modal(holder['c'], None)})
  holder['c'] = c
  if with_map:
    center = [lat, lng] if lat is not None else None
    mv = MapView(height='320px', center=center, zoom=14, on_click=set_point, classes='picking')
    c.add_component(mv.component, slot='map')
    for i, p in enumerate(context or []):
      mv.add_marker(p['lat'], p['lng'], ui.KINDS.get(p.get('kind'), ('📍',))[0], p.get('kind') or 'rest',
                    number=i + 1, layer='ctx', tooltip=p.get('name'))
    if context:
      mv.fit(context)
    mv.route(context or [], layer='ctx')
    if lat is not None:
      mv.when_ready(lambda: set_point(lat, lng))
  c.add_component(name_tb, slot='name')
  c.add_component(kind.component, slot='kind')
  if ask_desc:
    c.add_component(desc_ta, slot='desc')
  return ui.modal(c, large=True)


# ================================================================== reviews

def review(place_name, place_id=None, stop_id=None, walk_id=None, existing=None):
  """Write (or edit) a review. Returns True when saved."""
  ex = existing or {}
  stars = ui.Stars(ex.get('rating') or 0)
  title = ui.textbox('Sum it up in a few words', text=ex.get('title'))
  body = ui.textarea('What was it like? What should people order?', text=ex.get('body'), height=100)
  future = ui.textarea('Dear future me... (only you can see this)', text=ex.get('future_note'), height=70)
  default_public = ex.get('is_public') if existing else bool((state.me or {}).get('journal_public_default', False))
  again = ui.checkbox("I'd come back here", ex.get('would_return', True) if existing else True)
  public = ui.checkbox("🌍 Make this review public (+4 pts). Your note to future you stays private.", default_public)
  holder = {}

  def save(_):
    if not stars.value:
      ui.toast("Tap the stars to rate it.", 'warning')
      return
    data = {'place_id': place_id, 'stop_id': stop_id, 'walk_id': walk_id, 'review_id': ex.get('id'),
            'rating': stars.value, 'title': title.text, 'body': body.text, 'future_note': future.text,
            'would_return': again.checked, 'is_public': public.checked}
    res = ui.call('save_review', data)
    if res is not ui.FAIL:
      ui.toast(res['message'])
      ui.close_modal(holder['c'], True)

  c = ui.H(f'''<div>
      <div class="cc-modal-title">⭐ Review {esc(place_name)}</div>
      <div class="cc-modal-sub">Reviews live in your Journey. Keep them private as notes for future you, or share your taste with the world.</div>
      <div class="cc-field">{ui.slot("stars")}</div>
      {ui.field("Headline", "title")}
      {ui.field("Your review", "body")}
      <div class="cc-field"><label>💌 Note to future me</label>{ui.slot("future")}
        <div class="hint">e.g. “Order the cardamom bun, skip the latte. Sit upstairs.”</div></div>
      {ui.slot("again")}{ui.slot("public")}
      <div class="cc-row end" style="margin-top:14px"><button type="button" class="cc-btn ghost" data-act="no">Cancel</button>
      <button type="button" class="cc-btn orange" data-act="yes">Save review</button></div></div>''',
           actions={'yes': save, 'no': lambda a: ui.close_modal(holder['c'], False)})
  holder['c'] = c
  c.add_component(stars.component, slot='stars')
  c.add_component(title, slot='title')
  c.add_component(body, slot='body')
  c.add_component(future, slot='future')
  c.add_component(again, slot='again')
  c.add_component(public, slot='public')
  return bool(ui.modal(c, large=True))


def review_any():
  """Pick any place from the map, then review it."""
  places = ui.call('reviewable_places')
  if places is ui.FAIL:
    return False
  if not places:
    ui.toast("No places on the map yet. Add one from the Map page.", 'warning')
    return False
  dd = ui.dropdown([(ui.KINDS.get(p['kind'], ('📍',))[0] + ' ' + p['name'], p['id']) for p in places],
                   placeholder='Choose a place…')
  holder = {}

  def go(_):
    if not dd.selected_value:
      ui.toast("Pick a place first.", 'warning')
      return
    ui.close_modal(holder['c'], dd.selected_value)

  c = ui.H(f'''<div><div class="cc-modal-title">Which place?</div>
      <div class="cc-modal-sub">Any spot on the CityCrossers map. Not there? Add it from the Map page first.</div>
      {ui.field("Place", "dd")}
      <div class="cc-row end"><button type="button" class="cc-btn ghost" data-act="no">Cancel</button>
      <button type="button" class="cc-btn" data-act="go">Next</button></div></div>''',
           actions={'go': go, 'no': lambda a: ui.close_modal(holder['c'], None)})
  holder['c'] = c
  c.add_component(dd, slot='dd')
  pid = ui.modal(c, large=False)
  if not pid:
    return False
  name = [p['name'] for p in places if p['id'] == pid][0]
  return review(name, place_id=pid)


# ================================================================== journal

def entry(existing=None, walk=None):
  ex = existing or {}
  mood = ui.Chips(ui.MOODS, selected=ex.get('mood') or '🙂', multi=False)
  title = ui.textbox('A title for this moment', text=ex.get('title') or (f"Walking “{walk['title']}”" if walk else ''))
  body = ui.textarea('What happened? Who did you meet? What did you eat? Future you will love this.', text=ex.get('body'), height=150)
  dp = DatePicker(date=ex.get('date') or datetime.date.today(), format='%d %b %Y', pick_time=False,
                  spacing_above='none', spacing_below='none')
  kmb = ui.textbox('e.g. 14.5', text=ex.get('km') if ex.get('km') is not None else (walk.get('distance_km') if walk else ''), type='number')
  photo = FileLoader(text='📷 Add a photo', file_types='image/*', spacing_above='none', spacing_below='none')
  default_public = ex.get('is_public') if existing else bool((state.me or {}).get('journal_public_default', False))
  public = ui.checkbox('🌍 Show this on my public profile', default_public)
  holder = {}

  def save(_):
    data = {'id': ex.get('id'), 'mood': mood.value, 'title': title.text, 'body': body.text, 'entry_date': dp.date,
            'km': kmb.text, 'is_public': public.checked, 'walk_id': (walk or {}).get('id') or ex.get('walk_id')}
    if photo.file is not None:
      data['photo'] = photo.file
    res = ui.call('save_entry', data)
    if res is not ui.FAIL:
      ui.toast(res['message'])
      ui.close_modal(holder['c'], True)

  c = ui.H(f'''<div>
      <div class="cc-modal-title">📔 {"Edit entry" if existing else "New journey entry"}</div>
      <div class="cc-modal-sub">Your life, one walk at a time.</div>
      <div class="cc-field"><label>Mood</label>{ui.slot("mood")}</div>
      {ui.field("Title", "title")}
      <div class="cc-form-row">{ui.field("Date", "date")}{ui.field("Distance (km)", "km")}</div>
      {ui.field("Story", "body")}
      <div class="cc-row" style="margin-bottom:10px">{ui.slot("photo")}</div>
      {ui.slot("public")}
      <div class="cc-row end" style="margin-top:14px"><button type="button" class="cc-btn ghost" data-act="no">Cancel</button>
      <button type="button" class="cc-btn" data-act="yes">Save entry</button></div></div>''',
           actions={'yes': save, 'no': lambda a: ui.close_modal(holder['c'], False)})
  holder['c'] = c
  for comp, s in ((mood.component, 'mood'), (title, 'title'), (dp, 'date'), (kmb, 'km'), (body, 'body'),
                  (photo, 'photo'), (public, 'public')):
    c.add_component(comp, slot=s)
  return bool(ui.modal(c, large=True))


# ================================================================== reports

REASONS = ["Made me feel unsafe", "Harassment or inappropriate behaviour", "Fake profile or spam",
           "Didn't follow walk safety rules", "Walk details are misleading", "Something else"]


def report(user_id=None, walk_id=None, who=''):
  reason = ui.dropdown([(r, r) for r in REASONS], placeholder='Choose a reason…')
  details = ui.textarea('What happened? Include times and places if you can. This stays confidential.', height=120)
  holder = {}

  def send(_):
    if not reason.selected_value:
      ui.toast("Pick a reason.", 'warning')
      return
    if ui.call('report', user_id=user_id, walk_id=walk_id, reason=reason.selected_value, details=details.text) is not ui.FAIL:
      ui.toast("Thank you. Our team will review this quickly. 🛟")
      ui.close_modal(holder['c'], True)

  c = ui.H(f'''<div>
      <div class="cc-modal-title">🚩 Report {esc(who) or "a problem"}</div>
      <div class="cc-alert danger" style="margin:0 0 14px"><span class="ico">🚨</span>
        <span><b>In immediate danger?</b> Call your local emergency number first (999 / 112 / 911).</span></div>
      {ui.field("Reason", "reason")}
      {ui.field("Details", "details")}
      <div class="cc-row end"><button type="button" class="cc-btn ghost" data-act="no">Cancel</button>
      <button type="button" class="cc-btn dark" data-act="yes">Send report</button></div></div>''',
           actions={'yes': send, 'no': lambda a: ui.close_modal(holder['c'], False)})
  holder['c'] = c
  c.add_component(reason, slot='reason')
  c.add_component(details, slot='details')
  return ui.modal(c, large=True)


# ================================================================== invites

def invite(walk):
  friends = ui.call('my_friends')
  if friends is ui.FAIL:
    return
  holder = {}
  link = anvil.server.get_app_origin() + '/#walk/' + walk['id']
  picker = ui.Chips([(f['id'], f['name']) for f in friends], multi=True) if friends else None
  email = ui.textbox('friend@example.com', type='email')

  def send(_):
    n = 0
    if picker and picker.value:
      res = ui.call('invite_to_walk', walk['id'], picker.value)
      if res is ui.FAIL:
        return
      n = res
    if (email.text or '').strip():
      msg = ui.call('invite_by_email', walk['id'], email.text)
      if msg is ui.FAIL:
        return
      ui.toast(msg)
    if n:
      ui.toast(f"Invited {n} friend{'s' if n != 1 else ''} 💌")
    ui.close_modal(holder['c'], True)

  def copy(_):
    if ui.copy_text(link):
      ui.toast("Link copied. Paste it anywhere.")
    else:
      ui.toast(link, 'info', 8)

  friends_html = ui.slot('friends') if friends else ('<p class="muted small">No connections yet. Find walkers on the '
                                                      '<a href="#people">People</a> page, or invite by email below.</p>')
  c = ui.H(f'''<div>
      <div class="cc-modal-title">💌 Invite people</div>
      <div class="cc-modal-sub">Friends get a notification (and an email if they've switched those on).</div>
      <div class="cc-field"><label>Your connections</label>{friends_html}</div>
      {ui.field("Or invite by email", "email", "We'll send them the route and a link to join.")}
      <div class="cc-row between" style="margin-top:8px">
        <button type="button" class="cc-btn ghost sm" data-act="copy">🔗 Copy link</button>
        <div class="cc-row"><button type="button" class="cc-btn ghost" data-act="no">Close</button>
        <button type="button" class="cc-btn" data-act="send">Send invites</button></div></div></div>''',
           actions={'send': send, 'copy': copy, 'no': lambda a: ui.close_modal(holder['c'], False)})
  holder['c'] = c
  if picker:
    c.add_component(picker.component, slot='friends')
  c.add_component(email, slot='email')
  return ui.modal(c, large=True)


# ================================================================== place details

def place_details(place_id):
  p = ui.call('get_place', place_id)
  if p is ui.FAIL:
    return
  holder = {}
  emo, kind_name = ui.KINDS.get(p['kind'], ('📍', 'Spot'))
  deals = ''.join(f'''<div class="cc-card tint-orange flat" style="margin-bottom:8px;padding:12px 14px">
      <span class="cc-deal-tag">{(str(d["percent"]) + "% OFF") if d.get("percent") else "DEAL"}</span>
      <b style="margin-left:6px">{esc(d["title"])}</b><div class="small">{esc(d["description"])}</div>
      {('<div class="small" style="margin-top:6px">Code: <span class="cc-code">' + esc(d["code"]) + '</span></div>') if d.get("code") else ''}</div>'''
                  for d in p['deals'])
  revs = ''.join(f'''<div style="padding:10px 0;border-top:1px dashed #EEE5D2">{ui.person(r["user"], sub=ui.ago(r["created"]), size=34)}
      <div style="margin-top:6px"><span class="cc-rating">{ui.stars(r["rating"])}</span> <b>{esc(r["title"])}</b></div>
      <div class="small">{esc(r["body"])}</div></div>''' for r in p['reviews']) or '<p class="muted small">No public reviews yet. Be the first!</p>'
  rating = f'<span class="cc-rating">{ui.stars(p["avg_rating"])}</span> <span class="small muted">({p["review_count"]})</span>' if p['review_count'] else ''
  added = f'<div class="small muted">Added by {esc(p["added_by"]["name"])}</div>' if p.get('added_by') else ''

  def do_review(_):
    ui.close_modal(holder['c'], None)
    if review(p['name'], place_id=p['id']):
      pass

  def do_plan(_):
    ui.close_modal(holder['c'], None)
    state.go('plan/from/' + p['id'])

  c = ui.H(f'''<div>
      <div class="cc-row" style="gap:14px;margin-bottom:8px"><span style="font-size:44px">{emo}</span>
        <div><div class="cc-modal-title">{esc(p["name"])}{' <span class="cc-verified">✔</span>' if p.get("verified") else ''}</div>
        <div class="cc-row" style="gap:8px">{ui.pill(kind_name)} {rating}</div></div></div>
      <p>{esc(p["description"])}</p>{added}
      {('<h4 style="margin-top:14px">🏷️ CityCrossers deals</h4>' + deals) if deals else ''}
      <h4 style="margin-top:14px">What walkers say</h4>{revs}
      <div class="cc-row end" style="margin-top:14px">
        <button type="button" class="cc-btn ghost" data-act="review">{"✏️ Review again" if p["reviewed"] else "⭐ Review"}</button>
        <button type="button" class="cc-btn orange" data-act="plan">🗺️ Plan a walk from here</button></div></div>''',
           actions={'review': do_review, 'plan': do_plan})
  holder['c'] = c
  ui.modal(c, large=True)
