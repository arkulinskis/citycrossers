---
name: citycrossers
description: Context, workflow and recipes for CityCrossers, the user's Anvil walking-club app built as native Anvil Forms (group long walks with food/break stops; swipe deck, community map, walk planner, LinkedIn-style profiles, points and perks, safety features). Load this before any feature request, bug fix, restyle or deploy for CityCrossers.
---

# CityCrossers: working on the app

**What it is:** "modern running clubs for people who prefer walking", crossed with a little Tinder (swipe on group walks) and a little LinkedIn (walker profiles, endorsements). Someone plans a long walk with stops (cafés, food, parks, viewpoints), invites friends or opens it to the public, others join; afterwards they review stops, endorse their crew and write a journey entry. Points (six levels, Stroller → City Crosser) buy perks. Safety: pledge before the first walk, public walks need 3+ spots and host approval, reports, emergency contact.

**Where it lives:**
- Repo **github.com/arkulinskis/citycrossers**; Anvil pulls `master`. Live: https://citycrossers.com.
- Folder `C:\Users\arkvi\Documents\CLAUDE\citycrossers-forms` = the git clone ("git" layout: the folder *is* the Anvil app).
  Native Forms on master since 2026-11-08 (forms branch merged); the old classic folder `citycrossers` is retired (RETIRED.md): never commit or push from it.
- README.md describes every area; APP_MAP.md is the code map (read it first).

