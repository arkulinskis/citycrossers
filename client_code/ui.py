"""CityCrossers' constants and formatting: stop kinds, paces, vibes, levels, dates, distances and the route maths
(the same numbers the server uses). No HTML here: pages and items are Forms."""
import math
import datetime

import anvil.tz

KINDS = {
    'start': ('🚩', 'Meeting point'), 'cafe': ('☕', 'Coffee stop'), 'food': ('🥐', 'Food stop'),
    'treat': ('🍦', 'Treat stop'), 'park': ('🌳', 'Park'), 'view': ('👀', 'Viewpoint'),
    'rest': ('🪑', 'Rest stop'), 'water': ('🚰', 'Water refill'), 'culture': ('🏛️', 'Culture spot'),
    'finish': ('🏁', 'Finish line'),
}
PLACE_KINDS = ['cafe', 'food', 'treat', 'park', 'view', 'rest', 'water', 'culture']
STOP_KINDS = ['start', 'cafe', 'food', 'treat', 'park', 'view', 'rest', 'water', 'culture', 'finish']
BREAK_MIN = {'start': 0, 'cafe': 25, 'food': 40, 'treat': 15, 'park': 10, 'view': 10,
             'rest': 10, 'water': 5, 'culture': 20, 'finish': 0}
PACES = {'stroll': ('🐢', 'Stroll', '~3.6 km/h', 3.6), 'steady': ('🚶', 'Steady', '~4.5 km/h', 4.5),
         'brisk': ('⚡', 'Brisk', '~5.4 km/h', 5.4)}
VIBES = [
    ('pastry', '🥐', 'Pastry pilgrimage', 'grad-peach'),
    ('sunrise', '🌅', 'Sunrise stride', 'grad-sun'),
    ('parks', '🌳', 'Park hopper', 'grad-mint'),
    ('urban', '🏙️', 'Urban explorer', 'grad-sky'),
    ('river', '🌊', 'Riverside ramble', 'grad-sea'),
    ('food', '🍜', 'Food crawl', 'grad-berry'),
    ('night', '🌙', 'Night walk', 'grad-night'),
    ('history', '🏛️', 'History hunt', 'grad-sand'),
]
VIBE = {v[0]: v for v in VIBES}
INTERESTS = ["Coffee", "Bakeries", "Parks", "Rivers & canals", "Architecture", "History", "Street art", "Markets",
             "Photography", "Birdwatching", "Sunrise", "Night walks", "Dogs", "Picnics", "Podcasts", "Languages"]
WALK_TAGS = ["Beginner friendly", "Dog friendly", "Step-free", "Bakeries", "Coffee", "Parks", "History",
             "Rivers & canals", "Markets", "Photography", "Sunrise", "Night walks", "Picnics", "Quiet chat",
             "Language exchange"]
SNACK_STYLES = ["Pastry first", "Savory all day", "Coffee is a food group", "I pack my own", "Whatever's closest"]
SKILLS = ["🧭 Great navigator", "🥐 Snack scout", "⏱️ Pace keeper", "💬 Great company",
          "🛟 Safety-minded", "📸 Photo taker", "🗺️ Local legend", "🌅 Early riser"]
MOODS = ['🥰', '😄', '🙂', '😌', '🥵', '🥐', '🌅', '🤯', '😴']
LEVELS = [(0, "Stroller", "🚶"), (100, "Wanderer", "🥾"), (300, "Rambler", "🌿"), (700, "Pathfinder", "🧭"),
          (1500, "Trailblazer", "🔥"), (3000, "City Crosser", "🏙️")]
STATUS_PILLS = {
    'going': ('✓ Going', 'green'), 'requested': ('⏳ Requested', 'sun'), 'invited': ('💌 Invited', 'berry'),
    'waitlist': ('🕒 Waitlist', 'sky'), 'declined': ('Declined', ''), 'left': ('Left', ''),
}
STREET_FACTOR = 1.25

# Stop topics: a light conversation card at every stop, so first-timers have something easy to talk about.
# topic_for() picks one per stop from the walk's id, so every device shows the same topic; 🔀 cycles locally.
TOPIC_AT = {'start': 'At the start', 'cafe': 'At the café', 'food': 'Over lunch', 'treat': 'At the treat stop',
            'park': 'In the park', 'view': 'At the viewpoint', 'rest': 'On the bench', 'water': 'At the water refill',
            'culture': 'At the culture stop', 'finish': 'At the finish'}
