"""Walks: create, edit, copy (host again), join, invite, confirm spots, stops, chat, roll call + complete."""
import hashlib
import time
from datetime import timedelta

import anvil.server
import anvil.email
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

from .common import (current_user, rid, by_id, now, aware, user_card, notify, award, membership,
                     going_count, are_friends, friends_of, route_stats, co_walker_ids, match_score,
                     col, set_col, clean_tz, fmt_local, show_up, edition_of, PACES, STOP_KINDS)
from .serial import walk_summary, stop_dict, planned_stops, active_discounts
from . import seed

ACTIVE = ('planning', 'confirmed')
CONFIRM_WINDOW = timedelta(hours=48)   # "Still in?" shows to people going this long before the start
EMAIL_INVITES_PER_DAY = 10             # email invites one walker can send in a rolling 24 hours
EMAILS_PER_ADDRESS_PER_DAY = 2         # emails one address can get from anyone in 24 hours
INVITE_SENT = "Invite sent! If they join, you'll see them in the crew."


def _get_walk(walk_id):
  w = by_id(app_tables.walks, walk_id)
  if w is None:
    raise Exception("That walk doesn't exist any more.")
  return w


def _require_host(w, u):
  if w['host'] != u and not u['is_admin']:
    raise Exception("Only the host can do that.")


def _require_pledge(u):
  if not u['safety_pledge']:
    raise Exception("SAFETY_PLEDGE_REQUIRED")


def _can_view(w, u):
  if w['visibility'] == 'public' or w['host'] == u or u['is_admin']:
    return True
  m = membership(w, u)
  if m and m['status'] not in ('passed',):
    return True
  return are_friends(u, w['host'])


def _clean_walk_data(data, partial=False):
  title = (data.get('title') or '').strip()
  if len(title) < 3:
    raise Exception("Give your walk a name (at least 3 characters).")
  start = aware(data.get('start'))
  if start is None:
    raise Exception("Pick a date and time for the walk.")
  if not partial and start < now() - timedelta(minutes=30):
    raise Exception("The walk needs to start in the future.")
  pace = data.get('pace') if data.get('pace') in PACES else 'steady'
  vis = 'public' if data.get('visibility') == 'public' else 'friends'
  try:
    maxw = int(data.get('max_walkers') or 8)
  except (TypeError, ValueError):
    maxw = 8
  maxw = max(2, min(40, maxw))
  if vis == 'public' and maxw < 3:
    raise Exception("Public walks need room for at least 3 walkers (it's safer in a group).")
  stops = data.get('stops') or []
  if len(stops) < 2:
    raise Exception("Add at least a meeting point and a finish line on the map.")
  return {
    'title': title[:80], 'description': (data.get('description') or '').strip()[:2000],
    'start': start, 'pace': pace, 'visibility': vis, 'max_walkers': maxw,
    'vibe': (data.get('vibe') or 'urban')[:20], 'tags': list(data.get('tags') or [])[:8],
    'approval_required': bool(data.get('approval_required', True)),
    'city': (data.get('city') or '').strip()[:60],
    'meeting_note': (data.get('meeting_note') or '').strip()[:300],
  }, stops


def _save_stops(w, stops, u):
  for s in app_tables.stops.search(walk=w, status='planned'):
    s.delete()
  for i, s in enumerate(stops):
    kind = s.get('kind') if s.get('kind') in STOP_KINDS else 'rest'
    place = by_id(app_tables.places, s.get('place_id')) if s.get('place_id') else None
    app_tables.stops.add_row(walk=w, place=place, name=(s.get('name') or 'Stop')[:80], kind=kind,
                             lat=float(s['lat']), lng=float(s['lng']), position=i,
                             note=(s.get('note') or '')[:200], status='planned', proposed_by=u,
                             votes=[], created=now())


def _recompute(w):
  stops = planned_stops(w)
  pts = [{'lat': s['lat'], 'lng': s['lng'], 'kind': s['kind']} for s in stops]
  km, minutes, _b, _bm = route_stats(pts, w['pace'])
  first = stops[0] if stops else None
  w.update(distance_km=km, duration_min=minutes, lat=first['lat'] if first else None,
           lng=first['lng'] if first else None, updated=now())


def _set_member(w, user, status, role='walker', invited_by=None, message=None):
  m = membership(w, user)
  if m is None:
    m = app_tables.walk_members.add_row(walk=w, user=user, status=status, role=role, invited_by=invited_by,
                                        message=message, created=now(), updated=now())
  else:
    ch = {'status': status, 'updated': now()}
    if invited_by is not None: ch['invited_by'] = invited_by
    if message is not None: ch['message'] = message
    m.update(**ch)
  return m


