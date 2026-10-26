"""Shared server helpers: users, ids, points, notifications, route maths."""
import math
import random
import string
from datetime import datetime, timedelta

import anvil.server
import anvil.users
import anvil.email
import anvil.tz
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

# Anyone signing up with one of these emails becomes an admin automatically.
ADMIN_EMAILS = {"arkulinskis@gmail.com"}

# km/h for each pace
PACES = {'stroll': 3.6, 'steady': 4.5, 'brisk': 5.4}

# Minutes of break planned at each kind of stop
BREAK_MIN = {'start': 0, 'cafe': 25, 'food': 40, 'treat': 15, 'park': 10, 'view': 10,
             'rest': 10, 'water': 5, 'culture': 20, 'finish': 0}
STOP_KINDS = list(BREAK_MIN.keys())
PLACE_KINDS = [k for k in STOP_KINDS if k not in ('start', 'finish')]

# Streets are not straight lines: stretch crow-flies distance a little
STREET_FACTOR = 1.25

LEVELS = [
  (0, "Stroller", "🚶"),
  (100, "Wanderer", "🥾"),
  (300, "Rambler", "🌿"),
  (700, "Pathfinder", "🧭"),
  (1500, "Trailblazer", "🔥"),
  (3000, "City Crosser", "🏙️"),
]

AVATAR_COLORS = ['#17A673', '#FF7A3D', '#3BB3F5', '#FFB703', '#E84A7F', '#7B61FF', '#0FB5AE', '#F25C54']

ENDORSE_SKILLS = ["🧭 Great navigator", "🥐 Snack scout", "⏱️ Pace keeper", "💬 Great company",
                  "🛟 Safety-minded", "📸 Photo taker", "🗺️ Local legend", "🌅 Early riser"]


# ---------------------------------------------------------------- time & ids

def now():
  return datetime.now(anvil.tz.tzutc())


def aware(d):
  if d is None:
    return None
  if isinstance(d, datetime) and d.tzinfo is None:
    return d.replace(tzinfo=anvil.tz.tzutc())
  return d


def rid(row):
  """Row id as a URL-safe token."""
  if row is None:
    return None
  return row.get_id().strip('[]').replace(',', '_')


def by_id(table, token):
  if not token:
    return None
  token = str(token)
  try:
    if '_' in token:
      return table.get_by_id('[' + token.replace('_', ',') + ']')
    return table.get_by_id(token)
  except Exception:
    return None


def short_code(prefix="CC"):
  return prefix + "-" + "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))


# ---------------------------------------------------------------- users

def ensure_defaults(u):
  ch = {}
  if u['points'] is None: ch['points'] = 0
  if u['lifetime_points'] is None: ch['lifetime_points'] = 0
  if not u['display_name']:
    base = (u['email'] or 'Walker').split('@')[0]
    ch['display_name'] = base.replace('.', ' ').replace('_', ' ').title()[:40]
  if not u['avatar_color']: ch['avatar_color'] = random.choice(AVATAR_COLORS)
  if u['discoverable'] is None: ch['discoverable'] = True
  if u['email_notifications'] is None: ch['email_notifications'] = True
  if u['journal_public_default'] is None: ch['journal_public_default'] = False
  if not u['pace']: ch['pace'] = 'steady'
  if u['distance_pref'] is None: ch['distance_pref'] = 15
  if u['interests'] is None: ch['interests'] = []
  for k in ('walks_count', 'km_total', 'people_met'):
    if u[k] is None: ch[k] = 0
  if u['email'] and u['email'].strip().lower() in ADMIN_EMAILS and not u['is_admin']:
    ch['is_admin'] = True
  if ch:
    u.update(**ch)


def current_user(required=True):
  u = anvil.users.get_user()
  if u is None:
    if required:
      raise Exception("Please sign in first.")
    return None
  if u['enabled'] is False:
    raise Exception("This account is suspended. Contact support.")
  ensure_defaults(u)
  return u


def require_admin():
  u = current_user()
  if not u['is_admin']:
    raise Exception("Admins only.")
  return u


def initials(name):
  parts = [p for p in (name or "?").split() if p]
  if not parts:
    return "?"
  if len(parts) == 1:
    return parts[0][:2].upper()
  return (parts[0][0] + parts[-1][0]).upper()


def level_info(lp):
  lp = lp or 0
  idx = 0
  for i, (th, _n, _e) in enumerate(LEVELS):
    if lp >= th:
      idx = i
  cur = LEVELS[idx]
  nxt = LEVELS[idx + 1] if idx + 1 < len(LEVELS) else None
  progress = 1.0 if not nxt else (lp - cur[0]) / float(nxt[0] - cur[0])
  return {'name': cur[1], 'emoji': cur[2], 'index': idx,
          'next_name': nxt[1] if nxt else None, 'next_emoji': nxt[2] if nxt else None,
          'next_at': nxt[0] if nxt else None, 'progress': max(0.0, min(1.0, progress)),
          'points': lp}


def user_card(u):
  """Public-safe summary of a user (never includes email or emergency contact)."""
  if u is None:
    return None
  name = u['display_name'] or 'Walker'
  return {
    'id': rid(u), 'name': name, 'initials': initials(name),
    'headline': u['headline'] or '', 'avatar': u['avatar'],
    'avatar_color': u['avatar_color'] or '#17A673', 'city': u['city'] or '',
    'pace': u['pace'] or 'steady', 'distance_pref': u['distance_pref'] or 15,
    'interests': list(u['interests'] or []), 'snack_style': u['snack_style'] or '',
    'level': level_info(u['lifetime_points']), 'lifetime_points': u['lifetime_points'] or 0,
    'walks_count': u['walks_count'] or 0, 'km_total': round(u['km_total'] or 0, 1),
    'people_met': u['people_met'] or 0, 'verified': bool(u['verified']),
    'is_demo': bool(u['is_demo']),
  }


