"""Page addresses (the same ones the classic version had, so shared links keep working):

    #landing           the landing page (also what visitors see for every member page)
    #discover          home: the swipe deck, invites, walkers to meet        #map           the snack map
    #plan              plan a walk          #plan/from/<place id>   starting at a place     #edit/<walk id>
    #walk/<walk id>    a walk               #walks[/tab]            my walks (upcoming, hosting, invites, pending, past)
    #people            connections          #u/<user id>            a walker's profile      #me     my profile
    #me/edit           edit my profile      #welcome                first-time profile set-up
    #journey  #perks  #admin  #safety (also public)  #notifications
The bare address opens #discover for members and #landing for visitors. Unknown addresses open #discover.
Visitors asking for a member page see the landing page; the address is remembered and opened after they sign in.
Links in templates are plain <a href="#map">; code calls router.go("walk/123_456").
"""
import anvil
import anvil.js
from anvil.js import window

from . import state

APP_NAME = "CityCrossers"
_r: dict = {"listening": False, "page": None}


def current_route():
    h = window.location.hash or ""
    h = h[1:] if h.startswith("#") else h
    try:
        return str(window.decodeURIComponent(h))
    except Exception:
        return h


def _pick(parts):
    """(Form class, kwargs, nav key, shell mode, tab title) for the address parts."""
    head = parts[0] if parts else ""
    arg = parts[1] if len(parts) > 1 else None
    route = "/".join(parts)
    if not state.logged_in():
        if head == "safety":
            from .Pages.Safety import Safety
            return Safety, {"public": True}, None, "landing", "Safety center · CityCrossers"
        if head not in ("", "landing", "discover"):
            state.after_login(route)
        from .Pages.Landing import Landing
        return Landing, {}, None, "landing", "CityCrossers: a walking club for long city walks"
    if state.me() is None:
        state.refresh_me()
    if head == "landing":
        from .Pages.Landing import Landing
        return Landing, {}, None, "landing", "CityCrossers: a walking club for long city walks"
    if head == "map":
        from .Pages.MapPage import MapPage
        return MapPage, {}, "map", "", "The snack map · CityCrossers"
    if head == "plan":
        from .Pages.WalkEditor import WalkEditor
        start = parts[2] if arg == "from" and len(parts) > 2 else None
        return WalkEditor, {"start_place": start}, "plan", "", "Plan a walk · CityCrossers"
    if head == "edit" and arg:
        from .Pages.WalkEditor import WalkEditor
        return WalkEditor, {"walk_id": arg}, "plan", "", "Edit your walk · CityCrossers"
    if head == "walk" and arg:
        from .Pages.WalkDetail import WalkDetail
        return WalkDetail, {"walk_id": arg}, "walks", "", "A walk · CityCrossers"
    if head == "walks":
        from .Pages.MyWalks import MyWalks
        return MyWalks, {"tab": arg}, "walks", "", "My walks · CityCrossers"
    if head == "people":
        from .Pages.People import People
        return People, {}, "people", "", "People · CityCrossers"
    if head == "u" and arg:
        from .Pages.Profile import Profile
        return Profile, {"user_id": arg}, "people", "", "A walker · CityCrossers"
    if head == "me" and arg == "edit":
        from .Pages.ProfileEdit import ProfileEdit
        return ProfileEdit, {}, None, "", "Edit profile · CityCrossers"
    if head == "me":
        from .Pages.Profile import Profile
        return Profile, {"user_id": None}, None, "", "My profile · CityCrossers"
    if head == "welcome":
        from .Pages.ProfileEdit import ProfileEdit
        return ProfileEdit, {"welcome": True}, None, "", "Welcome · CityCrossers"
    if head == "journey":
        from .Pages.Journey import Journey
        return Journey, {}, "journey", "", "My journey · CityCrossers"
    if head == "perks":
        from .Pages.Perks import Perks
        return Perks, {}, None, "", "Points & perks · CityCrossers"
    if head == "admin":
        from .Pages.Admin import Admin
        return Admin, {}, None, "", "Admin · CityCrossers"
    if head == "safety":
        from .Pages.Safety import Safety
        return Safety, {}, None, "", "Safety center · CityCrossers"
    if head == "notifications":
        from .Pages.Notifications import Notifications
        return Notifications, {}, None, "", "Notifications · CityCrossers"
    from .Pages.Discover import Discover
    return Discover, {}, "discover", "", "Discover walks · CityCrossers"


def show():
    """Open the page for the current address."""
    parts = [p for p in current_route().split("/") if p != ""]
    form_cls, kwargs, nav, mode, title = _pick(parts)
    window.document.title = title
    window.UI_READY = False
    old = _r["page"]
    if old is not None and hasattr(old, "leave"):
        old.leave()
    page = form_cls(**kwargs)
    _r["page"] = page
    anvil.open_form(page)
    shell = getattr(page, "layout", None)
    if shell is not None and hasattr(shell, "refresh"):
        shell.refresh(nav, mode)  # Anvil reuses the layout between pages: tell it who is signed in and which page is open
    window.scrollTo(0, 0)
    window.UI_READY = True  # tests and screenshots wait for this


def shell():
    page = _r["page"]
    s = getattr(page, "layout", None) if page is not None else None
    return s if s is not None and hasattr(s, "refresh") else None


def refresh_shell():
    """Redraw the header for the person now signed in (keeps the open page and its menu highlight)."""
    s = shell()
    if s is not None:
        s.refresh(False, False)


def go(route):
    """Go to an address like 'walk/123_456'. Same address again = reload the page."""
    route = route or ""
    if current_route() == route:
        show()
    else:
        window.location.hash = route


def replace_hash(route):
    """Change the address without opening anything (a page that switches its own tab)."""
    window.history.replaceState(None, "", "#" + route)


def after_sign_in(default="discover"):
    """Open the page a visitor was heading for (or default) once they have signed in."""
    go(state.after_login() or default)


def _on_hash(event):
    show()


def start():
    if not _r["listening"]:
        window.addEventListener("hashchange", anvil.js.report_exceptions(_on_hash))
        _r["listening"] = True
    show()