def _promote_waitlist(w):
  while going_count(w) < (w['max_walkers'] or 8):
    waiting = sorted(app_tables.walk_members.search(walk=w, status='waitlist'), key=lambda m: m['created'])
    if not waiting:
      return
    m = waiting[0]
    m.update(status='going', updated=now())
    notify(m['user'], 'walk', f"A spot opened up! You're now going on “{w['title']}”.",
           link='walk/' + rid(w), walk=w, email_subject="You're off the waitlist 🎉")


def _invite_users(w, inviter, user_ids, message=None):
  n = 0
  for uid in user_ids or []:
    target = by_id(app_tables.users, uid)
    if target is None or target == inviter:
      continue
    m = membership(w, target)
    if m and m['status'] in ('going', 'invited', 'requested', 'waitlist'):
      continue
    _set_member(w, target, 'invited', invited_by=inviter)
    notify(target, 'invite', message or f"{inviter['display_name']} invited you on “{w['title']}”. Snacks included.",
           link='walk/' + rid(w), walk=w, from_user=inviter,
           email_subject=f"{inviter['display_name']} invited you on a long walk 🥾")
    n += 1
  return n


def _set_tz(w, data):
  """The host's time zone at the walk's start, sent by their browser (see common.walk_tz)."""
  name, off = clean_tz(data.get('tz_name'), data.get('tz_offset'))
  if off is not None:
    set_col(w, 'tz_name', name)
    set_col(w, 'tz_offset', off)


def _upcoming(w):
  return w['status'] in ACTIVE and not (w['start'] and aware(w['start']) < now())


def walk_url(w):
  """The shareable address of a walk: /w/<id> serves link previews and opens the walk (server_code/walk_pages.py)."""
  return anvil.server.get_app_origin().rstrip('/') + '/w/' + rid(w)


# ---------------------------------------------------------------- email invites (table email_invites)
# One row per email invite: who sent it, which walk, and a fingerprint of the address (never the address). It gives
# the daily limit, stops the same address being emailed twice about a walk, and lets someone who signs up with that
# address find their invite (get_walk). Before the user accepts the new table, a per-session count stands in.

def _email_hash(email):
  return hashlib.sha256(('citycrossers-invite:' + (email or '').strip().lower()).encode('utf-8')).hexdigest()[:40]


def _invite_table():
  try:
    return app_tables.email_invites
  except Exception:
    return None


def _invites_sent_today(u):
  t, since = _invite_table(), now() - timedelta(hours=24)
  if t is not None:
    try:
      return len(t.search(inviter=u, created=q.greater_than(since)))
    except Exception:
      pass
  cut = time.time() - 86400
  return len([x for x in (anvil.server.session.get('cc_email_invites') or []) if x > cut])


def _skip_email(w, h):
  """True when this address already got an invite to this walk, or its daily cap of emails from anyone."""
  t = _invite_table()
  if t is None:
    return False
  try:
    if len(t.search(walk=w, to_hash=h)):
      return True
    return len(t.search(to_hash=h, created=q.greater_than(now() - timedelta(hours=24)))) >= EMAILS_PER_ADDRESS_PER_DAY
  except Exception:
    return False


def _log_invite(u, w, h):
  t = _invite_table()
  try:
    if t is not None:
      t.add_row(inviter=u, walk=w, to_hash=h, created=now())
      return
  except Exception:
    pass
  sent = [x for x in (anvil.server.session.get('cc_email_invites') or []) if x > time.time() - 86400]
  anvil.server.session['cc_email_invites'] = sent + [time.time()]


def _claim_email_invite(w, u):
  """Someone invited by email who then made an account with that address: the invite becomes a normal walk invite
  (so a friends-only walk opens for them, and joining skips the host's approval like any invite)."""
  t = _invite_table()
  if t is None or not u['email'] or not _upcoming(w) or membership(w, u) is not None:
    return False
  try:
    rows = list(t.search(walk=w, to_hash=_email_hash(u['email'])))
  except Exception:
    return False
  if not rows:
    return False
  _set_member(w, u, 'invited', invited_by=rows[0]['inviter'])
  return True


# ---------------------------------------------------------------- create / edit

