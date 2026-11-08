import datetime

from anvil import *

from ._anvil_designer import WalkEditorTemplate
from ... import dialogs, router, state, ui
from ...ui import esc

SIZES = [2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30]
VIS = [('friends', '👯 Friends only', 'Only people you invite and your connections can see it.'),
       ('public', '🌍 Open to the public', "Shows up in walkers' Discover decks. Great when your friends are busy.")]


def next_saturday():
    today = datetime.date.today()
    days = (5 - today.weekday()) % 7 or 7
    d = today + datetime.timedelta(days=days)
    return datetime.datetime(d.year, d.month, d.day, 9, 30)


class WalkEditor(WalkEditorTemplate):
    """#plan (also #plan/from/<place>) and #edit/<walk>: plan a walk. The basics (name, vibe, description, tags),
    when and how fast, the route on the map (click to drop stops or "Add to route" on a place pin; live distance,
    time and breaks, with break-manifesto warnings), who's coming (friends only or public, approval, invites).
    create_walk / update_walk, then the walk page."""

    def __init__(self, walk_id=None, start_place=None, **properties):
        super().__init__(**properties)
        self.walk_id = walk_id
        self.stops = []
        existing = None
        self.denied_box.visible = False
        if walk_id:
            existing = state.call('get_walk_for_edit', walk_id)
            if existing is state.FAIL:
                self.denied_box.visible = True
                self.editor.visible = False
                return
        md = state.call('map_data')
        self.places = md['places'] if md is not state.FAIL else []
        friends = state.call('my_friends')
        self.friends = friends if friends is not state.FAIL else []
        ex = existing or {}
        editing = bool(walk_id)
        state.text(self.dom_nodes['h1'], '✏️ Edit your walk' if editing else '🗺️ Plan a walk')
        state.text(self.dom_nodes['lead'], "Changes notify everyone who's going." if editing else
                   "Pick a route, sprinkle in snack stops, and invite your crew. We'll handle the maths.")
        self.save_button.text = 'Save changes' if editing else 'Create walk & notify friends 🎉'
        self.title_box.text = ex.get('title') or ''
        self.desc_box.text = ex.get('description') or ''
        self.when_picker.date = ex.get('start') or next_saturday()
        self.when_picker.min_date = datetime.date.today()
        self.size_dd.items = [("%d walkers%s" % (n, " (incl. you)" if n == 2 else ""), n) for n in SIZES]
        self.size_dd.selected_value = ex.get('max_walkers') if ex.get('max_walkers') in SIZES else 8
        self.meeting_box.text = ex.get('meeting_note') or ''
        self.approval_box.checked = ex.get('approval_required', True)
        self.tag_chips.setup(ui.WALK_TAGS, selected=ex.get('tags') or [], limit=6)
        self.invite_chips.setup([(f['id'], f['name']) for f in self.friends], selected=ex.get('invited_ids') or [])
        self.invite_chips.visible = bool(self.friends)
        self.no_friends.visible = not self.friends
        self.vibe = ex.get('vibe') or 'urban'
        self.pace = ex.get('pace') or 'steady'
        self.visibility = ex.get('visibility') or 'friends'
        for s in ex.get('stops') or []:
            self.stops.append({'name': s['name'], 'kind': s['kind'], 'lat': s['lat'], 'lng': s['lng'],
                               'place_id': s.get('place_id'), 'note': s.get('note') or ''})
        self.mv = self.map_view.setup(height='420px', on_click=self.map_clicked, scroll_zoom=True, picking=True)
        if start_place and not self.stops:
            p = self._place(start_place)
            if p:
                self.stops.append({'name': p['name'], 'kind': 'start', 'lat': p['lat'], 'lng': p['lng'],
                                   'place_id': p['id'], 'note': ''})
                self.mv.center = [p['lat'], p['lng']]
        self.vibes_panel.add_event_handler('x-pick', self._vibe)
        self.pace_panel.add_event_handler('x-pick', self._pace)
        self.vis_panel.add_event_handler('x-pick', self._vis)
        self.stops_panel.add_event_handler('x-stop', self._stop)
        self.render_vibes()
        self.render_pace()
        self.render_vis()
        self.render_stops()
        if self.stops:
            self.mv.fit(self.stops, max_zoom=15)

    def _place(self, pid):
        for p in self.places:
            if p['id'] == pid:
                return p
        return None

    # ------------------------------------------------------------ pickers
    def render_vibes(self):
        self.vibes_panel.items = [{'key': k, 'emoji': e, 'title': n, 'on': k == self.vibe, 'cls': 'cc-vibe ' + g}
                                  for k, e, n, g in ui.VIBES]

    def _vibe(self, key=None, **event_args):
        self.vibe = key
        self.render_vibes()

    def render_pace(self):
        self.pace_panel.items = [{'key': k, 'title': '%s %s' % (v[0], v[1]), 'sub': v[2], 'on': k == self.pace}
                                 for k, v in ui.PACES.items()]

    def _pace(self, key=None, **event_args):
        self.pace = key
        self.render_pace()
        self.render_stops()

    def render_vis(self):
        self.vis_panel.items = [{'key': k, 'title': t, 'sub': s, 'on': k == self.visibility} for k, t, s in VIS]
        self.approval_box.visible = self.visibility == 'public'

    def _vis(self, key=None, **event_args):
        self.visibility = key
        if key == 'public' and (self.size_dd.selected_value or 8) < 3:
            self.size_dd.selected_value = 6
        self.render_vis()

    # ------------------------------------------------------------ stops
    def render_stops(self):
        has = bool(self.stops)
        self.no_stops.visible = not has
        self.summary.visible = has
        st = ui.route_stats(self.stops, self.pace) if has else None
        self.stops_panel.items = [{'i': i, 'stop': s, 'leg': st['legs'][i - 1] if i > 0 else None}
                                  for i, s in enumerate(self.stops)] if st else []
        if st:
            d = self.dom_nodes
            pace = ui.pace_of(self.pace)
            state.text(d['s_km'], st['km'])
            state.text(d['s_time'], ui.fmt_dur(st['minutes']))
            state.text(d['s_breaks'], st['breaks'])
            state.text(d['s_break_min'], 'breaks · %s' % ui.fmt_dur(st['break_min']))
            state.text(d['s_note'], '%s %s walking at %s · distances follow streets roughly' % (pace[0], ui.fmt_dur(st['walk_min']), pace[2]))
            # The break manifesto: flag long stretches without a pause
            run, longest = 0.0, 0.0
            for i, leg in enumerate(st['legs']):
                run += leg
                longest = max(longest, run)
                if ui.BREAK_MIN.get(self.stops[i + 1]['kind'], 0) > 0:
                    run = 0.0
            food = len([s for s in self.stops if s['kind'] in ('cafe', 'food', 'treat')])
            self.warn_long.visible = longest > 6
            state.text(d['warn_long_text'], "There's a %.1f km stretch without a break. The break manifesto suggests a pause every ~5 km." % longest)
            self.warn_food.visible = len(self.stops) >= 2 and food == 0
            self.warn_finish.visible = len(self.stops) >= 2 and self.stops[-1]['kind'] != 'finish'
        self.draw_route()

    def _insert(self, stop):
        if not self.stops:
            stop['kind'] = 'start'
            self.stops.append(stop)
        elif len(self.stops) == 1:
            if stop['kind'] == 'start':
                stop['kind'] = 'finish'
            self.stops.append(stop)
        elif self.stops[-1]['kind'] == 'finish' and stop['kind'] != 'finish':
            self.stops.insert(len(self.stops) - 1, stop)
        else:
            self.stops.append(stop)
        self.render_stops()

    def map_clicked(self, lat, lng):
        n = len(self.stops)
        default = 'start' if n == 0 else ('finish' if n == 1 else 'cafe')
        title = 'Add the meeting point' if n == 0 else ('Add the finish line' if n == 1 else 'Add a stop')
        res = dialogs.place_form(title, 'Give it a name people will recognise.', lat=lat, lng=lng, kinds=ui.STOP_KINDS,
                                 default_kind=default, button='Add to route')
        if res:
            self._insert({'name': res['name'], 'kind': res['kind'], 'lat': lat, 'lng': lng, 'place_id': None, 'note': ''})

    def add_place(self, pid):
        p = self._place(pid)
        if not p:
            return
        if any(s.get('place_id') == pid for s in self.stops):
            state.toast("That's already on your route.", 'info')
            return
        self._insert({'name': p['name'], 'kind': p['kind'], 'lat': p['lat'], 'lng': p['lng'], 'place_id': p['id'], 'note': ''})
        state.toast("Added %s ✓" % p['name'])

    def _stop(self, action=None, i=0, **event_args):
        s = self.stops[i]
        if action == 'edit':
            res = dialogs.place_form('Edit stop', '', lat=s['lat'], lng=s['lng'], kinds=ui.STOP_KINDS,
                                     default_kind=s['kind'], name=s['name'], button='Save')
            if not res:
                return
            s['name'], s['kind'] = res['name'], res['kind']
        elif action == 'up' and i > 0:
            self.stops[i - 1], self.stops[i] = self.stops[i], self.stops[i - 1]
        elif action == 'down' and i < len(self.stops) - 1:
            self.stops[i + 1], self.stops[i] = self.stops[i], self.stops[i + 1]
        elif action == 'del':
            self.stops.pop(i)
        else:
            return
        self.render_stops()

    # ------------------------------------------------------------ map
    def draw_places(self):
        mv = self.mv
        mv.clear('places')
        used = set(s.get('place_id') for s in self.stops)
        for p in self.places:
            if p['id'] in used:
                continue
            emo = ui.emoji(p['kind'])
            deal = p['deals'][0] if p['deals'] else None
            el = mv.popup_el(
                '<h4>%s %s</h4><div class="small muted">%s</div>%s'
                '<button type="button" class="cc-btn sm" data-act="add" data-arg="%s">➕ Add to route</button>'
                % (emo, esc(p['name']), esc((p['description'] or '')[:100]),
                   ('<div class="cc-pop-deal"><span class="cc-deal-tag">DEAL</span> <b class="small">%s</b></div>' % esc(deal['title'])) if deal else '',
                   esc(p['id'])), actions={'add': self.add_place})
            mv.add_marker(p['lat'], p['lng'], emo, p['kind'], popup=el, deal=bool(deal), layer='places', tooltip=p['name'])

    def draw_route(self):
        mv = self.mv
        mv.clear('route')
        mv.route(self.stops, layer='route')
        for i, s in enumerate(self.stops):
            mv.add_marker(s['lat'], s['lng'], ui.emoji(s['kind']), s['kind'], number=i + 1, layer='route', tooltip=s['name'])
        self.draw_places()

    @handle('locate_button', 'click')
    def locate_button_click(self, **event_args):
        self.mv.locate()

    # ------------------------------------------------------------ save
    @handle('cancel_button', 'click')
    def cancel_button_click(self, **event_args):
        router.go('walk/' + self.walk_id if self.walk_id else 'discover')

    @handle('save_button', 'click')
    def save_button_click(self, **event_args):
        title = (self.title_box.text or '').strip()
        if len(title) < 3:
            state.toast("Give your walk a name first.", 'warning')
            return
        if len(self.stops) < 2:
            state.toast("Add at least a meeting point and a finish line on the map.", 'warning')
            return
        if not self.when_picker.date:
            state.toast("Pick a start date and time.", 'warning')
            return
        data = {
            'title': title, 'description': self.desc_box.text, 'start': self.when_picker.date, 'pace': self.pace,
            'max_walkers': self.size_dd.selected_value or 8, 'visibility': self.visibility, 'vibe': self.vibe,
            'tags': self.tag_chips.value,
            'approval_required': self.approval_box.checked if self.visibility == 'public' else True,
            'meeting_note': self.meeting_box.text, 'stops': self.stops,
            'invite_ids': self.invite_chips.value if self.friends else [],
        }
        if self.walk_id:
            wid = state.call('update_walk', self.walk_id, data)
            if wid is state.FAIL:
                return
            state.toast("Walk updated ✓")
        else:
            wid = state.call('create_walk', data)
            if wid is state.FAIL:
                return
            state.confetti(['🥐', '☕', '🗺️', '🎉', '🥾'])
            state.toast("Your walk is live! +10 pts 🎉")
        state.refresh_me()
        router.go('walk/' + wid)
