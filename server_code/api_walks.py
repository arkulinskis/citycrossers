"""Walks: create, edit, join, invite, stops, chat, complete."""
from datetime import timedelta

import anvil.server
import anvil.email
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

from .common import (current_user, rid, by_id, now, aware, user_card, notify, award, membership,
                     going_count, are_friends, friends_of, route_stats, co_walker_ids, match_score,
                     PACES, STOP_KINDS)
from .serial import walk_summary, stop_dict, planned_stops, active_discounts
from . import seed

ACTIVE = ('planning', 'confirmed')


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


def _invite_users(w, inviter, user_ids):
  n = 0
  for uid in user_ids or []:
    target = by_id(app_tables.users, uid)
    if target is None or target == inviter:
      continue
    m = membership(w, target)
    if m and m['status'] in ('going', 'invited', 'requested', 'waitlist'):
      continue
    _set_member(w, target, 'invited', invited_by=inviter)
    notify(target, 'invite', f"{inviter['display_name']} invited you on “{w['title']}”. Snacks included.",
           link='walk/' + rid(w), walk=w, from_user=inviter,
           email_subject=f"{inviter['display_name']} invited you on a long walk 🥾")
    n += 1
  return n


# ---------------------------------------------------------------- create / edit

@anvil.server.callable(require_user=True)
def create_walk(data):
  u = current_user()
  _require_pledge(u)
  fields, stops = _clean_walk_data(data)
  w = app_tables.walks.add_row(host=u, status='planning', created=now(), updated=now(), is_demo=False, **fields)
  _save_stops(w, stops, u)
  _recompute(w)
  _set_member(w, u, 'going', role='host')
  award(u, 10, f"Planned “{w['title']}”")
  _invite_users(w, u, data.get('invite_ids'))
  return rid(w)


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
  if not _can_view(w, u):
    raise Exception("This walk is for the host's friends only.")
  is_host = w['host'] == u
  my = membership(w, u)
  my_status = my['status'] if my else None
  members = list(app_tables.walk_members.search(walk=w))
  groups = {'going': [], 'requested': [], 'invited': [], 'waitlist': []}
  for m in members:
    if m['user'] is None or m['status'] not in groups:
      continue
    card = user_card(m['user'])
    card['role'] = m['role'] or 'walker'
    card['message'] = m['message'] or ''
    groups[m['status']].append(card)
  insider = is_host or my_status == 'going' or u['is_admin']
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
    'friends_with_host': are_friends(u, w['host']) if w['host'] is not None and not is_host else False,
    'my_reviews': [rid(r['place']) for r in app_tables.reviews.search(user=u, walk=w) if r['place'] is not None],
  })
  return summary


@anvil.server.callable(require_user=True)
def my_walks():
  u = current_user()
  cutoff = now() - timedelta(hours=18)
  res = {'upcoming': [], 'hosting': [], 'invites': [], 'pending': [], 'past': [], 'requests_to_review': 0}
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
        res['upcoming'].append(walk_summary(w, u))
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


@anvil.server.callable(require_user=True)
def leave_walk(walk_id):
  u = current_user()
  w = _get_walk(walk_id)
  if w['host'] == u:
    raise Exception("Hosts can't leave their own walk. Cancel it instead, or hand it over.")
  m = membership(w, u)
  if m is None:
    return True
  was_going = m['status'] == 'going'
  m.update(status='left', updated=now())
  if was_going:
    notify(w['host'], 'left', f"{u['display_name']} can't make “{w['title']}” any more.", link='walk/' + rid(w),
           walk=w, from_user=u)
    _promote_waitlist(w)
  return True


@anvil.server.callable(require_user=True)
def invite_to_walk(walk_id, user_ids):
  u = current_user()
  w = _get_walk(walk_id)
  m = membership(w, u)
  if w['host'] != u and not (m and m['status'] == 'going'):
    raise Exception("Only people going on this walk can invite others.")
  return _invite_users(w, u, user_ids)


@anvil.server.callable(require_user=True)
def invite_by_email(walk_id, email):
  u = current_user()
  w = _get_walk(walk_id)
  email = (email or '').strip().lower()
  if '@' not in email or '.' not in email.split('@')[-1]:
    raise Exception("That doesn't look like an email address.")
  existing = app_tables.users.get(email=email)
  if existing is not None:
    _invite_users(w, u, [rid(existing)])
    return "They're already on CityCrossers, so we sent an in-app invite."
  url = anvil.server.get_app_origin() + "/#walk/" + rid(w)
  start = aware(w['start'])
  when = start.strftime('%A %d %B, %H:%M UTC') if start else 'soon'
  try:
    anvil.email.send(
      to=email, from_name="CityCrossers", subject=f"{u['display_name']} invited you on a long walk 🥐",
      html=(f"<div style='font-family:sans-serif;font-size:16px;line-height:1.55;color:#1E2A28'>"
            f"<h2 style='margin:0 0 8px'>{_e(w['title'])}</h2>"
            f"<p><b>{_e(u['display_name'])}</b> is planning a long walk on <b>{when}</b>, "
            f"about {w['distance_km'] or '?'} km with snack stops along the way, and wants you to come.</p>"
            f"<p><a href='{url}' style='background:#17A673;color:#fff;padding:12px 20px;border-radius:999px;"
            f"text-decoration:none;font-weight:bold'>See the route &amp; join</a></p>"
            f"<p style='color:#777;font-size:13px'>CityCrossers is a walking club for long city walks with breaks "
            f"and food stops. You got this because a friend typed your address.</p></div>"))
  except Exception as e:
    print("invite email failed", e)
    raise Exception("Couldn't send the email right now. Share the link instead: " + url)
  return "Invite sent! We'll let you know when they join."


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
def complete_walk(walk_id):
  u = current_user()
  w = _get_walk(walk_id)
  _require_host(w, u)
  if w['status'] not in ACTIVE:
    raise Exception("This walk is already wrapped up.")
  if w['start'] and aware(w['start']) > now():
    raise Exception("You can mark the walk complete once it has started.")
  km = w['distance_km'] or 0
  going = [m['user'] for m in app_tables.walk_members.search(walk=w, status='going') if m['user'] is not None]
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
  return {
    'deck': discover_walks(u),
    'upcoming': (mine['hosting'] + mine['upcoming'])[:6],
    'invites': mine['invites'],
    'suggestions': suggestions(u, 8),
    'counts': pending_counts(u),
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