@anvil.server.callable(require_user=True)
def create_walk(data):
  """data: the editor's fields + stops, invite_ids, tz_name/tz_offset (the host's browser), and for "Host again"
  copy_of (the walk it repeats) + invite_crew (invite the people who went last time; only when I hosted it)."""
  u = current_user()
  _require_pledge(u)
  fields, stops = _clean_walk_data(data)
  w = app_tables.walks.add_row(host=u, status='planning', created=now(), updated=now(), is_demo=False, **fields)
  _set_tz(w, data)
  _save_stops(w, stops, u)
  _recompute(w)
  _set_member(w, u, 'going', role='host')
  award(u, 10, f"Planned “{w['title']}”")
  src = by_id(app_tables.walks, data.get('copy_of')) if data.get('copy_of') else None
  if src is not None and src['host'] == u:
    set_col(w, 'repeat_of', src)  # a weekly series: the walk page shows "edition N"
    if data.get('invite_crew'):
      crew = [rid(m['user']) for m in app_tables.walk_members.search(walk=src, status='going')
              if m['user'] is not None and m['user'] != u]
      _invite_users(w, u, crew, message=f"{u['display_name']} is hosting “{w['title']}” again and saved you a "
                                        f"spot from last time. Coming? 🔁")
  _invite_users(w, u, data.get('invite_ids'))
  return rid(w)


@anvil.server.callable(require_user=True)
def walk_copy(walk_id):
  """A walk as a starting point for a new one (#plan/again/<id>). The host gets everything (title, description,
  route, pace, size, meeting spot, how many went last time) dated the same weekday and time next week; anyone else
  who can see the walk gets the route only, with no meeting spot and nobody to invite."""
  u = current_user()
  w = _get_walk(walk_id)
  if not _can_view(w, u):
    raise Exception("This walk is for the host's friends only.")
  is_host = w['host'] == u
  orig = aware(w['start']) or now()
  weeks = 1
  while orig + timedelta(days=7 * weeks) < now() + timedelta(minutes=30):
    weeks += 1
  crew = 0
  if is_host:
    crew = len([m for m in app_tables.walk_members.search(walk=w, status='going')
                if m['user'] is not None and m['user'] != u])
  return {
    'id': rid(w), 'is_host': is_host, 'title': w['title'] or '', 'description': (w['description'] or '') if is_host else '',
    'orig_start': orig, 'start': orig + timedelta(days=7 * weeks), 'weeks': weeks,
    'pace': w['pace'] or 'steady', 'vibe': w['vibe'] or 'urban', 'tags': list(w['tags'] or []),
    'max_walkers': (w['max_walkers'] or 8) if is_host else 8,
    'visibility': (w['visibility'] or 'friends') if is_host else 'friends',
    'approval_required': bool(w['approval_required']) if is_host else True,
    'city': w['city'] or '', 'meeting_note': (w['meeting_note'] or '') if is_host else '',
    'stops': [{'name': s['name'] or 'Stop', 'kind': s['kind'] or 'rest', 'lat': s['lat'], 'lng': s['lng'],
               'place_id': rid(s['place']) if s['place'] else None, 'note': s['note'] or ''} for s in planned_stops(w)],
    'crew': crew, 'edition_next': edition_of(w) + 1 if is_host else 1,
  }


@anvil.server.callable(require_user=True)
def update_walk(walk_id, data):
  u = current_user()
  w = _get_walk(walk_id)
  _require_host(w, u)
  if w['status'] not in ACTIVE:
    raise Exception("This walk can't be edited any more.")
  fields, stops = _clean_walk_data(data, partial=True)
  if fields['max_walkers'] < going_count(w):
    fields['max_walkers'] = going_count(w)
  w.update(**fields)
  _set_tz(w, data)
  _save_stops(w, stops, u)
  _recompute(w)
  _invite_users(w, u, data.get('invite_ids'))
  for m in app_tables.walk_members.search(walk=w, status='going'):
    if m['user'] != u:
      notify(m['user'], 'walk', f"The plan for “{w['title']}” was updated. Check the new route.",
             link='walk/' + rid(w), walk=w, from_user=u)
  return rid(w)


@anvil.server.callable(require_user=True)
def get_walk_for_edit(walk_id):
  u = current_user()
  w = _get_walk(walk_id)
  _require_host(w, u)
  return {
    'id': rid(w), 'title': w['title'], 'description': w['description'] or '', 'start': aware(w['start']),
    'pace': w['pace'], 'visibility': w['visibility'], 'max_walkers': w['max_walkers'], 'vibe': w['vibe'],
    'tags': list(w['tags'] or []), 'approval_required': bool(w['approval_required']), 'city': w['city'] or '',
    'meeting_note': w['meeting_note'] or '',
    'stops': [stop_dict(s, u) for s in planned_stops(w)],
    'invited_ids': [rid(m['user']) for m in app_tables.walk_members.search(walk=w)
                    if m['user'] is not None and m['status'] in ('invited', 'going')],
  }