**What the user wants:** bright, fresh look with a hint of "there will be breaks and food stops" (Bricolage Grotesque + DM Sans, green #17A673, orange food stops, sun for points). Map of places people can propose. Creative, assumed details are welcome. Claude deploys. Light theme only (no dark palette yet). Every page must fit 390 px.

## Workflow

1. `git pull --ff-only` (Anvil commits too); never touch someone else's uncommitted work.
2. Edit a page's template and Python side by side (`client_code/Pages/X/form_template.html` + `__init__.py`).
3. `python tools/check.py` (no -I) → **ALL CHECKS PASSED** (Anvil validator, JS syntax, asset hashes, server tests in
   tools/testing/test_server.py, design check summary).
4. `python -I tools/ui_test.py` (Docker running) → smoke.js opens every address signed out, as a new walker and as admin,
   desktop + 390 px. Container `citycrossers-dev`; `--stop` afterwards.
5. Commit only your files as arkulinskis with the Co-Authored-By line; push. New tables/columns: `anvil.yaml → db_schema`,
   the user accepts the **Schema Mismatch** alert.
6. After a change: `python -I C:/Users/arkvi/Documents/CLAUDE/APP_MAKER/standard/app_map.py citycrossers --folder=<this folder>`.

## Architecture (Forms)

```
startup.py   legal kit, get_me, router.start()          router.py  addresses -> Forms; visitors see Landing (target remembered)
state.py     me/counts, call() (toast on error, SAFETY_PLEDGE_REQUIRED -> pledge dialog + retry, "Please sign in" -> AuthDialog + retry)
ui.py        KINDS, PACES, VIBES, LEVELS, SKILLS..., fmt_*, km, route_stats (mirrors server)   dialogs.py  one function per dialog
mapkit.py    Leaflet engine (pins/popups are small escaped HTML strings)   avatar.py  paints avatars into DOM nodes
Layouts/Shell  header (6 nav links, points chip, bell polled every 60 s via a Timer, walker menu), footer; mode "landing" hides both
Pages/       Landing Discover MapPage WalkEditor WalkDetail MyWalks People Profile ProfileEdit Journey Perks Admin Safety Notifications
Items/       RepeatingPanel rows: Chip (filters/tabs/tags), Option (pace/vibe/visibility), WalkCard, WalkRow, PersonCard, PersonRow, ...
Components/  MapView (wraps mapkit), Avatar, AvatarStack, Strip (stop dots), Person (avatar+name line), Stars, Chips (picker)
Dialogs/     AuthDialog SafetyPledge PlaceForm Review ReviewPick Entry Report Invite PlaceDetails Prompt Endorse PickWalk Partner Info
server_code/ unchanged from the classic app: api_walks, api_social, api_me, api_admin, common, serial, seed, weather, legal_server, seo_routes, SchemaCheck
theme/assets app.css (old theme.css + design kit + role layer), theme.css (spinner only), app-kit.js, cc.js (swipe, confetti, copy, Watch video)
```

Addresses: `#landing #discover #map #plan #plan/from/<place> #plan/again/<id> #edit/<id> #walk/<id> #walks[/tab] #people #u/<id> #me #me/edit #welcome #journey #perks #admin #safety #notifications`.
Visitors on `#walk/<id>` get Pages/WalkPublic (the public walk page); members get WalkDetail. Shared links are `/w/<id>`
(server_code/walk_pages.py, an `anvil.server.route`): link-card tags + JSON-LD Event, then `location.replace('/#walk/<id>')`.

## Features added 2026-11-20 (improvement round)

- **Public walk pages:** `api_public.public_walk` (no require_user; public walks only; slim host = first name, initials,
  colour, avatar, level, walks, verified; never meeting_note/members/chat/emails) and `public_walks(limit)` (Landing's
  "Open walks this week", real walks only). Join on the public page: `state.want_join(id)` + `after_login` -> sign-up ->
  WalkDetail `_continue_join` (invited -> accept, else the normal join flow with pledge + hello).
- **invite_by_email (security fix):** host or going only (like invite_to_walk), upcoming walks only, 10 a day per walker
  (`EMAIL_INVITES_PER_DAY`), one email per address per walk and 2 a day per address, the same answer whether or not the
  address has an account. Table `email_invites` stores inviter, walk, created and a SHA-256 fingerprint of the address
  (never the address); someone who signs up with that address gets the invite (`_claim_email_invite` in get_walk).
  The email links to `/w/<id>` and shows the walk's local time.
- **Walk time zones:** the editor sends `tz_name` + `tz_offset` (cc.tz: minutes east of UTC at the start). Server
  helpers in common.py: `walk_tz`, `local_start`, `fmt_local` ('Sunday 7 December, 09:30 (Toronto time)'). Old walks
  fall back to the inviter's browser time zone, then UTC.
- **Show-up kit:** `walk_members.confirmed_at`; `confirm_spot(walk_id, coming)` (False = `_leave` -> waitlist promoted);
  get_walk `confirm_needed` / `my_confirmed` / `crew_confirmed` (host) / card `confirmed` + `show_up` (host, 3+ walks);
  home_feed `to_confirm`; `complete_walk(walk_id, absent_ids=None)` -> absent walkers become `no_show` (no points, not
  met, in-app note only). `common.show_up(u)`; 🎯 badge in `badges_for`. Client: calendar.py, Dialogs/AddCalendar,
  Dialogs/RollCall.
- **Host again:** `walk_copy(walk_id)` (host: everything + crew count; others: route only), `#plan/again/<id>` ->
  WalkEditor(copy_of); `create_walk` takes `copy_of` + `invite_crew` (crew only when the caller hosted the original) and
  sets `walks.repeat_of`; `common.edition_of(w)` follows it for "🔁 Weekly walk · edition N".
- **Stop topics:** `ui.TOPICS` (5 per stop kind) + `ui.topic_for(walk_id, i, kind, n)`, shown by Items/TimelineStop
  (`.tl-topic`, 🔀 cycles locally). No server or schema change.
- **Demo walks roll forward:** `seed.refresh_demo_dates()` (called from ensure_seeded) moves upcoming demo walks that
  slipped into the past forward by whole weeks, so Discover and the map never look empty. Real walks are never moved.
- Newer columns are read with `common.col(row, name)` and written with `set_col` (guarded) so the app keeps working
  until the user accepts the Schema Mismatch.

## How things are done here

- **Page** = `<anvil-form layout="CityCrossers.Layouts.Shell">`; register it in router._pick. Static copy in the template,
  changing text via `anvil:dom-node` + `state.text(...)`, show/hide via `anvil:name` + `.visible`.
- **Buttons** = Anvil Buttons with roles `["cc-btn", "orange"|"ghost"|"soft"|"danger"|"dark"|"sun", "sm"|"lg", "block"]`; app.css
  widens every old `.cc-btn.x` rule to `.anvil-role-cc-btn.anvil-role-x > button`. Chips, tabs, options, stars stay native
  `<button>`s with the old classes inside item templates (`anvil:on-dom:click`).
- **Lists** = RepeatingPanel + an `Items/` Form; grids via panel roles (`cc-cards`, `cc-cards-sm`, `cc-list`, `cc-rows`, `contents`).
  Item → page: `self.parent.raise_event("x-...")`.
- **Server calls** = `state.call(fn, ...)`; returns `state.FAIL` on error (the server raises `Exception("message")`).
- **Map** = `self.map_view.setup(height, on_click=..., picking=...)` returns the engine; popups use `mv.popup_el(html, actions)` with `ui.esc`.

## Recipes

- **New server function:** in the matching api_* module; `current_user()` first, membership/host checks via `membership()`; return serial.py dicts; add a test.
- **Points for a new action:** `common.award(user, amount, reason)` and mention it on the Perks page (static list in Pages/Perks).
- **New notification:** `common.notify(user, kind, message, link=..., email_subject=...)`; its icon in Items/NotifRow.

## Gotchas

- `.cc-map` itself becomes `.leaflet-container` (tests look for `.cc-map.leaflet-container`).
- The swipe card is one DOM element reused for the whole deck: cc.swipe is bound once (Discover show); render_deck resets transform/opacity.
- Continue with Google: auth.google; a brand-new account goes to #welcome (AuthDialog sets state.after_login).
- Leaflet 1.9.4 from unpkg + OpenStreetMap tiles + Open-Meteo: no API keys. Keep the OSM attribution. Another provider = update the legal kit facts.
- Watch section (`#watch` on Landing): YouTube iIDuAWF-BzI via `data-yt-film` (cc.js swaps in a youtube-nocookie player).
- Server modules pass `anvil validate` with type annotations only (`fields: dict = dict(...)`); seo_routes/legal_server are kit files.
- `python -I` hides PyYAML: run check.py without -I.
- `tools/assets.py` rewrites anvil.yaml in block style when a hash changes; keep the file's own format and change only
  the `?v=` hashes (and your schema lines).
- Public pages (WalkPublic) load their data on show with `call_s` (no spinner) so the "Lacing up" state draws first.

## Privacy & Terms (legal kit)

From `C:/Users/arkvi/Documents/CLAUDE/APP_MAKER/legal-kit`: change `apps/citycrossers.json` there, run build/install, then `python tools/assets.py`. Don't edit `theme/assets/legal-kit.js`, `client_code/legal.py` or `server_code/legal_server.py` here.
Sign-up keeps the consent tick (Dialogs/AuthDialog). Feedback = Prepsto only (code wzrzr2f, "Submit feedback").
