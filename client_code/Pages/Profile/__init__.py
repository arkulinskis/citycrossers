import anvil
import anvil.server
from anvil import *

from ._anvil_designer import ProfileTemplate
from ... import dialogs, state, ui


class Profile(ProfileTemplate):
    """#u/<id> (someone) and #me (my own): a LinkedIn-style walker profile. Hero (banner, avatar, headline, level,
    pace, match, numbers), about, endorsements (I can endorse connections and co-walkers), taste map (reviews),
    journey highlights, badges, walks they host, mutual connections. Someone else's: Connect / Accept, Invite to a
    walk, Report; mine: Edit profile, Copy profile link."""

    def __init__(self, user_id=None, **properties):
        super().__init__(**properties)
        self.user_id = user_id
        self.endorse_panel.add_event_handler('x-endorse', self._endorse)
        self.load()

    def load(self):
        p = state.call('get_profile', self.user_id)
        if p is state.FAIL:
            self.missing_box.visible = True
            self.profile_box.visible = False
            return
        self.missing_box.visible = False
        self.profile_box.visible = True
        self.p = p
        self.render()

    def render(self):
        p, d = self.p, self.dom_nodes
        rel = p['relationship']
        me = rel == 'self'
        lvl = p['level']
        pace = ui.pace_of(p['pace'])
        d['banner'].className = 'banner ' + ui.banner_of(p['id'])
        self.av.show(p, 120)
        self.edit_link.visible = me
        self.copy_button.visible = me
        self.connected_pill.visible = not me and rel == 'friends'
        self.requested_pill.visible = not me and rel == 'pending_out'
        self.accept_button.visible = not me and rel == 'pending_in'
        self.connect_button.visible = not me and rel not in ('friends', 'pending_out', 'pending_in')
        self.invite_button.visible = not me
        self.report_button.visible = not me
        state.set_control_attr(self.report_button, 'aria-label', 'Report %s' % p['name'])
        state.text(d['name'], p['name'])
        state.show(d['ver'], bool(p['verified']))
        state.text(d['headline'], p['headline'] or 'No headline yet')
        state.cls(d['headline'], 'muted', not p['headline'])
        since = p.get('member_since')
        meta = []
        if p['city']:
            meta.append('📍 ' + p['city'])
        if since:
            meta.append('member since %s %s' % (ui.MONTHS[since.month - 1], since.year))
        meta.append('%s connections' % p['friends_count'])
        state.text(d['meta'], ' · '.join(meta))
        pills = [{'text': '%s %s' % (lvl['emoji'], lvl['name']), 'color': 'sun'},
                 {'text': '%s %s walker' % (pace[0], pace[1])},
                 {'text': '🎯 Likes ~%s km' % p['distance_pref']}]
        if p.get('match'):
            pills.append({'text': '%s%% match with you' % p['match'], 'color': 'dark'})
        if p.get('walked_together'):
            pills.append({'text': "🥾 You've walked together", 'color': 'green'})
        self.pills_panel.items = pills
        state.text(d['k_walks'], p['walks_count'])
        state.text(d['k_km'], ui.km(p['km_total']))
        state.text(d['k_met'], p['people_met'])
        state.text(d['k_pts'], p['lifetime_points'])
        state.text(d['bio'], p['bio'] or 'This walker is a mystery. Ask them on a walk.')
        state.cls(d['bio'], 'muted', not p['bio'])
        state.text(d['snack'], p['snack_style'] or '—')
        state.text(d['langs'], p['languages'] or '—')
        self.interests_panel.items = [{'text': i, 'color': 'green'} for i in p['interests']]
        self.no_interests.visible = not p['interests']
        can = bool(p['can_endorse']) and not me
        ends = [{'e': e, 'can': can and e['skill'] in ui.SKILLS} for e in p['endorsements'] if e['count'] or can]
        self.endorse_panel.items = ends
        self.no_endorse.visible = not ends
        self.endorse_hint.visible = bool(ends) and not p['can_endorse'] and not me
        state.text(d['taste_sub'], 'Your reviews' if me else 'Public reviews')
        reviews = p['reviews'][:8]
        self.reviews_panel.items = [{'review': r, 'mode': 'profile'} for r in reviews]
        self.no_reviews.visible = not reviews
        self.journey_link.visible = me
        journal = p['journal'][:6]
        self.journal_panel.items = journal
        self.no_journal.visible = not journal
        badges = p['badges']
        self.badges_panel.items = badges
        state.text(d['badge_count'], '%d/%d' % (len([b for b in badges if b['earned']]), len(badges)))
        self.hosting_card.visible = bool(p['hosting'])
        self.hosting_panel.items = [{'walk': w, 'plain': True,
                                     'sub': '%s · %s' % (ui.fmt_when(w['start']), ui.km(w['distance_km']))} for w in p['hosting']]
        self.mutual_card.visible = bool(p['mutual'])
        self.mutual_panel.items = p['mutual']

    # ------------------------------------------------------------ actions
    @handle('connect_button', 'click')
    def connect_button_click(self, **event_args):
        res = state.call('send_friend_request', self.p['id'])
        if res is not state.FAIL:
            state.toast("Connected! 🤝" if res == 'friends' else "Request sent 👋")
            self.load()

    @handle('accept_button', 'click')
    def accept_button_click(self, **event_args):
        if state.call('respond_friend_request', self.p['id'], True) is not state.FAIL:
            self.load()

    def _endorse(self, skill=None, **event_args):
        res = state.call('endorse', self.p['id'], skill)
        if res is not state.FAIL:
            state.toast("Endorsed as %s 🏅" % skill if res else "Endorsement removed", 'ok' if res else 'info')
            self.load()

    @handle('invite_button', 'click')
    def invite_button_click(self, **event_args):
        mine = state.call('my_walks')
        if mine is state.FAIL:
            return
        walks = [w for w in mine['hosting'] + mine['upcoming'] if not w.get('needs_completion')]
        first = self.p['name'].split(' ')[0]
        if not walks:
            dialogs.info("You have no upcoming walks", text="Plan one and invite %s along." % first, emoji='🗺️',
                         button='Close', link=('Plan a walk', 'plan'))
            return
        from ...Dialogs.PickWalk import PickWalk
        anvil.alert(PickWalk(person=self.p, walks=walks), buttons=[], role='app-dialog')

    @handle('report_button', 'click')
    def report_button_click(self, **event_args):
        dialogs.report(user_id=self.p['id'], who=self.p['name'])

    @handle('copy_button', 'click')
    def copy_button_click(self, **event_args):
        link = anvil.server.get_app_origin() + '/#u/' + self.p['id']
        state.toast("Profile link copied 🔗" if state.copy_text(link) else link)
