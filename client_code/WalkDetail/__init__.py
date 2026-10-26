from ._anvil_designer import WalkDetailTemplate
from anvil import *
import anvil.js
import anvil.server
import datetime

from .. import ui, state, dialogs
from ..ui import esc
from ..mapkit import MapView


class WalkDetail(WalkDetailTemplate):
  def __init__(self, walk_id=None, **properties):
    self.init_components(**properties)
    self.walk_id = walk_id
    self.w = None
    self.forecast = None
    self.mv = MapView(height='380px')
    self.chat_box = ui.textbox('Say something to the group… (e.g. “I’ll bring plasters!”)')
    self.chat_box.add_event_handler('pressed_enter', lambda **e: self.send_chat())
    ui.bind(self, {
      'join': self.join, 'leave': self.leave, 'accept_invite': lambda a: self.respond(True),
      'decline_invite': lambda a: self.respond(False), 'edit': lambda a: state.go('edit/' + self.walk_id),
      'invite': lambda a: self.invite(), 'public': lambda a: self.set_vis('public'),
      'friends': lambda a: self.set_vis('friends'), 'complete': self.complete, 'cancel': self.cancel,
      'share': self.share, 'approve': lambda a: self.decide(a, True), 'reject': lambda a: self.decide(a, False),
      'vote': self.vote, 'accept_stop': self.accept_stop, 'remove_stop': self.remove_stop,
      'suggest': self.suggest, 'send': lambda a: self.send_chat(), 'review': self.review,
      'endorse': self.endorse, 'journal': self.journal, 'report': self.report, 'place': dialogs.place_details,
    })
    self.load()

  # ------------------------------------------------------------ data
  def load(self):
    w = ui.call('get_walk', self.walk_id)
    if w is ui.FAIL:
      self.clear()
      self.html = '<div class="cc-page">' + ui.empty('🙈', "We can't show this walk", 'It may be friends-only, cancelled, or the link is wrong.',
                                                     '<a class="cc-btn" href="#discover">Back to Discover</a>') + '</div>'
      return
    self.w = w
    self.render()
    if self.forecast is None and not w['is_past'] and w['status'] in ('planning', 'confirmed'):
      t = Timer(interval=0.2)
      t.add_event_handler('tick', self._load_forecast)
      self.add_component(t, slot='hidden')

  def _load_forecast(self, sender=None, **e):
    if sender is not None:
      sender.interval = 0
      sender.remove_from_parent()
    f = ui.call('walk_forecast', self.walk_id, _quiet=True)
    self.forecast = f if f is not ui.FAIL and f else False
    el = ui.dom(self).querySelector('.js-forecast')
    if el is not None:
      el.innerHTML = self.forecast_html()

  # ------------------------------------------------------------ render
  def render(self):
    w = self.w
    v = ui.vibe_of(w['vibe'])
    pace = ui.PACES.get(w['pace'], ui.PACES['steady'])
    status_pill = ''
    if w['status'] == 'completed':
      status_pill = ui.pill('🏁 Completed', 'dark')
    elif w['status'] == 'cancelled':
      status_pill = ui.pill('Cancelled', 'dark')
    match = ui.pill(f"{w['match']}% match", 'dark') if w.get('match') else ''
    vis = ui.pill('🌍 Public', 'sky') if w['visibility'] == 'public' else ui.pill('👯 Friends only', 'berry')
    self.clear()
    self.html = f'''
    <div class="cc-page">
      <a href="#walks" class="small" style="display:inline-block;margin-bottom:10px">← My walks</a>
      <div class="cc-walk-hero {v[3]} cc-fade-in">
        <span class="emo">{v[1]}</span>
        <div class="cc-pills" style="position:relative;margin-bottom:12px">{ui.pill(v[1] + " " + v[2])}{vis}{status_pill}{match}</div>
        <h1>{esc(w["title"])}</h1>
        <div class="facts">
          {ui.pill("🗓️ " + ui.fmt_date(w["start"]) + " (" + ui.fmt_rel(w["start"]) + ")")}
          {ui.pill("🕘 " + ui.fmt_time(w["start"]))}
          {ui.pill("📏 " + ui.km(w["distance_km"]))}{ui.pill("⏱️ ~" + ui.fmt_dur(w["duration_min"]))}
          {ui.pill(pace[0] + " " + pace[1] + " pace")}{ui.pill("👥 " + str(w["going"]) + "/" + str(w["max_walkers"]) + " going")}
        </div>
      </div>
      <div class="cc-actionbar">{self.actions_html()}</div>
      <div class="cc-grid two" style="margin-top:22px;align-items:start">
        <div class="cc-stack">
          {self.post_walk_html()}
          <div class="cc-card">
            <div class="cc-card-title"><h3>🗺️ Route &amp; stops</h3><span class="small muted">{len(w["stops_full"])} stops · {w["food_stops"]} food</span></div>
            <div class="cc-map-wrap" style="margin-bottom:16px">{ui.slot("map")}</div>
            {self.timeline_html()}
          </div>
          {self.proposed_html()}
          {self.about_html()}
          {self.chat_html()}
        </div>
        <div class="cc-stack">
          {self.host_html()}
          {self.crew_html()}
          <div class="cc-card js-forecast">{self.forecast_html()}</div>
          {self.safety_html()}
        </div>
      </div>
      {ui.slot("hidden", "hidden")}
    </div>'''
    self.add_component(self.mv.component, slot='map')
    if w['insider']:
      self.add_component(self.chat_box, slot='chat_input')
    self.draw_map()

  def actions_html(self):
    w = self.w
    st = w['my_status']
    b = ui.btn
    if w['status'] == 'cancelled':
      return '<span class="state">This walk was cancelled by the host. 😢</span>'
    if w['status'] == 'completed':
      extra = b('📔 Write about it', 'journal', kind='sm') if st == 'going' else ''
      return f'<span class="state">🏁 This walk is in the books.</span><span class="cc-spacer"></span>{extra}'
    if w['is_host'] or (w['is_admin'] and not st):
      vis_btn = b('🌍 Open to public', 'public', kind='ghost sm') if w['visibility'] != 'public' else b('👯 Make friends-only', 'friends', kind='ghost sm')
      done = b('🏁 Mark completed', 'complete', kind='sm') if w['is_past'] else ''
      req = len(w['members']['requested'])
      req_txt = f' · <b style="color:#E8601F">{req} request{"s" if req != 1 else ""} waiting</b>' if req else ''
      return (f'<span class="state">⭐ You\'re hosting{req_txt}</span><span class="cc-spacer"></span>'
              f'{done}{b("✏️ Edit", "edit", kind="ghost sm")}{b("💌 Invite", "invite", kind="sm orange")}{vis_btn}'
              f'{b("📤 Share plan", "share", kind="ghost sm")}{b("Cancel walk", "cancel", kind="danger sm")}')
    if st == 'going':
      return (f'<span class="state">✅ You\'re going! See you at the start.</span><span class="cc-spacer"></span>'
              f'{b("💌 Bring a friend", "invite", kind="sm orange")}{b("📤 Share plan", "share", kind="ghost sm")}'
              f'{b("Can’t make it", "leave", kind="danger sm")}')
    if st == 'requested':
      return (f'<span class="state">⏳ Request sent. Waiting for {esc(w["host"]["name"])} to say yes.</span>'
              f'<span class="cc-spacer"></span>{b("Withdraw request", "leave", kind="ghost sm")}')
    if st == 'waitlist':
      return (f'<span class="state">🕒 You\'re on the waitlist. We\'ll ping you if a spot opens.</span>'
              f'<span class="cc-spacer"></span>{b("Leave waitlist", "leave", kind="ghost sm")}')
    if st == 'invited':
      return (f'<span class="state">💌 You\'re invited!</span><span class="cc-spacer"></span>'
              f'{b("Can’t make it", "decline_invite", kind="ghost sm")}{b("💚 I’m in!", "accept_invite", kind="lg")}')
    if w['is_past']:
      return '<span class="state">This walk has already set off.</span>'
    full = w['spots_left'] <= 0
    if full:
      label = '🕒 Join the waitlist'
    elif w['visibility'] == 'public' and w['approval_required'] and not w.get('friends_with_host'):
      label = '🙋 Request to join'
    else:
      label = '💚 Join this walk'
    hint = f'{w["spots_left"]} spot{"s" if w["spots_left"] != 1 else ""} left' if not full else 'Walk is full'
    return f'<span class="state">{hint}</span><span class="cc-spacer"></span>{b(label, "join", kind="lg")}'

  def timeline_html(self):
    w = self.w
    stops = w['stops_full']
    if not stops:
      return '<p class="muted">No stops yet.</p>'
    stats = ui.route_stats(stops, w['pace'])
    t = ui.local(w['start'])
    walked = 0.0
    items = ''
    for i, s in enumerate(stops):
      if i > 0:
        leg = stats['legs'][i - 1]
        walked += leg
        mins = leg / stats['speed'] * 60
        t = t + datetime.timedelta(minutes=mins) if t else None
        items += f'<div class="leg">🚶 {leg:.1f} km · ~{ui.fmt_dur(mins)}</div>'
      emo, kname = ui.KINDS.get(s['kind'], ('📍', 'Stop'))
      brk = f'<span class="break">{s["break_min"]} min break</span>' if s['break_min'] else ''
      deal = ''
      if s['deals']:
        d = s['deals'][0]
        deal = f' <span class="cc-deal-tag">{(str(d["percent"]) + "% OFF") if d.get("percent") else "DEAL"}</span>'
      rating = f' <span class="cc-rating small">★ {s["rating"]}</span>' if s.get('rating') else ''
      name = (f'<a href="javascript:void(0)" data-act="place" data-arg="{s["place_id"]}" style="color:inherit">{esc(s["name"])}</a>'
              if s.get('place_id') else esc(s['name']))
      eta = ui.fmt_time(t) if t else ''
      km_in = (" · %.1f km in" % walked) if i else ""
      items += f'''<li><span class="bubble {s["kind"]}">{emo}</span><div class="what"><b>{name}{deal}{rating}</b>
        <span class="eta">{eta} · {esc(kname)}{km_in}</span>{brk}
        {('<div class="small muted">' + esc(s["note"]) + '</div>') if s.get("note") else ''}</div></li>'''
      if t:
        t = t + datetime.timedelta(minutes=s['break_min'])
    end = f'<p class="small muted" style="margin:10px 0 0">🏁 Back around <b>{ui.fmt_time(t)}</b> · ' \
          f'{stats["breaks"]} breaks totalling {ui.fmt_dur(stats["break_min"])} · distances are approximate</p>' if t else ''
    return f'<ul class="cc-timeline">{items}</ul>{end}'

  def proposed_html(self):
    w = self.w
    if w['status'] not in ('planning', 'confirmed'):
      return ''
    can = w['is_host'] or w['my_status'] == 'going'
    rows = ''
    for s in w['proposed']:
      emo = ui.KINDS.get(s['kind'], ('📍',))[0]
      by = s['proposed_by'] or {}
      ctl = ''
      if can:
        ctl += f'<button class="cc-btn sm {"" if s["voted"] else "ghost"}" data-act="vote" data-arg="{s["id"]}">👍 {s["votes"]}</button>'
      else:
        ctl += ui.pill(f'👍 {s["votes"]}')
      if w['is_host']:
        ctl += ui.btn('✓ Add', 'accept_stop', s['id'], 'soft sm')
      if w['is_host'] or (state.me and by.get('id') == state.me.get('id')):
        ctl += f'<button class="cc-btn ghost sm" data-act="remove_stop" data-arg="{s["id"]}" title="Remove">✕</button>'
      rows += f'''<div class="cc-stop-row"><span class="e">{emo}</span><div class="t"><b>{esc(s["name"])}</b>
        <span>suggested by {esc(by.get("name", "someone"))}{" · " + esc(s["note"]) if s.get("note") else ""}</span></div>
        <div class="cc-row" style="gap:6px;flex-wrap:nowrap">{ctl}</div></div>'''
    if not rows and not can:
      return ''
    if not rows:
      rows = '<p class="small muted" style="margin:0 0 10px">Know a great bakery on the way? Suggest it and the group votes.</p>'
    btn = ui.btn('➕ Suggest a stop', 'suggest', kind='ghost sm') if can else ''
    return f'''<div class="cc-card"><div class="cc-card-title"><h3>🗳️ Suggested stops</h3>{btn}</div>
      <p class="small muted" style="margin-top:-6px">Walkers vote, the host decides. Accepted stops earn the suggester +5 pts.</p>{rows}</div>'''

  def about_html(self):
    w = self.w
    tags = ''.join(ui.pill(t, 'outline') for t in w['tags'])
    meet = ''
    if w.get('meeting_note'):
      meet = f'<div class="cc-alert sky" style="margin-top:12px"><span class="ico">📍</span><span><b>Meeting spot:</b> {esc(w["meeting_note"])}</span></div>'
    elif not w['insider']:
      meet = '<p class="small muted" style="margin-top:10px">🔒 Exact meeting details are shared with people going.</p>'
    desc = esc(w['description']).replace('\n', '<br>') or '<span class="muted">No description yet.</span>'
    return f'''<div class="cc-card"><h3>📝 About this walk</h3><p>{desc}</p>
      <div class="cc-pills">{tags}</div>{meet}</div>'''

  def chat_html(self):
    w = self.w
    if not w['insider']:
      return ('<div class="cc-card tint-sun"><h3>💬 Group chat</h3><p class="muted" style="margin:0">'
              'Join the walk to chat with the group, coordinate snacks and say hi before you meet.</p></div>')
    msgs = ''
    for m in w['messages']:
      u = m['user'] or {}
      msgs += f'''<div class="cc-msg {"mine" if m["mine"] else ""}">{ui.avatar(u, 30)}
        <div class="b"><span class="who">{esc(u.get("name", ""))} · {ui.ago(m["created"])}</span>{esc(m["body"])}</div></div>'''
    if not msgs:
      msgs = '<p class="small muted center" style="margin:10px 0">No messages yet. Break the ice! 🧊</p>'
    return f'''<div class="cc-card"><div class="cc-card-title"><h3>💬 Group chat</h3><span class="small muted">{len(w["messages"])} messages</span></div>
      <div class="cc-chat js-chat">{msgs}</div>
      <div class="cc-row" style="margin-top:12px;flex-wrap:nowrap"><div style="flex:1">{ui.slot("chat_input")}</div>
      {ui.btn("Send", "send")}</div></div>'''

  def host_html(self):
    h = self.w['host'] or {}
    if not h:
      return ''
    lvl = h.get('level') or {}
    return f'''<div class="cc-card"><div class="small muted" style="font-weight:700;margin-bottom:8px">HOSTED BY</div>
      {ui.person(h, size=56)}
      <div class="cc-pills" style="margin-top:12px">{ui.pill(lvl.get("emoji", "") + " " + lvl.get("name", ""), "sun")}
        {ui.pill(str(h.get("walks_count", 0)) + " walks")}{ui.pill(ui.km(h.get("km_total", 0)))}</div></div>'''

  def crew_html(self):
    w = self.w
    m = w['members']
    going = ''.join(f'<div style="padding:6px 0">{ui.person(c, sub=("⭐ Host" if c.get("role") == "host" else esc(c.get("headline") or "")), size=38)}</div>'
                    for c in m['going'])
    out = f'<div class="cc-card"><div class="cc-card-title"><h3>👥 The crew</h3><span class="small muted">{len(m["going"])}/{w["max_walkers"]}</span></div>'
    out += f'<div class="cc-progress" style="margin-bottom:12px"><div style="width:{min(100, int(100.0 * len(m["going"]) / max(1, w["max_walkers"])))}%"></div></div>'
    out += going or '<p class="muted small">Nobody yet.</p>'
    if m['requested']:
      out += '<h4 style="margin-top:16px">🙋 Requests</h4>'
      for c in m['requested']:
        msg = f'<div class="small" style="background:#FFF5E4;border-radius:12px;padding:8px 10px;margin-top:6px">“{esc(c["message"])}”</div>' if c.get('message') else ''
        out += f'''<div style="padding:10px 0;border-top:1px dashed #EEE5D2">{ui.person(c, size=38)}{msg}
          <div class="cc-row" style="margin-top:8px">{ui.btn("✓ Accept", "approve", c["id"], "sm")}{ui.btn("Decline", "reject", c["id"], "ghost sm")}
          <a class="cc-btn ghost sm" href="#u/{c["id"]}">Profile</a></div></div>'''
    if m['waitlist']:
      out += '<h4 style="margin-top:16px">🕒 Waitlist</h4>' + ''.join(
        f'<div style="padding:6px 0" class="cc-row between">{ui.person(c, size=34)}'
        f'{ui.btn("Let in", "approve", c["id"], "soft sm") if w["is_host"] else ""}</div>' for c in m['waitlist'])
    if m['invited']:
      n = len(m['invited'])
      out += f'<p class="small muted" style="margin:12px 0 0">💌 {n} invite{"s" if n != 1 else ""} pending</p>'
    return out + '</div>'

  def forecast_html(self):
    f = self.forecast
    if self.w['is_past'] or self.w['status'] not in ('planning', 'confirmed'):
      return '<h3>🌤️ Weather</h3><p class="small muted" style="margin:0">Forecasts show for upcoming walks.</p>'
    if f is None:
      return '<h3>🌤️ Walk-day forecast</h3><p class="small muted" style="margin:0">Checking the skies…</p>'
    if f is False:
      return ('<h3>🌤️ Walk-day forecast</h3><p class="small muted" style="margin:0">Forecast appears about two weeks before the walk. '
              'Pack layers regardless, it\'s a long day out.</p>')
    rain = f'{f["rain"]}% chance of rain' if f.get('rain') is not None else ''
    return f'''<h3>🌤️ Walk-day forecast</h3><div class="cc-weather"><span class="e">{f["emoji"]}</span>
      <div><b>{round(f["temp"])}°C</b><div class="small muted">{esc(f["label"])} · {rain}<br>Range over the walk: {round(f["low"])}° to {round(f["high"])}°</div></div></div>
      <p class="small" style="margin:10px 0 0">💡 {esc(f["advice"])}</p>'''

  def safety_html(self):
    w = self.w
    return f'''<div class="cc-card tint-sky"><h3>🛟 Walk safe</h3>
      <ul class="cc-safety-list small">
        <li><span class="i">📍</span><span>Meet at the public start point, not someone's home or car.</span></li>
        <li><span class="i">📲</span><span>Share this plan with someone you trust before you set off.</span></li>
        <li><span class="i">👥</span><span>Stay with the group. Let someone know if you head off early.</span></li>
        <li><span class="i">💧</span><span>~{max(1, round((w["distance_km"] or 10) / 8.0))} L of water, snacks, comfy shoes, a charged phone.</span></li>
        <li><span class="i">🌗</span><span>Long walk? Check sunset time and bring a light layer.</span></li>
      </ul>
      <div class="cc-row" style="margin-top:10px">{ui.btn("📤 Share my plan", "share", kind="sm")}
        {ui.btn("🚩 Report", "report", kind="ghost sm") if not w["is_host"] else ""}
        <a class="small" href="#safety">Safety center →</a></div></div>'''

  def post_walk_html(self):
    w = self.w
    if w['status'] != 'completed' or w['my_status'] != 'going':
      return ''
    reviewed = set(w.get('my_reviews') or [])
    stops = ''
    for s in w['stops_full']:
      done = s.get('place_id') in reviewed
      emo = ui.KINDS.get(s['kind'], ('📍',))[0]
      action = ui.pill('✓ Reviewed', 'green') if done else ui.btn('⭐ Review', 'review', s['id'], 'sm orange')
      stops += f'<div class="cc-row between" style="padding:6px 0"><span>{emo} {esc(s["name"])}</span>{action}</div>'
    me_id = (state.me or {}).get('id')
    crew = ''.join(f'<div class="cc-row between" style="padding:6px 0">{ui.person(c, size=34)}{ui.btn("🏅 Endorse", "endorse", c["id"], "ghost sm")}</div>'
                   for c in w['members']['going'] if c.get('id') != me_id)
    return f'''<div class="cc-card tint-green"><h3>🏁 How was it?</h3>
      <p class="muted">Earn points by reviewing the stops (+8 to 12 each), endorsing your crew, and writing it into your Journey.</p>
      <div class="cc-grid halves"><div><h4>Rate the stops</h4>{stops}</div>
      <div><h4>Endorse your crew</h4>{crew or '<p class="small muted">Just you this time!</p>'}</div></div>
      <div style="margin-top:12px">{ui.btn("📔 Write it into my Journey", "journal")}</div></div>'''

  def draw_map(self):
    stops = self.w['stops_full']
    self.mv.clear('route')
    self.mv.clear('proposed')
    self.mv.route(stops, layer='route')
    for i, s in enumerate(stops):
      self.mv.add_marker(s['lat'], s['lng'], ui.KINDS.get(s['kind'], ('📍',))[0], s['kind'], number=i + 1,
                         deal=bool(s['deals']), layer='route', tooltip=s['name'])
    for s in self.w['proposed']:
      self.mv.add_marker(s['lat'], s['lng'], ui.KINDS.get(s['kind'], ('📍',))[0], s['kind'], draft=True, layer='proposed',
                         tooltip=f"Suggested: {s['name']} (👍 {s['votes']})")
    if stops:
      self.mv.fit(stops + self.w['proposed'])

  # ------------------------------------------------------------ actions
  def join(self, _=None):
    w = self.w
    message = None
    if w['visibility'] == 'public' and w['approval_required'] and not w.get('friends_with_host') and w['spots_left'] > 0:
      message = self._intro_message()
      if message is False:
        return
    status = ui.call('join_walk', self.walk_id, message)
    if status is ui.FAIL:
      return
    msgs = {'going': "You're in! 🎉", 'requested': "Request sent 🙋 The host will get back to you.",
            'waitlist': "You're on the waitlist 🤞"}
    ui.toast(msgs.get(status, 'Done'))
    if status == 'going':
      ui.confetti()
    self.load()

  def _intro_message(self):
    tb = ui.textarea(f"Hi {self.w['host']['name'].split(' ')[0]}! I walk at a steady pace and I'm in it for the pastries…", height=90)
    holder = {}
    c = ui.H(f'''<div><div class="cc-modal-title">🙋 Say hi to the host</div>
      <div class="cc-modal-sub">A friendly line helps hosts say yes. Optional, but recommended.</div>{ui.slot("tb")}
      <div class="cc-row end" style="margin-top:14px"><button class="cc-btn ghost" data-act="no">Cancel</button>
      <button class="cc-btn" data-act="yes">Send request</button></div></div>''',
             actions={'yes': lambda a: ui.close_modal(holder['c'], tb.text or ''), 'no': lambda a: ui.close_modal(holder['c'], False)})
    holder['c'] = c
    c.add_component(tb, slot='tb')
    res = ui.modal(c, large=False)
    return False if res is None or res is False else res

  def leave(self, _=None):
    if not ui.ask("Are you sure? Your spot goes to the next person on the waitlist.", yes="Yes, leave"):
      return
    if ui.call('leave_walk', self.walk_id) is not ui.FAIL:
      ui.toast("You've left the walk.", 'info')
      self.load()

  def respond(self, accept):
    status = ui.call('respond_invite', self.walk_id, accept)
    if status is ui.FAIL:
      return
    if status == 'going':
      ui.confetti()
      ui.toast("You're in! 🎉")
    self.load()

  def invite(self):
    if dialogs.invite(self.w):
      self.load()

  def set_vis(self, vis):
    if vis == 'public' and not ui.ask("Open this walk to everyone? It will appear in Discover decks, and you'll approve "
                                      "who joins (unless you switched that off).", yes="Open it up 🌍"):
      return
    if ui.call('set_visibility', self.walk_id, vis) is not ui.FAIL:
      ui.toast("Your walk is now public 🌍" if vis == 'public' else "Now friends-only 👯")
      self.load()

  def complete(self, _=None):
    if not ui.ask("Mark this walk as completed? Everyone going gets their points, and you all get prompted to review stops.",
                  yes="🏁 Complete it"):
      return
    if ui.call('complete_walk', self.walk_id) is not ui.FAIL:
      ui.confetti(['🏁', '🎉', '🥐', '⭐', '🥾'])
      ui.toast("Walk complete! Points are on their way ⭐")
      state.refresh_me()
      self.load()

  def cancel(self, _=None):
    if not ui.ask("Cancel this walk? Everyone going or invited will be notified. This can't be undone.", yes="Cancel walk"):
      return
    if ui.call('cancel_walk', self.walk_id) is not ui.FAIL:
      ui.toast("Walk cancelled.", 'info')
      self.load()

  def share(self, _=None):
    w = self.w
    url = anvil.server.get_app_origin() + '/#walk/' + w['id']
    stops = ' → '.join(s['name'] for s in w['stops_full'])
    text = (f"I'm going on a CityCrossers walk: “{w['title']}”\n"
            f"When: {ui.fmt_when(w['start'])} (about {ui.fmt_dur(w['duration_min'])})\n"
            f"Route ({ui.km(w['distance_km'])}): {stops}\n"
            f"Group: {w['going']} people, hosted by {w['host']['name']}\n{url}")
    nav = anvil.js.window.navigator
    try:
      if nav.share:
        nav.share({'title': w['title'], 'text': text, 'url': url})
        return
    except Exception:
      pass
    if ui.copy_text(text):
      ui.toast("Walk plan copied. Paste it to someone you trust 📲")
    else:
      ui.modal(ui.H(f'<pre style="white-space:pre-wrap">{esc(text)}</pre>'), title='Share your plan', buttons=[('Done', True)])

  def decide(self, uid, accept):
    res = ui.call('host_decide', self.walk_id, uid, accept)
    if res is not ui.FAIL:
      ui.toast("Welcome aboard! 🎉" if res == 'going' else ("Added to waitlist" if res == 'waitlist' else "Declined"),
               'success' if accept else 'info')
      self.load()

  def vote(self, sid):
    if ui.call('vote_stop', sid) is not ui.FAIL:
      self.load()

  def accept_stop(self, sid):
    if ui.call('accept_stop', sid) is not ui.FAIL:
      ui.toast("Added to the route ✓")
      self.load()

  def remove_stop(self, sid):
    if ui.ask("Remove this suggestion?", yes="Remove") and ui.call('remove_stop', sid) is not ui.FAIL:
      self.load()

  def suggest(self, _=None):
    s = self.w['stops_full']
    res = dialogs.place_form('Suggest a stop', 'Click the map where it is. The group votes, the host decides.',
                             lat=None, lng=None, with_map=True, context=s, default_kind='food', button='Suggest it')
    if not res:
      return
    if ui.call('propose_stop', self.walk_id, res) is not ui.FAIL:
      ui.toast("Suggestion posted 🗳️")
      self.load()

  def send_chat(self):
    body = (self.chat_box.text or '').strip()
    if not body:
      return
    if ui.call('post_message', self.walk_id, body) is ui.FAIL:
      return
    self.chat_box.text = ''
    me = state.me or {}
    self.w['messages'].append({'body': body, 'created': ui.now_local(), 'user': me, 'mine': True})
    el = ui.dom(self).querySelector('.js-chat')
    if el is not None:
      u = me
      if 'No messages yet' in el.innerHTML:
        el.innerHTML = ''
      el.insertAdjacentHTML('beforeend', f'''<div class="cc-msg mine">{ui.avatar(u, 30)}
        <div class="b"><span class="who">{esc(u.get("name", ""))} · just now</span>{esc(body)}</div></div>''')
      el.scrollTop = el.scrollHeight

  def review(self, stop_id):
    s = [x for x in self.w['stops_full'] if x['id'] == stop_id]
    if not s:
      return
    s = s[0]
    if dialogs.review(s['name'], place_id=s.get('place_id'), stop_id=None if s.get('place_id') else s['id'], walk_id=self.walk_id):
      state.refresh_me()
      self.load()

  def endorse(self, uid):
    person = [c for c in self.w['members']['going'] if c.get('id') == uid]
    name = person[0]['name'] if person else 'this walker'
    holder = {}

    def toggle(skill_idx):
      skill = ui.SKILLS[int(skill_idx)]
      res = ui.call('endorse', uid, skill)
      if res is ui.FAIL:
        return
      ui.toast(f"Endorsed {name.split(' ')[0]} as {skill}" if res else "Endorsement removed", 'success' if res else 'info')

    buttons = ''.join(f'<button class="cc-chip" data-act="skill" data-arg="{i}">{esc(s)}</button>' for i, s in enumerate(ui.SKILLS))
    c = ui.H(f'''<div><div class="cc-modal-title">🏅 Endorse {esc(name)}</div>
      <div class="cc-modal-sub">What were they great at? Tap once to endorse, again to undo. They get +3 pts per endorsement.</div>
      <div class="cc-chips">{buttons}</div>
      <div class="cc-row end" style="margin-top:16px"><button class="cc-btn" data-act="done">Done</button></div></div>''',
             actions={'skill': toggle, 'done': lambda a: ui.close_modal(holder['c'], True)})
    holder['c'] = c
    ui.modal(c, large=False)

  def journal(self, _=None):
    if dialogs.entry(walk=self.w):
      state.refresh_me()
      state.go('journey')

  def report(self, _=None):
    dialogs.report(walk_id=self.walk_id, who='this walk')
