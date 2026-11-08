import datetime

import anvil
import anvil.server
from anvil import *
from anvil.js import window

from ._anvil_designer import WalkDetailTemplate
from ... import dialogs, router, state, ui


class WalkDetail(WalkDetailTemplate):
    """#walk/<id>: one walk. The hero (vibe, when, distance, pace, spots), an action bar that fits who I am (host:
    edit / invite / open up / share / cancel / complete; walker: join, request, waitlist, leave, accept an invite),
    the route map + timeline with arrival times, suggested stops (vote, host adds), about + meeting spot, the group
    chat (people going), host, crew (+ requests and waitlist for the host), walk-day weather and safety tips. After a
    completed walk: rate the stops, endorse the crew, write a journey entry."""

    def __init__(self, walk_id=None, **properties):
        super().__init__(**properties)
        self.walk_id = walk_id
        self.w = state.loose(None)
        self.forecast = state.loose(None)  # None = not asked yet, False = none available, dict = the forecast
        self.mv = self.map_view.setup(height='380px')
        self.timeline_panel.add_event_handler('x-place', self._place)
        self.proposed_panel.add_event_handler('x-proposed', self._proposed)
        self.rate_panel.add_event_handler('x-review', self._review)
        for p in (self.endorse_panel, self.going_panel, self.requests_panel, self.waitlist_panel):
            p.add_event_handler('x-act', self._person)
        self._shown = False
        self.load()

    # ------------------------------------------------------------ data
    def load(self):
        w = state.call('get_walk', self.walk_id)
        if w is state.FAIL:
            self.missing_box.visible = True
            self.walk_box.visible = False
            return
        self.missing_box.visible = False
        self.walk_box.visible = True
        self.w = w
        self.render()

    @handle('', 'show')
    def form_show(self, **event_args):
        if self._shown:
            return
        self._shown = True
        w = self.w
        if w and self.forecast is None and not w['is_past'] and w['status'] in ('planning', 'confirmed'):
            window.setTimeout(self._load_forecast, 200)

    def _load_forecast(self):
        f = state.call('walk_forecast', self.walk_id, quiet=True)
        self.forecast = f if f is not state.FAIL and f else False
        self.render_forecast()

    # ------------------------------------------------------------ render
    def render(self):
        w, d = self.w, self.dom_nodes
        v = ui.vibe_of(w['vibe'])
        pace = ui.pace_of(w['pace'])
        d['hero'].className = 'cc-walk-hero cc-fade-in ' + v[3]
        state.text(d['emo'], v[1])
        state.text(d['p_vibe'], '%s %s' % (v[1], v[2]))
        public = w['visibility'] == 'public'
        d['p_vis'].className = 'cc-pill ' + ('sky' if public else 'berry')
        state.text(d['p_vis'], '🌍 Public' if public else '👯 Friends only')
        status = {'completed': '🏁 Completed', 'cancelled': 'Cancelled'}.get(w['status'], '')
        state.text(d['p_status'], status)
        state.show(d['p_status'], bool(status))
        state.text(d['p_match'], '%s%% match' % w.get('match') if w.get('match') else '')
        state.show(d['p_match'], bool(w.get('match')))
        state.text(d['title'], w['title'])
        state.text(d['f_date'], '🗓️ %s (%s)' % (ui.fmt_date(w['start']), ui.fmt_rel(w['start'])))
        state.text(d['f_time'], '🕘 ' + ui.fmt_time(w['start']))
        state.text(d['f_dist'], '📏 ' + ui.km(w['distance_km']))
        state.text(d['f_dur'], '⏱️ ~' + ui.fmt_dur(w['duration_min']))
        state.text(d['f_pace'], '%s %s pace' % (pace[0], pace[1]))
        state.text(d['f_going'], '👥 %s/%s going' % (w['going'], w['max_walkers']))
        self.render_actions()
        self.render_post()
        self.render_route()
        self.render_proposed()
        self.render_about()
        self.render_chat()
        self.render_people()
        self.render_forecast()
        state.text(d['water'], '~%s L of water, snacks, comfy shoes, a charged phone.' % max(1, round((w['distance_km'] or 10) / 8.0)))
        self.report_button.visible = not w['is_host']

    def render_actions(self):
        w, d = self.w, self.dom_nodes
        st = w['my_status']
        show = set()
        req_text, label = '', ''
        if w['status'] == 'cancelled':
            text = 'This walk was cancelled by the host. 😢'
        elif w['status'] == 'completed':
            text = '🏁 This walk is in the books.'
            if st == 'going':
                show.add('journal')
        elif w['is_host'] or (w['is_admin'] and not st):
            text = "⭐ You're hosting"
            req = len(w['members']['requested'])
            if req:
                req_text = ' · %d request%s waiting' % (req, 's' if req != 1 else '')
            show.update(['edit', 'invite', 'share', 'cancel', 'friends' if public_of(w) else 'public'])
            if w['is_past']:
                show.add('complete')
            self.invite_button.text = '💌 Invite'
        elif st == 'going':
            text = "✅ You're going! See you at the start."
            show.update(['invite', 'share', 'leave'])
            self.invite_button.text = '💌 Bring a friend'
            self.leave_button.text = 'Can’t make it'
            self.leave_button.role = ['cc-btn', 'danger', 'sm']
        elif st == 'requested':
            text = '⏳ Request sent. Waiting for %s to say yes.' % (w.get('host') or {}).get('name', 'the host')
            show.add('leave')
            self.leave_button.text = 'Withdraw request'
            self.leave_button.role = ['cc-btn', 'ghost', 'sm']
        elif st == 'waitlist':
            text = "🕒 You're on the waitlist. We'll ping you if a spot opens."
            show.add('leave')
            self.leave_button.text = 'Leave waitlist'
            self.leave_button.role = ['cc-btn', 'ghost', 'sm']
        elif st == 'invited':
            text = "💌 You're invited!"
            show.update(['decline', 'accept'])
        elif w['is_past']:
            text = 'This walk has already set off.'
        else:
            full = w['spots_left'] <= 0
            if full:
                label = '🕒 Join the waitlist'
            elif w['visibility'] == 'public' and w['approval_required'] and not w.get('friends_with_host'):
                label = '🙋 Request to join'
            else:
                label = '💚 Join this walk'
            text = 'Walk is full' if full else '%d spot%s left' % (w['spots_left'], 's' if w['spots_left'] != 1 else '')
            show.add('join')
            self.join_button.text = label
        state.text(d['state_text'], text)
        state.text(d['req_text'], req_text)
        state.show(d['req_text'], bool(req_text))
        for key in ('journal', 'complete', 'edit', 'invite', 'public', 'friends', 'share', 'cancel', 'leave', 'decline',
                    'accept', 'join'):
            getattr(self, key + '_button').visible = key in show

    def render_post(self):
        w = self.w
        on = w['status'] == 'completed' and w['my_status'] == 'going'
        self.post_card.visible = on
        if not on:
            return
        reviewed = set(w.get('my_reviews') or [])
        self.rate_panel.items = [{'stop': s, 'done': s.get('place_id') in reviewed} for s in w['stops_full']]
        me_id = (state.me() or {}).get('id')
        crew = [c for c in w['members']['going'] if c.get('id') != me_id]
        self.endorse_panel.items = [{'card': c, 'size': 34, 'side': ('🏅 Endorse', 'endorse', ['cc-btn', 'ghost', 'sm'])}
                                    for c in crew]
        self.just_you.visible = not crew

    def render_route(self):
        w, d = self.w, self.dom_nodes
        stops = w['stops_full']
        state.text(d['stops_count'], '%d stops · %s food' % (len(stops), w['food_stops']))
        self.no_stops.visible = not stops
        rows, end = [], ''
        if stops:
            stats = ui.route_stats(stops, w['pace'])
            t = ui.local(w['start'])
            walked = 0.0
            for i, s in enumerate(stops):
                leg = mins = None
                if i > 0:
                    leg = stats['legs'][i - 1]
                    walked += leg
                    mins = leg / stats['speed'] * 60
                    t = t + datetime.timedelta(minutes=mins) if t else None
                rows.append({'stop': s, 'leg': leg, 'leg_min': mins, 'eta': ui.fmt_time(t) if t else '',
                             'km_in': walked if i else None})
                if t:
                    t = t + datetime.timedelta(minutes=s['break_min'])
            if t:
                end = '🏁 Back around %s · %d breaks totalling %s · distances are approximate' % (
                    ui.fmt_time(t), stats['breaks'], ui.fmt_dur(stats['break_min']))
        self.timeline_panel.items = rows
        state.text(d['tl_end'], end)
        state.show(d['tl_end'], bool(end))
        mv = self.mv
        mv.clear('route')
        mv.clear('proposed')
        mv.route(stops, layer='route')
        for i, s in enumerate(stops):
            mv.add_marker(s['lat'], s['lng'], ui.emoji(s['kind']), s['kind'], number=i + 1, deal=bool(s['deals']),
                          layer='route', tooltip=s['name'])
        for s in w['proposed']:
            mv.add_marker(s['lat'], s['lng'], ui.emoji(s['kind']), s['kind'], draft=True, layer='proposed',
                          tooltip='Suggested: %s (👍 %s)' % (s['name'], s['votes']))
        if stops:
            mv.fit(stops + w['proposed'])

    def render_proposed(self):
        w = self.w
        can = w['is_host'] or w['my_status'] == 'going'
        rows = w['proposed'] if w['status'] in ('planning', 'confirmed') else []
        self.proposed_card.visible = w['status'] in ('planning', 'confirmed') and (bool(rows) or can)
        me_id = (state.me() or {}).get('id')
        self.proposed_panel.items = [{'stop': s, 'can_vote': can, 'is_host': w['is_host'],
                                      'mine': (s.get('proposed_by') or {}).get('id') == me_id} for s in rows]
        self.no_proposed.visible = not rows
        self.suggest_button.visible = can

    def render_about(self):
        w, d = self.w, self.dom_nodes
        state.text(d['desc'], w['description'] or 'No description yet.')
        state.cls(d['desc'], 'muted', not w['description'])
        self.tags_panel.items = [{'text': t, 'color': 'outline'} for t in w['tags']]
        self.meet_alert.visible = bool(w.get('meeting_note'))
        state.text(d['meet_text'], w.get('meeting_note'))
        self.meet_locked.visible = not w.get('meeting_note') and not w['insider']

    def render_chat(self):
        w, d = self.w, self.dom_nodes
        inside = bool(w['insider'])
        self.chat_card.visible = inside
        self.chat_locked.visible = not inside
        if not inside:
            return
        self.chat_panel.items = w['messages']
        self.no_msgs.visible = not w['messages']
        state.text(d['msg_count'], ui.plural(len(w['messages']), 'message'))
        window.setTimeout(lambda: setattr(d['chat'], 'scrollTop', d['chat'].scrollHeight), 50)

    def render_people(self):
        w, d = self.w, self.dom_nodes
        h = w.get('host') or {}
        self.host_card.visible = bool(h)
        if h:
            self.host.show(h, size=56)
            lvl = h.get('level') or {}
            state.text(d['h_level'], '%s %s' % (lvl.get('emoji', ''), lvl.get('name', '')))
            state.text(d['h_walks'], '%s walks' % h.get('walks_count', 0))
            state.text(d['h_km'], ui.km(h.get('km_total', 0)))
        m = w['members']
        going = m['going']
        state.text(d['crew_count'], '%d/%d' % (len(going), w['max_walkers']))
        pct = min(100, int(100.0 * len(going) / max(1, w['max_walkers'])))
        d['crew_bar'].style.width = '%d%%' % pct
        d['crew_bar_box'].setAttribute('aria-valuenow', str(pct))
        self.going_panel.items = [{'card': c, 'sub': '⭐ Host' if c.get('role') == 'host' else (c.get('headline') or '')}
                                  for c in going]
        self.nobody.visible = not going
        reqs = m['requested']
        self.requests_part.visible = bool(reqs)
        self.requests_panel.items = [{'card': c, 'divider': True, 'note': c.get('message'), 'profile': True,
                                      'under': [('✓ Accept', 'approve', ['cc-btn', 'sm']),
                                                ('Decline', 'reject', ['cc-btn', 'ghost', 'sm'])]} for c in reqs]
        wl = m['waitlist']
        self.waitlist_part.visible = bool(wl)
        self.waitlist_panel.items = [{'card': c, 'size': 34,
                                      'side': ('Let in', 'approve', ['cc-btn', 'soft', 'sm']) if w['is_host'] else None}
                                     for c in wl]
        n = len(m['invited'])
        state.text(d['invited'], '💌 %d invite%s pending' % (n, 's' if n != 1 else '') if n else '')
        state.show(d['invited'], bool(n))

    def render_forecast(self):
        w, d, f = self.w, self.dom_nodes, self.forecast
        if w is None:
            return
        upcoming = not w['is_past'] and w['status'] in ('planning', 'confirmed')
        has = upcoming and isinstance(f, dict)
        self.wx_box.visible = has
        state.text(d['wx_title'], '🌤️ Walk-day forecast' if upcoming else '🌤️ Weather')
        if not upcoming:
            note = 'Forecasts show for upcoming walks.'
        elif f is None:
            note = 'Checking the skies…'
        elif f is False:
            note = "Forecast appears about two weeks before the walk. Pack layers regardless, it's a long day out."
        else:
            note = ''
        state.text(d['wx_note'], note)
        state.show(d['wx_note'], bool(note))
        if has:
            state.text(d['wx_emoji'], f['emoji'])
            state.text(d['wx_temp'], '%s°C' % round(f['temp']))
            rain = '%s%% chance of rain' % f['rain'] if f.get('rain') is not None else ''
            state.text(d['wx_label'], '%s · %s' % (f['label'], rain) if rain else f['label'])
            state.text(d['wx_range'], 'Range over the walk: %s° to %s°' % (round(f['low']), round(f['high'])))
            state.text(d['wx_advice'], '💡 ' + f['advice'])

    # ------------------------------------------------------------ actions
    @handle('join_button', 'click')
    def join_button_click(self, **event_args):
        w = self.w
        message = None
        if w['visibility'] == 'public' and w['approval_required'] and not w.get('friends_with_host') and w['spots_left'] > 0:
            from ...Dialogs.Prompt import Prompt
            first = (w.get('host') or {}).get('name', 'there').split(' ')[0]
            message = anvil.alert(Prompt(title='🙋 Say hi to the host',
                                         sub='A friendly line helps hosts say yes. Optional, but recommended.',
                                         placeholder="Hi %s! I walk at a steady pace and I'm in it for the pastries…" % first,
                                         yes='Send request'), buttons=[], role='app-dialog')
            if message is None or message is False:
                return
        status = state.call('join_walk', self.walk_id, message)
        if status is state.FAIL:
            return
        msgs = {'going': "You're in! 🎉", 'requested': "Request sent 🙋 The host will get back to you.",
                'waitlist': "You're on the waitlist 🤞"}
        state.toast(msgs.get(status, 'Done'))
        if status == 'going':
            state.confetti()
        self.load()

    @handle('leave_button', 'click')
    def leave_button_click(self, **event_args):
        if not state.ask("Are you sure? Your spot goes to the next person on the waitlist.", yes="Yes, leave"):
            return
        if state.call('leave_walk', self.walk_id) is not state.FAIL:
            state.toast("You've left the walk.", 'info')
            self.load()

    def _respond(self, accept):
        status = state.call('respond_invite', self.walk_id, accept)
        if status is state.FAIL:
            return
        if status == 'going':
            state.confetti()
            state.toast("You're in! 🎉")
        self.load()

    @handle('accept_button', 'click')
    def accept_button_click(self, **event_args):
        self._respond(True)

    @handle('decline_button', 'click')
    def decline_button_click(self, **event_args):
        self._respond(False)

    @handle('edit_button', 'click')
    def edit_button_click(self, **event_args):
        router.go('edit/%s' % self.walk_id)

    @handle('invite_button', 'click')
    def invite_button_click(self, **event_args):
        if dialogs.invite(self.w):
            self.load()

    def _set_vis(self, vis):
        if vis == 'public' and not state.ask("Open this walk to everyone? It will appear in Discover decks, and you'll approve "
                                             "who joins (unless you switched that off).", yes="Open it up 🌍"):
            return
        if state.call('set_visibility', self.walk_id, vis) is not state.FAIL:
            state.toast("Your walk is now public 🌍" if vis == 'public' else "Now friends-only 👯")
            self.load()

    @handle('public_button', 'click')
    def public_button_click(self, **event_args):
        self._set_vis('public')

    @handle('friends_button', 'click')
    def friends_button_click(self, **event_args):
        self._set_vis('friends')

    @handle('complete_button', 'click')
    def complete_button_click(self, **event_args):
        if not state.ask("Mark this walk as completed? Everyone going gets their points, and you all get prompted to review stops.",
                         yes="🏁 Complete it"):
            return
        if state.call('complete_walk', self.walk_id) is not state.FAIL:
            state.confetti(['🏁', '🎉', '🥐', '⭐', '🥾'])
            state.toast("Walk complete! Points are on their way ⭐")
            state.refresh_me()
            self.load()

    @handle('cancel_button', 'click')
    def cancel_button_click(self, **event_args):
        if not state.ask("Cancel this walk? Everyone going or invited will be notified. This can't be undone.", yes="Cancel walk"):
            return
        if state.call('cancel_walk', self.walk_id) is not state.FAIL:
            state.toast("Walk cancelled.", 'info')
            self.load()

    def _share(self):
        w = self.w
        url = anvil.server.get_app_origin() + '/#walk/' + w['id']
        stops = ' → '.join(s['name'] for s in w['stops_full'])
        text = ("I'm going on a CityCrossers walk: “%s”\nWhen: %s (about %s)\nRoute (%s): %s\nGroup: %s people, hosted by %s\n%s"
                % (w['title'], ui.fmt_when(w['start']), ui.fmt_dur(w['duration_min']), ui.km(w['distance_km']), stops,
                   w['going'], (w.get('host') or {}).get('name', ''), url))
        nav = window.navigator
        try:
            if getattr(nav, 'share', None):
                nav.share({'title': w['title'], 'text': text, 'url': url})
                return
        except Exception:
            pass
        if state.copy_text(text):
            state.toast("Walk plan copied. Paste it to someone you trust 📲")
        else:
            dialogs.info('Share your plan', pre=text, button='Done')

    @handle('share_button', 'click')
    def share_button_click(self, **event_args):
        self._share()

    @handle('share2_button', 'click')
    def share2_button_click(self, **event_args):
        self._share()

    def _person(self, action=None, uid=None, **event_args):
        if action in ('approve', 'reject'):
            accept = action == 'approve'
            res = state.call('host_decide', self.walk_id, uid, accept)
            if res is not state.FAIL:
                state.toast("Welcome aboard! 🎉" if res == 'going' else ("Added to waitlist" if res == 'waitlist' else "Declined"),
                            'ok' if accept else 'info')
                self.load()
        elif action == 'endorse':
            person = [c for c in self.w['members']['going'] if c.get('id') == uid]
            from ...Dialogs.Endorse import Endorse
            anvil.alert(Endorse(user_id=uid, name=person[0]['name'] if person else 'this walker'), buttons=[],
                        role='app-dialog')

    def _proposed(self, action=None, sid=None, **event_args):
        if action == 'vote':
            if state.call('vote_stop', sid) is not state.FAIL:
                self.load()
        elif action == 'accept':
            if state.call('accept_stop', sid) is not state.FAIL:
                state.toast("Added to the route ✓")
                self.load()
        elif action == 'remove':
            if state.ask("Remove this suggestion?", yes="Remove") and state.call('remove_stop', sid) is not state.FAIL:
                self.load()

    @handle('suggest_button', 'click')
    def suggest_button_click(self, **event_args):
        res = dialogs.place_form('Suggest a stop', 'Click the map where it is. The group votes, the host decides.',
                                 with_map=True, context=self.w['stops_full'], default_kind='food', button='Suggest it')
        if not res:
            return
        if state.call('propose_stop', self.walk_id, res) is not state.FAIL:
            state.toast("Suggestion posted 🗳️")
            self.load()

    def _send(self):
        body = (self.chat_box.text or '').strip()
        if not body:
            return
        if state.call('post_message', self.walk_id, body) is state.FAIL:
            return
        self.chat_box.text = ''
        self.w['messages'].append({'body': body, 'created': ui.now_local(), 'user': state.me() or {}, 'mine': True})
        self.render_chat()

    @handle('send_button', 'click')
    def send_button_click(self, **event_args):
        self._send()

    @handle('chat_box', 'pressed_enter')
    def chat_box_pressed_enter(self, **event_args):
        self._send()

    def _review(self, sid=None, **event_args):
        s = [x for x in self.w['stops_full'] if x['id'] == sid]
        if not s:
            return
        s = s[0]
        if dialogs.review(s['name'], place_id=s.get('place_id'), stop_id=None if s.get('place_id') else s['id'],
                          walk_id=self.walk_id):
            state.refresh_me()
            self.load()

    def _journal(self):
        if dialogs.entry(walk=self.w):
            state.refresh_me()
            router.go('journey')

    @handle('journal_button', 'click')
    def journal_button_click(self, **event_args):
        self._journal()

    @handle('journal2_button', 'click')
    def journal2_button_click(self, **event_args):
        self._journal()

    @handle('report_button', 'click')
    def report_button_click(self, **event_args):
        dialogs.report(walk_id=self.walk_id, who='this walk')

    def _place(self, pid=None, **event_args):
        dialogs.place_details(pid)


def public_of(w):
    return w.get('visibility') == 'public'
