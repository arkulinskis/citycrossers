from ._anvil_designer import ProfileTemplate
from anvil import *

from .. import ui, state, dialogs
from ..ui import esc

BANNER_PATH = '''<svg class="path" viewBox="0 0 800 150" preserveAspectRatio="none" aria-hidden="true">
  <path d="M-10 120 C 120 40, 220 150, 360 80 S 600 20, 810 70" stroke="#fff" stroke-width="5" fill="none" stroke-dasharray="1 14" stroke-linecap="round"/></svg>'''


class Profile(ProfileTemplate):
  def __init__(self, user_id=None, **properties):
    self.init_components(**properties)
    self.user_id = user_id
    ui.bind(self, {'connect': self.connect, 'accept': lambda a: self.respond(True), 'remove': self.remove,
                   'endorse': self.endorse, 'invite': self.invite, 'report': self.report,
                   'copy': self.copy_link})
    self.load()

  def load(self):
    p = ui.call('get_profile', self.user_id)
    if p is ui.FAIL:
      self.html = '<div class="cc-page">' + ui.empty('🫥', "Walker not found", "They may have left, or the link is wrong.") + '</div>'
      return
    self.p = p
    self.render()

  def render(self):
    p = self.p
    me = p['relationship'] == 'self'
    lvl = p['level']
    pace = ui.PACES.get(p['pace'], ui.PACES['steady'])
    banner = ui.VIBES[hash(p['id']) % len(ui.VIBES)][3]
    rel = p['relationship']
    if me:
      actions = ('<a class="cc-btn" href="#me/edit">✏️ Edit profile</a>' + ui.btn('🔗 Copy profile link', 'copy', kind='ghost'))
    else:
      if rel == 'friends':
        primary = '<span class="cc-pill green" style="padding:10px 14px">✓ Connected</span>'
      elif rel == 'pending_out':
        primary = '<span class="cc-pill sun" style="padding:10px 14px">⏳ Request sent</span>'
      elif rel == 'pending_in':
        primary = ui.btn('✓ Accept connection', 'accept')
      else:
        primary = ui.btn('👋 Connect', 'connect')
      actions = primary + ui.btn('💌 Invite to a walk', 'invite', kind='orange') + ui.btn('🚩', 'report', kind='ghost icon', extra='title="Report"')
    since = f" · member since {ui.MONTHS[p['member_since'].month - 1]} {p['member_since'].year}" if p.get('member_since') else ''
    match = ui.pill(f"{p['match']}% match with you", 'dark') if p.get('match') else ''
    together = ui.pill('🥾 You\'ve walked together', 'green') if p.get('walked_together') else ''

    # endorsements
    ends = ''
    for e in p['endorsements']:
      btn = ''
      if p['can_endorse'] and not me:
        idx = ui.SKILLS.index(e['skill']) if e['skill'] in ui.SKILLS else -1
        if idx >= 0:
          btn = f'<button data-act="endorse" data-arg="{idx}">{"✓ Endorsed" if e["mine"] else "+ Endorse"}</button>'
      if e['count'] or btn:
        ends += f'<div class="cc-endorse {"mine" if e["mine"] else ""}"><span>{esc(e["skill"])}</span><span class="cc-row" style="gap:8px"><span class="count">{e["count"]}</span>{btn}</span></div>'
    if not ends:
      ends = '<p class="muted small">No endorsements yet. They come from people who walk together.</p>'
    elif not p['can_endorse'] and not me:
      ends += '<p class="tiny muted" style="margin-top:8px">Connect or walk together to endorse.</p>'

    badges = ''.join(f'<div class="cc-badge-tile {"" if b["earned"] else "locked"}" title="{esc(b["how"])}"><span class="e">{b["emoji"]}</span>'
                     f'<b>{esc(b["name"])}</b><span>{esc(b["how"])}</span></div>' for b in p['badges'])
    earned = len([b for b in p['badges'] if b['earned']])

    reviews = ''
    for r in p['reviews'][:8]:
      place = r.get('place') or {}
      lock = '' if r['is_public'] else ' <span class="cc-pill tiny">🔒 private</span>'
      reviews += f'''<div style="padding:12px 0;border-top:1px dashed #EEE5D2">
        <div class="cc-row between"><b>{ui.KINDS.get(place.get("kind"), ("📍",))[0]} {esc(place.get("name", "A place"))}{lock}</b>
        <span class="cc-rating">{ui.stars(r["rating"])}</span></div>
        {('<div style="font-weight:700;margin-top:4px">' + esc(r["title"]) + '</div>') if r["title"] else ''}
        <div class="small">{esc(r["body"])}</div>
        {('<div class="cc-future small">💌 Note to future me: ' + esc(r["future_note"]) + '</div>') if r.get("future_note") else ''}
        {'<div class="tiny muted" style="margin-top:4px">💚 Would go back</div>' if r["would_return"] else ''}</div>'''
    if not reviews:
      reviews = '<p class="muted small">No public reviews yet.</p>'

    journal = ''
    for j in p['journal'][:6]:
      photo = ui.media_url(j.get('photo'))
      lock = '' if j['is_public'] else ' <span class="cc-pill tiny">🔒 private</span>'
      journal += f'''<div style="padding:12px 0;border-top:1px dashed #EEE5D2">
        <div class="tiny muted" style="font-weight:700">{esc(ui.fmt_date(j["entry_date"], True)) if j.get("entry_date") else ""}{(" · " + ui.km(j["km"])) if j.get("km") else ""}</div>
        <b>{j["mood"]} {esc(j["title"])}</b>{lock}<div class="small">{esc(j["body"][:280])}{"…" if len(j["body"]) > 280 else ""}</div>
        {('<img class="cc-j-photo" src="' + esc(photo) + '" alt="">') if photo else ''}</div>'''
    if not journal:
      journal = '<p class="muted small">Nothing shared from their journey yet.</p>'

    hosting = ''.join(f'<a href="#walk/{w["id"]}" class="cc-row" style="gap:10px;padding:8px 0;color:inherit;text-decoration:none;flex-wrap:nowrap">'
                      f'<span style="font-size:24px">{ui.vibe_of(w["vibe"])[1]}</span><span><b style="display:block">{esc(w["title"])}</b>'
                      f'<span class="small muted">{esc(ui.fmt_when(w["start"]))} · {ui.km(w["distance_km"])}</span></span></a>' for w in p['hosting'])
    mutual = ''.join(f'<a href="#u/{m["id"]}" title="{esc(m["name"])}">{ui.avatar(m, 36)}</a>' for m in p['mutual'])
    interests = ''.join(ui.pill(i, 'green') for i in p['interests']) or '<span class="muted small">No interests listed yet.</span>'

    self.clear()
    self.html = f'''
    <div class="cc-page">
      <div class="cc-profile-hero cc-fade-in">
        <div class="banner {banner}">{BANNER_PATH}</div>
        <div class="inner">
          <div class="top">{ui.avatar(p, 120)}<div class="cc-row">{actions}</div></div>
          <h1>{esc(p["name"])}{' <span class="cc-verified" title="Verified walker">✔</span>' if p["verified"] else ''}</h1>
          <div class="headline">{esc(p["headline"]) or '<span class="muted">No headline yet</span>'}</div>
          <div class="small muted" style="margin-top:4px">{("📍 " + esc(p["city"])) if p["city"] else ""}{since} · {p["friends_count"]} connections</div>
          <div class="cc-pills" style="margin-top:12px">{ui.pill(lvl["emoji"] + " " + lvl["name"], "sun")}{ui.pill(pace[0] + " " + pace[1] + " walker")}
            {ui.pill("🎯 Likes ~" + str(p["distance_pref"]) + " km")}{match}{together}</div>
          <div class="cc-kpis">
            <div class="cc-kpi"><b>{p["walks_count"]}</b><span>walks</span></div>
            <div class="cc-kpi"><b>{ui.km(p["km_total"])}</b><span>walked</span></div>
            <div class="cc-kpi"><b>{p["people_met"]}</b><span>people met</span></div>
            <div class="cc-kpi"><b>{p["lifetime_points"]}</b><span>lifetime points</span></div>
          </div>
        </div>
      </div>
      <div class="cc-grid two" style="margin-top:20px;align-items:start">
        <div class="cc-stack">
          <div class="cc-card"><h3>👋 About</h3><p>{esc(p["bio"]).replace(chr(10), "<br>") or '<span class="muted">This walker is a mystery. Ask them on a walk.</span>'}</p>
            <div class="cc-form-row" style="margin-top:8px">
              <div><div class="cc-label">🥐 Snack philosophy</div><div>{esc(p["snack_style"]) or "—"}</div></div>
              <div><div class="cc-label">🗣️ Languages</div><div>{esc(p["languages"]) or "—"}</div></div></div>
            <div class="cc-label" style="margin-top:14px">💚 Into</div><div class="cc-pills">{interests}</div></div>
          <div class="cc-card"><div class="cc-card-title"><h3>🏅 Endorsements</h3></div><div class="cc-grid" style="gap:8px">{ends}</div></div>
          <div class="cc-card"><div class="cc-card-title"><h3>🍽️ Taste map</h3><span class="small muted">{"Your reviews" if me else "Public reviews"}</span></div>{reviews}</div>
          <div class="cc-card"><div class="cc-card-title"><h3>📔 Journey highlights</h3>{'<a class="small" href="#journey">Open my journey</a>' if me else ''}</div>{journal}</div>
        </div>
        <div class="cc-stack">
          <div class="cc-card"><div class="cc-card-title"><h3>🎖️ Badges</h3><span class="small muted">{earned}/{len(p["badges"])}</span></div>
            <div class="cc-grid" style="grid-template-columns:repeat(2,1fr);gap:8px">{badges}</div></div>
          {('<div class="cc-card"><h3>🗓️ Hosting soon</h3>' + hosting + '</div>') if hosting else ''}
          {('<div class="cc-card"><h3>🤝 Mutual connections</h3><div class="cc-row" style="gap:4px">' + mutual + '</div></div>') if mutual else ''}
          <div class="cc-card tint-sky small"><b>🛟 Meeting someone new?</b> Walk in groups, meet in public, and check
            endorsements from people who've walked with them. <a href="#safety">Safety tips</a></div>
        </div>
      </div>
    </div>'''

  # ------------------------------------------------------------ actions
  def connect(self, _=None):
    res = ui.call('send_friend_request', self.p['id'])
    if res is not ui.FAIL:
      ui.toast("Connected! 🤝" if res == 'friends' else "Request sent 👋")
      self.load()

  def respond(self, accept):
    if ui.call('respond_friend_request', self.p['id'], accept) is not ui.FAIL:
      self.load()

  def remove(self, _=None):
    if ui.ask("Remove this connection?", yes="Remove") and ui.call('remove_friend', self.p['id']) is not ui.FAIL:
      self.load()

  def endorse(self, idx):
    skill = ui.SKILLS[int(idx)]
    res = ui.call('endorse', self.p['id'], skill)
    if res is not ui.FAIL:
      ui.toast(f"Endorsed as {skill} 🏅" if res else "Endorsement removed", 'success' if res else 'info')
      self.load()

  def invite(self, _=None):
    mine = ui.call('my_walks')
    if mine is ui.FAIL:
      return
    walks = [w for w in mine['hosting'] + mine['upcoming'] if not w.get('needs_completion')]
    holder = {}
    if not walks:
      ui.modal(ui.H(ui.empty('🗺️', "You have no upcoming walks", f"Plan one and invite {self.p['name'].split(' ')[0]} along.",
                             '<a class="cc-btn orange" href="#plan">Plan a walk</a>')), large=False, buttons=[('Close', None)])
      return

    def pick(wid):
      n = ui.call('invite_to_walk', wid, [self.p['id']])
      if n is not ui.FAIL:
        ui.toast(f"Invite sent to {self.p['name'].split(' ')[0]} 💌" if n else "They're already on that walk (or invited).",
                 'success' if n else 'info')
        ui.close_modal(holder['c'], True)

    opts = ''.join(f'<button class="cc-option" data-act="pick" data-arg="{w["id"]}" style="margin-bottom:8px">'
                   f'<b>{ui.vibe_of(w["vibe"])[1]} {esc(w["title"])}</b><span>{esc(ui.fmt_when(w["start"]))} · {ui.km(w["distance_km"])} · {w["going"]}/{w["max_walkers"]} going</span></button>'
                   for w in walks)
    c = ui.H(f'<div><div class="cc-modal-title">💌 Invite {esc(self.p["name"])}</div><div class="cc-modal-sub">Pick one of your upcoming walks.</div>{opts}</div>',
             actions={'pick': pick})
    holder['c'] = c
    ui.modal(c, large=False, buttons=[('Cancel', None)])

  def report(self, _=None):
    dialogs.report(user_id=self.p['id'], who=self.p['name'])

  def copy_link(self, _=None):
    import anvil.server
    link = anvil.server.get_app_origin() + '/#u/' + self.p['id']
    ui.toast("Profile link copied 🔗" if ui.copy_text(link) else link)
