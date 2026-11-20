# CityCrossers 🥾

**Long walks. New people. Snack stops guaranteed.**

CityCrossers is a walking club app built on [Anvil](https://anvil.works): think modern running clubs for people who prefer
walking, crossed with a little Tinder (swipe on group walks) and a little LinkedIn (walker profiles and endorsements).

## What's in the app

| Area | What it does |
| --- | --- |
| **Landing page** | Full marketing page: "Open walks this week" (up to 3 real public walks with spots, hidden when there are none), a "Watch" section with the YouTube pitch video (cover image until you press play), how it works, the "break manifesto", features, points & perks, partner cafés, safety, FAQ. |
| **Public walk pages** | A shared walk link (`/w/<id>`, also in email invites) shows visitors the walk itself, no account needed: vibe, date and time in their time zone, km, pace, food stops, route map and stops, the host's first name and level, "4 of 8 going · 4 spots left". "Join this walk" signs them up and carries on with the join. `/w/<id>` gives WhatsApp, iMessage, Facebook and Meetup a link card and search engines a schema.org Event. Meeting spot, crew and chat stay members-only. |
| **Discover** | Swipe deck of walks ranked by a match score (pace, distance, interests). Swipe right to join or request, left to pass. Plus "walkers to meet" cards. |
| **Map** | Leaflet map of community-pinned places (cafés, food, parks, viewpoints, water, rest), partner deals and walk starts. Anyone can propose a place. |
| **Plan a walk** | Click the map to build a route, or add existing places. Live distance/time/break estimates, warnings for long stretches without a break, vibes, tags, friends-only or public visibility, host approval, invites. |
| **Walk page** | Route timeline with ETAs and break lengths and a conversation topic at every stop (🔀 for another), suggested stops with group voting, crew and join requests, group chat, walk-day weather (Open-Meteo), safety panel, "share my plan", invite by email (host or walkers going only, 10 a day), "🔁 Weekly walk · edition N". |
| **Show-up kit** | "Sunday's walk: still in?" 48 h before (Discover + walk page): Yes shows ✓ to the host, "Can't make it" frees the spot for the waitlist. 📅 Add to calendar (.ics made in the browser, or Google Calendar). The host sees "5 of 7 confirmed" and, on requests, "Came to 9 of 10 walks" (after 3+ walks). Completing a walk is a roll call: unticked walkers get no points and aren't counted as met. 🎯 Reliable walker badge. |
| **Host again** | On a walk they hosted, "🔁 Host again next week" opens the planner with the same route, stops, title, vibe, pace and size on the same weekday and time next week, and "Invite last time's crew" ticked. Walkers who went get "🗺️ Walk this route again" (route only). |
| **After a walk** | Review each stop, endorse your crew, write it into your Journey. |
| **People & profiles** | Connections, search, suggestions, LinkedIn-style profiles with stats, endorsements, badges, public reviews ("taste map") and journey highlights. |
| **My Journey** | Personal timeline of walks, journal entries and reviews, with private "notes to future me" and public/private toggles. |
| **Points & perks** | Points for walking, hosting, meeting new people, reviewing and journaling. Six levels from Stroller to City Crosser, and redeemable perks. |
| **Safety** | Safety pledge before your first walk, public walks need 3+ spots and host approval, report flow, emergency contact, safety center. |
| **Admin** | Partner deals for places on the map, place moderation, safety reports, member verification/admin/suspension, perks catalog, demo data. |

## Getting it running in Anvil

1. In the Anvil editor, pull this branch from GitHub (Version History → Git), or clone the repo as a new app.
2. Anvil will offer to **apply the data table schema** from `anvil.yaml`. Accept it (18 tables).
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
  calendar.py      .ics text + Google Calendar link for a walk
  Pages/           Landing Discover MapPage WalkEditor WalkDetail WalkPublic MyWalks People Profile ProfileEdit
                   Journey Perks Admin Safety Notifications
  Items/           RepeatingPanel rows and cards (WalkCard, PersonCard, TimelineStop, Chip, Option ...)
  Components/      MapView, Avatar, AvatarStack, Strip, Person, Stars, Chips
  Dialogs/         AuthDialog SafetyPledge PlaceForm Review ReviewPick Entry Report Invite PlaceDetails
                   Prompt Endorse PickWalk Partner Info AddCalendar RollCall
server_code/
  common.py        users, ids, points, levels, notifications, route maths, match score
  serial.py        rows → client-safe dicts (no emails or emergency contacts leak)
  api_walks.py     walks, copy (host again), membership, confirm spot, email invites, stops & votes, chat, roll call, home feed, map data
  api_public.py    public walks for visitors (no sign-in; never the meeting spot, crew or chat)
  walk_pages.py    /w/<id>: link cards (Open Graph) + schema.org Event, then on to /#walk/<id>
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
| [Leaflet](https://leafletjs.com) 1.9.4 | Loaded from a CDN | A light, simple interactive map: pan, zoom, pins and pop-ups. |
| [OpenStreetMap tiles](https://operations.osmfoundation.org/policies/tiles/) | Outside web service | The free map pictures behind the Leaflet maps. |
| [Open-Meteo](https://open-meteo.com) | Outside web service | Free weather forecasts (and place-name search) with no API key. |
| [YouTube embeds](https://developers.google.com/youtube/player_parameters) | Outside web service | Plays a YouTube video inside the page (the privacy-friendlier youtube-nocookie address). |
| [Google Fonts](https://fonts.google.com) | Loaded from a CDN | Bricolage Grotesque, DM Sans |

**Built into the browser:** Geolocation, localStorage, Clipboard, File downloads (Blob).

**Anvil platform:** Anvil, Anvil Data Tables, Anvil Email, Anvil JS bridge (anvil.js), Anvil Secrets, Anvil Users, Anvil Google service, Anvil HTTP, Anvil timezones (anvil.tz).

**Build and test tools (not shipped):** axe-core, Node.js, Headless Chrome (DevTools Protocol), PyYAML.

<!-- libraries:end -->
