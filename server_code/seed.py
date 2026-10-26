"""Demo content so a fresh app isn't empty.

Landmarks are real public places in London; cafés and food spots are fictional.
Everything created here is flagged is_demo=True and can be removed from the Admin page.
"""
from datetime import date, timedelta, datetime

import anvil.tz
import anvil.tables as tables
from anvil.tables import app_tables

from .common import now, route_stats, AVATAR_COLORS

PLACES = [
  # name, kind, lat, lng, description
  ("Little Venice", "view", 51.5226, -0.1836, "Where the canals meet. Narrowboats, willows, the works."),
  ("Little Venice Tea Boat", "cafe", 51.5222, -0.1828, "A floating café. Flat whites on the water."),
  ("Camden Lock", "culture", 51.5413, -0.1466, "Locks, market stalls and people-watching."),
  ("Second Breakfast Club", "food", 51.5390, -0.1426, "Brunch for people who have already walked 6 km."),
  ("Kettle & Crumb", "cafe", 51.5362, -0.1033, "Tiny café, giant cinnamon buns."),
  ("Canal-side benches, Islington", "rest", 51.5340, -0.0960, "A long row of benches facing the water."),
  ("Canal Bun Co.", "food", 51.5351, -0.0625, "Bao buns and cold brew near the market."),
  ("Victoria Park", "park", 51.5362, -0.0396, "East London's big green lung, with a boating lake."),
  ("Frosty Pause", "treat", 51.5365, -0.0450, "Small-batch ice cream. The pistachio is a reward in itself."),
  ("Limehouse Basin", "rest", 51.5117, -0.0372, "Marina views and a gentle finish line."),
  ("Primrose Hill summit", "view", 51.5394, -0.1606, "The classic skyline view. Worth the short climb."),
  ("Regent's Park drinking fountain", "water", 51.5273, -0.1536, "Refill stop before the hills."),
  ("Heathside Coffee Hatch", "cafe", 51.5570, -0.1540, "Takeaway hatch at the edge of the Heath."),
  ("Parliament Hill", "view", 51.5596, -0.1594, "Kite-flying hill with one of the best views of London."),
  ("Highgate Wood", "park", 51.5770, -0.1467, "Ancient woodland and shady paths."),
  ("Clissold Park", "park", 51.5616, -0.0880, "Deer, ponds and a perfect picnic lawn."),
  ("The Long Lunch Deli", "food", 51.5627, -0.0750, "Sandwiches built for hungry walkers."),
  ("Southbank Centre", "culture", 51.5065, -0.1169, "Riverside arts centre and book market."),
  ("The Gelato Detour", "treat", 51.5071, -0.1130, "Riverside gelato. Detours encouraged."),
  ("Tower Bridge", "culture", 51.5055, -0.0754, "Cross it slowly. Look up."),
  ("Pie & Pause", "food", 51.4985, -0.0790, "Proper pies, big tables for groups."),
  ("Halfway House Bakery", "food", 51.4810, -0.0090, "Sourdough, sausage rolls and a free water refill."),
  ("Royal Observatory viewpoint", "view", 51.4769, -0.0005, "Stand on the meridian, then look over the whole city."),
  ("St Paul's Cathedral steps", "culture", 51.5138, -0.0984, "A great meeting point and a moment to sit."),
  ("Battersea Park", "park", 51.4791, -0.1567, "Riverside park with a peace pagoda."),
]

