from anvil import *
import anvil.server

from ._anvil_designer import InviteTemplate
from ... import state


class Invite(InviteTemplate):
    """Invite connections (notification + email if they allow it) and/or one email address to a walk, or copy its
    link. Closes with True after sending."""

    def __init__(self, walk=None, friends=None, **properties):
        super().__init__(**properties)
        self.walk = walk or {}
        friends = friends or []
        self.friend_chips.setup([(f["id"], f["name"]) for f in friends], multi=True)
        self.friend_chips.visible = bool(friends)
        self.no_friends.visible = not friends
        self.link = anvil.server.get_app_origin() + "/#walk/" + self.walk.get("id", "")
        state.set_control_attr(self.email_box, "autocomplete", "email")

    @handle("yes_button", "click")
    def yes_button_click(self, **event_args):
        n = 0
        picked = self.friend_chips.value if self.friend_chips.visible else []
        if picked:
            res = state.call("invite_to_walk", self.walk["id"], picked)
            if res is state.FAIL:
                return
            n = res
        if (self.email_box.text or "").strip():
            msg = state.call("invite_by_email", self.walk["id"], self.email_box.text)
            if msg is state.FAIL:
                return
            state.toast(msg)
        if n:
            state.toast("Invited %d friend%s 💌" % (n, "s" if n != 1 else ""))
        self.raise_event("x-close-alert", value=True)

    @handle("copy_button", "click")
    def copy_button_click(self, **event_args):
        if state.copy_text(self.link):
            state.toast("Link copied. Paste it anywhere.")
        else:
            state.toast(self.link, "info", 8)

    @handle("no_button", "click")
    def no_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=False)
