from anvil import *

from ._anvil_designer import StarsTemplate
from ... import state


class Stars(StarsTemplate):
    """Tap to rate, 1 to 5 stars. .value is the rating (0 = not rated yet)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self._value = 0
        self._draw()

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self._value = int(v or 0)
        self._draw()

    def star_click(self, event):
        el = event.currentTarget
        self.value = int(el.getAttribute("data-n"))

    def _draw(self):
        for i in range(1, 6):
            el = state.loose(self.dom_nodes)["s%d" % i]
            state.cls(el, "on", i <= self._value)
            el.setAttribute("aria-pressed", "true" if i == self._value else "false")
