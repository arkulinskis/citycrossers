from anvil import *
from anvil.js import window

from ._anvil_designer import WalkPublicTemplate
from ... import router, state, ui


class WalkPublic(WalkPublicTemplate):
    """#walk/<id> for visitors (not signed in): the walk itself instead of the landing page, so a shared link (/w/<id>,
    email invites, Meetup posts) shows what the friend was invited to. The vibe hero, date and time in the visitor's
    own time zone, km, duration, pace, food stops, "4 of 8 going · 4 spots left", the route map and stops (with their
    conversation topics), and the host's first name, level and walk count (public_walk: never the meeting spot, the
    crew or the chat). "Join this walk" opens sign-up; afterwards the walk page opens and carries on with the join
    (router remembers the address, state.want_join). Friends-only, missing and cancelled walks get a friendly page
    with a way to find open walks. Shell mode "landing": this page draws its own top bar and footer."""

    def __init__(self, walk_id=None, **properties):
        super().__init__(**properties)
        self.walk_id = walk_id
        self.w = state.loose(None)
        self.mv = self.map_view.setup(height='340px')
        self.loading_box.visible = True
        self.missing_box.visible = False
        self.walk_box.visible = False
        self._shown = False

    @handle('', 'show')
    def form_show(self, **event_args):
        if not self._shown:
            self._shown = True
            window.setTimeout(self.load, 0)  # draw the "lacing up" state first, then fetch the walk

    # ------------------------------------------------------------ data
    def load(self):
        res = state.call('public_walk', self.walk_id, quiet=True)
        self.loading_box.visible = False
        if res is state.FAIL:
            return self.missing('📡', "We couldn't load this walk", "Check your connection and try again.", retry=True)
        if not res:
            return self.missing('🔒', 'This walk is private, or no longer here',
                                "Friends-only walks are for the host's connections and the people they invite. Got an "
                                "invite? Log in, or join with the email address it was sent to, and it opens for you.")
        if res['status'] == 'cancelled':
            return self.missing('😢', 'This walk was cancelled',
                                '“%s” was called off by the host. Plenty of other long walks with snack stops are '
                                'waiting.' % res['title'])
        self.w = res
        self.render()

    def missing(self, emoji, title, text, retry=False):
        d = self.dom_nodes
        state.text(d['missing_emoji'], emoji)
        state.text(d['missing_title'], title)
        state.text(d['missing_text'], text)
        self.retry_button.visible = retry
        self.find_button.visible = not retry
        self.missing_login_button.visible = not retry
        self.missing_box.visible = True
        self.walk_box.visible = False

    # ------------------------------------------------------------ render
    def render(self):
        w, d = self.w, self.dom_nodes
        window.document.title = '%s · CityCrossers' % w['title']
        v = ui.vibe_of(w['vibe'])
        pace = ui.pace_of(w['pace'])
        d['hero'].className = 'cc-walk-hero cc-fade-in ' + v[3]
        state.text(d['emo'], v[1])
        state.text(d['p_vibe'], '%s %s' % (v[1], v[2]))
        ed = w.get('edition') or 1
        state.text(d['p_series'], '🔁 Weekly walk · edition %d' % ed if ed > 1 else '')
        state.show(d['p_series'], ed > 1)
        done = w['is_past'] or w['status'] == 'completed'
        state.text(d['p_status'], '🏁 This walk has happened' if done else '')
        state.show(d['p_status'], done)
        state.text(d['title'], w['title'])
        state.text(d['f_date'], '🗓️ %s (%s)' % (ui.fmt_date(w['start']), ui.fmt_rel(w['start'])))
        state.text(d['f_time'], '🕘 ' + ui.fmt_time(w['start']))
        state.text(d['f_dist'], '📏 ' + ui.km(w['distance_km']))
        state.text(d['f_dur'], '⏱️ ~' + ui.fmt_dur(w['duration_min']))
        state.text(d['f_pace'], '%s %s pace' % (pace[0], pace[1]))
        n = w['food_stops']
        state.text(d['f_food'], '🥐 %d food stop%s' % (n, '' if n == 1 else 's'))
        # who's going (a count only) and the join call
        left, going, maxw = w['spots_left'], w['going'], w['max_walkers']
        if done:
            spots, note = '%d walked this one' % going, 'New walks go up every week.'
            label = '🧭 Find upcoming walks'
        elif left <= 0:
            spots, note = '%d of %d going · full' % (going, maxw), "Join the waitlist: if a spot opens, it's yours."
            label = '🕒 Join the waitlist'
        else:
            spots = '%d of %d going · %d spot%s left' % (going, maxw, left, '' if left == 1 else 's')
            note = ('Free. The host says hi and approves new walkers.' if w['approval_required']
                    else 'Free, and you can join straight away.')
            label = '💚 Join this walk'
        state.text(d['spots_text'], spots)
        state.text(d['join_note'], note)
        pct = min(100, int(100.0 * going / max(1, maxw)))
        d['bar'].style.width = '%d%%' % pct
        d['bar_box'].setAttribute('aria-valuenow', str(pct))
        self.join_button.text = label
        self.join2_button.text = label
        # route and stops
        stops = w.get('stops') or []
        state.text(d['stops_count'], '%d stops · %d food' % (len(stops), n))
        rows, end = ui.timeline(stops, w['pace'], w['start'])
        for i, r in enumerate(rows):
            r.update({'walk_id': w['id'], 'i': i, 'link': False})
        self.timeline_panel.items = rows
        state.text(d['tl_end'], end)
        state.show(d['tl_end'], bool(end))
        mv = self.mv
        mv.clear('route')
        mv.route(stops, layer='route')
        for i, s in enumerate(stops):
            mv.add_marker(s['lat'], s['lng'], ui.emoji(s['kind']), s['kind'], number=i + 1, layer='route', tooltip=s['name'])
        if stops:
            mv.fit(stops)
        # about + host
        state.text(d['desc'], w['description'] or 'The host will share more in the group chat.')
        state.cls(d['desc'], 'muted', not w['description'])
        self.tags_panel.items = [{'text': t, 'color': 'outline'} for t in w['tags']]
        h = w.get('host') or {}
        self.host_card.visible = bool(h)
        if h:
            lvl = h.get('level') or {}
            self.host.show(h, sub='%s %s' % (lvl.get('emoji', ''), lvl.get('name', '')), size=56, link=False)
            state.text(d['h_level'], '%s %s' % (lvl.get('emoji', ''), lvl.get('name', '')))
            wc = h.get('walks_count', 0)
            state.text(d['h_walks'], '%d walk%s done' % (wc, '' if wc == 1 else 's'))
        self.walk_box.visible = True
        self.missing_box.visible = False

    # ------------------------------------------------------------ actions
    def _join(self):
        w = self.w
        if w and (w['is_past'] or w['status'] == 'completed'):
            return self._find()
        state.want_join(self.walk_id)
        state.after_login('walk/%s' % self.walk_id)
        if state.ask_login('signup'):
            router.after_sign_in()
        else:
            state.want_join(None)

    def _find(self):
        """Sign up, then Discover (a new account first visits #welcome)."""
        state.after_login(None)
        if state.ask_login('signup'):
            router.after_sign_in()

    def _login(self):
        state.after_login('walk/%s' % self.walk_id)
        if state.ask_login('login'):
            router.after_sign_in()

    @handle('join_button', 'click')
    def join_button_click(self, **event_args):
        self._join()

    @handle('join2_button', 'click')
    def join2_button_click(self, **event_args):
        self._join()

    @handle('join_top_button', 'click')
    def join_top_button_click(self, **event_args):
        if self.w:
            self._join()
        else:
            self._find()

    @handle('login_button', 'click')
    def login_button_click(self, **event_args):
        self._login()

    @handle('missing_login_button', 'click')
    def missing_login_button_click(self, **event_args):
        self._login()

    @handle('find_button', 'click')
    def find_button_click(self, **event_args):
        self._find()

    @handle('retry_button', 'click')
    def retry_button_click(self, **event_args):
        self.missing_box.visible = False
        self.loading_box.visible = True
        window.setTimeout(self.load, 0)
