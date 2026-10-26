"""My profile, journey (journal + reviews), places and perks."""
from datetime import date, timedelta

import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

from .common import (current_user, rid, by_id, now, aware, user_card, award, notify, level_info,
                     short_code, PLACE_KINDS, PACES)
from .serial import place_dict, active_discounts, discount_dict, walk_summary

PROFILE_FIELDS = ['display_name', 'headline', 'bio', 'city', 'pace', 'distance_pref', 'snack_style',
                  'interests', 'languages', 'emergency_contact', 'discoverable', 'journal_public_default',
                  'email_notifications']


def _completeness(u):
  checks = [bool(u['display_name']), bool(u['headline']), bool(u['bio']), bool(u['city']),
            u['avatar'] is not None, len(u['interests'] or []) >= 3, bool(u['emergency_contact']),
            bool(u['snack_style'])]
  return int(round(100.0 * sum(checks) / len(checks))), checks


def me_dict(u):
  d = user_card(u)
  pct, checks = _completeness(u)
  d.update({
    'email': u['email'], 'bio': u['bio'] or '', 'languages': u['languages'] or '',
    'emergency_contact': u['emergency_contact'] or '', 'points': u['points'] or 0,
    'is_admin': bool(u['is_admin']), 'discoverable': u['discoverable'] is not False,
    'journal_public_default': bool(u['journal_public_default']),
    'email_notifications': u['email_notifications'] is not False,
    'safety_pledge': u['safety_pledge'], 'completeness': pct,
    'missing': [name for name, ok in zip(['name', 'headline', 'bio', 'city', 'photo', '3+ interests',
                                         'emergency contact', 'snack style'], checks) if not ok],
    'is_new': not u['headline'] and not u['bio'],
  })
  return d


@anvil.server.callable(require_user=True)
def get_me():
  return me_dict(current_user())


@anvil.server.callable(require_user=True)
def update_me(data):
  u = current_user()
  ch = {}
  for k in PROFILE_FIELDS:
    if k not in data:
      continue
    v = data[k]
    if k in ('discoverable', 'journal_public_default', 'email_notifications'):
      v = bool(v)
    elif k == 'distance_pref':
      try:
        v = max(3, min(60, int(v or 15)))
      except (TypeError, ValueError):
        v = 15
    elif k == 'interests':
      v = [str(x)[:30] for x in (v or [])][:12]
    elif k == 'pace':
      v = v if v in PACES else 'steady'
    else:
      v = (v or '').strip()
      limit = 1500 if k == 'bio' else (120 if k == 'headline' else 80)
      v = v[:limit]
    ch[k] = v
  if 'display_name' in ch and len(ch['display_name']) < 2:
    raise Exception("Your name needs at least 2 characters.")
  u.update(**ch)
  msg = None
  pct, _ = _completeness(u)
  if pct == 100 and not u['profile_bonus']:
    u['profile_bonus'] = True
    award(u, 25, "Completed your profile")
    msg = "Profile complete! +25 pts"
  return {'me': me_dict(u), 'message': msg}


@anvil.server.callable(require_user=True)
def set_avatar(media):
  u = current_user()
  if media is not None:
    if media.content_type and not media.content_type.startswith('image/'):
      raise Exception("Please upload an image.")
    if len(media.get_bytes()) > 5 * 1024 * 1024:
      raise Exception("That photo is over 5 MB. Try a smaller one.")
  u['avatar'] = media
  return me_dict(u)


@anvil.server.callable(require_user=True)
def accept_safety_pledge():
  u = current_user()
  if not u['safety_pledge']:
    u['safety_pledge'] = now()
    award(u, 10, "Took the CityCrossers safety pledge")
  return me_dict(u)


# ---------------------------------------------------------------- places

@anvil.server.callable(require_user=True)
def add_place(data):
  u = current_user()
  name = (data.get('name') or '').strip()
  if len(name) < 2:
    raise Exception("Give the place a name.")
  kind = data.get('kind') if data.get('kind') in PLACE_KINDS else 'rest'
  lat, lng = float(data['lat']), float(data['lng'])
  p = app_tables.places.add_row(name=name[:80], kind=kind, lat=lat, lng=lng,
                                description=(data.get('description') or '').strip()[:500],
                                address=(data.get('address') or '').strip()[:120], city=(u['city'] or ''),
                                created_by=u, created=now(), avg_rating=0, review_count=0,
                                verified=bool(u['is_admin']), is_demo=False)
  # Only reward the first 5 places per day to keep things honest
  today = len([x for x in app_tables.places.search(created_by=u, created=q.greater_than(now() - timedelta(days=1)))])
  if today <= 5:
    award(u, 3, f"Put “{p['name']}” on the map")
  return place_dict(p)


