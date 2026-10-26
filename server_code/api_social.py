"""People: friends, profiles, endorsements, reports, notifications."""
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

from .common import (current_user, rid, by_id, now, aware, user_card, notify, award, are_friends,
                     friendship_between, friends_of, co_walker_ids, match_score, ENDORSE_SKILLS)
from .serial import walk_summary


def pending_counts(u):
  return {
    'friend_requests': len(app_tables.friendships.search(addressee=u, status='pending')),
    'invites': len([m for m in app_tables.walk_members.search(user=u, status='invited')
                    if m['walk'] is not None and m['walk']['status'] in ('planning', 'confirmed')]),
    'notifications': len(app_tables.notifications.search(user=u, read=False)),
  }


def suggestions(u, limit=8):
  friend_ids = set(f.get_id() for f in friends_of(u))
  pending = set()
  for f in app_tables.friendships.search(requester=u):
    if f['addressee'] is not None: pending.add(f['addressee'].get_id())
  for f in app_tables.friendships.search(addressee=u):
    if f['requester'] is not None: pending.add(f['requester'].get_id())
  out = []
  for other in app_tables.users.search(discoverable=True):
    if other == u or other.get_id() in friend_ids or other.get_id() in pending or other['enabled'] is False:
      continue
    if not other['display_name']:
      continue
    c = user_card(other)
    c['match'] = match_score(u, other=other)
    c['shared'] = sorted(set(u['interests'] or []) & set(other['interests'] or []))
    c['top_endorsement'] = _top_endorsement(other)
    out.append(c)
  out.sort(key=lambda c: -c['match'])
  return out[:limit]


def _top_endorsement(user):
  counts = {}
  for e in app_tables.endorsements.search(to_user=user):
    counts[e['skill']] = counts.get(e['skill'], 0) + 1
  if not counts:
    return None
  skill = max(counts, key=lambda k: counts[k])
  return {'skill': skill, 'count': counts[skill]}


def _relationship(u, other):
  if u == other:
    return 'self'
  f = friendship_between(u, other)
  if f is None:
    return 'none'
  if f['status'] == 'accepted':
    return 'friends'
  return 'pending_out' if f['requester'] == u else 'pending_in'


@anvil.server.callable(require_user=True)
def people_page():
  u = current_user()
  friends = []
  for f in friends_of(u):
    c = user_card(f)
    c['top_endorsement'] = _top_endorsement(f)
    friends.append(c)
  friends.sort(key=lambda c: c['name'].lower())
  incoming = [dict(user_card(f['requester']), request_id=rid(f), created=f['created'])
              for f in app_tables.friendships.search(addressee=u, status='pending') if f['requester'] is not None]
  outgoing = [user_card(f['addressee']) for f in app_tables.friendships.search(requester=u, status='pending')
              if f['addressee'] is not None]
  return {'friends': friends, 'incoming': incoming, 'outgoing': outgoing, 'suggestions': suggestions(u, 12)}


@anvil.server.callable(require_user=True)
def search_people(text):
  u = current_user()
  text = (text or '').strip()
  if len(text) < 2:
    return []
  friend_ids = set(f.get_id() for f in friends_of(u))
  seen, out = set(), []
  for col in ('display_name', 'city', 'headline'):
    for other in app_tables.users.search(**{col: q.ilike('%' + text + '%')}):
      if other == u or other.get_id() in seen or other['enabled'] is False:
        continue
      if not other['discoverable'] and other.get_id() not in friend_ids:
        continue
      seen.add(other.get_id())
      c = user_card(other)
      c['relationship'] = _relationship(u, other)
      c['match'] = match_score(u, other=other)
      out.append(c)
      if len(out) >= 24:
        return out
  return out