# ---------------------------------------------------------------- read

@anvil.server.callable(require_user=True)
def get_walk(walk_id):
  u = current_user()
  w = _get_walk(walk_id)
  _claim_email_invite(w, u)
  if not _can_view(w, u):
    raise Exception("This walk is for the host's friends only.")
  is_host = w['host'] == u
  hostish = is_host or bool(u['is_admin'])
  my = membership(w, u)
  my_status = my['status'] if my else None
  members = list(app_tables.walk_members.search(walk=w))
  groups = {'going': [], 'requested': [], 'invited': [], 'waitlist': []}
  walkers = confirmed = 0
  for m in members:
    if m['user'] is None or m['status'] not in groups:
      continue
    card = user_card(m['user'])
    card['role'] = m['role'] or 'walker'
    card['message'] = m['message'] or ''
    if m['status'] == 'going' and card['role'] != 'host':
      walkers += 1
      if col(m, 'confirmed_at'):
        confirmed += 1
        if hostish:
          card['confirmed'] = True  # ✓ next to their name, for the host
    if hostish and m['status'] in ('requested', 'waitlist'):
      su = show_up(m['user'])
      if su['total'] >= 3:  # "Came to 9 of 10 walks", only once there's a pattern
        card['show_up'] = su
    groups[m['status']].append(card)
  insider = is_host or my_status == 'going' or u['is_admin']
  start = aware(w['start'])
  upcoming = _upcoming(w)
  my_confirmed = bool(my and col(my, 'confirmed_at'))
  if not is_host and not u['is_admin']:
    groups['requested'] = []
    groups['invited'] = [{'id': None}] * len(groups['invited'])  # only a count for non-hosts
  all_stops = list(app_tables.stops.search(walk=w))
  planned = sorted([s for s in all_stops if (s['status'] or 'planned') == 'planned'], key=lambda s: s['position'] or 0)
  proposed = sorted([s for s in all_stops if s['status'] == 'proposed'],
                    key=lambda s: -len(s['votes'] or []))
  messages = []
  if insider:
    for msg in app_tables.messages.search(tables.order_by('created', ascending=True), walk=w):
      messages.append({'id': rid(msg), 'body': msg['body'], 'created': msg['created'],
                       'user': user_card(msg['user']), 'mine': msg['user'] == u})
  summary = walk_summary(w, u, with_score=not is_host)
  summary.update({
    'description': w['description'] or '', 'meeting_note': w['meeting_note'] if insider else '',
    'stops_full': [stop_dict(s, u) for s in planned],
    'proposed': [stop_dict(s, u) for s in proposed],
    'members': groups, 'messages': messages[-80:], 'insider': insider,
    'can_invite': is_host or my_status == 'going',
    'is_host': is_host, 'is_admin': bool(u['is_admin']),
    'my_confirmed': my_confirmed,
    'confirm_needed': (my_status == 'going' and not is_host and upcoming and not my_confirmed
                       and start is not None and start - now() <= CONFIRM_WINDOW),
    'crew_confirmed': {'confirmed': confirmed, 'walkers': walkers} if hostish else None,
    'edition': edition_of(w),
    'friends_with_host': are_friends(u, w['host']) if w['host'] is not None and not is_host else False,
    'my_reviews': [rid(r['place']) for r in app_tables.reviews.search(user=u, walk=w) if r['place'] is not None],
  })
  return summary


@anvil.server.callable(require_user=True)
def my_walks():
  u = current_user()
  cutoff = now() - timedelta(hours=18)
  res: dict = {'upcoming': [], 'hosting': [], 'invites': [], 'pending': [], 'past': [], 'requests_to_review': 0}
  for m in app_tables.walk_members.search(user=u):
    w = m['walk']
    if w is None or w['status'] == 'cancelled':
      continue
    st = m['status']
    start = aware(w['start'])
    upcoming = w['status'] in ACTIVE and start is not None and start >= cutoff
    if w['status'] == 'completed' and st == 'going':
      res['past'].append(walk_summary(w, u))
    elif upcoming:
      if m['role'] == 'host':
        s = walk_summary(w, u)
        s['requests'] = len(app_tables.walk_members.search(walk=w, status='requested'))
        res['requests_to_review'] += s['requests']
        res['hosting'].append(s)
      elif st == 'going':
        s = walk_summary(w, u)
        s['confirmed'] = bool(col(m, 'confirmed_at'))
        res['upcoming'].append(s)
      elif st == 'invited':
        res['invites'].append(walk_summary(w, u))
      elif st in ('requested', 'waitlist'):
        res['pending'].append(walk_summary(w, u))
    elif m['role'] == 'host' and w['status'] in ACTIVE:
      # Started but not marked complete yet
      s = walk_summary(w, u)
      s['needs_completion'] = True
      res['hosting'].append(s)
  for k in ('upcoming', 'hosting', 'invites', 'pending'):
    res[k].sort(key=lambda s: s['start'] or now())
  res['past'].sort(key=lambda s: s['start'] or now(), reverse=True)
  return res


