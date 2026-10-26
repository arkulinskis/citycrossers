from ._anvil_designer import ProfileEditTemplate
from anvil import *

from .. import ui, state, dialogs
from ..ui import esc

DISTANCES = [5, 8, 10, 12, 15, 18, 21, 25, 30, 40]


class ProfileEdit(ProfileEditTemplate):
  def __init__(self, welcome=False, **properties):
    self.init_components(**properties)
    self.welcome = welcome
    me = ui.call('get_me')
    if me is ui.FAIL:
      return
    self.me = me
    state.set_me(me)
    self.pace = me['pace']
    self.name = ui.textbox('Your name', text=me['name'])
    self.headline = ui.textbox('e.g. Weekend 25k wanderer · canal enthusiast · will stop for any bun', text=me['headline'])
    self.city = ui.textbox('e.g. London', text=me['city'])
    self.bio = ui.textarea("A few lines about you: why you walk, what you love finding on the way, what you're like at km 18.",
                           text=me['bio'], height=120)
    self.languages = ui.textbox('e.g. English, Spanish, a bit of Swedish', text=me['languages'])
    self.emergency = ui.textbox('Name and phone number of someone we can tell you about', text=me['emergency_contact'])
    self.distance = ui.dropdown([(f"{d} km", d) for d in DISTANCES], value=me['distance_pref'] if me['distance_pref'] in DISTANCES else 15)
    self.snack = ui.Chips(ui.SNACK_STYLES, selected=me['snack_style'] or None, multi=False, color='orange')
    self.interests = ui.Chips(ui.INTERESTS, selected=me['interests'], limit=8)
    self.discoverable = ui.checkbox('🔎 Show me in “Walkers to meet” suggestions and search', me['discoverable'])
    self.journal_public = ui.checkbox('🌍 Make new journal entries & reviews public by default', me['journal_public_default'])
    self.emails = ui.checkbox('📧 Email me about invites, requests and walk changes', me['email_notifications'])
    self.photo = FileLoader(text='📷 Upload a photo', file_types='image/*', spacing_above='none', spacing_below='none')
    self.photo.add_event_handler('change', self.upload)
    self.pace_view = ui.H('', actions={'pace': self.set_pace})
    ui.bind(self, {'save': self.save, 'remove_photo': self.remove_photo, 'pledge': self.pledge})
    self.render()

  def render(self):
    me = self.me
    welcome = ''
    if self.welcome:
      welcome = f'''<div class="cc-hello" style="margin-bottom:20px"><h1>Welcome, {esc(me["name"].split(" ")[0])}! 🎉</h1>
        <p style="margin:0;font-size:1.08rem">Let's set up your walker profile. It's how hosts decide to say yes, and how we match you with
        walks at your pace. Complete it for <b>+25 pts</b>.</p></div>'''
    pct = me['completeness']
    missing = ', '.join(me['missing'])
    pledge = ('<div class="cc-alert" style="margin-top:12px"><span class="ico">✅</span><span>Safety pledge taken. Thank you!</span></div>'
              if me.get('safety_pledge') else
              '<div class="cc-alert orange" style="margin-top:12px"><span class="ico">🛟</span><span style="flex:1">You haven\'t taken the safety pledge yet.</span>'
              + ui.btn('Take it (+10)', 'pledge', kind='sm orange') + '</div>')
    photo_rm = ui.btn('Remove', 'remove_photo', kind='ghost sm') if me.get('avatar') else ''
    self.clear()
    self.html = f'''
    <div class="cc-page narrow">
      {welcome}
      <div class="cc-row between" style="margin-bottom:16px"><h1 style="margin:0">{"Your walker profile" if self.welcome else "✏️ Edit profile"}</h1>
        <a href="#me" class="small">View public profile →</a></div>
      <div class="cc-card tint-sun" style="margin-bottom:18px">
        <div class="cc-row between"><b>Profile strength: {pct}%</b><span class="small muted">{("Missing: " + esc(missing)) if missing else "Looking great ✨"}</span></div>
        <div class="cc-progress sun" style="margin-top:8px"><div style="width:{pct}%"></div></div>
      </div>
      <div class="cc-stack">
        <div class="cc-card">
          <h3>🪪 The basics</h3>
          <div class="cc-row" style="gap:16px;margin-bottom:16px">{ui.avatar(me, 84)}<div>{ui.slot("photo")}<div style="margin-top:6px">{photo_rm}</div>
            <div class="tiny muted" style="margin-top:4px">A clear, friendly face photo helps people recognise you at the meeting point.</div></div></div>
          <div class="cc-form-row">{ui.field("Name", "name")}{ui.field("City", "city")}</div>
          {ui.field("Headline", "headline", "Your one-liner. Think LinkedIn, but for walking.")}
          {ui.field("About you", "bio")}
          {ui.field("Languages", "languages")}
        </div>
        <div class="cc-card">
          <h3>🥾 How you walk</h3>
          <div class="cc-field"><label>Usual pace</label>{ui.slot("pace")}</div>
          {ui.field("Favourite walk length", "distance")}
          <div class="cc-field"><label>Snack philosophy</label>{ui.slot("snack")}</div>
          <div class="cc-field"><label>Into (pick up to 8)</label>{ui.slot("interests")}</div>
        </div>
        <div class="cc-card">
          <h3>🛟 Safety &amp; privacy</h3>
          {ui.field("Emergency contact (private, never shown to other walkers)", "emergency", "Only you can see this. Handy to have on file for long days out.")}
          {ui.slot("discoverable")}{ui.slot("journal_public")}{ui.slot("emails")}
          {pledge}
        </div>
      </div>
      <div class="cc-row end" style="margin-top:18px;position:sticky;bottom:12px">
        <button class="cc-btn lg" data-act="save" style="box-shadow:var(--shadow-lg)">{"Save & start walking →" if self.welcome else "Save profile"}</button>
      </div>
    </div>'''
    for comp, s in ((self.photo, 'photo'), (self.name, 'name'), (self.city, 'city'), (self.headline, 'headline'),
                    (self.bio, 'bio'), (self.languages, 'languages'), (self.pace_view, 'pace'), (self.distance, 'distance'),
                    (self.snack.component, 'snack'), (self.interests.component, 'interests'), (self.emergency, 'emergency'),
                    (self.discoverable, 'discoverable'), (self.journal_public, 'journal_public'), (self.emails, 'emails')):
      self.add_component(comp, slot=s)
    self.render_pace()

  def render_pace(self):
    self.pace_view.html = '<div class="cc-options" style="grid-template-columns:repeat(3,1fr)">' + ''.join(
      f'<button type="button" class="cc-option {"on" if k == self.pace else ""}" data-act="pace" data-arg="{k}"><b>{v[0]} {v[1]}</b><span>{v[2]}</span></button>'
      for k, v in ui.PACES.items()) + '</div>'

  def set_pace(self, k):
    self.pace = k
    self.render_pace()

  def upload(self, file=None, **e):
    if file is None:
      return
    res = ui.call('set_avatar', file)
    if res is not ui.FAIL:
      self.me = res
      state.set_me(res)
      ui.toast("Looking good! 📸")
      self.render()

  def remove_photo(self, _=None):
    res = ui.call('set_avatar', None)
    if res is not ui.FAIL:
      self.me = res
      state.set_me(res)
      self.render()

  def pledge(self, _=None):
    if dialogs.safety_pledge():
      self.me = state.me
      self.render()

  def save(self, _=None):
    data = {
      'display_name': self.name.text, 'headline': self.headline.text, 'city': self.city.text, 'bio': self.bio.text,
      'languages': self.languages.text, 'emergency_contact': self.emergency.text, 'pace': self.pace,
      'distance_pref': self.distance.selected_value, 'snack_style': self.snack.value or '',
      'interests': self.interests.value, 'discoverable': self.discoverable.checked,
      'journal_public_default': self.journal_public.checked, 'email_notifications': self.emails.checked,
    }
    res = ui.call('update_me', data)
    if res is ui.FAIL:
      return
    self.me = res['me']
    state.set_me(res['me'])
    if res.get('message'):
      ui.confetti(['⭐', '🎉', '🪪'])
      ui.toast(res['message'])
    else:
      ui.toast("Profile saved ✓")
    if self.welcome:
      if not self.me.get('safety_pledge'):
        dialogs.safety_pledge()
      state.go('discover')
    else:
      state.go('me')
