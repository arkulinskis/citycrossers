---
name: citycrossers
description: Context, workflow and recipes for CityCrossers, the user's Anvil walking-club app (group long walks with food/break stops; swipe deck, community map, walk planner, LinkedIn-style profiles, points and perks, safety features). Load this before any feature request, bug fix, restyle or deploy for CityCrossers.
---

# CityCrossers: working on the app

**What it is:** "modern running clubs for people who prefer walking", crossed with a little Tinder (swipe on group walks) and a little LinkedIn (walker profiles, endorsements). Someone plans a long walk with stops (cafés, food, parks, viewpoints), invites friends or opens it to the public, others join; afterwards they review stops, endorse their crew and write a journey entry. Points (six levels, Stroller → City Crosser) buy perks. Safety: pledge before the first walk, public walks need 3+ spots and host approval, reports, emergency contact.

**Where it lives:**
- App repo **github.com/arkulinskis/citycrossers**, branch `master`; Anvil pulls master. Live: https://citycrossers.com (per apps.json).
- This folder (`C:\Users\arkvi\Documents\CLAUDE\citycrossers`) **is** the Anvil repo ("git" layout). README.md describes every area and the design; keep it current.

**What the user wants:** bright, fresh look with a hint of "there will be breaks and food stops" (Bricolage Grotesque + DM Sans, green #17A673). Map of places people can propose. Creative, assumed details are welcome. Claude deploys.

## Workflow

1. `python -I C:\Users\arkvi\Documents\CLAUDE\APP_MAKER\tools\apps_status.py citycrossers -v`; pull Anvil's commits (`git pull --ff-only`); never touch someone else's uncommitted work.
2. Edit the files here.
3. `python C:\Users\arkvi\Documents\CLAUDE\APP_MAKER\tools\gitapp_check.py citycrossers` → `ALL CHECKS PASSED`.
   Server logic: `python ...\APP_MAKER\tools\gitapp_test.py citycrossers <script>`; `anvil.server.call("admin_seed_demo")` as an admin loads 25 places, 8 demo walkers and 5 walks under the mock, a good base for tests.
   The UI (Python forms) can't run locally: re-read client changes, and tell the user what to click.
4. Commit only your files as arkulinskis with the Co-Authored-By line; `git push origin master`.
5. New tables/columns: `anvil.yaml → db_schema` (same format); the user accepts the **Schema Mismatch** alert.

## Architecture

```
client_code/Main/      app shell (header nav, points chip, notifications bell, user menu, footer) + #hash router; polls poll_counts every 60 s
  routes: #landing #discover #map #plan #edit/<id> #walk/<id> #walks #people #u/<id> #me #me/edit #journey #perks #admin #safety #notifications
client_code/<Page>/    Landing, Discover (swipe deck), MapPage, WalkEditor, WalkDetail, MyWalks, People, Profile, ProfileEdit, Journey, Perks, Admin, Safety, Notifications
client_code/ui.py      constants, HTML builders, formatting (fmt_time/date/when, km, stars), route_stats, level_for, server-call wrapper, chips/stars widgets
client_code/dialogs.py auth, safety_pledge, place_form, review, entry (journal), report, invite, place_details
client_code/mapkit.py  Leaflet wrapper (CARTO Voyager tiles, routes)      state.py signed-in user, counts, go(route)
server_code/common.py  ADMIN_EMAILS, current_user/require_admin, ids (rid/by_id), points (award), levels, notify (+ optional email), haversine/route_stats, match_score
server_code/serial.py  rows → client-safe dicts (no emails or emergency contacts leak)
server_code/api_walks.py   walks, membership (join/pass/invite/host_decide/leave), stops + votes, chat, completion, home_feed, map_data
server_code/api_social.py  friends, people, profiles, endorsements, reports, notifications, poll_counts
server_code/api_me.py      profile, avatar, safety pledge, places, reviews, journal, journey, perks
server_code/api_admin.py   deals, place moderation, reports, member verification/admin/suspension, perks catalog, demo data
server_code/seed.py        demo content (London landmarks, fictional cafés, demo walkers)    weather.py   walk-day forecast (Open-Meteo)
theme/assets/          theme.css (design system), cc.js (swipe, confetti, clipboard), logo.svg, spinner.svg, favicon/apple-touch icons
```

**Page pattern:** same as MonShop/Addanapp: a Form with an empty HtmlTemplate; Python builds the HTML string, `ui.bind`/`on_click` delegates clicks, data loads in `show` through the ui call wrapper (returns `ui.FAIL` + toast on error). Main swaps pages into the `content` slot.

**Tables** (16, all server-only): users (profile, pace, points, levels, safety_pledge, stats, is_admin, verified, is_demo…), walks, stops, places, walk_members, friendships, endorsements, reviews, journal, points_ledger, notifications, discounts, perks, redemptions, messages, reports.

**Admins:** `arkulinskis@gmail.com` (ADMIN_EMAILS in server_code/common.py). Demo walkers can't log in.

## Recipes

- **New server function:** in the matching api_* module; `current_user()` first, membership/host checks via `membership()`; return serial.py dicts.
- **Points for a new action:** `common.award(user, amount, reason)` (writes points_ledger) and mention it on the Perks page.
- **New notification:** `common.notify(user, kind, message, link=..., email_subject=...)`.

## Gotchas

- Leaflet 1.9.4 from unpkg + CARTO Voyager tiles + Open-Meteo: no API keys. Adding another provider = update the legal kit facts.
- `python -I` hides PyYAML: run gitapp_check/gitapp_test without `-I`.
- Consider 18+ for this app (adults meeting strangers): an open suggestion in the legal kit README, not done.

## Privacy & Terms (legal kit)

From `C:/Users/arkvi/Documents/CLAUDE/APP_MAKER/legal-kit` (see its README). Don't edit `theme/assets/legal-kit.js`, `client_code/legal.py` or `server_code/legal_server.py` here: change `apps/citycrossers.json` there, run `python -I build.py citycrossers && python -I install.py citycrossers`, then commit and push here. Update the facts when the app collects new personal data, adds a third-party service or asks for a new permission.
- Sign-up keeps the consent tick box (dialogs.auth); `legal.refresh_soon()` after sign-in, `legal.signed_out()` after sign-out.
