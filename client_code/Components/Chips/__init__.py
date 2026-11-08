from anvil import *

from ._anvil_designer import ChipsTemplate
from ... import state


class Chips(ChipsTemplate):
    """Pick one (multi=False) or several chips. setup(options, selected=None, multi=True, color="", limit=None,
    on_change=None): options are values or (value, label) pairs. .value = the list (multi) or the one value."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.options, self.selected, self.multi, self.color, self.limit = [], [], True, "", None
        self.on_change = state.loose(None)
        self.panel.add_event_handler("x-pick", self._pick)

    def setup(self, options, selected=None, multi=True, color="", limit=None, on_change=None):
        self.options = [(o[0], o[1]) if isinstance(o, (list, tuple)) else (o, o) for o in options]
        self.multi, self.color, self.limit, self.on_change = multi, color, limit, on_change
        if multi:
            self.selected = list(selected or [])
        else:
            self.selected = [selected] if selected not in (None, "") else []
        self._draw()
        return self

    def _draw(self, focus=None):
        cls = "cc-chip " + self.color if self.color else "cc-chip"
        self.panel.items = [{"key": i, "label": label, "on": val in self.selected, "cls": cls}
                            for i, (val, label) in enumerate(self.options)]

    def _pick(self, key=0, **event_args):
        val = self.options[int(key)][0]
        if self.multi:
            if val in self.selected:
                self.selected.remove(val)
            else:
                if self.limit and len(self.selected) >= self.limit:
                    state.toast("Pick up to %d." % self.limit, "warning")
                    return
                self.selected.append(val)
        else:
            self.selected = [val]
        self._draw()
        if self.on_change:
            self.on_change(self.value)

    @property
    def value(self):
        return list(self.selected) if self.multi else (self.selected[0] if self.selected else None)
