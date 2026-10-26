from ._anvil_designer import PerksTemplate
from anvil import *

from .. import ui, state, dialogs
from ..ui import esc

EARN = [("🥾", "Finish a walk", "15 pts + 2 per km"), ("🎪", "Host a walk to the finish", "+25 pts"),
        ("👋", "Each new person you walk with", "+5 pts (up to 50)"), ("🗺️", "Plan a walk", "+10 pts"),
        ("⭐", "Review a place", "+8 pts, +4 if public"), ("📍", "Put a place on the map", "+3 pts"),
        ("🗳️", "Your suggested stop makes the route", "+5 pts"), ("🏅", "Get endorsed", "+3 pts"),
        ("📔", "Write in your journey", "+5 pts a day"), ("🪪", "Complete your profile", "+25 pts once"),
        ("🛟", "Take the safety pledge", "+10 pts once")]


class Perks(PerksTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    ui.bind(self, {'redeem': self.redeem, 'place': dialogs.place_details, 'copy': self.copy})
    self.load()

  def load(self):
    d = ui.call('perks_page')
    if d is ui.FAIL:
      return
    self.d = d
    self.render()

  def render(self):
    d = self.d
    lvl = d['level']
    levels = ''.join(f'<div class="cc-level {"on" if i == lvl["index"] else ""}"><span class="e">{e}</span>{esc(n)}<br><span style="opacity:.7">{t}</span></div>'
                     for i, (t, n, e) in enumerate(ui.LEVELS))
    to_next = f'{lvl["next_at"] - lvl["points"]} pts to {lvl["next_emoji"]} {lvl["next_name"]}' if lvl.get('next_name') else 'Top level reached. Legend.'
    perks = ''
    for p in d['perks']:
      can = d['points'] >= p['cost']
      btn = (ui.btn(f'Redeem for {p["cost"]}', 'redeem', p['id'], 'sm') if can
             else f'<span class="cc-pill">🔒 {p["cost"] - d["points"]} more pts</span>')
      perks += f'''<div class="cc-card cc-perk"><span class="e">{p["emoji"]}</span><h4 style="margin:0">{esc(p["name"])}</h4>
        <p class="small muted" style="flex:1;margin:0">{esc(p["description"])}</p>
        <div class="cc-row between"><span class="cost">⭐ {p["cost"]}</span>{btn}</div></div>'''
    redeemed = ''.join(f'<li><span>{esc(r["perk"])}<br><span class="tiny muted">{ui.ago(r["created"])}</span></span>'
                       f'<span class="cc-code" data-act="copy" data-arg="{esc(r["code"])}" style="cursor:pointer" title="Copy">{esc(r["code"])}</span></li>'
                       for r in d['redemptions'])
    deals = ''
    for x in d['deals']:
      pl = x.get('place') or {}
      tag = f'{x["percent"]}% OFF' if x.get('percent') else 'DEAL'
      code = f'<div class="small" style="margin-top:6px">Code: <span class="cc-code">{esc(x["code"])}</span></div>' if x.get('code') else ''
      until = f'<div class="tiny muted">Until {ui.fmt_date(x["valid_until"], True)}</div>' if x.get('valid_until') else ''
      deals += f'''<div class="cc-card tint-orange cc-clickable" data-act="place" data-arg="{pl.get("id")}">
        <div class="cc-row between"><span class="cc-deal-tag">{tag}</span><span class="small">{ui.KINDS.get(pl.get("kind"), ("📍",))[0]} {esc(pl.get("name", ""))}</span></div>
        <h4 style="margin:10px 0 2px">{esc(x["title"])}</h4><div class="small">{esc(x["description"])}</div>{code}{until}</div>'''
    ledger = ''.join(f'<li><span>{esc(l["reason"])}<br><span class="tiny muted">{ui.ago(l["created"])}</span></span>'
                     f'<span class="{"plus" if l["amount"] >= 0 else "minus"}">{"+" if l["amount"] >= 0 else ""}{l["amount"]}</span></li>'
                     for l in d['ledger']) or '<li class="muted">No points yet. Go for a walk!</li>'
    earn = ''.join(f'<li><span class="i">{e}</span><span style="flex:1">{esc(t)}</span><b class="small" style="color:#0E8A5D">{esc(p)}</b></li>'
                   for e, t, p in EARN)
    self.html = f'''
    <div class="cc-page">
      <div class="cc-points-hero cc-fade-in">
        <span class="sparkle">⭐</span>
        <div class="small" style="opacity:.75;font-weight:700">POINTS TO SPEND</div>
        <h1>⭐ {d["points"]}</h1>
        <div style="margin:6px 0 14px;opacity:.9">{lvl["emoji"]} <b>{esc(lvl["name"])}</b> · {lvl["points"]} lifetime pts · {esc(to_next)}</div>
        <div class="cc-progress sun"><div style="width:{int(lvl["progress"] * 100)}%"></div></div>
        <div class="cc-levels" style="margin-top:18px">{levels}</div>
      </div>
      <div class="cc-grid two" style="margin-top:22px;align-items:start">
        <div>
          <div class="cc-section-title" style="margin-top:0"><h2>🎁 Perks</h2><span class="small muted">Spending points never lowers your level</span></div>
          <div class="cc-grid cards-sm">{perks}</div>
          <div class="cc-section-title"><h2>🏷️ Partner deals</h2><span class="small muted">Show the code at the counter</span></div>
          <div class="cc-grid cards-sm">{deals or ui.empty("🏷️", "No deals right now", "Check back soon.")}</div>
        </div>
        <div class="cc-stack">
          <div class="cc-card"><h3>💡 How to earn</h3><ul class="cc-safety-list small">{earn}</ul></div>
          {('<div class="cc-card tint-sun"><h3>🎟️ Your perk codes</h3><ul class="cc-ledger">' + redeemed + '</ul></div>') if redeemed else ''}
          <div class="cc-card"><h3>📜 History</h3><ul class="cc-ledger small">{ledger}</ul></div>
        </div>
      </div>
    </div>'''

  def redeem(self, pid):
    p = [x for x in self.d['perks'] if x['id'] == pid][0]
    if not ui.ask(f"Spend {p['cost']} points on {p['emoji']} {p['name']}?", yes="Redeem"):
      return
    code = ui.call('redeem_perk', pid)
    if code is ui.FAIL:
      return
    ui.confetti(['🎁', '⭐', '🎉'])
    ui.modal(ui.H(f'''<div class="center"><div style="font-size:56px">{p["emoji"]}</div><div class="cc-modal-title">Enjoy!</div>
      <p>Your code for <b>{esc(p["name"])}</b>:</p><p><span class="cc-code" style="font-size:22px">{esc(code)}</span></p>
      <p class="small muted">It's saved on this page any time you need it.</p></div>'''), large=False, buttons=[('Yay!', True)])
    state.refresh_me()
    self.load()

  def copy(self, code):
    ui.toast("Code copied 📋" if ui.copy_text(code) else code)