def discover_walks(u, limit=30):
  seen = set()
  for m in app_tables.walk_members.search(user=u):
    if m['walk'] is not None:
      seen.add(m['walk'].get_id())
  friend_ids = set(f.get_id() for f in friends_of(u))
  out = []
  for w in app_tables.walks.search(tables.order_by('start', ascending=True),
                                   status=q.any_of(*ACTIVE), start=q.greater_than(now())):
    if w.get_id() in seen or w['host'] is None or w['host'] == u:
      continue
    if w['visibility'] != 'public' and w['host'].get_id() not in friend_ids:
      continue
    s = walk_summary(w, u, with_score=True)
    s['from_friend'] = w['host'].get_id() in friend_ids
    out.append(s)
  out.sort(key=lambda s: (-(s['match'] + (15 if s['from_friend'] else 0))))
  return out[:limit]


# ---------------------------------------------------------------- membership actions

@anvil.server.callable(require_user=True)
def join_walk(walk_id, message=None):
  u = current_user()
  _require_pledge(u)
  w = _get_walk(walk_id)
  if w['status'] not in ACTIVE or (w['start'] and aware(w['start']) < now()):
    raise Exception("This walk has already started or ended.")
  if w['host'] == u:
    return 'going'
  m = membership(w, u)
  if m and m['status'] == 'going':
    return 'going'
  invited = bool(m and m['status'] == 'invited')
  if w['visibility'] != 'public' and not invited and not are_friends(u, w['host']):
    raise Exception("This walk is friends-only. Ask the host for an invite.")
  if going_count(w) >= (w['max_walkers'] or 8):
    status = 'waitlist'
  elif invited or not w['approval_required']:
    status = 'going'
  else:
    status = 'requested'
  _set_member(w, u, status, message=(message or '')[:280] or None)
  host = w['host']
  if status == 'requested':
    notify(host, 'request', f"{u['display_name']} wants to join “{w['title']}”.", link='walk/' + rid(w),
           walk=w, from_user=u, email_subject="Someone wants to join your walk 👋")
  elif status == 'going':
    notify(host, 'join', f"{u['display_name']} is coming on “{w['title']}” 🎉", link='walk/' + rid(w),
           walk=w, from_user=u)
  return status


@anvil.server.callable(require_user=True)
def pass_walk(walk_id):
  u = current_user()
  w = _get_walk(walk_id)
  if membership(w, u) is None:
    _set_member(w, u, 'passed')
  return True


@anvil.server.callable(require_user=True)
def respond_invite(walk_id, accept):
  u = current_user()
  w = _get_walk(walk_id)
  m = membership(w, u)
  if m is None or m['status'] != 'invited':
    raise Exception("No open invite for this walk.")
  if not accept:
    m.update(status='declined', updated=now())
    return 'declined'
  return join_walk(walk_id)


@anvil.server.callable(require_user=True)
def host_decide(walk_id, user_id, accept):
  u = current_user()
  w = _get_walk(walk_id)
  _require_host(w, u)
  target = by_id(app_tables.users, user_id)
  m = membership(w, target)
  if m is None or m['status'] not in ('requested', 'waitlist'):
    raise Exception("That request isn't open any more.")
  if accept:
    status = 'going' if going_count(w) < (w['max_walkers'] or 8) else 'waitlist'
    m.update(status=status, updated=now())
    notify(target, 'accepted', f"You're in! {u['display_name']} accepted you on “{w['title']}”."
           if status == 'going' else f"“{w['title']}” is full, you're first in line on the waitlist.",
           link='walk/' + rid(w), walk=w, from_user=u, email_subject="You're in! 🥾")
    return status
  m.update(status='declined', updated=now())
  notify(target, 'declined', f"“{w['title']}” couldn't fit you this time. Plenty more walks out there!",
         link='discover', walk=w)
  return 'declined'