USERS = [
  # name, headline, pace, km, interests, snack, city, bio
  ("Maya Okafor", "Weekend 25k wanderer · canal enthusiast · will stop for any bun", "steady", 22,
   ["Rivers & canals", "Bakeries", "Street art", "Coffee"], "Pastry first", "London",
   "Product designer by week, canal towpath regular by weekend. I host relaxed long walks with proper breaks."),
  ("Tom Lindqvist", "Sunrise strider · hill collector · flask of tea always", "brisk", 18,
   ["Sunrise", "Parks", "Photography", "History"], "Coffee is a food group", "London",
   "Swedish, so I walk in any weather. I love early starts and big views."),
  ("Priya Raman", "Pastry critic (self-appointed) · slow walker, fast talker", "stroll", 15,
   ["Bakeries", "Markets", "Architecture", "Coffee"], "Pastry first", "London",
   "I plan walks around bakeries, not the other way round."),
  ("Jonas Weber", "Park hopper · plant nerd · 12 parks in a day record", "steady", 20,
   ["Parks", "Birdwatching", "Dogs", "Picnics"], "I pack my own", "London",
   "I like walks where you can lie on grass halfway through."),
  ("Lucía Fernández", "Night walker · bridges & stories · history PhD dropout", "steady", 16,
   ["History", "Architecture", "Rivers & canals", "Night walks"], "Savory all day", "London",
   "Ask me about any bridge and I'll tell you who fell off it."),
  ("Sam Carter", "New to London · looking for walking buddies", "stroll", 10,
   ["Coffee", "Markets", "Street art"], "Coffee is a food group", "London",
   "Just moved here and want to see the city on foot with nice people."),
  ("Aiko Tanaka", "Ultra-walker in training · 40 km is a normal Sunday", "brisk", 35,
   ["Photography", "Sunrise", "Rivers & canals", "Architecture"], "Savory all day", "London",
   "Training for a 100 km challenge walk. Happy to go slower and chat on social walks."),
  ("Noah Brennan", "Dog dad · park benches connoisseur · snack sharer", "stroll", 12,
   ["Dogs", "Parks", "Picnics", "Coffee"], "I pack my own", "London",
   "My dog Biscuit sets the pace. He likes everyone."),
]

PERKS = [
  ("☕", "Free flat white at partner cafés", "Show your code at any partner café for a free coffee.", 150),
  ("⭐", "Spotlight your walk", "Pin one of your walks to the top of Discover for a week.", 200),
  ("🩹", "Blister rescue kit", "Plasters, tape and a tiny pep talk, posted to you.", 250),
  ("🧦", "CityCrossers walking socks", "Cushioned socks made for 30 km days.", 400),
  ("🥐", "Pastry passport", "Five bakery stamps for five free pastries along popular routes.", 500),
  ("🎟️", "Big Crossing early access", "First dibs on our seasonal 30 km group crossings.", 600),
]

DEALS = [
  ("Kettle & Crumb", "15% off for CityCrossers", "Show the app at the counter on walk days.", 15, "CROSS15"),
  ("Second Breakfast Club", "Free pastry for groups of 4+", "Bring the crew, get a basket of pastries on the house.", None, "CREWBASKET"),
  ("The Gelato Detour", "2-for-1 gelato after 15 km", "Show today's walk in the app to prove you earned it.", 50, "EARNEDIT"),
  ("Halfway House Bakery", "10% off + free water refill", "For anyone walking through Greenwich.", 10, "HALFWAY10"),
  ("Pie & Pause", "Group table saved for walkers", "Message ahead and they'll hold a big table for your crew.", None, ""),
]


def _at(days, hour, minute=0):
  d = (now() + timedelta(days=days)).replace(hour=hour, minute=minute, second=0, microsecond=0)
  return d


def ensure_seeded():
  """First run only: the perks catalog doubles as the 'already set up' marker
  (perks can be switched off in Admin but never deleted), so clearing demo data
  doesn't bring it back."""
  if len(app_tables.perks.search()) == 0:
    for i, (emoji, name, desc, cost) in enumerate(PERKS):
      app_tables.perks.add_row(name=name, emoji=emoji, description=desc, cost=cost, active=True, sort=i)
    if len(app_tables.places.search()) == 0:
      seed_demo()


