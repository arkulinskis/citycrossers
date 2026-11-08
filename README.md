# CityCrossers 🥾

**Long walks. New people. Snack stops guaranteed.**

CityCrossers is a walking club app built on [Anvil](https://anvil.works): think modern running clubs for people who prefer
walking, crossed with a little Tinder (swipe on group walks) and a little LinkedIn (walker profiles and endorsements).

## What's in the app

| Area | What it does |
| --- | --- |
| **Landing page** | Full marketing page: a "Watch" section with the YouTube pitch video (cover image until you press play), how it works, the "break manifesto", features, points & perks, partner cafés, safety, FAQ. |
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
External: Leaflet 1.9.4 + OpenStreetMap tiles (no API key; CARTO until Nov 2026), Open-Meteo forecasts (no API key), Google Fonts.

## Code map

```
client_code/                 native Anvil Forms (Python + HTML templates)
  startup.py       start-up: legal kit, get_me, router.start()
  router.py        hash addresses -> page Forms (#walk/ID, #u/ID, #plan, ...), visitors -> landing
  state.py         signed-in walker, counts, server-call wrapper (toasts, pledge, sign-in), DOM helpers
  auth.py          sign in / up / reset / Google / sign out
  ui.py            constants (kinds, paces, vibes, levels), formatting, route maths
  dialogs.py       one call per dialog (pledge, place form, review, entry, report, invite, place details, info)
  mapkit.py        the Leaflet engine (Components/MapView wraps it)
  avatar.py        draws avatars into DOM nodes
  Layouts/Shell    header, walker menu, notifications poll, footer, phone tab bar
  Pages/           Landing Discover MapPage WalkEditor WalkDetail MyWalks People Profile ProfileEdit
                   Journey Perks Admin Safety Notifications
  Items/           RepeatingPanel rows and cards (WalkCard, PersonCard, TimelineStop, Chip, Option ...)
  Components/      MapView, Avatar, AvatarStack, Strip, Person, Stars, Chips
  Dialogs/         AuthDialog SafetyPledge PlaceForm Review ReviewPick Entry Report Invite PlaceDetails
                   Prompt Endorse PickWalk Partner Info
server_code/
  common.py        users, ids, points, levels, notifications, route maths, match score
  serial.py        rows → client-safe dicts (no emails or emergency contacts leak)
  api_walks.py     walks, membership, stops & votes, chat, completion, home feed, map data
  api_social.py    friends, profiles, endorsements, reports, notifications
  api_me.py        profile, places, reviews, journal, perks
  api_admin.py     admin tools
  seed.py          demo content
  weather.py       walk-day forecast
theme/assets/      app.css (design system + Forms role layer), theme.css (spinner), app-kit.js, cc.js (swipe, confetti, clipboard, Watch video)
tools/             check.py, ui_test.py + ui/smoke.js, testing/test_server.py
```

## Design

Bright cream background, leaf green for go, tangerine for food stops, sunshine yellow for points.
Headings in Bricolage Grotesque, body in DM Sans. Routes are dotted "footstep" lines, and food stops are always highlighted:
there will be breaks.

<!-- libraries:start -->
## Libraries and outside services

What this project uses besides its own code. Generated by `APP_MAKER/tools/libraries.py`; to change it, edit `APP_MAKER/libraries/catalog.py` and re-run the script.

| Name | How it gets in | Used here for |
|---|---|---|
| [Leaflet](https://leafletjs.com) 1.9.4 | Loaded from a CDN | walk routes and meeting points |
| [OpenStreetMap tiles](https://operations.osmfoundation.org/policies/tiles/) | Outside web service | The free map pictures behind the Leaflet maps. |
| [Open-Meteo](https://open-meteo.com) | Outside web service | the weather for a planned walk |
| [YouTube embeds](https://developers.google.com/youtube/player_parameters) | Outside web service | Plays a YouTube video inside the page (the privacy-friendlier youtube-nocookie address). |
| [Google Fonts](https://fonts.google.com) | Loaded from a CDN | Bricolage Grotesque, DM Sans |

**Built into the browser:** Geolocation, Clipboard.

**Anvil platform:** Anvil, Anvil Data Tables, Anvil Google service, Anvil JS bridge (anvil.js), Anvil Users, Anvil HTTP, Anvil Email, Anvil timezones (anvil.tz).

<!-- libraries:end -->
