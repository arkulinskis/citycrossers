"""A thin Leaflet wrapper for Anvil (bright CARTO Voyager tiles, emoji pins)."""
import anvil.js
from anvil.js import window

from . import ui

TILES = 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png'
ATTRIBUTION = ('&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> '
               '&copy; <a href="https://carto.com/attributions">CARTO</a>')
DEFAULT_CENTER = [51.5185, -0.1050]   # central London, where the demo walks live
DEFAULT_ZOOM = 13


class MapView(object):
  def __init__(self, height='420px', center=None, zoom=None, on_click=None, scroll_zoom=False, classes=''):
    self.height = height
    self.center = center or DEFAULT_CENTER
    self.zoom = zoom or DEFAULT_ZOOM
    self.on_click = on_click
    self.scroll_zoom = scroll_zoom
    self.map = None
    self.layers = {}
    self._queue = []
    self.component = ui.H(f'<div class="cc-map {classes}" style="height:{height}"></div>')
    self.component.add_event_handler('show', self._on_show)

  # -------------------------------------------------------------- setup
  def _el(self):
    return ui.dom(self.component).querySelector('.cc-map')

  def _on_show(self, **e):
    if self.map is not None:
      window.setTimeout(lambda: self.map.invalidateSize(), 150)
      return
    try:
      L = window.L
    except Exception:
      L = None
    if L is None:
      self._el().innerHTML = '<div class="cc-empty" style="margin:20px">🗺️ The map couldn\'t load. Check your connection.</div>'
      return
    self.map = L.map(self._el(), {'scrollWheelZoom': self.scroll_zoom, 'zoomControl': True})
    self.map.setView(self.center, self.zoom)
    L.tileLayer(TILES, {'attribution': ATTRIBUTION, 'maxZoom': 19, 'subdomains': 'abcd'}).addTo(self.map)
    if self.on_click:
      self.map.on('click', self._clicked)
    queued, self._queue = self._queue, []
    for fn in queued:
      fn()
    # Leaflet needs a nudge when it appears inside animated containers (modals, tabs)
    window.setTimeout(lambda: self.map.invalidateSize(), 250)
    window.setTimeout(lambda: self.map.invalidateSize(), 700)

  def _clicked(self, e):
    self.on_click(e.latlng.lat, e.latlng.lng)

  def when_ready(self, fn):
    if self.map is not None:
      fn()
    else:
      self._queue.append(fn)

  def set_picking(self, on):
    el = self._el()
    if on:
      el.classList.add('picking')
    else:
      el.classList.remove('picking')

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
  @staticmethod
  def pin_html(emoji, kind='rest', deal=False, number=None, draft=False):
    extra = '<span class="deal">%</span>' if deal else ''
    if number is not None:
      extra += f'<span class="num">{number}</span>'
    return f'<div class="cc-pin {kind}{" draft" if draft else ""}"><span>{emoji}</span>{extra}</div>'

  def add_marker(self, lat, lng, emoji='📍', kind='rest', popup=None, on_click=None, deal=False, number=None,
                 layer='default', tooltip=None, draft=False):
    def go():
      L = window.L
      icon = L.divIcon({'className': 'cc-pin-wrap', 'html': self.pin_html(emoji, kind, deal, number, draft),
                        'iconSize': [38, 38], 'iconAnchor': [19, 40], 'popupAnchor': [0, -38]})
      m = L.marker([lat, lng], {'icon': icon, 'riseOnHover': True})
      if popup is not None:
        m.bindPopup(popup, {'maxWidth': 280})
      if tooltip:
        m.bindTooltip(tooltip, {'direction': 'top', 'offset': [0, -36]})
      if on_click:
        m.on('click', lambda e: on_click())
      m.addTo(self.layer(layer))
    self.when_ready(go)

  def popup_el(self, html, actions=None):
    """Build a popup DOM element whose [data-act] buttons call Python."""
    el = window.document.createElement('div')
    el.innerHTML = html
    if actions:
      def handler(e):
        t = e.target.closest('[data-act]')
        if t is None:
          return
        fn = actions.get(t.getAttribute('data-act'))
        if fn:
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
    self.when_ready(lambda: self.map.setView([lat, lng], zoom or self.map.getZoom()))

  def locate(self, on_found=None):
    def ok(pos):
      lat, lng = pos.coords.latitude, pos.coords.longitude
      self.set_view(lat, lng, 14)
      self.add_marker(lat, lng, '🙋', 'walk', layer='me', tooltip='You are here')
      if on_found:
        on_found(lat, lng)

    def err(e):
      ui.toast("Couldn't get your location. Check your browser's location permission.", 'warning')

    try:
      window.navigator.geolocation.getCurrentPosition(ok, err, {'enableHighAccuracy': False, 'timeout': 10000})
    except Exception:
      ui.toast("Location isn't available in this browser.", 'warning')
