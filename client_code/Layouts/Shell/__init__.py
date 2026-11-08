from anvil import *
import anvil.js
from anvil.js import window

from ._anvil_designer import ShellTemplate
from ... import auth, avatar, router, state


class Shell(ShellTemplate):
    """The frame around every page: the header (six places, points chip, notifications bell, the walker menu), the
    footer (Submit feedback, Privacy & Terms, Contact developer, Parent company) and, on phones, the nav as a bottom
    tab bar (CSS). Pages use it with <anvil-form layout="CityCrossers.Layouts.Shell">.

    Anvil keeps ONE Shell while pages come and go, so everything that depends on who is signed in or which page is
    open is drawn in refresh(nav, mode), which router.show() calls after every page change.
    mode "landing" hides the header and footer (the landing page and the public safety page draw their own).
    The bell's count is polled here every 60 s (poll_counts) while someone is signed in."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self._nav, self._mode, self._open = None, "landing", False
        self._links = {"discover": self.nav_discover, "map": self.nav_map, "plan": self.nav_plan,
                       "walks": self.nav_walks, "people": self.nav_people, "journey": self.nav_journey}
        self._outside = anvil.js.report_exceptions(self._close_menu_outside)
        self._keys = anvil.js.report_exceptions(self._key)
        self.refresh(None, "landing")

    def refresh(self, nav, mode):
        """nav/mode False = keep the current ones (a redraw after sign-in, a profile change or new counts)."""
        if nav is not False:
            self._nav = nav
        if mode is not False:
            self._mode = mode or ""
            self._menu(False)
        me = state.me() if state.logged_in() else None
        self.shell.classes["landing-mode"] = self._mode == "landing" or not me
        for key, link in self._links.items():
            link.classes["active"] = key == self._nav
            state.set_attr(link, "aria-current", "page" if key == self._nav else None)
        self.menu_admin.visible = bool(me and me.get("is_admin"))
        d = self.dom_nodes
        if me:
            avatar.paint(d["me_av"], me, 40)
            state.text(d["menu_name"], me.get("name") or "You")
            lvl = me.get("level") or {}
            state.text(d["menu_level"], "%s %s · %s lifetime pts" % (lvl.get("emoji", ""), lvl.get("name", ""),
                                                                      me.get("lifetime_points", 0)))
            state.text(d["points"], me.get("points", 0))
        n = state.counts().get("notifications", 0) if me else 0
        state.text(d["badge"], n if n < 100 else "99+")
        state.show(d["badge"], bool(n))
        self.poll_timer.interval = 60 if me else 0

    # ---- notifications count
    @handle("poll_timer", "tick")
    def poll_timer_tick(self, **event_args):
        if not state.logged_in():
            self.poll_timer.interval = 0
            return
        res = state.call("poll_counts", quiet=True)
        if res is not state.FAIL and res:
            state.set_counts(res)

    # ---- the walker menu
    def _menu(self, on):
        self._open = bool(on)
        self.me_box.classes["open"] = self._open

    def me_click(self, event):
        self._menu(not self._open)

    def logout_click(self, event):
        self._menu(False)
        auth.sign_out()
        state.set_counts({"notifications": 0})
        state.toast("See you on the next walk 👋")
        router.go("landing")

    def _close_menu_outside(self, event):
        if self._open and not event.target.closest(".cc-me"):
            self._menu(False)

    def _key(self, event):
        if event.key == "Escape":
            self._menu(False)

    @handle("", "show")
    def form_show(self, **event_args):
        window.document.addEventListener("click", self._outside, True)
        window.document.addEventListener("keydown", self._keys)

    @handle("", "hide")
    def form_hide(self, **event_args):
        window.document.removeEventListener("click", self._outside, True)
        window.document.removeEventListener("keydown", self._keys)
