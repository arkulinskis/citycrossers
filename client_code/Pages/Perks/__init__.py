from anvil import *

from ._anvil_designer import PerksTemplate
from ... import dialogs, state, ui


class Perks(PerksTemplate):
    """#perks: my points and level (six levels, Stroller to City Crosser), perks to redeem (redeem_perk gives a
    code), partner deals, how to earn, my perk codes and the points history."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.perks_panel.add_event_handler('x-redeem', self._redeem)
        self.deals_panel.add_event_handler('x-place', self._place)
        self.load()

    def load(self):
        d = state.call('perks_page')
        if d is state.FAIL:
            d = {'level': {'index': 0, 'emoji': '🚶', 'name': 'Stroller', 'points': 0, 'progress': 0}, 'points': 0,
                 'perks': [], 'redemptions': [], 'deals': [], 'ledger': []}
        self.d = state.loose(d)
        self.render()

    def render(self):
        d, n = self.d, self.dom_nodes
        lvl = d['level']
        state.text(n['points'], '⭐ %s' % d['points'])
        to_next = ('%s pts to %s %s' % (lvl['next_at'] - lvl['points'], lvl['next_emoji'], lvl['next_name'])
                   if lvl.get('next_name') else 'Top level reached. Legend.')
        state.text(n['level'], '%s %s · %s lifetime pts · %s' % (lvl['emoji'], lvl['name'], lvl['points'], to_next))
        pct = int(lvl.get('progress', 0) * 100)
        n['bar'].style.width = '%d%%' % pct
        n['bar_box'].setAttribute('aria-valuenow', str(pct))
        self.levels_panel.items = [{'emoji': e, 'name': nm, 'at': t, 'on': i == lvl['index']}
                                   for i, (t, nm, e) in enumerate(ui.LEVELS)]
        self.perks_panel.items = [{'perk': p, 'points': d['points']} for p in d['perks']]
        self.deals_panel.items = [{'deal': x, 'place': x.get('place'), 'mode': 'perks'} for x in d['deals']]
        self.deals_panel.visible = bool(d['deals'])
        self.no_deals.visible = not d['deals']
        self.codes_card.visible = bool(d['redemptions'])
        self.codes_panel.items = [{'left': r['perk'], 'sub': ui.ago(r['created']), 'code': r['code']} for r in d['redemptions']]
        self.ledger_panel.items = [{'left': l['reason'], 'sub': ui.ago(l['created']), 'plus': l['amount'] >= 0,
                                    'right': ('+' if l['amount'] >= 0 else '') + str(l['amount'])} for l in d['ledger']]
        self.no_ledger.visible = not d['ledger']

    def _redeem(self, pid=None, **event_args):
        p = [x for x in self.d['perks'] if x['id'] == pid][0]
        if not state.ask("Spend %s points on %s %s?" % (p['cost'], p['emoji'], p['name']), yes="Redeem"):
            return
        code = state.call('redeem_perk', pid)
        if code is state.FAIL:
            return
        state.confetti(['🎁', '⭐', '🎉'])
        dialogs.info('Enjoy!', text='Your code for %s (saved on this page any time you need it):' % p['name'],
                     emoji=p['emoji'], code=code, button='Yay!')
        state.refresh_me()
        self.load()

    def _place(self, pid=None, **event_args):
        dialogs.place_details(pid)
