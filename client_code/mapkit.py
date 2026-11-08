"""The map engine: a thin Leaflet wrapper (OpenStreetMap tiles, emoji pins, dotted routes). Components/MapView owns
one; pages talk to it through `map_view.engine`. Pins and popups are drawn by Leaflet from small HTML strings (the
engine's own drawing, every text escaped with ui.esc); everything around the map is Forms."""
from anvil.js import window

from . import state, ui

# OpenStreetMap's own tiles (CARTO's free basemaps started asking for an API key in Oct 2026).
# OSM tile policy: show the attribution, no bulk downloading, max zoom 19.
TILES = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
DEFAULT_CENTER = [51.5185, -0.1050]   # central London, where the demo walks live
DEFAULT_ZOOM = 13
NO_MAP = '<div class="cc-empty cc-map-off">🗺️ The map couldn’t load. Check your connection.</div>'


def pin_html(emoji, kind='rest', deal=False, number=None, draft=False):
    extra = '<span class="deal">%</span>' if deal else ''
    if number is not None:
        extra += '<span class="num">%d</span>' % number
    return '<div class="cc-pin %s%s"><span>%s</span>%s</div>' % (ui.esc(kind), " draft" if draft else "",
                                                                 ui.esc(emoji), extra)


class MapView(object):
    def __init__(self, el):
        """Draws into the DOM element `el` once start() is called (the component's show event: Leaflet needs the
        element on the page). Calls made before that are queued."""
        self.center = list(DEFAULT_CENTER)
        self.zoom = DEFAULT_ZOOM
        self.scroll_zoom = False
        self.on_click = state.loose(None)
        self.map = state.loose(None)  # a Leaflet map once start() ran
        self.layers = {}
        self._queue = []
        self._dom = el

    def start(self):
        if self.map is not None:
            window.setTimeout(lambda: self.map.invalidateSize(), 150)
            return
        L = getattr(window, "L", None)
        if L is None:
            self._dom.innerHTML = NO_MAP
            return
        self.map = L.map(self._dom, {'scrollWheelZoom': self.scroll_zoom, 'zoomControl': True})
        self.map.setView(self.center, self.zoom)
        # OSM answers "403 Access blocked" to tile requests without a Referer, so always send our origin.
        L.tileLayer(TILES, {'attribution': ATTRIBUTION, 'maxZoom': 19,
                            'referrerPolicy': 'strict-origin-when-cross-origin'}).addTo(self.map)
        self.map.on('click', self._clicked)
        queued, self._queue = self._queue, []
        for fn in queued:
            fn()
        # Leaflet needs a nudge when it appears inside animated containers (dialogs, tabs)
        window.setTimeout(lambda: self.map.invalidateSize(), 250)
        window.setTimeout(lambda: self.map.invalidateSize(), 700)

    def _clicked(self, e):
        if self.on_click:
            self.on_click(e.latlng.lat, e.latlng.lng)

    def when_ready(self, fn):
        if self.map is not None:
            fn()
        else:
            self._queue.append(fn)

    def set_picking(self, on):
        state.cls(self._dom, 'picking', bool(on))

    # -------------------------------------------------------------- layers
    def layer(self, name='default'):
        if name not in self.layers:
            self.layers[name] = window.L.layerGroup().addTo(self.map)
        return self.layers[name]

    def clear(self, name='default'):
        def go():
            if name in self.layers:
                self.layers[name].clearLayers()
        self.when_ready(go)

    # -------------------------------------------------------------- markers
    def add_marker(self, lat, lng, emoji='📍', kind='rest', popup=None, on_click=None, deal=False, number=None,
                   layer='default', tooltip=None, draft=False):
        def go():
            L = window.L
            icon = L.divIcon({'className': 'cc-pin-wrap', 'html': pin_html(emoji, kind, deal, number, draft),
                              'iconSize': [38, 38], 'iconAnchor': [19, 40], 'popupAnchor': [0, -38]})
            m = L.marker([lat, lng], {'icon': icon, 'riseOnHover': True, 'alt': tooltip or 'Map pin'})
            if popup is not None:
                m.bindPopup(popup, {'maxWidth': 280})
            if tooltip:
                m.bindTooltip(ui.esc(tooltip), {'direction': 'top', 'offset': [0, -36]})
            if on_click:
                m.on('click', lambda e: on_click())
            m.addTo(self.layer(layer))
        self.when_ready(go)

    def popup_el(self, html, actions=None):
        """A popup DOM element whose [data-act] buttons call Python (escape every text put into html)."""
        el = window.document.createElement('div')
        el.innerHTML = html
        if actions:
            def handler(e):
                t = e.target.closest('[data-act]')
                if t is None:
                    return
                fn = actions.get(t.getAttribute('data-act'))
                if fn:
                    e.preventDefault()
                    self.close_popups()
                    fn(t.getAttribute('data-arg'))
            el.addEventListener('click', handler)
        return el

    def close_popups(self):
        if self.map is not None:
            self.map.closePopup()

    def route(self, points, layer='route', color='#17A673', dashed=True):
        def go():
            L = window.L
            latlngs = [[p['lat'], p['lng']] for p in points]
            if len(latlngs) < 2:
                return
            L.polyline(latlngs, {'color': '#ffffff', 'weight': 9, 'opacity': 0.9, 'lineCap': 'round',
                                 'lineJoin': 'round'}).addTo(self.layer(layer))
            opts = {'color': color, 'weight': 5, 'opacity': 0.95, 'lineCap': 'round', 'lineJoin': 'round'}
            if dashed:
                opts['dashArray'] = '1 10'
                opts['weight'] = 6
            L.polyline(latlngs, opts).addTo(self.layer(layer))
        self.when_ready(go)

    def fit(self, points, padding=40, max_zoom=15):
        def go():
            pts = [[p['lat'], p['lng']] for p in points if p.get('lat') is not None]
            if not pts:
                return
            if len(pts) == 1:
                self.map.setView(pts[0], max_zoom)
            else:
                self.map.fitBounds(pts, {'padding': [padding, padding], 'maxZoom': max_zoom})
        self.when_ready(go)

    def set_view(self, lat, lng, zoom=None):
        self.center = [lat, lng]
        self.when_ready(lambda: self.map.setView([lat, lng], zoom or self.map.getZoom()))

    def locate(self, on_found=None):
        def ok(pos):
            lat, lng = pos.coords.latitude, pos.coords.longitude
            self.set_view(lat, lng, 14)
            self.clear('me')
            self.add_marker(lat, lng, '🙋', 'walk', layer='me', tooltip='You are here')
            if on_found:
                on_found(lat, lng)

        def err(e):
            state.toast("Couldn't get your location. Check your browser's location permission.", 'warning')

        try:
            window.navigator.geolocation.getCurrentPosition(ok, err, {'enableHighAccuracy': False, 'timeout': 10000})
        except Exception:
            state.toast("Location isn't available in this browser.", 'warning')
