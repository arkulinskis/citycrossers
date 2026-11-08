import datetime

from anvil import *

from ._anvil_designer import AdminTemplate
from ... import dialogs, state, ui

TABS = [('deals', '🏷️ Deals'), ('places', '📍 Places'), ('reports', '🚩 Safety reports'), ('users', '👥 Users'),
        ('perks', '🎁 Perks'), ('demo', '🧪 Demo data')]


class Admin(AdminTemplate):
    """#admin (admins only): run the club. Numbers at the top, then tabs: partner deals (list + form), places
    (verify, + deal, delete, add), safety reports (resolve), members (verify, admin, suspend), the perks catalog and
    demo data (reload / remove)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.tab = 'deals'
        self.editing_deal = None
        self.editing_perk = None
        admin = state.is_admin()
        self.denied_box.visible = not admin
        self.admin_box.visible = admin
        if not admin:
            return
        self.tabs_panel.add_event_handler('x-pick', self._tab)
        self.deals_panel.add_event_handler('x-deal', self._deal)
        self.places_panel.add_event_handler('x-place', self._place)
        self.reports_panel.add_event_handler('x-resolve', self._resolve)
        self.users_panel.add_event_handler('x-user', self._user)
        self.perks_panel.add_event_handler('x-perk', self._edit_perk)
        self.d_until.date = datetime.date.today() + datetime.timedelta(days=60)
        self.load()

    def load(self):
        d = state.call('admin_overview')
        if d is state.FAIL:
            return
        self.d = state.loose(d)
        self.d_place.items = [('%s %s' % (ui.emoji(p['kind']), p['name']), p['id']) for p in d['places']]
        self.render()

    def _tab(self, key='deals', **event_args):
        self.tab = key
        self.render()

    def render(self):
        s, n = self.d['stats'], self.dom_nodes
        state.text(n['s_users'], s['users'])
        state.text(n['s_walks'], s['walks'])
        state.text(n['s_walks_l'], 'walks (%s done)' % s['completed'])
        state.text(n['s_places'], s['places'])
        state.text(n['s_reviews'], s['reviews'])
        state.text(n['s_deals'], s['active_deals'])
        state.text(n['s_reports'], s['open_reports'])
        state.cls(n['s_reports_box'], 'alarm', bool(s['open_reports']))
        self.tabs_panel.items = [{'key': k, 'label': l, 'on': k == self.tab, 'cls': '',
                                  'count': s['open_reports'] if k == 'reports' else 0} for k, l in TABS]
        for k, _ in TABS:
            getattr(self, k + '_tab').visible = k == self.tab
        getattr(self, 'render_' + self.tab)()

    # ------------------------------------------------------------ tabs
    def render_deals(self):
        deals = self.d['deals']
        self.deals_panel.items = deals
        self.deals_table.visible = bool(deals)
        self.no_deals.visible = not deals
        state.text(self.dom_nodes['deal_h'], '🏷️ %s' % ('Edit deal' if self.editing_deal else 'New deal'))
        self.new_deal_button.visible = bool(self.editing_deal)

    def render_places(self):
        deal_places = set((d.get('place') or {}).get('id') for d in self.d['deals'] if d['active'])
        state.text(self.dom_nodes['places_h'], '📍 Places on the map (%d)' % len(self.d['places']))
        self.places_panel.items = [{'place': p, 'deal': p['id'] in deal_places} for p in self.d['places']]

    def render_reports(self):
        self.reports_panel.items = self.d['reports']
        self.reports_panel.visible = bool(self.d['reports'])
        self.no_reports.visible = not self.d['reports']

    def render_users(self):
        f = (self.user_filter.text or '').strip().lower()
        users = [u for u in self.d['users'] if not f or f in (u['name'] + ' ' + u['email']).lower()]
        self.users_panel.items = users
        self.users_table.visible = bool(users)
        self.no_users.visible = not users

    def render_perks(self):
        self.perks_panel.items = self.d['perks']
        state.text(self.dom_nodes['perk_h'], 'Edit perk' if self.editing_perk else 'New perk')
        self.new_perk_button.visible = bool(self.editing_perk)

    def render_demo(self):
        n = self.d['stats']['demo_rows']
        state.text(self.dom_nodes['demo_n'], '%d demo walker%s.' % (n, 's' if n != 1 else ''))

    @handle('user_filter', 'change')
    def user_filter_change(self, **event_args):
        self.render_users()

    # ------------------------------------------------------------ deals
    def _reset_deal(self):
        self.editing_deal = None
        self.d_place.selected_value = None
        self.d_title.text = ''
        self.d_code.text = ''
        self.d_desc.text = ''
        self.d_pct.text = ''
        self.d_active.checked = True
        self.d_until.date = datetime.date.today() + datetime.timedelta(days=60)

    @handle('new_deal_button', 'click')
    def new_deal_button_click(self, **event_args):
        self._reset_deal()
        self.render()

    def _deal(self, action=None, did=None, **event_args):
        if action == 'edit':
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
        elif action == 'toggle':
            if state.call('admin_toggle_deal', did) is not state.FAIL:
                self.load()
        elif action == 'delete':
            if state.ask("Delete this deal?", yes="Delete") and state.call('admin_delete_deal', did) is not state.FAIL:
                self.load()

    @handle('save_deal_button', 'click')
    def save_deal_button_click(self, **event_args):
        data = {'id': self.editing_deal, 'place_id': self.d_place.selected_value, 'title': self.d_title.text,
                'description': self.d_desc.text, 'percent': self.d_pct.text, 'code': self.d_code.text,
                'valid_until': self.d_until.date, 'active': self.d_active.checked}
        if state.call('admin_save_deal', data) is not state.FAIL:
            state.toast("Deal saved 🏷️")
            self.editing_deal = None
            self.d_title.text = ''
            self.d_desc.text = ''
            self.d_code.text = ''
            self.d_pct.text = ''
            self.load()

    # ------------------------------------------------------------ places, reports, members
    def _place(self, action=None, pid=None, **event_args):
        if action == 'deal':
            self.tab = 'deals'
            self._reset_deal()
            self.d_place.selected_value = pid
            self.render()
            return
        if action == 'delete' and not state.ask("Delete this place? Its reviews and deals go too.", yes="Delete"):
            return
        if state.call('admin_place', pid, action) is not state.FAIL:
            self.load()

    @handle('add_place_button', 'click')
    def add_place_button_click(self, **event_args):
        res = dialogs.place_form('Add a place', 'Click the map to place it.', with_map=True, ask_desc=True, button='Add place')
        if res and state.call('add_place', res) is not state.FAIL:
            state.toast("Place added ✓")
            self.load()

    def _resolve(self, rid=None, **event_args):
        if state.call('admin_resolve_report', rid) is not state.FAIL:
            self.load()

    def _user(self, uid=None, flag=None, **event_args):
        if flag == 'enabled' and not state.ask("Change this member's access?", yes="Yes"):
            return
        if state.call('admin_user', uid, flag) is not state.FAIL:
            self.load()

    # ------------------------------------------------------------ perks
    @handle('new_perk_button', 'click')
    def new_perk_button_click(self, **event_args):
        self.editing_perk = None
        self.p_emoji.text = ''
        self.p_name.text = ''
        self.p_desc.text = ''
        self.p_cost.text = ''
        self.p_active.checked = True
        self.render()

    def _edit_perk(self, pid=None, **event_args):
        p = [x for x in self.d['perks'] if x['id'] == pid][0]
        self.editing_perk = pid
        self.p_emoji.text = p['emoji']
        self.p_name.text = p['name']
        self.p_desc.text = p['description']
        self.p_cost.text = p['cost']
        self.p_active.checked = p['active']
        self.render()

    @handle('save_perk_button', 'click')
    def save_perk_button_click(self, **event_args):
        data = {'id': self.editing_perk, 'emoji': self.p_emoji.text, 'name': self.p_name.text,
                'description': self.p_desc.text, 'cost': self.p_cost.text, 'active': self.p_active.checked}
        if state.call('admin_save_perk', data) is not state.FAIL:
            state.toast("Perk saved 🎁")
            self.editing_perk = None
            self.load()

    # ------------------------------------------------------------ demo data
    @handle('seed_button', 'click')
    def seed_button_click(self, **event_args):
        if not state.ask("Reload demo data? Existing demo data is removed first.", yes="Reload"):
            return
        msg = state.call('admin_seed_demo')
        if msg is not state.FAIL:
            state.toast(msg)
            self.load()

    @handle('clear_demo_button', 'click')
    def clear_demo_button_click(self, **event_args):
        if not state.ask("Remove all demo walkers, walks, places and deals?", yes="Remove"):
            return
        msg = state.call('admin_clear_demo')
        if msg is not state.FAIL:
            state.toast(msg)
            self.load()