TOPICS = {
    'start': ["names, and which neighbourhood you walked in from?", "what's the best walk you've ever done?",
              "how long have you lived in this city?", "which part of town do you know least?",
              "what brought you here today?"],
    'cafe': ["what food would you cross the city for?", "what's your go-to order, and why?",
             "best café you found by accident?", "coffee person, tea person, or 'whatever's warm'?",
             "what's a small thing that makes your week better?"],
    'food': ["what's a dish from home you wish you could get here?", "what's the best meal you've had on a trip?",
             "if this city were a dish, what would it be?", "a food you hated as a kid and love now?",
             "who's the best cook you know?"],
    'treat': ["what's your ultimate treat after a long day?", "a flavour everyone should try once?",
              "what's a guilty pleasure that isn't food?", "best thing you've bought for under five dollars?",
              "sweet or salty, and defend it?"],
    'park': ["where do you go when you need some quiet?", "a hobby you'd pick up if you had a free month?",
             "what did you love doing outside as a kid?", "do you have a favourite tree, bench or spot?",
             "if you had a dog, what would you name it?"],
    'view': ["what's one thing you'd show a visitor here?", "a place you'd love to see the view from?",
             "what's changed the most in this city since you arrived?", "where would you live if you could pick any street?",
             "best sunrise or sunset you remember?"],
    'rest': ["what are you reading, watching or listening to?", "what's a skill you're learning right now?",
             "a podcast or song for long walks?", "what's on your list for this year?",
             "what's something you're looking forward to?"],
    'water': ["how far is the longest you've ever walked?", "what keeps you going on a long day?",
              "rain walks: yes or no?", "early bird or night owl?", "what got you into walking?"],
    'culture': ["a fact about this place you'd tell a friend?", "a museum, gig or show you loved?",
                "if you could time-travel to this spot, which year?", "a local legend or story you know?",
                "what's the most interesting job you've heard of?"],
    'finish': ["best moment today?", "which stop would you come back to?", "one thing you learned about someone today?",
               "where should the next walk go?", "how many steps do you think we did?"],
}
DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
FULL_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def esc(s):
    """HTML-escape text for the map engine's popups (the only HTML strings left)."""
    if s is None:
        return ''
    return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            .replace('"', '&quot;').replace("'", '&#39;'))


def kind(k):
    return KINDS.get(k or '', ('📍', 'Stop'))


def emoji(k):
    return kind(k)[0]


def vibe_of(key):
    return VIBE.get(key or '') or VIBE['urban']


def pace_of(key):
    return PACES.get(key or '', PACES['steady'])


def deal_tag(d):
    return (str(d['percent']) + '% OFF') if d.get('percent') else 'DEAL'


def plural(n, one, many=None):
    return "%s %s" % (n, one if n == 1 else (many or one + 's'))


# ------------------------------------------------------------------ dates

def local(d):
    if d is None:
        return None
    try:
        if isinstance(d, datetime.datetime) and d.tzinfo is not None:
            return d.astimezone(anvil.tz.tzlocal())
    except Exception:
        pass
    return d


def now_local():
    return datetime.datetime.now(anvil.tz.tzlocal())


def fmt_time(d):
    d = local(d)
    return "%02d:%02d" % (d.hour, d.minute) if d else ''


def fmt_date(d, year=False):
    if d is None:
        return ''
    d = local(d)
    s = "%s %d %s" % (DAYS[d.weekday()], d.day, MONTHS[d.month - 1])
    if year:
        s += " %d" % d.year
    return s


def fmt_when(d):
    if d is None:
        return 'Date TBC'
    return "%s · %s" % (fmt_date(d), fmt_time(d))


def days_until(d):
    if d is None:
        return None
    d = local(d)
    try:
        return (d.date() - now_local().date()).days
    except Exception:
        return None


