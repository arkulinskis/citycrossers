from anvil import *

from ._anvil_designer import PlaceFormTemplate
from ... import state, ui


class PlaceForm(PlaceFormTemplate):
    """Name + kind for a place on the map or a stop on a route, optionally with its own map to drop the pin
    (with_map: the walk's stops shown for context) and a description. Closes with
    {'name', 'kind', 'lat', 'lng', 'description'} or None."""

    def __init__(self, title="", subtitle="", lat=None, lng=None, kinds=None, default_kind="cafe", with_map=False,
                 context=None, ask_desc=False, name="", button="Add", **properties):
        super().__init__(**properties)
        self.title.text = title
        self.sub.text = subtitle
        self.sub.visible = bool(subtitle)
        state.heading(self.title, 2)
        self.default_kind = default_kind
        self.pick = {"lat": lat, "lng": lng}
        self.name_box.text = name or ""
        self.desc_field.visible = ask_desc
        self.yes_button.text = button
        kinds = kinds or ui.PLACE_KINDS
        self.kind_chips.setup([(k, "%s %s" % ui.kind(k)) for k in kinds], selected=default_kind, multi=False)
        self.map_part.visible = with_map
        self.with_map = with_map
        if with_map:
            center = [lat, lng] if lat is not None else None
            e = self.map_view.setup(height="320px", center=center, zoom=14, on_click=self._set_point, scroll_zoom=True,
                                    picking=True)
            context = context or []
            for i, p in enumerate(context):
                e.add_marker(p["lat"], p["lng"], ui.emoji(p.get("kind")), p.get("kind") or "rest", number=i + 1,
                             layer="ctx", tooltip=p.get("name"))
            if context:
                e.fit(context)
            e.route(context, layer="ctx")
            if lat is not None:
                e.when_ready(lambda: self._set_point(lat, lng))

    def _set_point(self, lat, lng):
        self.pick = {"lat": lat, "lng": lng}
        e = self.map_view.engine
        k = self.kind_chips.value or "rest"
        e.clear("pick")
        e.add_marker(lat, lng, ui.emoji(k), k, layer="pick", draft=True)
        self.pick_hint.text = "📍 Spot picked. Click again to move it."

    @handle("yes_button", "click")
    def yes_button_click(self, **event_args):
        nm = (self.name_box.text or "").strip()
        if len(nm) < 2:
            state.toast("Give it a name.", "warning")
            return
        if self.pick["lat"] is None:
            state.toast("Click the map to drop the pin.", "warning")
            return
        self.raise_event("x-close-alert", value={
            "name": nm, "kind": self.kind_chips.value or self.default_kind, "lat": self.pick["lat"],
            "lng": self.pick["lng"], "description": (self.desc_box.text or "").strip()})

    @handle("no_button", "click")
    def no_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=None)

    @handle("name_box", "pressed_enter")
    def name_box_pressed_enter(self, **event_args):
        self.yes_button_click()