@anvil.server.callable(require_user=True)
def get_place(place_id):
  u = current_user()
  p = by_id(app_tables.places, place_id)
  if p is None:
    raise Exception("That place has gone off the map.")
  reviews = []
  for r in app_tables.reviews.search(tables.order_by('created', ascending=False), place=p, is_public=True):
    reviews.append({'id': rid(r), 'rating': r['rating'], 'title': r['title'] or '', 'body': r['body'] or '',
                    'would_return': bool(r['would_return']), 'created': r['created'], 'user': user_card(r['user'])})
  d = place_dict(p)
  mine = app_tables.reviews.get(user=u, place=p)
  d.update({'reviews': reviews[:20], 'reviewed': mine is not None,
            'added_by': user_card(p['created_by']) if p['created_by'] is not None else None})
  return d


def _refresh_rating(p):
  rs = [r['rating'] for r in app_tables.reviews.search(place=p) if r['rating']]
  p.update(avg_rating=(sum(rs) / float(len(rs))) if rs else 0, review_count=len(rs))


# ---------------------------------------------------------------- reviews

@anvil.server.callable(require_user=True)
def save_review(data):
  """data: place_id or stop_id or new place (name/kind/lat/lng), rating, title, body, future_note,
  is_public, would_return, walk_id, review_id (to edit)."""
  u = current_user()
  rating = int(data.get('rating') or 0)
  if rating < 1 or rating > 5:
    raise Exception("Pick a rating from 1 to 5 stars.")
  review = by_id(app_tables.reviews, data.get('review_id')) if data.get('review_id') else None
  if review is not None and review['user'] != u:
    raise Exception("That's not your review.")
  place = review['place'] if review is not None else None
  if place is None and data.get('place_id'):
    place = by_id(app_tables.places, data['place_id'])
  if place is None and data.get('stop_id'):
    s = by_id(app_tables.stops, data['stop_id'])
    if s is not None:
      place = s['place']
      if place is None:
        place = app_tables.places.add_row(name=s['name'], kind=s['kind'] if s['kind'] in PLACE_KINDS else 'rest',
                                          lat=s['lat'], lng=s['lng'], description='', address='', city='',
                                          created_by=u, created=now(), avg_rating=0, review_count=0,
                                          verified=False, is_demo=False)
        s['place'] = place
  if place is None:
    raise Exception("Choose a place to review.")
  walk = by_id(app_tables.walks, data.get('walk_id')) if data.get('walk_id') else None
  fields = dict(rating=rating, title=(data.get('title') or '').strip()[:100],
                body=(data.get('body') or '').strip()[:3000],
                future_note=(data.get('future_note') or '').strip()[:1000],
                is_public=bool(data.get('is_public')), would_return=bool(data.get('would_return')))
  first_here = app_tables.reviews.get(user=u, place=place) is None
  if review is None:
    review = app_tables.reviews.add_row(user=u, place=place, walk=walk, visited_on=date.today(),
                                        created=now(), **fields)
  else:
    review.update(**fields)
  _refresh_rating(place)
  msg = "Saved to your journey."
  if first_here:
    pts = 8 + (4 if fields['is_public'] else 0)
    award(u, pts, f"Reviewed {place['name']}")
    msg = f"Saved! +{pts} pts"
  return {'id': rid(review), 'message': msg}


@anvil.server.callable(require_user=True)
def delete_review(review_id):
  u = current_user()
  r = by_id(app_tables.reviews, review_id)
  if r is None or r['user'] != u:
    raise Exception("Can't delete that.")
  p = r['place']
  r.delete()
  if p is not None:
    _refresh_rating(p)
  return True


@anvil.server.callable(require_user=True)
def set_review_public(review_id, is_public):
  u = current_user()
  r = by_id(app_tables.reviews, review_id)
  if r is None or r['user'] != u:
    raise Exception("Can't change that.")
  r['is_public'] = bool(is_public)
  return True


# ---------------------------------------------------------------- journal

@anvil.server.callable(require_user=True)
def save_entry(data):
  u = current_user()
  title = (data.get('title') or '').strip()
  body = (data.get('body') or '').strip()
  if not title and not body:
    raise Exception("Write at least a title or a few words.")
  entry = by_id(app_tables.journal, data.get('id')) if data.get('id') else None
  if entry is not None and entry['user'] != u:
    raise Exception("That's not your entry.")
  km = data.get('km')
  try:
    km = round(float(km), 1) if km not in (None, '') else None
  except (TypeError, ValueError):
    km = None
  fields = dict(title=title[:120] or 'Untitled moment', body=body[:6000], mood=(data.get('mood') or '🙂')[:4],
                is_public=bool(data.get('is_public')), entry_date=data.get('entry_date') or date.today(), km=km)
  if 'photo' in data:
    fields['photo'] = data.get('photo')
  walk = by_id(app_tables.walks, data.get('walk_id')) if data.get('walk_id') else None
  msg = "Entry saved."
  if entry is None:
    since = now() - timedelta(hours=20)
    recent = len(app_tables.journal.search(user=u, created=q.greater_than(since)))
    entry = app_tables.journal.add_row(user=u, walk=walk, created=now(), **fields)
    if recent == 0:
      award(u, 5, "Wrote in your journey")
      msg = "Entry saved! +5 pts"
  else:
    entry.update(**fields)
  return {'id': rid(entry), 'message': msg}