def _leave(w, u, why="can't make"):
  m = membership(w, u)
  if m is None:
    return True
  was_going = m['status'] == 'going'
  m.update(status='left', updated=now())
  set_col(m, 'confirmed_at', None)
  if was_going:
    notify(w['host'], 'left', f"{u['display_name']} {why} “{w['title']}” any more.", link='walk/' + rid(w),
           walk=w, from_user=u)
    _promote_waitlist(w)  # the first person waiting gets the spot (and a notification + email)
  return True


@anvil.server.callable(require_user=True)
def leave_walk(walk_id):
  u = current_user()
  w = _get_walk(walk_id)
  if w['host'] == u:
    raise Exception("Hosts can't leave their own walk. Cancel it instead, or hand it over.")
  return _leave(w, u)


@anvil.server.callable(require_user=True)
def confirm_spot(walk_id, coming):
  """The "Still in?" check before a walk. coming=True: I'll be there (the host sees ✓ next to my name).
  coming=False: free my spot now, so the first person on the waitlist gets it."""
  u = current_user()
  w = _get_walk(walk_id)
  if w['host'] == u:
    raise Exception("You're the host, so you're always in.")
  m = membership(w, u)
  if m is None or m['status'] != 'going':
    raise Exception("Only people going on this walk can confirm a spot.")
  if not _upcoming(w):
    raise Exception("This walk has already started or ended.")
  if not coming:
    _leave(w, u, why="answered “still in?”: can't make")
    return 'left'
  set_col(m, 'confirmed_at', now())
  return 'confirmed'


@anvil.server.callable(require_user=True)
def invite_to_walk(walk_id, user_ids):
  u = current_user()
  w = _get_walk(walk_id)
  m = membership(w, u)
  if w['host'] != u and not (m and m['status'] == 'going'):
    raise Exception("Only people going on this walk can invite others.")
  return _invite_users(w, u, user_ids)


@anvil.server.callable(require_user=True)
def invite_by_email(walk_id, email, tz=None):
  """Email someone an invite to a walk. Only the host or someone going may send one, at most EMAIL_INVITES_PER_DAY
  a day; one address gets one email per walk (and EMAILS_PER_ADDRESS_PER_DAY a day from anyone). The answer is
  the same whether or not the address has an account (members get an in-app invite instead), so nobody can use
  it to find out who is on CityCrossers. tz = {'name', 'offset'} from the inviter's browser: the time zone for
  the email's date when the walk was saved before walks stored one."""
  u = current_user()
  w = _get_walk(walk_id)
  m = membership(w, u)
  if w['host'] != u and not (m and m['status'] == 'going'):
    raise Exception("Only people going on this walk can invite others.")
  if not _upcoming(w):
    raise Exception("This walk has already started or ended, so there's nothing to invite people to.")
  email = (email or '').strip().lower()
  if len(email) > 254 or ' ' in email or '@' not in email or '.' not in email.split('@')[-1]:
    raise Exception("That doesn't look like an email address.")
  url = walk_url(w)
  if _invites_sent_today(u) >= EMAIL_INVITES_PER_DAY:
    raise Exception(f"That's {EMAIL_INVITES_PER_DAY} email invites today, the daily limit. Share the walk's link "
                    f"instead: {url}")
  h = _email_hash(email)
  if _skip_email(w, h):
    _log_invite(u, w, h)
    return INVITE_SENT
  existing = app_tables.users.get(email=email)
  if existing is not None:
    _invite_users(w, u, [rid(existing)])
    _log_invite(u, w, h)
    return INVITE_SENT
  fb = (tz.get('name'), tz.get('offset')) if isinstance(tz, dict) else None
  when = fmt_local(w, fallback=fb, long=True) or 'soon'
  food = len([s for s in planned_stops(w) if s['kind'] in ('cafe', 'food', 'treat')])
  try:
    anvil.email.send(
      to=email, from_name="CityCrossers", subject=f"{u['display_name']} invited you on a long walk 🥐",
      html=(f"<div style='font-family:sans-serif;font-size:16px;line-height:1.55;color:#1E2A28'>"
            f"<h2 style='margin:0 0 8px'>{_e(w['title'])}</h2>"
            f"<p><b>{_e(u['display_name'])}</b> is going on a long walk on <b>{_e(when)}</b>, about "
            f"{w['distance_km'] or '?'} km with {food} food stop{'s' if food != 1 else ''} along the way, and wants "
            f"you to come.</p>"
            f"<p><a href='{url}' style='background:#17A673;color:#fff;padding:12px 20px;border-radius:999px;"
            f"text-decoration:none;font-weight:bold'>See the walk &amp; join</a></p>"
            f"<p style='color:#777;font-size:13px'>The link shows the route and stops, no account needed. "
            f"CityCrossers is a walking club for long city walks with breaks and food stops. You got this because "
            f"{_e(u['display_name'])} typed your address; we don't keep it or email you again unless you join.</p></div>"))
  except Exception as e:
    print("invite email failed", e)
    raise Exception("Couldn't send the email right now. Share the walk's link instead: " + url)
  _log_invite(u, w, h)
  return INVITE_SENT


