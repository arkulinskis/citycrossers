from ._anvil_designer import AdminTemplate
from anvil import *
import datetime

from .. import ui, state, dialogs
from ..ui import esc

TABS = [('deals', '🏷️ Deals'), ('places', '📍 Places'), ('reports', '🚩 Safety reports'), ('users', '👥 Users'),
        ('perks', '🎁 Perks'), ('demo', '🧪 Demo data')]


class Admin(AdminTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.tab = 'deals'
    self.editing_deal = None
    self.editing_perk = None
    if not (state.me or {}).get('is_admin'):
      self.html = '<div class="cc-page">' + ui.empty('🔒', 'Admins only', 'This area is for the CityCrossers team.') + '</div>'
      return
    # deal form
    self.d_place = ui.dropdown([], placeholder='Choose a place…')
    self.d_title = ui.textbox('e.g. 15% off pastries for CityCrossers')
    self.d_desc = ui.textarea('Details walkers should know (when it applies, how to claim)', height=70)
    self.d_pct = ui.textbox('e.g. 15', type='number')
    self.d_code = ui.textbox('e.g. CROSS15 (optional)')
    self.d_until = DatePicker(format='%d %b %Y', pick_time=False, spacing_above='none', spacing_below='none',
                              date=datetime.date.today() + datetime.timedelta(days=60))
    self.d_active = ui.checkbox('Active (visible on the map)', True)
    # perk form
    self.p_emoji = ui.textbox('🎁')
    self.p_name = ui.textbox('Perk name')
    self.p_desc = ui.textbox('Short description')
    self.p_cost = ui.textbox('Cost in points', type='number')
    self.p_active = ui.checkbox('Active', True)
    self.user_filter = ui.textbox('Filter users by name or email…')
    self.user_filter.add_event_handler('change', lambda **e: self.render_users_table())
    self.users_view = ui.H('', actions={'uflag': self.user_flag})
    ui.bind(self, {
      'tab': self.set_tab, 'save_deal': self.save_deal, 'edit_deal': self.edit_deal, 'toggle_deal': self.toggle_deal,
      'del_deal': self.del_deal, 'new_deal': self.reset_deal, 'place_verify': lambda a: self.place(a, 'verify'),
      'place_delete': lambda a: self.place(a, 'delete'), 'add_place': self.add_place, 'resolve': self.resolve,
      'save_perk': self.save_perk, 'edit_perk': self.edit_perk, 'new_perk': self.reset_perk,
      'seed': self.seed, 'clear_demo': self.clear_demo, 'deal_for': self.deal_for,
    })
    self.load()

  def load(self):
    d = ui.call('admin_overview')
    if d is ui.FAIL:
      return
    self.d = d
    self.d_place.items = [(ui.KINDS.get(p['kind'], ('📍',))[0] + ' ' + p['name'], p['id']) for p in d['places']]
    self.render()

  def set_tab(self, t):
    self.tab = t
    self.render()

  # ------------------------------------------------------------ render
  def render(self):
    s = self.d['stats']
    tabs = ''.join(f'<button class="{"on" if k == self.tab else ""}" data-act="tab" data-arg="{k}">{l}'
                   f'{"<span class=cnt>" + str(s["open_reports"]) + "</span>" if k == "reports" and s["open_reports"] else ""}</button>'
                   for k, l in TABS)
    body = getattr(self, 'tab_' + self.tab)()
    self.clear()
    self.html = f'''
    <div class="cc-page">
      <h1 style="margin:0">🛠️ Admin</h1>
      <p class="muted" style="margin:4px 0 18px">Run the club: partner deals, places, safety and members.</p>
      <div class="cc-stat-row" style="margin:0 0 20px">
        <div class="cc-stat" style="background:#fff;border-color:#EEE5D2"><b>{s["users"]}</b><span>members</span></div>
        <div class="cc-stat" style="background:#fff;border-color:#EEE5D2"><b>{s["walks"]}</b><span>walks ({s["completed"]} done)</span></div>
        <div class="cc-stat" style="background:#fff;border-color:#EEE5D2"><b>{s["places"]}</b><span>places</span></div>
        <div class="cc-stat" style="background:#fff;border-color:#EEE5D2"><b>{s["reviews"]}</b><span>reviews</span></div>
        <div class="cc-stat" style="background:#fff;border-color:#EEE5D2"><b>{s["active_deals"]}</b><span>active deals</span></div>
        <div class="cc-stat" style="background:{"#FFF0EE" if s["open_reports"] else "#fff"};border-color:#EEE5D2"><b>{s["open_reports"]}</b><span>open reports</span></div>
      </div>
      <div class="cc-tabs" style="margin-bottom:20px">{tabs}</div>
      {body}
    </div>'''
    if self.tab == 'deals':
      for comp, sl in ((self.d_place, 'd_place'), (self.d_title, 'd_title'), (self.d_desc, 'd_desc'), (self.d_pct, 'd_pct'),
                       (self.d_code, 'd_code'), (self.d_until, 'd_until'), (self.d_active, 'd_active')):
        self.add_component(comp, slot=sl)
    elif self.tab == 'perks':
      for comp, sl in ((self.p_emoji, 'p_emoji'), (self.p_name, 'p_name'), (self.p_desc, 'p_desc'), (self.p_cost, 'p_cost'),
                       (self.p_active, 'p_active')):
        self.add_component(comp, slot=sl)
    elif self.tab == 'users':
      self.add_component(self.user_filter, slot='filter')
      self.add_component(self.users_view, slot='users')
      self.render_users_table()

  def tab_deals(self):
    rows = ''
    for d in self.d['deals']:
      p = d.get('place') or {}
      expired = d.get('valid_until') and d['valid_until'] < datetime.date.today()
      status = ('<span class="cc-pill">Expired</span>' if expired else
                ('<span class="cc-pill green">Live</span>' if d['active'] else '<span class="cc-pill">Paused</span>'))
      rows += f'''<tr><td><b>{esc(d["title"])}</b><div class="tiny muted">{esc(d["description"][:80])}</div></td>
        <td>{ui.KINDS.get(p.get("kind"), ("📍",))[0]} {esc(p.get("name", "?"))}</td>
        <td>{(str(d["percent"]) + "%") if d.get("percent") else "—"}</td><td>{('<span class="cc-code">' + esc(d["code"]) + '</span>') if d["code"] else "—"}</td>
        <td>{ui.fmt_date(d["valid_until"], True) if d.get("valid_until") else "No end"}</td><td>{status}</td>
        <td class="nowrap">{ui.btn("Edit", "edit_deal", d["id"], "ghost sm")}{ui.btn("Pause" if d["active"] else "Activate", "toggle_deal", d["id"], "soft sm")}
        {ui.btn("✕", "del_deal", d["id"], "danger sm")}</td></tr>'''
    table = (f'<div class="cc-table-wrap"><table class="cc-table"><tr><th>Deal</th><th>Place</th><th>%</th><th>Code</th><th>Until</th><th>Status</th><th></th></tr>{rows}</table></div>'
             if rows else ui.empty('🏷️', 'No deals yet', 'Create the first one with the form.'))
    title = 'Edit deal' if self.editing_deal else 'New deal'
    return f'''<div class="cc-grid two" style="align-items:start">
      <div class="cc-card"><div class="cc-card-title"><h3>All deals</h3></div>{table}</div>
      <div class="cc-card tint-orange"><div class="cc-card-title"><h3>🏷️ {title}</h3>{ui.btn("+ New", "new_deal", kind="ghost sm") if self.editing_deal else ""}</div>
        <p class="small" style="margin-top:-6px">Deals show as a <b>%</b> badge on the map, in place details, on walk routes and on the Perks page.
        People who reviewed the place and would go back get notified.</p>
        {ui.field("Place", "d_place")}{ui.field("Headline", "d_title")}{ui.field("Details", "d_desc")}
        <div class="cc-form-row">{ui.field("Percent off", "d_pct")}{ui.field("Code", "d_code")}</div>
        {ui.field("Valid until", "d_until")}{ui.slot("d_active")}
        <div style="margin-top:14px">{ui.btn("Save deal", "save_deal", kind="orange block")}</div></div></div>'''

  def tab_places(self):
    rows = ''
    deal_places = set((d.get('place') or {}).get('id') for d in self.d['deals'] if d['active'])
    for p in self.d['places']:
      rows += f'''<tr><td><b>{ui.KINDS.get(p["kind"], ("📍",))[0]} {esc(p["name"])}</b><div class="tiny muted">{esc(p["description"][:70])}</div></td>
        <td>{esc(ui.KINDS.get(p["kind"], ("", p["kind"]))[1])}</td>
        <td>{('<span class="cc-rating">★ ' + str(p["avg_rating"]) + '</span> (' + str(p["review_count"]) + ')') if p["review_count"] else "—"}</td>
        <td>{"🏷️" if p["id"] in deal_places else ""}</td>
        <td class="nowrap">{ui.btn("✔ Verified" if p["verified"] else "Verify", "place_verify", p["id"], "soft sm" if p["verified"] else "ghost sm")}
        {ui.btn("+ Deal", "deal_for", p["id"], "ghost sm")}{ui.btn("✕", "place_delete", p["id"], "danger sm")}</td></tr>'''
    return f'''<div class="cc-card"><div class="cc-card-title"><h3>📍 Places on the map ({len(self.d["places"])})</h3>{ui.btn("➕ Add a place", "add_place", kind="sm")}</div>
      <div class="cc-table-wrap"><table class="cc-table"><tr><th>Place</th><th>Kind</th><th>Rating</th><th>Deal</th><th></th></tr>{rows}</table></div></div>'''

  def tab_reports(self):
    cards = ''
    for r in self.d['reports']:
      who = ui.person(r['reported_user'], size=36) if r.get('reported_user') else ''
      walk = f'<div class="small">Walk: <a href="#walk/{r["walk"]["id"]}">{esc(r["walk"]["title"])}</a></div>' if r.get('walk') else ''
      cards += f'''<div class="cc-card {"tint-berry" if r["status"] == "open" else "flat"}" style="margin-bottom:12px">
        <div class="cc-row between"><b>🚩 {esc(r["reason"])}</b><span class="cc-pill {"orange" if r["status"] == "open" else "green"}">{esc(r["status"])}</span></div>
        <div class="small muted">Reported {ui.ago(r["created"])} by <a href="#u/{(r["reporter"] or {}).get("id", "")}">{esc((r["reporter"] or {}).get("name", "someone"))}</a></div>
        {('<div style="margin-top:10px">' + who + '</div>') if who else ''}{walk}
        <p style="margin:10px 0;white-space:pre-wrap">{esc(r["details"]) or '<span class="muted">No details given.</span>'}</p>
        <div class="cc-row">{ui.btn("Mark resolved" if r["status"] == "open" else "Re-open", "resolve", r["id"], "sm" if r["status"] == "open" else "ghost sm")}
        {('<a class="cc-btn ghost sm" href="#u/' + r["reported_user"]["id"] + '">View profile</a>') if r.get("reported_user") else ''}</div></div>'''
    return cards or ui.empty('🕊️', 'No reports', "All calm on the towpath.")

  def tab_users(self):
    return f'''<div class="cc-card"><div class="cc-card-title"><h3>👥 Members</h3></div>
      <div style="margin-bottom:12px">{ui.slot("filter")}</div>{ui.slot("users")}</div>'''

  def render_users_table(self):
    f = (self.user_filter.text or '').strip().lower()
    rows = ''
    for u in self.d['users']:
      if f and f not in (u['name'] + ' ' + u['email']).lower():
        continue
      rows += f'''<tr><td>{ui.person(u, sub=esc(u["email"]), size=34)}</td><td>{ui.level_pill(u)}</td>
        <td>{u["walks_count"]} · {ui.km(u["km_total"])}</td><td class="tiny muted">{ui.ago(u.get("signed_up"))}</td>
        <td class="nowrap">
          {ui.btn("✔ Verified" if u["verified"] else "Verify", "uflag", u["id"] + "|verified", "soft sm" if u["verified"] else "ghost sm")}
          {ui.btn("★ Admin" if u["is_admin"] else "Make admin", "uflag", u["id"] + "|admin", "sun sm" if u["is_admin"] else "ghost sm")}
          {ui.btn("Suspend" if u["enabled"] else "Reinstate", "uflag", u["id"] + "|enabled", "danger sm" if u["enabled"] else "sm")}
        </td></tr>'''
    self.users_view.html = (f'<div class="cc-table-wrap"><table class="cc-table"><tr><th>Member</th><th>Level</th><th>Walks</th><th>Joined</th><th></th></tr>{rows}</table></div>'
                            if rows else '<p class="muted">No matches.</p>')

  def tab_perks(self):
    rows = ''.join(f'''<tr><td>{p["emoji"]} <b>{esc(p["name"])}</b><div class="tiny muted">{esc(p["description"])}</div></td>
      <td>⭐ {p["cost"]}</td><td>{'<span class="cc-pill green">Active</span>' if p["active"] else '<span class="cc-pill">Off</span>'}</td>
      <td>{ui.btn("Edit", "edit_perk", p["id"], "ghost sm")}</td></tr>''' for p in self.d['perks'])
    return f'''<div class="cc-grid two" style="align-items:start">
      <div class="cc-card"><h3>🎁 Perks catalog</h3><div class="cc-table-wrap"><table class="cc-table">
        <tr><th>Perk</th><th>Cost</th><th>Status</th><th></th></tr>{rows}</table></div></div>
      <div class="cc-card tint-sun"><div class="cc-card-title"><h3>{"Edit perk" if self.editing_perk else "New perk"}</h3>
        {ui.btn("+ New", "new_perk", kind="ghost sm") if self.editing_perk else ""}</div>
        <div class="cc-form-row">{ui.field("Emoji", "p_emoji")}{ui.field("Cost (points)", "p_cost")}</div>
        {ui.field("Name", "p_name")}{ui.field("Description", "p_desc")}{ui.slot("p_active")}
        <p class="tiny muted">Perks can be switched off but not deleted, so past redemptions keep their history.</p>
        {ui.btn("Save perk", "save_perk", kind="block")}</div></div>'''

  def tab_demo(self):
    n = self.d['stats']['demo_rows']
    return f'''<div class="cc-card" style="max-width:720px">
      <h3>🧪 Demo data</h3>
      <p>A fresh app comes with demo content so it doesn't feel empty: London landmarks plus fictional cafés, {8} demo walkers,
        upcoming walks, reviews and partner deals. Demo walkers can't log in.</p>
      <p><b>Currently loaded:</b> {n} demo walker{"s" if n != 1 else ""}.</p>
      <div class="cc-row">{ui.btn("Reload demo data", "seed", kind="")}{ui.btn("Remove all demo data", "clear_demo", kind="danger")}</div>
      <p class="small muted" style="margin-top:12px">Removing demo data also removes members' reviews of demo places and their spots on demo walks.</p></div>'''

  # ------------------------------------------------------------ deal actions
  def reset_deal(self, _=None):
    self.editing_deal = None
    self.d_place.selected_value = None
    for tb in (self.d_title, self.d_code):
      tb.text = ''
    self.d_desc.text = ''
    self.d_pct.text = None
    self.d_active.checked = True
    self.d_until.date = datetime.date.today() + datetime.timedelta(days=60)
    self.render()

  def deal_for(self, pid):
    self.tab = 'deals'
    self.reset_deal()
    self.d_place.selected_value = pid

  def edit_deal(self, did):
    d = [x for x in self.d['deals'] if x['id'] == did][0]
    self.editing_deal = did
    self.d_place.selected_value = (d.get('place') or {}).get('id')
    self.d_title.text = d['title']
    self.d_desc.text = d['description']
    self.d_pct.text = d.get('percent')
    self.d_code.text = d['code']
    self.d_until.date = d.get('valid_until')
    self.d_active.checked = d['active']
    self.render()

  def save_deal(self, _=None):
    data = {'id': self.editing_deal, 'place_id': self.d_place.selected_value, 'title': self.d_title.text,
            'description': self.d_desc.text, 'percent': self.d_pct.text, 'code': self.d_code.text,
            'valid_until': self.d_until.date, 'active': self.d_active.checked}
    if ui.call('admin_save_deal', data) is not ui.FAIL:
      ui.toast("Deal saved 🏷️")
      self.editing_deal = None
      self.reset_fields_after_save()
      self.load()

  def reset_fields_after_save(self):
    self.d_title.text = ''
    self.d_desc.text = ''
    self.d_code.text = ''
    self.d_pct.text = None

  def toggle_deal(self, did):
    if ui.call('admin_toggle_deal', did) is not ui.FAIL:
      self.load()

  def del_deal(self, did):
    if ui.ask("Delete this deal?", yes="Delete") and ui.call('admin_delete_deal', did) is not ui.FAIL:
      self.load()

  # ------------------------------------------------------------ other actions
  def place(self, pid, action):
    if action == 'delete' and not ui.ask("Delete this place? Its reviews and deals go too.", yes="Delete"):
      return
    if ui.call('admin_place', pid, action) is not ui.FAIL:
      self.load()

  def add_place(self, _=None):
    res = dialogs.place_form('Add a place', 'Click the map to place it.', with_map=True, ask_desc=True, button='Add place')
    if res and ui.call('add_place', res) is not ui.FAIL:
      ui.toast("Place added ✓")
      self.load()

  def resolve(self, rid):
    if ui.call('admin_resolve_report', rid) is not ui.FAIL:
      self.load()

  def user_flag(self, arg):
    uid, flag = arg.split('|')
    if flag == 'enabled' and not ui.ask("Change this member's access?", yes="Yes"):
      return
    if ui.call('admin_user', uid, flag) is not ui.FAIL:
      self.load()

  def reset_perk(self, _=None):
    self.editing_perk = None
    self.p_emoji.text = ''
    self.p_name.text = ''
    self.p_desc.text = ''
    self.p_cost.text = None
    self.p_active.checked = True
    self.render()

  def edit_perk(self, pid):
    p = [x for x in self.d['perks'] if x['id'] == pid][0]
    self.editing_perk = pid
    self.p_emoji.text = p['emoji']
    self.p_name.text = p['name']
    self.p_desc.text = p['description']
    self.p_cost.text = p['cost']
    self.p_active.checked = p['active']
    self.render()

  def save_perk(self, _=None):
    data = {'id': self.editing_perk, 'emoji': self.p_emoji.text, 'name': self.p_name.text, 'description': self.p_desc.text,
            'cost': self.p_cost.text, 'active': self.p_active.checked}
    if ui.call('admin_save_perk', data) is not ui.FAIL:
      ui.toast("Perk saved 🎁")
      self.editing_perk = None
      self.load()

  def seed(self, _=None):
    if not ui.ask("Reload demo data? Existing demo data is removed first.", yes="Reload"):
      return
    msg = ui.call('admin_seed_demo')
    if msg is not ui.FAIL:
      ui.toast(msg)
      self.load()

  def clear_demo(self, _=None):
    if not ui.ask("Remove all demo walkers, walks, places and deals?", yes="Remove"):
      return
    msg = ui.call('admin_clear_demo')
    if msg is not ui.FAIL:
      ui.toast(msg)
      self.load()
