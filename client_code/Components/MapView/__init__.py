from anvil import *

from ._anvil_designer import MapViewTemplate
from ... import mapkit


class MapView(MapViewTemplate):
    """The map component: wraps the Leaflet engine (client_code/mapkit.py). The engine draws when the component is
    on the page (show event); anything asked of it earlier is queued."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.engine = mapkit.MapView(self.dom_nodes["map"])

    def setup(self, height="420px", center=None, zoom=None, on_click=None, scroll_zoom=False, picking=False):
        """Call before the map is shown: its height, where it starts, and what a click on the map does."""
        e = self.engine
        self.dom_nodes["map"].style.height = height
        if center:
            e.center = list(center)
        if zoom:
            e.zoom = zoom
        e.on_click, e.scroll_zoom = on_click, scroll_zoom
        e.set_picking(picking)
        return e

    @handle("", "show")
    def form_show(self, **event_args):
        self.engine.start()