def _e(s):
  return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


@anvil.server.callable(require_user=True)
def set_visibility(walk_id, visibility):
  u = current_user()
  w = _get_walk(walk_id)
  _require_host(w, u)
  vis = 'public' if visibility == 'public' else 'friends'
  ch = {'visibility': vis, 'updated': now()}
  if vis == 'public':
    if (w['max_walkers'] or 0) < 3:
      ch['max_walkers'] = 6
    ch['approval_required'] = True if w['approval_required'] is None else w['approval_required']
  w.update(**ch)
  return vis


# ---------------------------------------------------------------- stops & votes

@anvil.server.callable(require_user=True)
def propose_stop(walk_id, stop):
  u = current_user()
  w = _get_walk(walk_id)
  m = membership(w, u)
  if w['host'] != u and not (m and m['status'] == 'going'):
    raise Exception("Join the walk to suggest stops.")
  kind = stop.get('kind') if stop.get('kind') in STOP_KINDS else 'rest'
  place = by_id(app_tables.places, stop.get('place_id')) if stop.get('place_id') else None
  s = app_tables.stops.add_row(walk=w, place=place, name=(stop.get('name') or 'Suggested stop')[:80], kind=kind,
                               lat=float(stop['lat']), lng=float(stop['lng']), position=999,
                               note=(stop.get('note') or '')[:200], status='proposed', proposed_by=u,
                               votes=[u.get_id()], created=now())
  if w['host'] != u:
    notify(w['host'], 'stop', f"{u['display_name']} suggested a stop at {s['name']} for “{w['title']}”.",
           link='walk/' + rid(w), walk=w, from_user=u)
  return rid(s)


@anvil.server.callable(require_user=True)
def vote_stop(stop_id):
  u = current_user()
  s = by_id(app_tables.stops, stop_id)
  if s is None:
    raise Exception("That stop is gone.")
  w = s['walk']
  m = membership(w, u)
  if w['host'] != u and not (m and m['status'] == 'going'):
    raise Exception("Only walkers on this walk can vote.")
  votes = list(s['votes'] or [])
  if u.get_id() in votes:
    votes.remove(u.get_id())
  else:
    votes.append(u.get_id())
  s['votes'] = votes
  return len(votes)


@anvil.server.callable(require_user=True)
def accept_stop(stop_id):
  u = current_user()
  s = by_id(app_tables.stops, stop_id)
  if s is None:
    raise Exception("That stop is gone.")
  w = s['walk']
  _require_host(w, u)
  planned = planned_stops(w)
  # Insert just before the finish line
  insert_at = max(1, len(planned) - 1) if len(planned) >= 2 else len(planned)
  for i, p in enumerate(planned):
    p['position'] = i if i < insert_at else i + 1
  s.update(status='planned', position=insert_at)
  _recompute(w)
  if s['proposed_by'] is not None and s['proposed_by'] != u:
    award(s['proposed_by'], 5, f"Your stop “{s['name']}” made the route")
    notify(s['proposed_by'], 'stop', f"Your stop {s['name']} was added to “{w['title']}” (+5 pts)",
           link='walk/' + rid(w), walk=w, from_user=u)
  return True


@anvil.server.callable(require_user=True)
def remove_stop(stop_id):
  u = current_user()
  s = by_id(app_tables.stops, stop_id)
  if s is None:
    return True
  w = s['walk']
  if w['host'] != u and s['proposed_by'] != u:
    raise Exception("Only the host or whoever suggested it can remove this stop.")
  if s['status'] == 'planned' and len(planned_stops(w)) <= 2:
    raise Exception("A walk needs at least a start and a finish.")
  s.delete()
  _recompute(w)
  return True


# ---------------------------------------------------------------- chat

@anvil.server.callable(require_user=True)
def post_message(walk_id, body):
  u = current_user()
  w = _get_walk(walk_id)
  m = membership(w, u)
  if w['host'] != u and not (m and m['status'] == 'going') and not u['is_admin']:
    raise Exception("Join the walk to chat with the group.")
  body = (body or '').strip()
  if not body:
    return None
  app_tables.messages.add_row(walk=w, user=u, body=body[:800], created=now())
  return True