@anvil.server.callable(require_user=True)
def delete_entry(entry_id):
  u = current_user()
  e = by_id(app_tables.journal, entry_id)
  if e is None or e['user'] != u:
    raise Exception("Can't delete that.")
  e.delete()
  return True


@anvil.server.callable(require_user=True)
def journey():
  u = current_user()
  items = []
  for j in app_tables.journal.search(user=u):
    items.append({'type': 'entry', 'id': rid(j), 'title': j['title'], 'body': j['body'] or '', 'mood': j['mood'] or '🙂',
                  'date': j['entry_date'], 'km': j['km'], 'photo': j['photo'], 'is_public': bool(j['is_public']),
                  'walk_id': rid(j['walk']) if j['walk'] is not None else None,
                  'walk_title': j['walk']['title'] if j['walk'] is not None else None})
  for r in app_tables.reviews.search(user=u):
    p = r['place']
    items.append({'type': 'review', 'id': rid(r), 'rating': r['rating'], 'title': r['title'] or '',
                  'body': r['body'] or '', 'future_note': r['future_note'] or '', 'is_public': bool(r['is_public']),
                  'would_return': bool(r['would_return']), 'date': r['visited_on'] or (r['created'].date() if r['created'] else None),
                  'place': {'id': rid(p), 'name': p['name'], 'kind': p['kind']} if p else None})
  for m in app_tables.walk_members.search(user=u, status='going'):
    w = m['walk']
    if w is not None and w['status'] == 'completed':
      start = aware(w['start'])
      items.append({'type': 'walk', 'id': rid(w), 'title': w['title'], 'km': w['distance_km'],
                    'vibe': w['vibe'], 'date': start.date() if start else None,
                    'host': user_card(w['host'])})
  items.sort(key=lambda i: i['date'] or date(2000, 1, 1), reverse=True)
  stats = {'km': round(u['km_total'] or 0, 1), 'walks': u['walks_count'] or 0, 'people': u['people_met'] or 0,
           'reviews': len([i for i in items if i['type'] == 'review']),
           'entries': len([i for i in items if i['type'] == 'entry'])}
  return {'items': items, 'stats': stats, 'public_default': bool(u['journal_public_default'])}


@anvil.server.callable(require_user=True)
def reviewable_places():
  """Places for the 'review a place' picker: my walks' stops first, then everything."""
  current_user()
  return sorted([{'id': rid(p), 'name': p['name'], 'kind': p['kind']} for p in app_tables.places.search()],
                key=lambda d: d['name'].lower())


# ---------------------------------------------------------------- perks

@anvil.server.callable(require_user=True)
def perks_page():
  u = current_user()
  ledger = [{'amount': l['amount'], 'reason': l['reason'], 'created': l['created']}
            for l in app_tables.points_ledger.search(tables.order_by('created', ascending=False), user=u)[:40]]
  perks = [{'id': rid(p), 'name': p['name'], 'emoji': p['emoji'] or '🎁', 'description': p['description'] or '',
            'cost': p['cost'] or 0} for p in app_tables.perks.search(tables.order_by('sort'), active=True)]
  redemptions = [{'code': r['code'], 'created': r['created'],
                  'perk': (r['perk']['emoji'] or '🎁') + ' ' + r['perk']['name'] if r['perk'] is not None else 'Perk'}
                 for r in app_tables.redemptions.search(tables.order_by('created', ascending=False), user=u)]
  deals = []
  today = date.today()
  for d in app_tables.discounts.search(active=True):
    if d['valid_until'] and d['valid_until'] < today:
      continue
    if d['place'] is None:
      continue
    deals.append(discount_dict(d))
  return {'points': u['points'] or 0, 'level': level_info(u['lifetime_points']),
          'ledger': ledger, 'perks': perks, 'redemptions': redemptions, 'deals': deals}


@anvil.server.callable(require_user=True)
@tables.in_transaction
def redeem_perk(perk_id):
  u = current_user()
  p = by_id(app_tables.perks, perk_id)
  if p is None or not p['active']:
    raise Exception("That perk isn't available.")
  cost = p['cost'] or 0
  if (u['points'] or 0) < cost:
    raise Exception(f"You need {cost - (u['points'] or 0)} more points for this one. Go for a walk!")
  code = short_code("PERK")
  app_tables.redemptions.add_row(user=u, perk=p, code=code, created=now())
  app_tables.points_ledger.add_row(user=u, amount=-cost, reason=f"Redeemed {p['name']}", created=now())
  u['points'] = (u['points'] or 0) - cost
  return code