def seed_demo(force=False):
  if force:
    clear_demo()
  elif len(app_tables.users.search(is_demo=True)) > 0:
    return "Demo data already loaded."
  t = now()
  places = {}
  for name, kind, lat, lng, desc in PLACES:
    places[name] = app_tables.places.add_row(name=name, kind=kind, lat=lat, lng=lng, description=desc, address='',
                                             city='London', created=t, avg_rating=0, review_count=0, verified=True,
                                             is_demo=True)
  users = {}
  for i, (name, headline, pace, km, interests, snack, city, bio) in enumerate(USERS):
    users[name] = app_tables.users.add_row(
      display_name=name, headline=headline, pace=pace, distance_pref=km, interests=interests, snack_style=snack,
      city=city, bio=bio, enabled=True, is_demo=True, discoverable=True, avatar_color=AVATAR_COLORS[i % len(AVATAR_COLORS)],
      points=0, lifetime_points=[120, 760, 340, 410, 1620, 20, 980, 150][i],
      walks_count=[6, 21, 9, 11, 34, 0, 18, 4][i], km_total=[118.0, 402.5, 131.2, 214.8, 551.3, 0, 640.0, 46.5][i],
      people_met=[14, 37, 12, 22, 61, 0, 25, 8][i], verified=i in (0, 1, 4), signed_up=t - timedelta(days=200 - i * 20),
      safety_pledge=t, journal_public_default=True, email_notifications=False)
  # A little social graph
  pairs = [("Maya Okafor", "Priya Raman"), ("Maya Okafor", "Lucía Fernández"), ("Tom Lindqvist", "Aiko Tanaka"),
           ("Jonas Weber", "Noah Brennan"), ("Priya Raman", "Lucía Fernández"), ("Jonas Weber", "Maya Okafor")]
  for a, b in pairs:
    app_tables.friendships.add_row(requester=users[a], addressee=users[b], status='accepted', created=t, responded=t)
  endorse = [("Priya Raman", "Maya Okafor", "🥐 Snack scout"), ("Lucía Fernández", "Maya Okafor", "💬 Great company"),
             ("Jonas Weber", "Maya Okafor", "⏱️ Pace keeper"), ("Aiko Tanaka", "Tom Lindqvist", "🌅 Early riser"),
             ("Maya Okafor", "Lucía Fernández", "🗺️ Local legend"), ("Priya Raman", "Lucía Fernández", "🗺️ Local legend"),
             ("Noah Brennan", "Jonas Weber", "🧭 Great navigator"), ("Maya Okafor", "Priya Raman", "🥐 Snack scout"),
             ("Tom Lindqvist", "Aiko Tanaka", "📸 Photo taker"), ("Maya Okafor", "Jonas Weber", "🛟 Safety-minded")]
  for a, b, s in endorse:
    app_tables.endorsements.add_row(from_user=users[a], to_user=users[b], skill=s, created=t)

  walks = [
    dict(title="Canal Crawl: Little Venice → Limehouse", vibe='river', host="Maya Okafor", start=_at(4, 8, 30),
         pace='steady', max_walkers=10, tags=["Rivers & canals", "Bakeries", "Beginner friendly"],
         description="The whole Regent's Canal in one glorious day. Flat, scenic, and carefully engineered around "
                     "buns. We regroup at every stop; nobody gets left on the towpath.",
         stops=[("Little Venice", 'start'), ("Little Venice Tea Boat", 'cafe'), ("Camden Lock", 'culture'),
                ("Second Breakfast Club", 'food'), ("Kettle & Crumb", 'cafe'), ("Canal Bun Co.", 'food'),
                ("Limehouse Basin", 'finish')],
         going=["Priya Raman", "Jonas Weber", "Sam Carter"], approval=True),
    dict(title="Heath & Hills Sunrise Stride", vibe='sunrise', host="Tom Lindqvist", start=_at(6, 5, 45),
         pace='brisk', max_walkers=8, tags=["Sunrise", "Parks", "Photography"],
         description="Primrose Hill at golden hour, coffee at the Heath, then Parliament Hill for the big view. "
                     "Brisk but friendly, with a proper coffee break halfway.",
         stops=[("Regent's Park drinking fountain", 'start'), ("Primrose Hill summit", 'view'),
                ("Heathside Coffee Hatch", 'cafe'), ("Parliament Hill", 'view'), ("Highgate Wood", 'finish')],
         going=["Aiko Tanaka"], approval=True),
    dict(title="South Bank Pastry Pilgrimage", vibe='pastry', host="Priya Raman", start=_at(9, 9, 30),
         pace='stroll', max_walkers=12, tags=["Bakeries", "Markets", "Architecture"],
         description="Along the river from the Southbank to Greenwich, rating every pastry on the way. "
                     "Slow pace, many stops, scorecards provided.",
         stops=[("Southbank Centre", 'start'), ("The Gelato Detour", 'treat'), ("Tower Bridge", 'culture'),
                ("Pie & Pause", 'food'), ("Halfway House Bakery", 'food'), ("Royal Observatory viewpoint", 'finish')],
         going=["Maya Okafor", "Lucía Fernández", "Noah Brennan"], approval=False),
    dict(title="North London Park Hopper", vibe='parks', host="Jonas Weber", start=_at(12, 10, 0),
         pace='steady', max_walkers=8, tags=["Parks", "Picnics", "Dogs"],
         description="Five parks, one picnic, zero rush. Dogs welcome; Biscuit will be there.",
         stops=[("Victoria Park", 'start'), ("Frosty Pause", 'treat'), ("Canal Bun Co.", 'food'),
                ("Clissold Park", 'park'), ("The Long Lunch Deli", 'food'), ("Highgate Wood", 'finish')],
         going=["Noah Brennan"], approval=False),
    dict(title="Bridges by Night", vibe='night', host="Lucía Fernández", start=_at(-10, 18, 30),
         pace='steady', max_walkers=10, tags=["History", "Night walks", "Architecture"],
         description="Seven bridges, seven stories, one late dinner.", completed=True,
         stops=[("Battersea Park", 'start'), ("Southbank Centre", 'culture'), ("St Paul's Cathedral steps", 'culture'),
                ("Tower Bridge", 'view'), ("Pie & Pause", 'finish')],
         going=["Maya Okafor", "Priya Raman", "Tom Lindqvist"], approval=True),
  ]
  for spec in walks:
    host = users[spec['host']]
    w = app_tables.walks.add_row(
      title=spec['title'], description=spec['description'], host=host, start=spec['start'], pace=spec['pace'],
      max_walkers=spec['max_walkers'], visibility='public', status='completed' if spec.get('completed') else 'planning',
      vibe=spec['vibe'], tags=spec['tags'], approval_required=spec['approval'], city='London', meeting_note='',
      created=t, updated=t, is_demo=True, completed_at=t if spec.get('completed') else None)
    pts = []
    for i, (pname, kind) in enumerate(spec['stops']):
      p = places[pname]
      app_tables.stops.add_row(walk=w, place=p, name=p['name'], kind=kind, lat=p['lat'], lng=p['lng'], position=i,
                               note='', status='planned', proposed_by=host, votes=[], created=t)
      pts.append({'lat': p['lat'], 'lng': p['lng'], 'kind': kind})
    km, minutes, _b, _bm = route_stats(pts, spec['pace'])
    w.update(distance_km=km, duration_min=minutes, lat=pts[0]['lat'], lng=pts[0]['lng'])
    app_tables.walk_members.add_row(walk=w, user=host, status='going', role='host', created=t, updated=t)
    for name in spec['going']:
      app_tables.walk_members.add_row(walk=w, user=users[name], status='going', role='walker', created=t, updated=t)
    if spec['title'] == "Canal Crawl: Little Venice → Limehouse":
      app_tables.stops.add_row(walk=w, place=places["Frosty Pause"], name="Frosty Pause", kind='treat',
                               lat=places["Frosty Pause"]['lat'], lng=places["Frosty Pause"]['lng'], position=999,
                               note="Small detour but the pistachio is worth it", status='proposed',
                               proposed_by=users["Priya Raman"], votes=[users["Priya Raman"].get_id(),
                                                                        users["Jonas Weber"].get_id()], created=t)
      app_tables.messages.add_row(walk=w, user=host, created=t - timedelta(hours=5),
                                  body="Hi all! We'll meet by the café boat. I'll bring plasters and a spare battery pack 🔋")
      app_tables.messages.add_row(walk=w, user=users["Priya Raman"], created=t - timedelta(hours=3),
                                  body="Second Breakfast Club is non-negotiable 🥐")

  reviews = [
    ("Maya Okafor", "Pie & Pause", 5, "Saved our lives at km 14", "Massive tables, kind staff, the mushroom pie is elite.", True),
    ("Priya Raman", "Pie & Pause", 4, "Solid pies", "Pastry a bit thick but the gravy forgives everything.", True),
    ("Tom Lindqvist", "Tower Bridge", 5, "Go at dusk", "Lights come on and the whole river glows.", True),
    ("Priya Raman", "Halfway House Bakery", 5, "Best sausage roll south of the river", "Flaky, peppery, perfect.", True),
    ("Maya Okafor", "Kettle & Crumb", 5, "Cinnamon bun heaven", "Get there before 11 or they sell out.", True),
    ("Jonas Weber", "Clissold Park", 4, "Deer + picnic = joy", "Lawn by the ponds is the best spot.", True),
  ]
  for uname, pname, rating, title, body, pub in reviews:
    app_tables.reviews.add_row(user=users[uname], place=places[pname], rating=rating, title=title, body=body,
                               future_note='', is_public=pub, would_return=rating >= 4,
                               visited_on=date.today() - timedelta(days=10), created=t)
  for p in places.values():
    rs = [r['rating'] for r in app_tables.reviews.search(place=p)]
    if rs:
      p.update(avg_rating=sum(rs) / float(len(rs)), review_count=len(rs))

  journal = [
    ("Maya Okafor", "🥰", "The night we crossed seven bridges",
     "Lucía told us a story at every bridge. I didn't know the Thames had so much drama. Ended with pie, obviously.", 13.4),
    ("Tom Lindqvist", "🌅", "Parliament Hill at 6:52am",
     "Mist over the city, two strangers who are now friends, and the best coffee of the year from a hatch.", 9.8),
    ("Priya Raman", "🥐", "Pastry scorecard, week 12",
     "Halfway House takes the lead. Note to self: do not eat three before km 5 again.", 17.0),
  ]
  for uname, mood, title, body, km in journal:
    app_tables.journal.add_row(user=users[uname], title=title, body=body, mood=mood, is_public=True,
                               entry_date=date.today() - timedelta(days=9), km=km, created=t)

  for pname, title, desc, pct, code in DEALS:
    app_tables.discounts.add_row(place=places[pname], title=title, description=desc, percent=pct, code=code,
                                 valid_until=date.today() + timedelta(days=60), active=True, created=t)
  return f"Loaded {len(PLACES)} places, {len(USERS)} demo walkers and {len(walks)} walks."