@anvil.server.callable(require_user=True)
def send_friend_request(user_id):
  u = current_user()
  other = by_id(app_tables.users, user_id)
  if other is None or other == u:
    raise Exception("Can't connect with that walker.")
  f = friendship_between(u, other)
  if f is not None:
    if f['status'] == 'accepted':
      return 'friends'
    if f['addressee'] == u:  # they already asked us, so accept
      f.update(status='accepted', responded=now())
      notify(other, 'friend', f"{u['display_name']} accepted your connection. Time to plan a walk!",
             link='u/' + rid(u), from_user=u)
      return 'friends'
    return 'pending_out'
  app_tables.friendships.add_row(requester=u, addressee=other, status='pending', created=now())
  notify(other, 'friend_request', f"{u['display_name']} wants to connect and walk together.",
         link='people', from_user=u, email_subject=f"{u['display_name']} wants to walk with you 👋")
  return 'pending_out'


@anvil.server.callable(require_user=True)
def respond_friend_request(user_id, accept):
  u = current_user()
  other = by_id(app_tables.users, user_id)
  f = app_tables.friendships.get(requester=other, addressee=u, status='pending') if other is not None else None
  if f is None:
    raise Exception("That request isn't open any more.")
  if accept:
    f.update(status='accepted', responded=now())
    notify(other, 'friend', f"{u['display_name']} accepted your connection. Time to plan a walk!",
           link='u/' + rid(u), from_user=u)
    return 'friends'
  f.delete()
  return 'none'


@anvil.server.callable(require_user=True)
def remove_friend(user_id):
  u = current_user()
  other = by_id(app_tables.users, user_id)
  f = friendship_between(u, other)
  if f is not None:
    f.delete()
  return 'none'


@anvil.server.callable(require_user=True)
def my_friends():
  u = current_user()
  return sorted([user_card(f) for f in friends_of(u)], key=lambda c: c['name'].lower())


# ---------------------------------------------------------------- profiles

def badges_for(user):
  reviews = len(app_tables.reviews.search(user=user))
  entries = len(app_tables.journal.search(user=user))
  hosted = len(app_tables.walks.search(host=user, status='completed'))
  longest = 0
  for m in app_tables.walk_members.search(user=user, status='going'):
    w = m['walk']
    if w is not None and w['status'] == 'completed':
      longest = max(longest, w['distance_km'] or 0)
  km = user['km_total'] or 0
  defs = [
    ("👣", "First steps", "Finish your first walk", (user['walks_count'] or 0) >= 1),
    ("🏃", "Half-marathoner", "One walk of 21 km or more", longest >= 21),
    ("💯", "Century", "100 km walked in total", km >= 100),
    ("🦋", "Social butterfly", "Walk with 10 different people", (user['people_met'] or 0) >= 10),
    ("🍽️", "Critic", "Review 5 places", reviews >= 5),
    ("🎪", "Host with the most", "Host 3 completed walks", hosted >= 3),
    ("📔", "Storyteller", "Write 5 journal entries", entries >= 5),
    ("🛟", "Safety first", "Take the safety pledge", bool(user['safety_pledge'])),
  ]
  return [{'emoji': e, 'name': n, 'how': h, 'earned': bool(ok)} for e, n, h, ok in defs]


