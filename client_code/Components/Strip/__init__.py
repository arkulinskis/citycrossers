from anvil import *
from anvil.js import window

from ._anvil_designer import StripTemplate
from ... import ui


class Strip(StripTemplate):
    """The stop strip: start --- coffee --- food --- finish (a small drawing). show(stops, limit=8)."""

    def __init__(self, **properties):
        super().__init__(**properties)

    def show(self, stops, limit=8):
        box = self.dom_nodes["strip"]
        box.textContent = ""
        stops = stops or []
        items = stops if len(stops) <= limit else stops[:limit - 1] + [stops[-1]]
        names = []
        for i, s in enumerate(items):
            k = s.get("kind") or "rest"
            if i:
                seg = window.document.createElement("span")
                seg.className = "seg"
                box.appendChild(seg)
            dot = window.document.createElement("span")
            dot.className = "dot " + k
            dot.textContent = ui.emoji(k)
            dot.setAttribute("title", s.get("name") or "")
            box.appendChild(dot)
            names.append(s.get("name") or ui.kind(k)[1])
        box.setAttribute("role", "img")
        box.setAttribute("aria-label", "Stops: " + ", ".join(names) if names else "No stops yet")