# ---------------------------------------------------------------- social helpers

def friendship_between(a, b):
  if a is None or b is None:
    return None
  return (app_tables.friendships.get(requester=a, addressee=b) or
          app_tables.friendships.get(requester=b, addressee=a))


def are_friends(a, b):
  f = friendship_between(a, b)
  return bool(f and f['status'] == 'accepted')


def friends_of(u):
  out = []
  for f in app_tables.friendships.search(requester=u, status='accepted'):
    if f['addressee'] is not None:
      out.append(f['addressee'])
  for f in app_tables.friendships.search(addressee=u, status='accepted'):
    if f['requester'] is not None:
      out.append(f['requester'])
  return out


def co_walker_ids(u, exclude_walk=None):
  """Ids of everyone this user has finished a walk with."""
  seen = set()
  for m in app_tables.walk_members.search(user=u, status='going'):
    w = m['walk']
    if w is None or w['status'] != 'completed':
      continue
    if exclude_walk is not None and w == exclude_walk:
      continue
    for m2 in app_tables.walk_members.search(walk=w, status='going'):
      if m2['user'] is not None and m2['user'] != u:
        seen.add(m2['user'].get_id())
  return seen


# ---------------------------------------------------------------- points & notifications

def award(u, amount, reason):
  if u is None or not amount:
    return
  before = level_info(u['lifetime_points'])
  app_tables.points_ledger.add_row(user=u, amount=amount, reason=reason, created=now())
  ch = {'points': (u['points'] or 0) + amount}
  if amount > 0:
    ch['lifetime_points'] = (u['lifetime_points'] or 0) + amount
  u.update(**ch)
  after = level_info(u['lifetime_points'])
  if after['index'] > before['index']:
    notify(u, 'level', f"{after['emoji']} Level up! You're now a {after['name']}.", link='perks')


def notify(user, kind, message, link=None, walk=None, from_user=None, email_subject=None):
  if user is None:
    return
  app_tables.notifications.add_row(user=user, kind=kind, message=message, link=link, walk=walk,
                                   from_user=from_user, read=False, created=now())
  if email_subject and user['email'] and user['email_notifications'] is not False and not user['is_demo']:
    try:
      url = anvil.server.get_app_origin() + ("/#" + link if link else "")
      anvil.email.send(
        to=user['email'], from_name="CityCrossers", subject=email_subject,
        html=(f"<div style='font-family:sans-serif;font-size:16px;line-height:1.5'>"
              f"<p>{_esc(message)}</p><p><a href='{url}' style='background:#17A673;color:#fff;"
              f"padding:10px 18px;border-radius:999px;text-decoration:none'>Open CityCrossers</a></p>"
              f"<p style='color:#888;font-size:13px'>You can turn these emails off in your profile.</p></div>"))
    except Exception as e:
      print("Email failed:", e)


def _esc(s):
  return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------- geo

def haversine(lat1, lng1, lat2, lng2):
  r = 6371.0
  p1, p2 = math.radians(lat1), math.radians(lat2)
  dp = math.radians(lat2 - lat1)
  dl = math.radians(lng2 - lng1)
  a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
  return 2 * r * math.asin(math.sqrt(a))


def route_stats(points, pace):
  """points: list of dicts with lat, lng, kind. Returns (km, minutes, breaks, break_minutes)."""
  km = 0.0
  for a, b in zip(points, points[1:]):
    km += haversine(a['lat'], a['lng'], b['lat'], b['lng'])
  km *= STREET_FACTOR
  speed = PACES.get(pace, 4.5)
  brk = [BREAK_MIN.get(p.get('kind'), 0) for p in points]
  walking = km / speed * 60
  return round(km, 1), int(round(walking + sum(brk))), len([b for b in brk if b]), sum(brk)


def membership(walk, user):
  if walk is None or user is None:
    return None
  return app_tables.walk_members.get(walk=walk, user=user)


def going_count(walk):
  return len(app_tables.walk_members.search(walk=walk, status='going'))


# ---------------------------------------------------------------- matching

def match_score(u, walk=None, other=None):
  """A friendly 'compatibility' percentage, Tinder style."""
  score = 40
  my_pace = u['pace'] or 'steady'
  order = ['stroll', 'steady', 'brisk']
  if walk is not None:
    their_pace = walk['pace'] or 'steady'
    km = walk['distance_km'] or 0
    host = walk['host']
  else:
    their_pace = other['pace'] or 'steady'
    km = other['distance_pref'] or 15
    host = other
  try:
    gap = abs(order.index(my_pace) - order.index(their_pace))
  except ValueError:
    gap = 1
  score += {0: 25, 1: 12}.get(gap, 0)
  diff = abs((u['distance_pref'] or 15) - km)
  score += 18 if diff <= 3 else (10 if diff <= 8 else 3)
  mine = set(u['interests'] or [])
  theirs = set((host['interests'] if host is not None else None) or [])
  if walk is not None:
    theirs |= set(walk['tags'] or [])
  score += min(14, 5 * len(mine & theirs))
  if host is not None and are_friends(u, host):
    score += 8
  return max(35, min(99, score))