@anvil.server.callable(require_user=True)
def get_profile(user_id):
  u = current_user()
  other = by_id(app_tables.users, user_id) if user_id else u
  if other is None or (other['enabled'] is False and not u['is_admin']):
    raise Exception("We couldn't find that walker.")
  rel = _relationship(u, other)
  walked_together = 0
  if rel != 'self':
    walked_together = 1 if other.get_id() in co_walker_ids(u) else 0
  card = user_card(other)
  endorsements = {}
  for e in app_tables.endorsements.search(to_user=other):
    d = endorsements.setdefault(e['skill'], {'skill': e['skill'], 'count': 0, 'mine': False})
    d['count'] += 1
    if e['from_user'] == u:
      d['mine'] = True
  for s in ENDORSE_SKILLS:
    endorsements.setdefault(s, {'skill': s, 'count': 0, 'mine': False})
  public_reviews = []
  show_private = rel == 'self'
  for r in app_tables.reviews.search(tables.order_by('created', ascending=False), user=other):
    if not r['is_public'] and not show_private:
      continue
    p = r['place']
    public_reviews.append({'id': rid(r), 'rating': r['rating'], 'title': r['title'] or '', 'body': r['body'] or '',
                           'future_note': r['future_note'] if show_private else '',
                           'is_public': bool(r['is_public']),
                           'would_return': bool(r['would_return']), 'created': r['created'],
                           'place': {'id': rid(p), 'name': p['name'], 'kind': p['kind']} if p else None})
  journal = []
  for j in app_tables.journal.search(tables.order_by('entry_date', ascending=False), user=other):
    if not j['is_public'] and not show_private:
      continue
    journal.append({'id': rid(j), 'title': j['title'] or '', 'body': j['body'] or '', 'mood': j['mood'] or '🙂',
                    'entry_date': j['entry_date'], 'km': j['km'], 'photo': j['photo'], 'is_public': bool(j['is_public'])})
  hosting = []
  for w in app_tables.walks.search(tables.order_by('start', ascending=True), host=other,
                                   status=q.any_of('planning', 'confirmed'), start=q.greater_than(now())):
    if w['visibility'] == 'public' or rel in ('self', 'friends'):
      hosting.append(walk_summary(w, u))
  friends = friends_of(other)
  my_friend_ids = set(f.get_id() for f in friends_of(u))
  mutual = [user_card(f) for f in friends if f.get_id() in my_friend_ids][:8]
  card.update({
    'bio': other['bio'] or '', 'languages': other['languages'] or '',
    'relationship': rel, 'walked_together': walked_together, 'friends_count': len(friends),
    'mutual': mutual, 'match': match_score(u, other=other) if rel != 'self' else None,
    'endorsements': sorted(endorsements.values(), key=lambda d: -d['count']),
    'can_endorse': rel == 'friends' or walked_together > 0,
    'badges': badges_for(other), 'reviews': public_reviews[:30], 'journal': journal[:20],
    'hosting': hosting[:6], 'member_since': other['signed_up'],
  })
  return card


@anvil.server.callable(require_user=True)
def endorse(user_id, skill):
  u = current_user()
  other = by_id(app_tables.users, user_id)
  if other is None or other == u:
    raise Exception("You can't endorse yourself (nice try).")
  if skill not in ENDORSE_SKILLS:
    raise Exception("Unknown skill.")
  if not (are_friends(u, other) or other.get_id() in co_walker_ids(u)):
    raise Exception("Connect or walk together first, then you can endorse.")
  e = app_tables.endorsements.get(from_user=u, to_user=other, skill=skill)
  if e is not None:
    e.delete()
    return False
  app_tables.endorsements.add_row(from_user=u, to_user=other, skill=skill, created=now())
  award(other, 3, f"Endorsed as {skill}")
  notify(other, 'endorse', f"{u['display_name']} endorsed you as {skill} (+3 pts)", link='u/' + rid(other),
         from_user=u)
  return True


@anvil.server.callable(require_user=True)
def report(user_id=None, walk_id=None, reason='', details=''):
  u = current_user()
  other = by_id(app_tables.users, user_id) if user_id else None
  w = by_id(app_tables.walks, walk_id) if walk_id else None
  if other is None and w is None:
    raise Exception("Nothing to report.")
  app_tables.reports.add_row(reporter=u, reported_user=other, walk=w, reason=(reason or 'Other')[:80],
                             details=(details or '')[:2000], status='open', created=now())
  for admin in app_tables.users.search(is_admin=True):
    notify(admin, 'report', f"🚩 New safety report: {reason}", link='admin', from_user=u,
           email_subject="CityCrossers safety report")
  return True


# ---------------------------------------------------------------- notifications

@anvil.server.callable(require_user=True)
def get_notifications():
  u = current_user()
  out = []
  for n in app_tables.notifications.search(tables.order_by('created', ascending=False), user=u)[:60]:
    out.append({'id': rid(n), 'kind': n['kind'], 'message': n['message'], 'link': n['link'],
                'read': bool(n['read']), 'created': n['created'],
                'from_user': user_card(n['from_user']) if n['from_user'] is not None else None})
  return out


@anvil.server.callable(require_user=True)
def mark_notifications_read():
  u = current_user()
  for n in app_tables.notifications.search(user=u, read=False):
    n['read'] = True
  return True


@anvil.server.callable(require_user=True)
def poll_counts():
  u = current_user()
  u['last_seen'] = now()
  c = pending_counts(u)
  c['points'] = u['points'] or 0
  return c
