"""Public walks for visitors without an account: the public walk page (#walk/<id> signed out = Pages/WalkPublic),
the link previews at /w/<id> (walk_pages.py) and the landing page's "Open walks this week".

No sign-in is needed here, so these return only what a stranger may see on a PUBLIC walk: the summary, the route
and stops, how many are going and a slim host card (first name, level, walk count). Never the meeting spot, the
crew, the chat, emails or emergency contacts, and nothing at all about friends-only walks.
"""
from datetime import timedelta

import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

from .common import by_id, rid, now, aware, going_count, level_info, initials, col, edition_of, BREAK_MIN

FOOD = ('cafe', 'food', 'treat')


def slim_host(u):
  """A host as strangers see them: first name, initials, colour, photo, level, walks, verified. No id, no email."""
  if u is None:
    return None
  name = (u['display_name'] or 'Walker').strip() or 'Walker'
  return {'name': name.split()[0], 'initials': initials(name), 'avatar_color': u['avatar_color'] or '#17A673',
          'avatar': u['avatar'], 'level': level_info(u['lifetime_points']), 'walks_count': u['walks_count'] or 0,
          'verified': bool(u['verified'])}


def _stops(w):
  return sorted([s for s in app_tables.stops.search(walk=w) if (s['status'] or 'planned') == 'planned'],
                key=lambda s: s['position'] or 0)


def public_summary(w, with_stops=True):
  """The public view of a public walk (None for anything else)."""
  if w is None or w['visibility'] != 'public':
    return None
  start = aware(w['start'])
  going = going_count(w)
  maxw = w['max_walkers'] or 8
  stops = _stops(w)
  res = {
    'id': rid(w), 'title': w['title'] or 'Untitled walk', 'description': w['description'] or '',
    'vibe': w['vibe'] or 'urban', 'start': start, 'pace': w['pace'] or 'steady',
    'distance_km': w['distance_km'] or 0, 'duration_min': w['duration_min'] or 0,
    'max_walkers': maxw, 'going': going, 'spots_left': max(0, maxw - going),
    'status': w['status'] or 'planning', 'approval_required': bool(w['approval_required']),
    'tags': list(w['tags'] or []), 'city': w['city'] or '',
    'food_stops': len([s for s in stops if s['kind'] in FOOD]),
    'is_past': bool(start and start < now()), 'edition': edition_of(w),
    'tz_name': col(w, 'tz_name'), 'tz_offset': col(w, 'tz_offset'),
    'host': slim_host(w['host']),
  }
  if with_stops:
    res['stops'] = [{'name': s['name'] or 'Stop', 'kind': s['kind'] or 'rest', 'lat': s['lat'], 'lng': s['lng'],
                     'break_min': BREAK_MIN.get(s['kind'], 0)} for s in stops]
  return res


@anvil.server.callable
def public_walk(walk_id):
  """A public walk for anyone with its link, signed in or not. None when it doesn't exist or isn't public."""
  return public_summary(by_id(app_tables.walks, walk_id))


@anvil.server.callable
def public_walks(limit=3):
  """Up to `limit` (max 6) public walks starting in the next 7 days with spots left, soonest first. Demo walks are
  left out, so the landing page's strip only ever shows real walks (and hides itself when there are none)."""
  try:
    limit = max(1, min(6, int(limit or 3)))
  except (TypeError, ValueError):
    limit = 3
  t = now()
  out = []
  for w in app_tables.walks.search(tables.order_by('start', ascending=True), visibility='public',
                                   status=q.any_of('planning', 'confirmed'),
                                   start=q.between(t, t + timedelta(days=7))):
    if w['is_demo'] or w['host'] is None:
      continue
    s = public_summary(w, with_stops=False)
    if s and s['spots_left'] > 0:
      out.append(s)
    if len(out) >= limit:
      break
  return out
