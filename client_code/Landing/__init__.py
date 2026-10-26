from ._anvil_designer import LandingTemplate
from anvil import *
import anvil.js

from .. import ui, state, dialogs
from ..landing_content import HTML


class Landing(LandingTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.html = HTML
    ui.bind(self, {
      'signup': lambda a: self.auth('signup'),
      'login': lambda a: self.auth('login'),
      'scroll': lambda a: anvil.js.window.cc.scrollTo(a),
      'safety': lambda a: state.go('safety'),
      'partner': self.partner,
      'open': lambda a: state.go('discover'),
    })
    if state.logged_in():
      auth = ui.dom(self).querySelector('.lp-auth')
      if auth:
        auth.innerHTML = '<button class="cc-btn" data-act="open">Open the app →</button>'

  def auth(self, mode):
    if state.logged_in():
      state.go('discover')
      return
    if dialogs.auth(mode):
      state.main.on_login()

  def partner(self, _=None):
    ui.modal(ui.H('''<div>
      <div class="cc-modal-title">🏷️ Become a partner stop</div>
      <p>Partner places get a deal badge on the CityCrossers map, appear in the Perks page, and are suggested
        to hosts planning routes nearby.</p>
      <ul class="cc-safety-list">
        <li><span class="i">1️⃣</span><span>Pick an offer walkers will love: a discount, a free refill, a group table.</span></li>
        <li><span class="i">2️⃣</span><span>Our team adds your place and deal to the map (admins do this from the Admin page).</span></li>
        <li><span class="i">3️⃣</span><span>Hungry groups arrive. You get reviews from people who walked 12 km to reach you.</span></li>
      </ul>
      <p class="small muted">The partner programme is opening city by city. Create an account and say hello in your
        profile bio with your café's name, and an admin will reach out.</p></div>'''), title=None, large=False,
             buttons=[("Sounds good", True)])