def clear_demo():
  demo_users = list(app_tables.users.search(is_demo=True))
  demo_walks = list(app_tables.walks.search(is_demo=True))
  demo_places = list(app_tables.places.search(is_demo=True))
  for w in demo_walks:
    for tbl in (app_tables.stops, app_tables.walk_members, app_tables.messages):
      for r in tbl.search(walk=w):
        r.delete()
    for tbl in (app_tables.notifications, app_tables.reviews, app_tables.journal, app_tables.reports):
      for r in tbl.search(walk=w):
        r['walk'] = None
    w.delete()
  for p in demo_places:
    for d in app_tables.discounts.search(place=p):
      d.delete()
    for r in app_tables.reviews.search(place=p):
      r.delete()
    for s in app_tables.stops.search(place=p):
      s['place'] = None
    p.delete()
  for u in demo_users:
    for col, tbl in (('requester', app_tables.friendships), ('addressee', app_tables.friendships),
                     ('from_user', app_tables.endorsements), ('to_user', app_tables.endorsements),
                     ('user', app_tables.reviews), ('user', app_tables.journal), ('user', app_tables.walk_members),
                     ('user', app_tables.messages), ('user', app_tables.notifications),
                     ('user', app_tables.points_ledger)):
      for r in tbl.search(**{col: u}):
        r.delete()
    for n in app_tables.notifications.search(from_user=u):
      n['from_user'] = None
    for w in app_tables.walks.search(host=u):
      w['host'] = None
    u.delete()
  return f"Removed {len(demo_users)} demo walkers, {len(demo_walks)} walks and {len(demo_places)} places."
