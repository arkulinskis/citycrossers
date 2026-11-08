from anvil import *

from ._anvil_designer import MapPageTemplate
from ... import dialogs, router, state, ui
from ...ui import esc

FILTERS = [('all', '✨ Everything'), ('deals', '🏷️ Deals'), ('walks', '🚩 Walks')] + \
          [(k, ui.KINDS[k][0] + ' ' + ui.KINDS[k][1]) for k in ui.PLACE_KINDS]


class MapPage(MapPageTemplate):
    """#map, the snack map: every place walkers pinned (filter by kind, deals or walk starts), popups with
    "Reviews & more" (dialogs.place_details) and "Start here" (#plan/from/<id>); "Propose a place" turns the next
    map click into a new place (add_place, +3 pts). Under the map: partner deals and walks starting soon."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.filter, self.picking, self._fitted = 'all', False, False
        data = state.call('map_data')
        self.data = state.loose(data if data is not state.FAIL else {'places': [], 'walks': []})
        self.mv = self.map_view.setup(height='min(64vh, 620px)', on_click=self.map_clicked, scroll_zoom=True)
        self.filters_panel.add_event_handler('x-pick', self._filter)
        self.deals_panel.add_event_handler('x-place', self._place_event)
        self.render()

    def render(self):
        places, walks = self.data['places'], self.data['walks']
        self.filters_panel.items = [{'key': k, 'label': l, 'on': k == self.filter} for k, l in FILTERS]
        deals = [{'deal': d, 'place': p, 'mode': 'map'} for p in places for d in (p.get('deals') or [])]
        self.deals_panel.items = deals
        self.deals_panel.visible = bool(deals)
        self.deals_empty.visible = not deals
        soon = sorted(walks, key=lambda w: w['start'])[:8]
        self.walks_panel.items = [{'walk': w, 'sub': '%s · %s · %s/%s going' % (ui.fmt_when(w['start']), ui.km(w['distance_km']),
                                                                            w['going'], w['max_walkers'])} for w in soon]
        self.walks_empty.visible = not soon
        state.text(self.dom_nodes['counts'], '%d places · %d upcoming walks' % (len(places), len(walks)))
        self.draw()

    def draw(self):
        mv = self.mv
        mv.clear('places')
        mv.clear('walks')
        shown = []
        f = self.filter
        if f in ('all', 'walks'):
            for w in self.data['walks']:
                el = mv.popup_el(
                    '<h4>%s %s</h4><div class="small muted">%s<br>%s · %s/%s going</div>'
                    '<button type="button" class="cc-btn sm" data-act="walk" data-arg="%s">See the walk</button>'
                    % (ui.vibe_of(w['vibe'])[1], esc(w['title']), esc(ui.fmt_when(w['start'])), ui.km(w['distance_km']),
                       w['going'], w['max_walkers'], esc(w['id'])),
                    actions={'walk': lambda a: router.go('walk/' + a)})
                mv.add_marker(w['lat'], w['lng'], '🚩', 'walk', popup=el, layer='walks', tooltip=w['title'])
                shown.append(w)
        if f != 'walks':
            for p in self.data['places']:
                if f == 'deals' and not p['deals']:
                    continue
                if f not in ('all', 'deals') and p['kind'] != f:
                    continue
                emo, kind_name = ui.kind(p['kind'])
                deal = p['deals'][0] if p['deals'] else None
                deal_html = ('<div class="cc-pop-deal"><span class="cc-deal-tag">%s</span> <b class="small">%s</b></div>'
                             % (ui.deal_tag(deal), esc(deal['title']))) if deal else ''
                rating = ('<span class="cc-rating">%s</span> <span class="small muted">(%s)</span>' % (ui.stars(p['avg_rating']), p['review_count'])
                          if p['review_count'] else '<span class="small muted">No reviews yet</span>')
                el = mv.popup_el(
                    '<h4>%s %s</h4><div class="small muted">%s</div><div>%s</div><div class="small cc-pop-desc">%s</div>%s'
                    '<div class="cc-row cc-pop-acts"><button type="button" class="cc-btn sm" data-act="place" data-arg="%s">Reviews &amp; more</button>'
                    '<button type="button" class="cc-btn sm ghost" data-act="plan" data-arg="%s">Start here</button></div>'
                    % (emo, esc(p['name']), esc(kind_name), rating, esc((p['description'] or '')[:120]), deal_html,
                       esc(p['id']), esc(p['id'])),
                    actions={'place': dialogs.place_details, 'plan': lambda a: router.go('plan/from/' + a)})
                mv.add_marker(p['lat'], p['lng'], emo, p['kind'], popup=el, deal=bool(deal), layer='places', tooltip=p['name'])
                shown.append(p)
        if shown and not self._fitted:
            self._fitted = True
            mv.fit(shown, padding=30, max_zoom=14)

    def _filter(self, key='all', **event_args):
        self.filter = key
        self.filters_panel.items = [{'key': k, 'label': l, 'on': k == self.filter} for k, l in FILTERS]
        self.draw()

    def _place_event(self, pid=None, **event_args):
        dialogs.place_details(pid)

    @handle('locate_button', 'click')
    def locate_button_click(self, **event_args):
        self.mv.locate()

    @handle('propose_button', 'click')
    def propose_button_click(self, **event_args):
        self._picking(not self.picking)

    def _picking(self, on):
        self.picking = on
        self.mv.set_picking(on)
        self.propose_button.text = '✖ Cancel' if on else '➕ Propose a place'
        if on:
            state.toast('Click the map where the place is 👇', 'info')

    def map_clicked(self, lat, lng):
        if not self.picking:
            return
        self._picking(False)
        res = dialogs.place_form('Propose a place', 'Share a stop worth stopping for. Other walkers can review it and add it to routes.',
                                 lat=lat, lng=lng, ask_desc=True, button='Put it on the map (+3 pts)')
        if not res:
            return
        place = state.call('add_place', res)
        if place is state.FAIL:
            return
        state.toast('%s is on the map! +3 pts 📍' % place['name'])
        self.data['places'].append(place)
        self.render()
        state.refresh_me()
