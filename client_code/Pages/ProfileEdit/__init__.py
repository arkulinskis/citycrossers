from anvil import *

from ._anvil_designer import ProfileEditTemplate
from ... import dialogs, router, state, ui

DISTANCES = [5, 8, 10, 12, 15, 18, 21, 25, 30, 40]


class ProfileEdit(ProfileEditTemplate):
    """#me/edit (and #welcome right after sign-up): my walker profile. Photo, name, city, headline, bio, languages,
    pace, favourite distance, snack philosophy, interests, the private emergency contact, privacy switches and the
    safety pledge. A profile strength bar; update_me (+25 pts once at 100%)."""

    def __init__(self, welcome=False, **properties):
        super().__init__(**properties)
        self.welcome = welcome
        me = state.call('get_me')
        if me is state.FAIL:
            me = state.me() or {}
        self.me = me
        if me:
            state.set_me(me)
        self.pace = me.get('pace') or 'steady'
        self.name_box.text = me.get('name') or ''
        self.headline_box.text = me.get('headline') or ''
        self.city_box.text = me.get('city') or ''
        self.bio_box.text = me.get('bio') or ''
        self.langs_box.text = me.get('languages') or ''
        self.emergency_box.text = me.get('emergency_contact') or ''
        self.distance_dd.items = [("%d km" % d, d) for d in DISTANCES]
        self.distance_dd.selected_value = me.get('distance_pref') if me.get('distance_pref') in DISTANCES else 15
        self.snack_chips.setup(ui.SNACK_STYLES, selected=me.get('snack_style') or None, multi=False, color='orange')
        self.interest_chips.setup(ui.INTERESTS, selected=me.get('interests') or [], limit=8)
        self.discoverable_box.checked = bool(me.get('discoverable', True))
        self.public_box.checked = bool(me.get('journal_public_default'))
        self.emails_box.checked = bool(me.get('email_notifications', True))
        state.set_control_attr(self.name_box, 'autocomplete', 'name')
        self.pace_panel.add_event_handler('x-pick', self._pace)
        self.welcome_box.visible = welcome
        state.text(self.dom_nodes['welcome_h'], 'Welcome, %s! 🎉' % (me.get('name') or 'walker').split(' ')[0])
        state.text(self.dom_nodes['h1'], 'Your walker profile' if welcome else '✏️ Edit profile')
        self.save_button.text = 'Save & start walking →' if welcome else 'Save profile'
        self.render()

    def render(self):
        me, d = self.me, self.dom_nodes
        pct = me.get('completeness', 0)
        missing = ', '.join(me.get('missing') or [])
        state.text(d['strength'], 'Profile strength: %s%%' % pct)
        state.text(d['missing'], ('Missing: ' + missing) if missing else 'Looking great ✨')
        d['bar'].style.width = '%s%%' % pct
        d['bar_box'].setAttribute('aria-valuenow', str(pct))
        self.av.show(me, 84)
        self.remove_photo_button.visible = bool(me.get('avatar'))
        self.pledged_alert.visible = bool(me.get('safety_pledge'))
        self.pledge_alert.visible = not me.get('safety_pledge')
        self.render_pace()

    def render_pace(self):
        self.pace_panel.items = [{'key': k, 'title': '%s %s' % (v[0], v[1]), 'sub': v[2], 'on': k == self.pace}
                                 for k, v in ui.PACES.items()]

    def _pace(self, key=None, **event_args):
        self.pace = key
        self.render_pace()

    @handle('photo_loader', 'change')
    def photo_loader_change(self, file=None, **event_args):
        if file is None:
            return
        res = state.call('set_avatar', file)
        if res is not state.FAIL:
            self.me = res
            state.set_me(res)
            state.toast("Looking good! 📸")
            self.render()

    @handle('remove_photo_button', 'click')
    def remove_photo_button_click(self, **event_args):
        res = state.call('set_avatar', None)
        if res is not state.FAIL:
            self.me = res
            state.set_me(res)
            self.render()

    @handle('pledge_button', 'click')
    def pledge_button_click(self, **event_args):
        if dialogs.safety_pledge():
            self.me = state.me() or self.me
            self.render()

    @handle('save_button', 'click')
    def save_button_click(self, **event_args):
        data = {
            'display_name': self.name_box.text, 'headline': self.headline_box.text, 'city': self.city_box.text,
            'bio': self.bio_box.text, 'languages': self.langs_box.text, 'emergency_contact': self.emergency_box.text,
            'pace': self.pace, 'distance_pref': self.distance_dd.selected_value,
            'snack_style': self.snack_chips.value or '', 'interests': self.interest_chips.value,
            'discoverable': self.discoverable_box.checked, 'journal_public_default': self.public_box.checked,
            'email_notifications': self.emails_box.checked,
        }
        res = state.call('update_me', data)
        if res is state.FAIL:
            return
        self.me = res['me']
        state.set_me(res['me'])
        if res.get('message'):
            state.confetti(['⭐', '🎉', '🪪'])
            state.toast(res['message'])
        else:
            state.toast("Profile saved ✓")
        if self.welcome:
            if not self.me.get('safety_pledge'):
                dialogs.safety_pledge()
            router.go('discover')
        else:
            router.go('me')
