from anvil import *

from ._anvil_designer import WalkRowTemplate
from ... import state, ui


class WalkRow(WalkRowTemplate):
    """A walk in one line, linking to #walk/<id>: the vibe tile, the title and one line under it.
    item = {walk, sub, plain?}: plain = just the emoji (profile "Hosting soon")."""

    def __init__(self, **properties):
        super().__init__(**properties)
        w, d = self.item["walk"], self.dom_nodes
        v = ui.vibe_of(w.get("vibe"))
        state.href(d["link"], "#walk/%s" % w["id"])
        d["sq"].className = "sq " + ("plain" if self.item.get("plain") else v[3])
        state.text(d["sq"], v[1])
        state.text(d["title"], w.get("title"))
        state.text(d["sub"], self.item.get("sub"))
