"""Shareable walk links: https://citycrossers.com/w/<walk id>.

WhatsApp, iMessage, Facebook, Meetup and search engines don't run the app's JavaScript, so this small server page
gives them the walk itself as a link card ("Plateau Long Walk · Sun 7 Dec · 15 km · 3 food stops · 4 spots left"),
a schema.org Event, and sends real browsers straight on to /#walk/<id> (the public walk page for visitors, the
full walk page for members). Friends-only or missing walks get the generic CityCrossers card only.

The SEO kit's seo_routes.py (robots.txt, sitemap, /about) is a kit file: leave it alone, routes live here.
"""
import html
import json
from datetime import timedelta

import anvil
import anvil.server
from anvil.tables import app_tables

from .api_public import public_summary
from .common import by_id, rid, fmt_local, local_start

SITE_TITLE = "CityCrossers: a walking club for long city walks"
SITE_DESC = ("The walking club for people who would rather stroll 20 km than sprint 5: join group walks, plan routes "
             "with café stops, meet new people and earn points and perks.")


def _origin():
  return anvil.server.get_app_origin().rstrip('/')


def _km(v):
  v = v or 0
  return ('%.1f' % v).rstrip('0').rstrip('.') + ' km'


def card_text(s, w):
  """(title, description) for the link card of a public walk summary s."""
  bits = []
  when = fmt_local(w)
  if when:
    _t, label = local_start(w)
    bits.append(when if label != 'UTC' else when.split(',')[0])  # no stored time zone: the date only
  bits.append(_km(s['distance_km']))
  n = s['food_stops']
  bits.append('%d food stop%s' % (n, '' if n == 1 else 's'))
  if s['status'] == 'cancelled':
    bits.append('cancelled')
  elif s['is_past'] or s['status'] == 'completed':
    bits.append('this walk has happened')
  else:
    left = s['spots_left']
    bits.append('%d spot%s left' % (left, '' if left == 1 else 's') if left else 'waitlist open')
  host = (s.get('host') or {}).get('name')
  desc = ' · '.join(bits) + ('. Hosted by %s on CityCrossers.' % host if host else '.')
  return s['title'], desc


def event_ld(s, w, url, image):
  """schema.org Event for a public walk (startDate in UTC; the first stop as the place)."""
  start = s['start']
  stops = s.get('stops') or []
  first = stops[0] if stops else None
  ld = {
    '@context': 'https://schema.org', '@type': 'Event', 'name': s['title'], 'url': url, 'image': image,
    'description': s['description'][:500] or card_text(s, w)[1],
    'eventAttendanceMode': 'https://schema.org/OfflineEventAttendanceMode',
    'eventStatus': 'https://schema.org/EventCancelled' if s['status'] == 'cancelled' else 'https://schema.org/EventScheduled',
    'isAccessibleForFree': True,
    'maximumAttendeeCapacity': s['max_walkers'], 'remainingAttendeeCapacity': s['spots_left'],
    'organizer': {'@type': 'Person', 'name': (s.get('host') or {}).get('name') or 'A CityCrossers host'},
  }
  if start is not None:
    ld['startDate'] = start.strftime('%Y-%m-%dT%H:%M:%SZ')
    ld['endDate'] = (start + timedelta(minutes=s['duration_min'] or 0)).strftime('%Y-%m-%dT%H:%M:%SZ')
  if first:
    ld['location'] = {'@type': 'Place', 'name': first['name'], 'address': s['city'] or first['name'],
                      'geo': {'@type': 'GeoCoordinates', 'latitude': first['lat'], 'longitude': first['lng']}}
  return ld


def render(walk_id):
  """The whole HTML page for /w/<walk_id> (also called by the server tests)."""
  o = _origin()
  w = by_id(app_tables.walks, walk_id)
  s = public_summary(w)
  image = o + '/_/theme/og-image.png'
  safe_id = ''.join(ch for ch in str(walk_id or '') if ch.isalnum() or ch in '_-')[:40]
  target = '/#walk/' + (rid(w) if w is not None else safe_id)
  if s is not None:
    title, desc = card_text(s, w)
    url = o + '/w/' + s['id']
    ld = json.dumps(event_ld(s, w, url, image), ensure_ascii=False).replace('</', '<\\/')
    robots = 'index, follow, max-image-preview:large'
    page_title = '%s · CityCrossers' % title
  else:
    title, desc, url, ld = SITE_TITLE, SITE_DESC, o + '/', ''
    robots = 'noindex, follow'
    page_title = SITE_TITLE
  e = lambda x: html.escape(x or '', quote=True)  # noqa: E731
  head = [
    '<!doctype html><html lang="en"><head><meta charset="utf-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1">',
    '<title>%s</title>' % e(page_title),
    '<meta name="description" content="%s">' % e(desc),
    '<meta name="robots" content="%s">' % robots,
    '<link rel="canonical" href="%s">' % e(url),
    '<meta property="og:type" content="%s">' % ('event' if s else 'website'),
    '<meta property="og:site_name" content="CityCrossers">',
    '<meta property="og:title" content="%s">' % e(title),
    '<meta property="og:description" content="%s">' % e(desc),
    '<meta property="og:url" content="%s">' % e(url),
    '<meta property="og:image" content="%s">' % e(image),
    '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">',
    '<meta name="twitter:card" content="summary_large_image">',
    '<meta name="twitter:title" content="%s">' % e(title),
    '<meta name="twitter:description" content="%s">' % e(desc),
    '<meta name="twitter:image" content="%s">' % e(image),
    '<meta name="theme-color" content="#17A673">',
    '<link rel="icon" href="/_/theme/logo.svg">',
  ]
  if ld:
    head.append('<script type="application/ld+json">%s</script>' % ld)
  head.append('<meta http-equiv="refresh" content="0; url=%s">' % e(target))
  head.append('<script>location.replace(%s);</script>' % json.dumps(target).replace('</', '<\\/'))
  body = ('</head><body style="font-family:system-ui,sans-serif;background:#FFFBF2;color:#1D2B27;padding:40px 20px;'
          'text-align:center"><p style="font-size:40px;margin:0">🥾</p><h1 style="font-size:22px">%s</h1><p>%s</p>'
          '<p><a href="%s" style="background:#0E8A5D;color:#fff;padding:12px 20px;border-radius:999px;'
          'text-decoration:none;font-weight:700">Open the walk</a></p></body></html>') % (e(title), e(desc), e(target))
  return ''.join(head) + body


def _page(walk_id):
  return anvil.server.HttpResponse(200, anvil.BlobMedia('text/html; charset=utf-8', render(walk_id).encode('utf-8')),
                                   headers={'Cache-Control': 'public, max-age=300'})


ROUTE = getattr(anvil.server, 'route', None)
if ROUTE:  # root routes (Python 3.10+ server runtimes and the local App Server)
  @ROUTE('/w/:walk_id')
  def walk_page(walk_id='', **params):
    return _page(walk_id)
