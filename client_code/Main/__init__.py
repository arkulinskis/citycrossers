from ._anvil_designer import MainTemplate
from anvil import *
import anvil.js
import anvil.users
import anvil.server

from .. import ui, state, legal
from ..Landing import Landing
from ..Discover import Discover
from ..MapPage import MapPage
from ..WalkEditor import WalkEditor
from ..WalkDetail import WalkDetail
from ..MyWalks import MyWalks
from ..People import People
from ..Profile import Profile
from ..ProfileEdit import ProfileEdit
from ..Journey import Journey
from ..Perks import Perks
from ..Admin import Admin
from ..Safety import Safety
from ..Notifications import Notifications


class Main(MainTemplate):
  """App shell + hash router. Routes look like #walk/123_456."""

  def __init__(self, **properties):
    self.init_components(**properties)
    state.main = self
    self.page = None
    self.node = anvil.js.get_dom_node(self)
    self.shell = self.node.querySelector('.cc-shell')
    self.menu = self.node.querySelector('.cc-me')
    self.node.querySelector('.js-me-btn').addEventListener('click', self._toggle_menu)
    self.node.querySelector('.js-logout').addEventListener('click', self._logout)
    anvil.js.window.document.addEventListener('click', self._outside_click)
    anvil.js.window.addEventListener('hashchange', self._on_hash)

    self.timer = Timer(interval=0)
    self.timer.add_event_handler('tick', self._poll)
    self.add_component(self.timer, slot='hidden')

    if state.logged_in():
      state.refresh_me()
      self._start_polling()
    self.route()

  # ------------------------------------------------------------ header
  def _toggle_menu(self, e):
    e.stopPropagation()
    self.menu.classList.toggle('open')

  def _outside_click(self, e):
    if not self.menu.contains(e.target):
      self.menu.classList.remove('open')

  def update_header(self):
    me = state.me
    if not me:
      return
    def q(sel):
      return self.node.querySelector(sel)
    q('.js-points').textContent = str(me.get('points', 0))
    q('.js-avatar').innerHTML = ui.avatar(me, 40)
    q('.js-name').textContent = me.get('name') or 'You'
    lvl = me.get('level') or {}
    q('.js-level').textContent = f"{lvl.get('emoji', '')} {lvl.get('name', '')} · {me.get('lifetime_points', 0)} lifetime pts"
    admin = q('.js-admin')
    if me.get('is_admin'):
      admin.classList.remove('hidden')
    else:
      admin.classList.add('hidden')
    self.update_counts(state.counts)

  def update_counts(self, counts):
    state.counts = counts or {}
    badge = self.node.querySelector('.js-notif')
    n = state.counts.get('notifications', 0)
    badge.textContent = str(n if n < 100 else '99+')
    if n:
      badge.classList.remove('hidden')
    else:
      badge.classList.add('hidden')
    if 'points' in state.counts and state.me:
      state.me['points'] = state.counts['points']
      self.node.querySelector('.js-points').textContent = str(state.counts['points'])

  def _start_polling(self):
    self._poll()
    self.timer.interval = 60

  def _poll(self, **e):
    if not state.logged_in():
      self.timer.interval = 0
      return
    res = ui.call('poll_counts', _quiet=True)
    if res is not ui.FAIL and res:
      self.update_counts(res)

  # ------------------------------------------------------------ auth
  def on_login(self):
    state.refresh_me()
    self._start_polling()
    target = state.after_login or 'discover'
    state.after_login = None
    state.go(target)

  def _logout(self, e=None):
    anvil.users.logout()
    state.me = None
    legal.signed_out()
    state.counts = {}
    self.timer.interval = 0
    self.menu.classList.remove('open')
    ui.toast("See you on the next walk 👋")
    state.go('landing')

  # ------------------------------------------------------------ routing
  def _on_hash(self, e=None):
    self.route()

  def _set_nav(self, head):
    links = self.node.querySelectorAll('.cc-nav a')
    for i in range(links.length):
      a = links.item(i)
      if a.getAttribute('data-nav') == head:
        a.classList.add('active')
      else:
        a.classList.remove('active')

  def set_page(self, page, nav=None, landing=False):
    if self.page is not None:
      self.page.remove_from_parent()
    self.page = page
    if landing:
      self.shell.classList.add('landing-mode')
    else:
      self.shell.classList.remove('landing-mode')
    self.add_component(page, slot='content')
    self._set_nav(nav)
    self.menu.classList.remove('open')
    anvil.js.window.scrollTo(0, 0)

  def route(self):
    r = state.current_route()
    parts = [p for p in r.split('/') if p != '']
    head = parts[0] if parts else 'discover'
    arg = parts[1] if len(parts) > 1 else None
    logged_in = state.logged_in()

    if not logged_in:
      if head == 'safety':
        return self.set_page(Safety(public=True), landing=True)
      if head not in ('landing', 'discover'):
        state.after_login = r
      return self.set_page(Landing(), landing=True)

    if state.me is None:
      state.refresh_me()

    if head == 'landing':
      return self.set_page(Landing(), landing=True)
    if head == 'discover':
      page = Discover()
    elif head == 'map':
      page = MapPage()
    elif head == 'plan':
      start_place = parts[2] if arg == 'from' and len(parts) > 2 else None
      page = WalkEditor(start_place=start_place)
    elif head == 'edit' and arg:
      page = WalkEditor(walk_id=arg)
    elif head == 'walk' and arg:
      page = WalkDetail(walk_id=arg)
    elif head == 'walks':
      page = MyWalks(tab=arg)
    elif head == 'people':
      page = People()
    elif head == 'u' and arg:
      page = Profile(user_id=arg)
    elif head == 'me' and arg == 'edit':
      page = ProfileEdit()
    elif head == 'me':
      page = Profile(user_id=None)
    elif head == 'welcome':
      page = ProfileEdit(welcome=True)
    elif head == 'journey':
      page = Journey()
    elif head == 'perks':
      page = Perks()
    elif head == 'admin':
      page = Admin()
    elif head == 'safety':
      page = Safety()
    elif head == 'notifications':
      page = Notifications()
    else:
      page = Discover()
      head = 'discover'
    self.set_page(page, nav=head)
