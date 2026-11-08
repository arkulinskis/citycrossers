from anvil import *
import anvil
from anvil.js import window

from ._anvil_designer import LandingTemplate
from ... import router, state


class Landing(LandingTemplate):
    """#landing: the pitch (live route-map hero, Watch video, how it works, the break manifesto, perks, partners,
    safety, FAQ). Every page a visitor asks for shows this; Log in / Join open the sign-in dialog and then go where
    they were heading (or #welcome for a new account, #discover otherwise). The page's buttons carry data-act
    (one delegated click handler); the Watch video is cc.js's click-to-play."""

    def __init__(self, **properties):
        super().__init__(**properties)
        member = state.logged_in()
        self.auth_guest.visible = not member
        self.auth_member.visible = member

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
