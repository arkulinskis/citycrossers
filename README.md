# CityCrossers 🥾

**Long walks. New people. Snack stops guaranteed.**

CityCrossers is a walking club app built on [Anvil](https://anvil.works): think modern running clubs for people who prefer
walking, crossed with a little Tinder (swipe on group walks) and a little LinkedIn (walker profiles and endorsements).

## What's in the app

| Area | What it does |
| --- | --- |
| **Landing page** | Full marketing page: how it works, the "break manifesto", features, points & perks, partner cafés, safety, FAQ. |
| **Discover** | Swipe deck of walks ranked by a match score (pace, distance, interests). Swipe right to join or request, left to pass. Plus "walkers to meet" cards. |
| **Map** | Leaflet map of community-pinned places (cafés, food, parks, viewpoints, water, rest), partner deals and walk starts. Anyone can propose a place. |
| **Plan a walk** | Click the map to build a route, or add existing places. Live distance/time/break estimates, warnings for long stretches without a break, vibes, tags, friends-only or public visibility, host approval, invites. |
| **Walk page** | Route timeline with ETAs and break lengths, suggested stops with group voting, crew and join requests, group chat, walk-day weather (Open-Meteo), safety panel, "share my plan", invite by email, mark complete. |
| **After a walk** | Review each stop, endorse your crew, write it into your Journey. |
| **People & profiles** | Connections, search, suggestions, LinkedIn-style profiles with stats, endorsements, badges, public reviews ("taste map") and journey highlights. |
| **My Journey** | Personal timeline of walks, journal entries and reviews, with private "notes to future me" and public/private toggles. |
| **Points & perks** | Points for walking, hosting, meeting new people, reviewing and journaling. Six levels from Stroller to City Crosser, and redeemable perks. |
| **Safety** | Safety pledge before your first walk, public walks need 3+ spots and host approval, report flow, emergency contact, safety center. |
| **Admin** | Partner deals for places on the map, place moderation, safety reports, member verification/admin/suspension, perks catalog, demo data. |

## Getting it running in Anvil

1. In the Anvil editor, pull this branch from GitHub (Version History → Git), or clone the repo as a new app.
2. Anvil will offer to **apply the data table schema** from `anvil.yaml`. Accept it (16 tables).
3. Run the app and sign up.
   - The email listed in `ADMIN_EMAILS` (`server_code/common.py`) becomes an **admin** automatically.
4. The first signed-in visit loads **demo data** (London landmarks, fictional cafés, demo walkers, walks, deals).
   Remove or reload it from **Admin → Demo data**. Demo walkers can't log in.

Services used: Data Tables, Users (email + password, no email confirmation), Email (invites and notifications).
External: Leaflet 1.9.4 + CARTO Voyager tiles (no API key), Open-Meteo forecasts (no API key), Google Fonts.

## Code map

```
client_code/
  Main/            app shell + hash router (#walk/ID, #u/ID, #plan, ...)
  Landing/         marketing page (markup in landing_content.py)
  Discover/ MapPage/ WalkEditor/ WalkDetail/ MyWalks/ People/
  Profile/ ProfileEdit/ Journey/ Perks/ Admin/ Safety/ Notifications/
  ui.py            constants, HTML builders, formatting, server-call wrapper, chips/stars widgets
  dialogs.py       auth, safety pledge, place/stop picker, reviews, journal entries, reports, invites
  mapkit.py        Leaflet wrapper
  state.py         signed-in user, counts, navigation
server_code/
  common.py        users, ids, points, levels, notifications, route maths, match score
  serial.py        rows → client-safe dicts (no emails or emergency contacts leak)
  api_walks.py     walks, membership, stops & votes, chat, completion, home feed, map data
  api_social.py    friends, profiles, endorsements, reports, notifications
  api_me.py        profile, places, reviews, journal, perks
  api_admin.py     admin tools
  seed.py          demo content
  weather.py       walk-day forecast
theme/assets/      theme.css (design system), cc.js (swipe, confetti, clipboard)
```

## Design

Bright cream background, leaf green for go, tangerine for food stops, sunshine yellow for points.
Headings in Bricolage Grotesque, body in DM Sans. Routes are dotted "footstep" lines, and food stops are always highlighted:
there will be breaks.
