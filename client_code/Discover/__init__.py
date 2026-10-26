from ._anvil_designer import DiscoverTemplate
from anvil import *
import anvil.js
import random

from .. import ui, state, dialogs
from ..ui import esc

ROUTE_DECO = '''<svg class="cc-route-deco" viewBox="0 0 340 200" aria-hidden="true">
  <path d="M10 170 C 80 120, 120 190, 170 120 S 260 60, 330 30" stroke="#17A673" stroke-width="5" fill="none"
        stroke-dasharray="1 12" stroke-linecap="round"/>
  <text x="160" y="118" font-size="26">☕</text><text x="300" y="40" font-size="26">🥐</text><text x="8" y="182" font-size="22">🚩</text>
</svg>'''

TAGLINES = ["Ready for a long one?", "Somewhere out there is a cinnamon bun with your name on it.",
            "Every 5 km deserves a snack.", "Your next crew is one swipe away.",
            "Walk far, eat well, meet people."]


class Discover(DiscoverTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.tab = 'walks'
    self.idx = 0
    data = ui.call('home_feed')
    self.data = data if data is not ui.FAIL else {'deck': [], 'upcoming': [], 'invites': [], 'suggestions': [], 'counts': {}}
    if data is not ui.FAIL and state.main:
      state.main.update_counts(dict(state.counts, **data['counts']))
    self.deck = self.data['deck']
    self.deck_view = ui.H('', actions={'pass': lambda a: self._fly('left'), 'join': lambda a: self._fly('right'),
                                       'details': lambda a: state.go('walk/' + a)})
    ui.bind(self, {
      'tab': self.set_tab, 'connect': self.connect, 'accept': self.accept_invite, 'decline': self.decline_invite,
      'pledge': self.pledge, 'open': lambda a: state.go('walk/' + a),
    })
    self.render()

  # ------------------------------------------------------------ page
  def greeting(self):
    h = ui.now_local().hour
    if h < 5:
      return "Night owl mode", "🌙"
    if h < 12:
      return "Good morning", "☀️"
    if h < 18:
      return "Good afternoon", "🌤️"
    return "Good evening", "🌆"

  def render(self):
    me = state.me or {}
    hello, emo = self.greeting()
    first = (me.get('name') or 'walker').split(' ')[0]
    lvl = me.get('level') or {}
    nxt = (self.data['upcoming'] or [None])[0]
    nxt_html = (f'<div class="cc-stat"><b>{esc(ui.fmt_rel(nxt["start"]))}</b><span>Next: {esc(nxt["title"][:26])}</span></div>'
                if nxt else '<div class="cc-stat"><b>No plans</b><span>Swipe below 👇</span></div>')
    alerts = ''
    inv = len(self.data['invites'])
    if inv:
      alerts += f'<div class="cc-alert berry"><span class="ico">💌</span><span><b>You have {inv} walk invite{"s" if inv != 1 else ""}.</b> Answer them on the right.</span></div>'
    fr = self.data['counts'].get('friend_requests', 0)
    if fr:
      alerts += f'<div class="cc-alert sky"><span class="ico">👋</span><span><b>{fr} walker{"s" if fr != 1 else ""} want{"s" if fr == 1 else ""} to connect.</b> <a href="#people">Say hi</a></span></div>'
    if me and not me.get('safety_pledge'):
      alerts += ('<div class="cc-alert"><span class="ico">🛟</span><span style="flex:1"><b>Take the 20-second safety pledge</b> '
                 'before your first walk with new people (+10 pts).</span>' + ui.btn('Take it', 'pledge', kind='sm') + '</div>')
    elif me and me.get('completeness', 100) < 75:
      alerts += (f'<div class="cc-alert orange"><span class="ico">🪪</span><span style="flex:1"><b>Your profile is {me.get("completeness")}% done.</b> '
                 f'Walkers say yes faster to profiles with a photo and a headline. Finish it for +25 pts.</span>'
                 f'<a class="cc-btn sm orange" href="#me/edit">Finish profile</a></div>')
    tabs = (f'<div class="cc-tabs"><button class="{"on" if self.tab == "walks" else ""}" data-act="tab" data-arg="walks">🔥 Walks for you'
            f'{"<span class=cnt>" + str(len(self.deck)) + "</span>" if self.deck else ""}</button>'
            f'<button class="{"on" if self.tab == "people" else ""}" data-act="tab" data-arg="people">👋 Walkers to meet</button></div>')
    self.clear()
    body = self.walks_tab_html() if self.tab == 'walks' else self.people_tab_html()
    self.html = f'''
    <div class="cc-page">
      <div class="cc-hello cc-fade-in">{ROUTE_DECO}
        <h1>{hello}, {esc(first)} {emo}</h1>
        <p class="muted" style="font-size:1.08rem;margin:0">{esc(random.choice(TAGLINES))}</p>
        <div class="cc-stat-row">
          <a class="cc-stat" href="#perks" style="text-decoration:none;color:inherit"><b>⭐ {me.get("points", 0)}</b><span>points to spend</span></a>
          <div class="cc-stat"><b>{lvl.get("emoji", "🚶")} {esc(lvl.get("name", "Stroller"))}</b><span>{int(lvl.get("progress", 0) * 100)}% to {esc(lvl.get("next_name") or "the top")}</span></div>
          <div class="cc-stat"><b>{ui.km(me.get("km_total", 0))}</b><span>walked with CityCrossers</span></div>
          {nxt_html}
        </div>
      </div>
      {alerts}
      <div class="cc-row between" style="margin:28px 0 18px">{tabs}
        <a class="cc-btn orange" href="#plan">➕ Plan a walk</a></div>
      {body}
    </div>'''
    if self.tab == 'walks':
      self.add_component(self.deck_view, slot='deck')
      self.render_deck()

  def set_tab(self, tab):
    self.tab = tab
    self.render()

  # ------------------------------------------------------------ walks tab
  def walks_tab_html(self):
    side = ''
    if self.data['invites']:
      items = ''
      for w in self.data['invites']:
        items += f'''<div style="padding:10px 0;border-top:1px dashed #EEE5D2">
          <a href="#walk/{w["id"]}" style="font-weight:700;color:inherit">{ui.vibe_of(w["vibe"])[1]} {esc(w["title"])}</a>
          <div class="small muted">{esc(ui.fmt_when(w["start"]))} · {ui.km(w["distance_km"])} · from {esc((w.get("host") or {}).get("name", ""))}</div>
          <div class="cc-row" style="margin-top:6px">{ui.btn("I'm in", "accept", w["id"], "sm")}{ui.btn("Can't make it", "decline", w["id"], "ghost sm")}</div></div>'''
      side += f'<div class="cc-card tint-berry"><div class="cc-card-title"><h3>💌 Invites</h3></div>{items}</div>'
    up = self.data['upcoming']
    if up:
      items = ''.join(f'''<a href="#walk/{w["id"]}" class="cc-row" style="gap:12px;padding:10px 0;border-top:1px dashed #EEE5D2;color:inherit;text-decoration:none;flex-wrap:nowrap">
          <span class="{ui.vibe_of(w["vibe"])[3]}" style="border-radius:14px;width:48px;height:48px;display:flex;align-items:center;justify-content:center;font-size:24px;flex-shrink:0">{ui.vibe_of(w["vibe"])[1]}</span>
          <span style="min-width:0"><b style="display:block">{esc(w["title"])}</b><span class="small muted">{esc(ui.fmt_rel(w["start"]))} · {esc(ui.fmt_time(w["start"]))} · {w["going"]} going</span></span></a>'''
                      for w in up[:4])
      side += f'<div class="cc-card"><div class="cc-card-title"><h3>🗓️ Coming up</h3><a href="#walks" class="small">All</a></div>{items}</div>'
    else:
      side += ('<div class="cc-card tint-sun"><h3>🗓️ Nothing planned yet</h3><p class="muted">Swipe right on a walk, or '
               'be the host. Hosts earn +25 pts per walk.</p><a class="cc-btn sun" href="#plan">Plan my first walk</a></div>')
    side += '''<div class="cc-card tint-green"><h3>🥐 How it works</h3>
      <ul class="cc-safety-list small">
        <li><span class="i">👉</span><span>Swipe right (or tap 💚) to ask to join. Hosts approve requests for public walks.</span></li>
        <li><span class="i">👈</span><span>Swipe left to pass. We won't show it again.</span></li>
        <li><span class="i">🎯</span><span>Match % compares your pace, preferred distance and interests.</span></li>
      </ul></div>'''
    return f'<div class="cc-grid two"><div>{ui.slot("deck")}</div><div class="cc-stack">{side}</div></div>'

  def render_deck(self):
    if self.idx >= len(self.deck):
      self.deck_view.html = ui.empty('🎉', "You've seen every walk around",
                                     "New walks pop up all the time. Or be the person who plans the next great one.",
                                     '<div class="cc-row" style="justify-content:center"><a class="cc-btn orange" href="#plan">➕ Plan a walk</a>'
                                     '<a class="cc-btn ghost" href="#map">🗺️ Explore the map</a></div>')
      return
    w = self.deck[self.idx]
    v = ui.vibe_of(w['vibe'])
    pace = ui.PACES.get(w['pace'], ui.PACES['steady'])
    host = w.get('host') or {}
    remaining = len(self.deck) - self.idx
    shadows = ''
    if remaining > 2:
      shadows += '<div class="cc-deck-shadow two"></div>'
    if remaining > 1:
      shadows += '<div class="cc-deck-shadow"></div>'
    match = (f'<span class="cc-match friend">💞 Friend\'s walk · {w.get("match", 0)}%</span>' if w.get('from_friend')
             else f'<span class="cc-match">{w.get("match", 0)}% match</span>')
    tags = ''.join(ui.pill(t, 'outline') for t in w['tags'][:4])
    approval = '🙋 Host approves requests' if w.get('approval_required') else '⚡ Instant join'
    self.deck_view.html = f'''
    <div class="cc-deck">
      <div class="cc-deck-stack">{shadows}
        <div class="cc-swipe cc-fade-in">
          <span class="stamp yes">I'M IN</span><span class="stamp no">NOPE</span>
          <div class="cover {v[3]}">
            <span class="vibe">{v[1]} {esc(v[2])}</span>{match}
            <span class="when">{esc(ui.fmt_rel(w["start"]))}<small>{esc(ui.fmt_when(w["start"]))}</small></span>
            <span class="emo">{v[1]}</span>
          </div>
          <div class="body">
            <h2>{esc(w["title"])}</h2>
            <div class="facts">
              {ui.pill("📏 " + ui.km(w["distance_km"]))}{ui.pill("⏱️ " + ui.fmt_dur(w["duration_min"]))}
              {ui.pill(pace[0] + " " + pace[1])}{ui.pill("🥐 " + str(w["food_stops"]) + " food stops", "orange")}
              {ui.pill("👥 " + str(w["spots_left"]) + " spots left", "green")}
            </div>
            <div style="margin-bottom:14px">{ui.strip(w["stops"])}</div>
            <p class="desc">{esc(w["description"])}</p>
            <div class="cc-pills" style="margin-bottom:14px">{tags}</div>
            <div class="cc-row between">{ui.person(host, sub=esc(host.get("level", {}).get("emoji", "") + " " + host.get("level", {}).get("name", "") + " · " + str(host.get("walks_count", 0)) + " walks"), size=42)}
              <span class="small muted">{approval}</span></div>
          </div>
        </div>
      </div>
      <div class="cc-deck-actions">
        <button class="cc-round no" data-act="pass" title="Not for me">✕</button>
        <button class="cc-round small" data-act="details" data-arg="{w["id"]}" title="See details">👀</button>
        <button class="cc-round big" data-act="join" title="I'm in!">💚</button>
      </div>
      <div class="cc-deck-hint">Drag the card, or use the buttons · {remaining} walk{"s" if remaining != 1 else ""} in your deck</div>
    </div>'''
    card = ui.dom(self.deck_view).querySelector('.cc-swipe')
    try:
      anvil.js.window.cc.swipe(card, self._swiped)
    except Exception:
      pass

  def _fly(self, direction):
    card = ui.dom(self.deck_view).querySelector('.cc-swipe')
    if card is None:
      return
    try:
      anvil.js.window.cc.fly(card, direction, self._swiped)
    except Exception:
      self._swiped(direction)

  def _swiped(self, direction):
    if self.idx >= len(self.deck):
      return
    w = self.deck[self.idx]
    if direction == 'right':
      status = ui.call('join_walk', w['id'])
      if status is ui.FAIL:
        self.render_deck()   # put the card back
        return
      msgs = {'going': "You're in! 🎉 See you at the meeting point.",
              'requested': "Request sent! 🙋 We'll ping you when the host says yes.",
              'waitlist': "It's full, so you're on the waitlist. Fingers crossed 🤞"}
      ui.toast(msgs.get(status, "Done!"))
      if status == 'going':
        ui.confetti()
    else:
      ui.call('pass_walk', w['id'], _quiet=True)
    self.idx += 1
    self.render_deck()

  # ------------------------------------------------------------ people tab
  def people_tab_html(self):
    people = self.data['suggestions']
    if not people:
      return ui.empty('👋', 'No new walkers to suggest', 'Invite friends, or check back after a few more people join.')
    cards = ''
    for p in people:
      top = p.get('top_endorsement')
      top_html = ui.pill(f"{top['skill']} ×{top['count']}", 'violet') if top else ''
      shared = ''.join(ui.pill(s, 'green') for s in (p.get('shared') or [])[:3])
      pace = ui.PACES.get(p['pace'], ui.PACES['steady'])
      cards += f'''
      <div class="cc-person-card">
        <div class="banner {ui.VIBES[hash(p["id"]) % len(ui.VIBES)][3]}"></div>
        {ui.avatar(p, 76)}
        <div class="inner">
          <h4><a href="#u/{p["id"]}" style="color:inherit">{esc(p["name"])}</a>{' <span class="cc-verified">✔</span>' if p["verified"] else ''}</h4>
          <div class="headline">{esc(p["headline"] or "New walker, say hi!")}</div>
          <div class="cc-pills">{ui.pill(str(p["match"]) + "% match", "dark")}{ui.level_pill(p)}{ui.pill(pace[0] + " " + pace[1])}</div>
          <div class="small muted">{ui.km(p["km_total"])} walked · {p["walks_count"]} walks · {p["people_met"]} people met</div>
          <div class="cc-pills">{top_html}{shared}</div>
          <div class="actions">
            <a class="cc-btn ghost sm" href="#u/{p["id"]}">View</a>
            <button class="cc-btn sm" data-act="connect" data-arg="{p["id"]}">👋 Connect</button>
          </div>
        </div>
      </div>'''
    return f'<div class="cc-grid cards">{cards}</div>'

  # ------------------------------------------------------------ actions
  def connect(self, uid):
    res = ui.call('send_friend_request', uid)
    if res is ui.FAIL:
      return
    ui.toast("Connected! 🤝" if res == 'friends' else "Request sent 👋")
    self.data['suggestions'] = [p for p in self.data['suggestions'] if p['id'] != uid]
    self.render()

  def accept_invite(self, wid):
    status = ui.call('respond_invite', wid, True)
    if status is ui.FAIL:
      return
    ui.toast("You're in! 🎉" if status == 'going' else "Added to the waitlist 🤞")
    if status == 'going':
      ui.confetti()
    state.go('walk/' + wid)

  def decline_invite(self, wid):
    if ui.call('respond_invite', wid, False) is not ui.FAIL:
      self.data['invites'] = [w for w in self.data['invites'] if w['id'] != wid]
      ui.toast("No worries, maybe next time.", 'info')
      self.render()

  def pledge(self, _=None):
    if dialogs.safety_pledge():
      self.render()