def fmt_rel(d):
    n = days_until(d)
    if n is None:
        return ''
    if n == 0:
        return 'Today'
    if n == 1:
        return 'Tomorrow'
    if n == -1:
        return 'Yesterday'
    if 1 < n < 7:
        return 'In %d days' % n
    if n < 0:
        return '%d days ago' % -n
    if n < 14:
        return 'Next week'
    return 'In %d weeks' % (n // 7)


def day_word(d):
    """'Today', 'Tomorrow' or the weekday ('Sunday'), for "Sunday's walk: still in?"."""
    n = days_until(d)
    if n == 0:
        return 'Today'
    if n == 1:
        return 'Tomorrow'
    d = local(d)
    return FULL_DAYS[d.weekday()] if d else 'The'


def ago(d):
    if d is None:
        return ''
    try:
        secs = (now_local() - local(d)).total_seconds()
    except Exception:
        return ''
    if secs < 60:
        return 'just now'
    if secs < 3600:
        return '%dm ago' % int(secs // 60)
    if secs < 86400:
        return '%dh ago' % int(secs // 3600)
    if secs < 86400 * 7:
        return '%dd ago' % int(secs // 86400)
    return fmt_date(d)


def fmt_dur(minutes):
    minutes = int(minutes or 0)
    h, m = minutes // 60, minutes % 60
    if h and m:
        return "%dh %02dm" % (h, m)
    return ("%dh" % h) if h else ("%dm" % m)


def km(v):
    v = v or 0
    return ("%.1f km" % v) if v < 100 else ("%d km" % int(v))


def stars(n):
    n = int(round(n or 0))
    return '★' * n + '☆' * (5 - n)


# ------------------------------------------------------------------ geo (mirrors the server)

def haversine(a, b):
    r = 6371.0
    p1, p2 = math.radians(a['lat']), math.radians(b['lat'])
    dp = math.radians(b['lat'] - a['lat'])
    dl = math.radians(b['lng'] - a['lng'])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def route_stats(stops, pace):
    dist = 0.0
    legs = []
    for a, b in zip(stops, stops[1:]):
        d = haversine(a, b) * STREET_FACTOR
        legs.append(d)
        dist += d
    speed = pace_of(pace)[3]
    breaks = [BREAK_MIN.get(s.get('kind'), 0) for s in stops]
    walking = dist / speed * 60
    return {'km': round(dist, 1), 'minutes': int(round(walking + sum(breaks))),
            'walk_min': int(round(walking)), 'breaks': len([b for b in breaks if b]),
            'break_min': sum(breaks), 'legs': legs, 'speed': speed}


def timeline(stops, pace, start):
    """A walk's timeline rows (for Items/TimelineStop) with arrival times from the start, and the line under it
    ('🏁 Back around 16:40 · 4 breaks totalling 1h 50m ...'). start = the walk's start (shown in this browser's time)."""
    rows, end = [], ''
    if not stops:
        return rows, end
    stats = route_stats(stops, pace)
    t = local(start)
    walked = 0.0
    for i, s in enumerate(stops):
        leg = mins = None
        if i > 0:
            leg = stats['legs'][i - 1]
            walked += leg
            mins = leg / stats['speed'] * 60
            t = t + datetime.timedelta(minutes=mins) if t else None
        rows.append({'stop': s, 'leg': leg, 'leg_min': mins, 'eta': fmt_time(t) if t else '', 'km_in': walked if i else None})
        if t:
            t = t + datetime.timedelta(minutes=s.get('break_min') or 0)
    if t:
        end = '🏁 Back around %s · %d breaks totalling %s · distances are approximate' % (
            fmt_time(t), stats['breaks'], fmt_dur(stats['break_min']))
    return rows, end


def media_url(m):
    if m is None:
        return None
    try:
        return m.url
    except Exception:
        return None


def banner_of(key):
    """A vibe gradient picked from an id, so a person's banner always looks the same."""
    n = 0
    for ch in str(key or ''):
        n = (n * 31 + ord(ch)) % 1000003
    return VIBES[n % len(VIBES)][3]


def topic_for(walk_id, i, kind, n=0):
    """The conversation card for stop i of a walk: '💬 At the café: what food would you cross the city for?'.
    The same on every device (picked from the walk's id and the stop's place on the route); n = 🔀 presses."""
    kind = kind if kind in TOPICS else 'rest'
    options = TOPICS[kind]
    h = 0
    for ch in str(walk_id or ''):
        h = (h * 31 + ord(ch)) % 1000003
    return '%s: %s' % (TOPIC_AT.get(kind, 'Here'), options[(h + i * 3 + n) % len(options)])
