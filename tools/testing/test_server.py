"""Server tests against the strict mock of Anvil (tools/testing/mock).

    python tools/testing/test_server.py          -> prints ALL OK, or the first failure

call(name, ...) runs a server function the way the browser does: by name, with require_user enforced. Replies carry
datetimes and Media (Anvil sends those fine), so replies are not forced through JSON; dict keys must be strings
(Anvil refuses others). Add tests for every new server function: the happy path, bad input, and someone who isn't
allowed. The server raises Exception("...") for expected problems (the client shows the message as a toast).
"""
import datetime as dt
import importlib
import os
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
_tmp = pathlib.Path(tempfile.mkdtemp())
shutil.copytree(PROJECT / "server_code", _tmp / "app")
(_tmp / "app" / "__init__.py").write_text("")
os.environ["ANVIL_APP_YAML"] = str(PROJECT / "anvil.yaml")  # the mock's tables follow the app's own schema
sys.path[:0] = [str(HERE / "mock"), str(_tmp)]
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import anvil.server  # noqa: E402
import anvil.users  # noqa: E402
from anvil.tables import app_tables as T  # noqa: E402

M = {p.stem: importlib.import_module("app." + p.stem) for p in sorted((PROJECT / "server_code").glob("*.py"))}
now = dt.datetime.now(dt.timezone.utc)


def keys_ok(x, path="reply"):
    if isinstance(x, dict):
        for k, v in x.items():
            assert isinstance(k, str), "%s has a non-string key %r" % (path, k)
            keys_ok(v, path + "." + k)
    elif isinstance(x, (list, tuple)):
        for i, v in enumerate(x):
            keys_ok(v, "%s[%d]" % (path, i))


def call(name, *args, **kw):
    r = anvil.server.call(name, *args, **kw)
    keys_ok(r, name)
    return r


def as_user(row):
    anvil.users.CURRENT[0] = row
    anvil.server.session.use(row.get_id() if row is not None else None)


def fails(name, *args, **kw):
    """True when the call is refused (not signed in, not allowed, bad input)."""
    try:
        call(name, *args, **kw)
    except Exception:
        return True
    return False


def person(email, name=None, **kw):
    return T.users.add_row(email=email, enabled=True, signed_up=now, display_name=name, **kw)


def rid(row):
    return row.get_id().strip("[]").replace(",", "_")


# ---------------------------------------------------------------------------------- accounts
admin = person("arkulinskis@gmail.com", "The Admin")
ana = person("ana@example.com", "Ana Walker")
ben = person("ben@example.com", "Ben Rambler")

as_user(None)
assert fails("get_me"), "get_me needs a signed-in walker"
assert fails("admin_overview")
as_user(admin)
assert call("get_me")["is_admin"] is True, "ADMIN_EMAILS become admins"
call("admin_seed_demo")
as_user(ana)
me = call("get_me")
assert me["name"] == "Ana Walker" and me["is_admin"] is False and "email" in me
r = call("update_me", {"display_name": "Ana W.", "headline": "Weekend 20k", "pace": "stroll"})
assert r["me"]["name"] == "Ana W." and r["me"]["pace"] == "stroll"
assert fails("update_me", {"display_name": "A"}), "names need 2+ characters"
assert fails("admin_overview"), "walkers aren't admins"
assert call("accept_safety_pledge")["safety_pledge"] is not None

# ---------------------------------------------------------------------------------- discover + map
feed = call("home_feed")
assert {"deck", "upcoming", "invites", "suggestions", "counts"} <= set(feed)
md = call("map_data")
assert len(md["places"]) >= 10, "demo places appear on the map"
place = md["places"][0]
assert call("get_place", place["id"])["name"] == place["name"]
added = call("add_place", {"name": "Test Bench", "kind": "rest", "lat": 51.51, "lng": -0.1, "description": "A view"})
assert added["name"] == "Test Bench"

# ---------------------------------------------------------------------------------- plan, chat, join
start = now + dt.timedelta(days=5)
stops = [{"name": "Start", "kind": "start", "lat": 51.50, "lng": -0.12, "place_id": None, "note": ""},
         {"name": "Cafe", "kind": "cafe", "lat": 51.51, "lng": -0.11, "place_id": place["id"], "note": ""},
         {"name": "Finish", "kind": "finish", "lat": 51.52, "lng": -0.10, "place_id": None, "note": ""}]
wid = call("create_walk", {"title": "Test Crossing", "description": "Pastries", "start": start, "pace": "steady",
                           "max_walkers": 6, "visibility": "public", "vibe": "pastry", "tags": ["Coffee"],
                           "approval_required": False, "meeting_note": "By the fountain", "stops": stops,
                           "invite_ids": []})
w = call("get_walk", wid)
assert w["is_host"] and w["title"] == "Test Crossing" and len(w["stops_full"]) == 3
assert call("get_walk_for_edit", wid)["title"] == "Test Crossing"
call("post_message", wid, "Hello crew")
as_user(ben)
assert fails("get_walk_for_edit", wid), "only the host edits"
call("accept_safety_pledge")
assert call("join_walk", wid, None) in ("going", "requested", "waitlist")
mine = call("my_walks")
assert any(x["id"] == wid for x in mine["upcoming"] + mine["pending"])
assert call("send_friend_request", rid(ana)) in ("pending_out", "friends", "requested", True)
assert {"friends", "incoming", "outgoing", "suggestions"} <= set(call("people_page"))
as_user(ana)
prof = call("get_profile", None)
assert prof["relationship"] == "self" and "badges" in prof
assert "items" in call("journey")
perks = call("perks_page")
assert "perks" in perks and "level" in perks
assert isinstance(call("get_notifications"), list)
assert isinstance(call("poll_counts"), dict)
assert call("cancel_walk", wid) is True

# ---------------------------------------------------------------------------------- admin
as_user(admin)
ov = call("admin_overview")
assert {"stats", "deals", "places", "reports", "users", "perks"} <= set(ov)
call("admin_clear_demo")
assert call("admin_overview")["stats"]["demo_rows"] == 0

print("ALL OK")