# ---------------------------------------------------------------- lifecycle

@anvil.server.callable(require_user=True)
def complete_walk(walk_id, absent_ids=None):
  """The host's roll call: everyone going gets points, km and new faces, except the walkers in absent_ids (user ids
  the host unticked): they become no_show (no points, not counted as met) and get a kind in-app note, no email.
  No absent_ids = everyone came (the old behaviour)."""
  u = current_user()
  w = _get_walk(walk_id)
  _require_host(w, u)
  if w['status'] not in ACTIVE:
    raise Exception("This walk is already wrapped up.")
  if w['start'] and aware(w['start']) > now():
    raise Exception("You can mark the walk complete once it has started.")
  km = w['distance_km'] or 0
  absent = set(str(x) for x in (absent_ids or []) if x)
  going = []
  for m in app_tables.walk_members.search(walk=w, status='going'):
    who = m['user']
    if who is None:
      continue
    if rid(who) in absent and who != w['host']:
      m.update(status='no_show', updated=now())
      notify(who, 'missed', f"The host's roll call for “{w['title']}” says we missed you. Life happens! "
                            f"If that's not right, send the host a message.", link='walk/' + rid(w), walk=w)
    else:
      going.append(who)
  ids = set(x.get_id() for x in going)
  for walker in going:
    prev = co_walker_ids(walker, exclude_walk=w)
    new_faces = len((ids - {walker.get_id()}) - prev)
    pts = 15 + int(round(2 * km))
    award(walker, pts, f"Walked “{w['title']}” ({km} km)")
    if new_faces:
      award(walker, min(50, 5 * new_faces), f"Met {new_faces} new walker{'s' if new_faces != 1 else ''}")
    if walker == w['host']:
      award(walker, 25, "Hosted a walk")
    walker.update(walks_count=(walker['walks_count'] or 0) + 1, km_total=round((walker['km_total'] or 0) + km, 1),
                  people_met=(walker['people_met'] or 0) + new_faces)
    notify(walker, 'complete', f"🏁 “{w['title']}” is in the books! Rate your stops and endorse your crew.",
           link='walk/' + rid(w), walk=w)
  w.update(status='completed', completed_at=now())
  return True


@anvil.server.callable(require_user=True)
def cancel_walk(walk_id):
  u = current_user()
  w = _get_walk(walk_id)
  _require_host(w, u)
  w.update(status='cancelled', updated=now())
  for m in app_tables.walk_members.search(walk=w):
    if m['user'] is not None and m['user'] != u and m['status'] in ('going', 'invited', 'requested', 'waitlist'):
      notify(m['user'], 'cancelled', f"“{w['title']}” was cancelled by the host.", link='discover', walk=w,
             email_subject="A walk you joined was cancelled")
  return True


# ---------------------------------------------------------------- home & map

@anvil.server.callable(require_user=True)
def home_feed():
  u = current_user()
  seed.ensure_seeded()
  from .api_social import suggestions, pending_counts
  mine = my_walks()
  soon = now() + CONFIRM_WINDOW
  return {
    'deck': discover_walks(u),
    'upcoming': (mine['hosting'] + mine['upcoming'])[:6],
    'invites': mine['invites'],
    'suggestions': suggestions(u, 8),
    'counts': pending_counts(u),
    # "Still in?": walks I'm going on (not hosting) that start within 48 hours and I haven't confirmed yet
    'to_confirm': [s for s in mine['upcoming']
                   if not s.get('confirmed') and s['start'] is not None and now() < s['start'] <= soon],
  }


@anvil.server.callable(require_user=True)
def map_data():
  u = current_user()
  seed.ensure_seeded()
  from .serial import place_dict
  places = [place_dict(p) for p in app_tables.places.search()]
  walks = []
  for w in app_tables.walks.search(status=q.any_of(*ACTIVE), start=q.greater_than(now())):
    if w['lat'] is None:
      continue
    if w['visibility'] == 'public' or w['host'] == u or are_friends(u, w['host']):
      walks.append({'id': rid(w), 'title': w['title'], 'lat': w['lat'], 'lng': w['lng'], 'vibe': w['vibe'],
                    'start': aware(w['start']), 'distance_km': w['distance_km'], 'going': going_count(w),
                    'max_walkers': w['max_walkers']})
  return {'places': places, 'walks': walks}
