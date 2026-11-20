"""Add a walk to a calendar: an .ics file (Apple Calendar, Outlook, most phones) or a Google Calendar link.

    calendar.ics_text(walk, url)     RFC 5545 text: UID <id>@citycrossers.com, UTC start/end (Z), escaped text, CRLF
    calendar.download(walk, url)     saves it as "<title>.ics" on the device (cc.download: nothing leaves the browser)
    calendar.google_link(walk, url)  calendar.google.com/calendar/render?action=TEMPLATE... (opened only when pressed)
walk = the walk dict from get_walk (title, start, duration_min, stops_full / stops); url = its /w/<id> address.
Times are written in UTC, so every calendar shows them at the right local time.
"""
import datetime

import anvil.tz


def _utc(d):
    if d.tzinfo is None:
        d = d.replace(tzinfo=anvil.tz.tzlocal())
    return d.astimezone(anvil.tz.tzutc())


def stamp(d):
    """20261207T143000Z"""
    u = _utc(d)
    return '%04d%02d%02dT%02d%02d%02dZ' % (u.year, u.month, u.day, u.hour, u.minute, u.second)


def esc(text):
    """TEXT escaping: backslash, semicolon, comma, newlines."""
    s = str(text or '')
    for a, b in (('\\', '\\\\'), (';', '\\;'), (',', '\\,'), ('\r\n', '\\n'), ('\n', '\\n'), ('\r', '\\n')):
        s = s.replace(a, b)
    return s


def _octets(ch):
    o = ord(ch)
    return 1 if o < 0x80 else (2 if o < 0x800 else (3 if o < 0x10000 else 4))


def fold(line):
    """Lines longer than 75 octets continue on the next line after a space (never inside an emoji)."""
    out, cur, n = [], '', 0
    for ch in line:
        k = _octets(ch)
        low_surrogate = 0xDC00 <= ord(ch) <= 0xDFFF
        if n + k > 75 and cur and not low_surrogate:
            out.append(cur)
            cur, n = ' ', 1
        cur += ch
        n += k
    out.append(cur)
    return '\r\n'.join(out)


def _times(walk):
    start = walk['start']
    end = start + datetime.timedelta(minutes=int(walk.get('duration_min') or 180))
    return start, end


def _stops(walk):
    return walk.get('stops_full') or walk.get('stops') or []


def details(walk, url):
    stops = _stops(walk)
    route = ' → '.join(s.get('name') or 'Stop' for s in stops)
    lines = ['A CityCrossers walk: about %s km with %s food stop%s.' % (
        walk.get('distance_km') or '?', walk.get('food_stops', 0), '' if walk.get('food_stops') == 1 else 's')]
    if route:
        lines.append('Route: ' + route)
    if walk.get('meeting_note'):
        lines.append('Meeting spot: ' + walk['meeting_note'])
    lines.append('Walk page: ' + url)
    return '\n'.join(lines)


def ics_text(walk, url, now=None):
    start, end = _times(walk)
    stops = _stops(walk)
    first = stops[0] if stops else None
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//CityCrossers//Walks//EN', 'CALSCALE:GREGORIAN',
             'METHOD:PUBLISH', 'BEGIN:VEVENT',
             'UID:%s@citycrossers.com' % walk['id'],
             'DTSTAMP:' + stamp(now or datetime.datetime.now(anvil.tz.tzutc())),
             'DTSTART:' + stamp(start), 'DTEND:' + stamp(end),
             'SUMMARY:' + esc(walk.get('title') or 'CityCrossers walk'),
             'LOCATION:' + esc(first.get('name') if first else ''),
             'DESCRIPTION:' + esc(details(walk, url)),
             'URL:' + url]
    if first and first.get('lat') is not None:
        lines.append('GEO:%.6f;%.6f' % (first['lat'], first['lng']))
    lines += ['BEGIN:VALARM', 'ACTION:DISPLAY', 'DESCRIPTION:' + esc('Walk tomorrow: ' + (walk.get('title') or '')),
              'TRIGGER:-PT18H', 'END:VALARM', 'END:VEVENT', 'END:VCALENDAR']
    return '\r\n'.join(fold(x) for x in lines) + '\r\n'


def filename(walk):
    safe = ''.join(ch if ch.isalnum() else '-' for ch in (walk.get('title') or 'walk'))[:40].strip('-') or 'walk'
    return safe.lower() + '.ics'


def download(walk, url):
    from anvil.js import window
    return bool(window.cc.download(ics_text(walk, url), filename(walk), 'text/calendar'))


def google_link(walk, url):
    from anvil.js import window
    start, end = _times(walk)
    stops = _stops(walk)
    params = [('action', 'TEMPLATE'), ('text', walk.get('title') or 'CityCrossers walk'),
              ('dates', stamp(start) + '/' + stamp(end)), ('details', details(walk, url)),
              ('location', stops[0].get('name') if stops else '')]
    return 'https://calendar.google.com/calendar/render?' + '&'.join(
        k + '=' + str(window.encodeURIComponent(v or '')) for k, v in params)
