from anvil import *

from ._anvil_designer import LedgerRowTemplate
from ... import state


class LedgerRow(LedgerRowTemplate):
    """A line in the points history (reason, when, +/- points) or one of my perk codes (tap to copy).
    item = {left, sub, right?, plus?, code?}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it, d = self.item, self.dom_nodes
        state.text(d["left"], it.get("left"))
        state.text(d["sub"], it.get("sub"))
        code = it.get("code")
        state.text(d["right"], it.get("right"))
        d["right"].className = "plus" if it.get("plus") else "minus"
        state.show(d["right"], not code)
        state.text(d["code"], code)
        state.show(d["code"], bool(code))
        if code:
            d["code"].setAttribute("aria-label", "Copy code %s" % code)

    def code_click(self, event):
        code = self.item.get("code")
        state.toast("Code copied 📋" if state.copy_text(code) else code)
