from anvil import *
import anvil
from anvil.js import window

from ._anvil_designer import LandingTemplate
from ... import router, state, ui


class Landing(LandingTemplate):
    """#landing: the pitch (live route-map hero, Watch video, how it works, the break manifesto, perks, partners,
    safety, FAQ). Every page a visitor asks for shows this; Log in / Join open the sign-in dialog and then go where
    they were heading (or #welcome for a new account, #discover otherwise). The page's buttons carry data-act
    (one delegated click handler); the Watch video is cc.js's click-to-play. "Open walks this week" (public_walks:
    up to 3 real public walks with spots, each opening its public walk page) loads after the page draws and stays
    hidden when there are none."""

    def __init__(self, **properties):
        super().__init__(**properties)
        member = state.logged_in()
        self.auth_guest.visible = not member
        self.auth_member.visible = member
        self.open_box.visible = False
        self._shown = False

    @handle("", "show")
    def form_show(self, **event_args):
        if not self._shown:
            self._shown = True
            window.setTimeout(self._load_open, 300)

    def _load_open(self):
        walks = state.call("public_walks", 3, quiet=True)
        if walks is state.FAIL or not walks:
            return
        rows = []
        for w in walks:
            n, left = w["food_stops"], w["spots_left"]
            rows.append({"walk": w, "sub": "%s · %s · %d food stop%s · %d spot%s left" % (
                ui.fmt_when(w["start"]), ui.km(w["distance_km"]), n, "" if n == 1 else "s", left, "" if left == 1 else "s")})
        self.open_panel.items = rows
        self.open_box.visible = True

    def lp_click(self, event):
        el = event.target.closest("[data-act]")
        if el is None:
            return
        act, arg = el.getAttribute("data-act"), el.getAttribute("data-arg")
        if act in ("signup", "login"):
            self.auth(act)
        elif act == "scroll":
            window.cc.scrollTo(arg)
        elif act == "safety":
            router.go("safety")
        elif act == "partner":
            from ...Dialogs.Partner import Partner
            anvil.alert(Partner(), buttons=[], role="app-dialog")

    def auth(self, mode):
        if state.logged_in():
            router.go("discover")
            return
        if state.ask_login(mode):
            router.after_sign_in()
