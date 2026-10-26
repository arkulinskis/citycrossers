"""Turn rows into plain dicts for the client."""
from datetime import date

import anvil.tables.query as q
from anvil.tables import app_tables

from .common import (rid, user_card, aware, now, membership, going_count, match_score, BREAK_MIN)


def active_discounts(place):
  today = date.today()
  out = []
  if place is None:
    return out
  for d in app_tables.discounts.search(place=place, active=True):
    if d['valid_until'] and d['valid_until'] < today:
      continue
    out.append(discount_dict(d, include_place=False))
  return out


def discount_dict(d, include_place=True):
  res = {'id': rid(d), 'title': d['title'] or '', 'description': d['description'] or '',
         'percent': d['percent'], 'code': d['code'] or '', 'valid_until': d['valid_until'],
         'active': bool(d['active'])}
  if include_place:
    p = d['place']
    res['place'] = {'id': rid(p), 'name': p['name'], 'kind': p['kind'], 'lat': p['lat'], 'lng': p['lng']} if p else None
  return res


def place_dict(p, with_deals=True):
  res = {'id': rid(p), 'name': p['name'] or 'Unnamed spot', 'kind': p['kind'] or 'rest',
         'lat': p['lat'], 'lng': p['lng'], 'description': p['description'] or '',
         'address': p['address'] or '', 'avg_rating': round(p['avg_rating'] or 0, 1),
         'review_count': p['review_count'] or 0, 'verified': bool(p['verified'])}
  if with_deals:
    res['deals'] = active_discounts(p)
  return res


def stop_dict(s, viewer=None):
  votes = list(s['votes'] or [])
  vid = viewer.get_id() if viewer is not None else None
  p = s['place']
  return {'id': rid(s), 'name': s['name'] or 'Stop', 'kind': s['kind'] or 'rest',
          'lat': s['lat'], 'lng': s['lng'], 'position': s['position'] or 0,
          'note': s['note'] or '', 'status': s['status'] or 'planned',
          'place_id': rid(p) if p else None,
          'deals': active_discounts(p) if p else [],
          'rating': round(p['avg_rating'] or 0, 1) if p else 0,
          'break_min': BREAK_MIN.get(s['kind'], 0),
          'votes': len(votes), 'voted': vid in votes,
          'proposed_by': user_card(s['proposed_by']) if s['proposed_by'] else None}


def planned_stops(walk):
  return sorted([s for s in app_tables.stops.search(walk=walk) if (s['status'] or 'planned') == 'planned'],
                key=lambda s: s['position'] or 0)


def walk_summary(w, viewer=None, with_score=False):
  going = going_count(w)
  maxw = w['max_walkers'] or 8
  stops = planned_stops(w)
  my = membership(w, viewer) if viewer is not None else None
  res = {
    'id': rid(w), 'title': w['title'] or 'Untitled walk', 'description': w['description'] or '',
    'vibe': w['vibe'] or 'urban', 'start': aware(w['start']), 'pace': w['pace'] or 'steady',
    'distance_km': w['distance_km'] or 0, 'duration_min': w['duration_min'] or 0,
    'max_walkers': maxw, 'going': going, 'spots_left': max(0, maxw - going),
    'visibility': w['visibility'] or 'friends', 'status': w['status'] or 'planning',
    'approval_required': bool(w['approval_required']), 'tags': list(w['tags'] or []),
    'city': w['city'] or '', 'lat': w['lat'], 'lng': w['lng'],
    'host': user_card(w['host']),
    'stops': [{'name': s['name'], 'kind': s['kind']} for s in stops],
    'food_stops': len([s for s in stops if s['kind'] in ('cafe', 'food', 'treat')]),
    'my_status': my['status'] if my else None,
    'is_host': viewer is not None and w['host'] is not None and w['host'] == viewer,
    'is_past': bool(w['start'] and aware(w['start']) < now()),
  }
  if with_score and viewer is not None:
    res['match'] = match_score(viewer, walk=w)
  return res
