"""Admin tools: deals, places, reports, users, perks, demo data."""
from datetime import date

import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

from .common import require_admin, rid, by_id, now, user_card, notify, PLACE_KINDS
from .serial import discount_dict, place_dict
from . import seed


@anvil.server.callable(require_user=True)
def admin_overview():
  require_admin()
  deals = [discount_dict(d) for d in app_tables.discounts.search(tables.order_by('created', ascending=False))]
  places = sorted([place_dict(p, with_deals=False) for p in app_tables.places.search()], key=lambda d: d['name'].lower())
  reports = []
  for r in app_tables.reports.search(tables.order_by('created', ascending=False)):
    reports.append({'id': rid(r), 'reason': r['reason'], 'details': r['details'] or '', 'status': r['status'],
                    'created': r['created'], 'reporter': user_card(r['reporter']),
                    'reported_user': user_card(r['reported_user']) if r['reported_user'] is not None else None,
                    'walk': {'id': rid(r['walk']), 'title': r['walk']['title']} if r['walk'] is not None else None})
  users = []
  for u in app_tables.users.search(tables.order_by('signed_up', ascending=False))[:200]:
    c = user_card(u)
    c.update({'email': u['email'] or '(demo walker)', 'is_admin': bool(u['is_admin']),
              'enabled': u['enabled'] is not False, 'signed_up': u['signed_up']})
    users.append(c)
  perks = [{'id': rid(p), 'name': p['name'], 'emoji': p['emoji'], 'description': p['description'], 'cost': p['cost'],
            'active': bool(p['active'])} for p in app_tables.perks.search(tables.order_by('sort'))]
  stats = {
    'users': len([u for u in app_tables.users.search() if not u['is_demo']]),
    'walks': len(app_tables.walks.search()),
    'completed': len(app_tables.walks.search(status='completed')),
    'places': len(places), 'reviews': len(app_tables.reviews.search()),
    'open_reports': len([r for r in reports if r['status'] == 'open']),
    'active_deals': len([d for d in deals if d['active']]),
    'demo_rows': len(app_tables.users.search(is_demo=True)),
  }
  return {'deals': deals, 'places': places, 'reports': reports, 'users': users, 'perks': perks, 'stats': stats,
          'kinds': PLACE_KINDS}


@anvil.server.callable(require_user=True)
def admin_save_deal(data):
  admin = require_admin()
  place = by_id(app_tables.places, data.get('place_id'))
  if place is None:
    raise Exception("Pick the place this deal is for.")
  title = (data.get('title') or '').strip()
  if len(title) < 3:
    raise Exception("Give the deal a short headline, e.g. “15% off pastries”.")
  try:
    pct = int(data.get('percent')) if data.get('percent') not in (None, '') else None
  except (TypeError, ValueError):
    pct = None
  if pct is not None and not (1 <= pct <= 100):
    raise Exception("Percent should be between 1 and 100.")
  fields = dict(place=place, title=title[:80], description=(data.get('description') or '').strip()[:500],
                percent=pct, code=(data.get('code') or '').strip().upper()[:24], valid_until=data.get('valid_until'),
                active=bool(data.get('active', True)))
  d = by_id(app_tables.discounts, data.get('id')) if data.get('id') else None
  if d is None:
    d = app_tables.discounts.add_row(created_by=admin, created=now(), **fields)
    # Let people who reviewed this place know
    told = set()
    for r in app_tables.reviews.search(place=place):
      if r['user'] is not None and r['user'].get_id() not in told and r['would_return']:
        told.add(r['user'].get_id())
        notify(r['user'], 'deal', f"🏷️ New deal at {place['name']}: {title}", link='map')
  else:
    d.update(**fields)
  return rid(d)


@anvil.server.callable(require_user=True)
def admin_toggle_deal(deal_id):
  require_admin()
  d = by_id(app_tables.discounts, deal_id)
  if d is not None:
    d['active'] = not d['active']
  return True


@anvil.server.callable(require_user=True)
def admin_delete_deal(deal_id):
  require_admin()
  d = by_id(app_tables.discounts, deal_id)
  if d is not None:
    d.delete()
  return True


@anvil.server.callable(require_user=True)
def admin_place(place_id, action):
  require_admin()
  p = by_id(app_tables.places, place_id)
  if p is None:
    return True
  if action == 'verify':
    p['verified'] = not p['verified']
  elif action == 'delete':
    for d in app_tables.discounts.search(place=p):
      d.delete()
    for s in app_tables.stops.search(place=p):
      s['place'] = None
    for r in app_tables.reviews.search(place=p):
      r.delete()
    p.delete()
  return True


@anvil.server.callable(require_user=True)
def admin_resolve_report(report_id):
  require_admin()
  r = by_id(app_tables.reports, report_id)
  if r is not None:
    r['status'] = 'resolved' if r['status'] == 'open' else 'open'
  return True


@anvil.server.callable(require_user=True)
def admin_user(user_id, flag):
  admin = require_admin()
  u = by_id(app_tables.users, user_id)
  if u is None:
    raise Exception("User not found.")
  if flag == 'verified':
    u['verified'] = not u['verified']
    if u['verified']:
      notify(u, 'verified', "✅ Your profile is now verified. Walkers will see the badge.", link='me')
  elif flag == 'admin':
    if u == admin:
      raise Exception("You can't remove your own admin role.")
    u['is_admin'] = not u['is_admin']
  elif flag == 'enabled':
    if u == admin:
      raise Exception("You can't suspend yourself.")
    u['enabled'] = u['enabled'] is False
  return True


@anvil.server.callable(require_user=True)
def admin_save_perk(data):
  require_admin()
  name = (data.get('name') or '').strip()
  if len(name) < 3:
    raise Exception("Name the perk.")
  fields = dict(name=name[:60], emoji=(data.get('emoji') or '🎁')[:4], description=(data.get('description') or '')[:300],
                cost=max(0, int(data.get('cost') or 0)), active=bool(data.get('active', True)))
  p = by_id(app_tables.perks, data.get('id')) if data.get('id') else None
  if p is None:
    app_tables.perks.add_row(sort=len(app_tables.perks.search()) + 1, **fields)
  else:
    p.update(**fields)
  return True


@anvil.server.callable(require_user=True)
def admin_seed_demo():
  require_admin()
  return seed.seed_demo(force=True)


@anvil.server.callable(require_user=True)
def admin_clear_demo():
  require_admin()
  return seed.clear_demo()
