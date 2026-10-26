"""App-wide state: who's signed in, counts, and navigation."""
import anvil.js
import anvil.users

me = None          # dict from get_me()
counts = {}        # unread notifications, invites, friend requests
main = None        # the Main form (router)
after_login = None  # route to open once the user signs in


def current_route():
  h = anvil.js.window.location.hash or ''
  return h[1:] if h.startswith('#') else h


def go(route):
  """Navigate to a route like 'walk/123_456'."""
  route = route or 'discover'
  if current_route() == route:
    if main is not None:
      main.route()
  else:
    anvil.js.window.location.hash = route


def logged_in():
  return anvil.users.get_user() is not None


def refresh_me():
  global me
  from . import ui
  res = ui.call('get_me', _quiet=True)
  if res is not ui.FAIL:
    me = res
    if main is not None:
      main.update_header()
  from . import legal
  legal.refresh_soon()  # Privacy & Terms: records the sign-up tick, or reminds people to review
  return me


def set_me(value):
  global me
  me = value
  if main is not None:
    main.update_header()
