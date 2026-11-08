from anvil import *

from ._anvil_designer import AdminUserRowTemplate
from ... import state, ui


class AdminUserRow(AdminUserRowTemplate):
    """A member for admins: name + email, level, walks and km, joined; Verify, Make admin, Suspend / Reinstate.
    item = a user from admin_overview; buttons raise x-user(uid=..., flag="verified" | "admin" | "enabled")."""

    def __init__(self, **properties):
        super().__init__(**properties)
        u, d = self.item, self.dom_nodes
        self.person.show(u, sub=u.get("email"), size=34)
        lvl = u.get("level") or {}
        state.text(d["level"], "%s %s" % (lvl.get("emoji", "🚶"), lvl.get("name", "Stroller")))
        state.text(d["walks"], "%s · %s" % (u.get("walks_count", 0), ui.km(u.get("km_total"))))
        state.text(d["joined"], ui.ago(u.get("signed_up")))
        self.verify_button.text = "✔ Verified" if u.get("verified") else "Verify"
        self.verify_button.role = ["cc-btn", "soft" if u.get("verified") else "ghost", "sm"]
        self.admin_button.text = "★ Admin" if u.get("is_admin") else "Make admin"
        self.admin_button.role = ["cc-btn", "sun" if u.get("is_admin") else "ghost", "sm"]
        self.enabled_button.text = "Suspend" if u.get("enabled") else "Reinstate"
        self.enabled_button.role = ["cc-btn", "danger", "sm"] if u.get("enabled") else ["cc-btn", "sm"]

    def _raise(self, flag):
        self.parent.raise_event("x-user", uid=self.item["id"], flag=flag)

    @handle("verify_button", "click")
    def verify_button_click(self, **event_args):
        self._raise("verified")

    @handle("admin_button", "click")
    def admin_button_click(self, **event_args):
        self._raise("admin")

    @handle("enabled_button", "click")
    def enabled_button_click(self, **event_args):
        self._raise("enabled")
