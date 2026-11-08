from anvil import *

from ._anvil_designer import EndorseTemplate
from ... import state, ui


class Endorse(EndorseTemplate):
    """Endorse someone from the walk for a skill ("Pace keeper", "Snack scout" ...). Each tap toggles the
    endorsement on the server straight away; the chip shows which ones are on (this dialog only)."""

    def __init__(self, user_id=None, name="this walker", **properties):
        super().__init__(**properties)
        self.user_id, self.name = user_id, name
        self.on = set()
        self.title.text = "🏅 Endorse %s" % name
        state.heading(self.title, 2)
        self.skills_panel.add_event_handler("x-pick", self._pick)
        self._draw()

    def _draw(self):
        self.skills_panel.items = [{"key": i, "label": s, "on": i in self.on} for i, s in enumerate(ui.SKILLS)]

    def _pick(self, key=0, **event_args):
        skill = ui.SKILLS[int(key)]
        res = state.call("endorse", self.user_id, skill)
        if res is state.FAIL:
            return
        if res:
            self.on.add(int(key))
        else:
            self.on.discard(int(key))
        state.toast("Endorsed %s as %s" % (self.name.split(" ")[0], skill) if res else "Endorsement removed",
                    "ok" if res else "info")
        self._draw()

    @handle("done_button", "click")
    def done_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=True)
