"""Walk-day forecast from Open-Meteo (free, no API key)."""
import anvil.server
import anvil.http
import anvil.tz
from anvil.tables import app_tables

from .common import current_user, by_id, aware, now

CODES = {0: ("☀️", "Clear skies"), 1: ("🌤️", "Mostly sunny"), 2: ("⛅", "Partly cloudy"), 3: ("☁️", "Overcast"),
         45: ("🌫️", "Foggy"), 48: ("🌫️", "Frosty fog"), 51: ("🌦️", "Light drizzle"), 53: ("🌦️", "Drizzle"),
         55: ("🌧️", "Heavy drizzle"), 61: ("🌦️", "Light rain"), 63: ("🌧️", "Rain"), 65: ("🌧️", "Heavy rain"),
         71: ("🌨️", "Light snow"), 73: ("🌨️", "Snow"), 75: ("❄️", "Heavy snow"), 80: ("🌦️", "Showers"),
         81: ("🌧️", "Heavy showers"), 82: ("⛈️", "Violent showers"), 95: ("⛈️", "Thunderstorms"),
         96: ("⛈️", "Thunder & hail"), 99: ("⛈️", "Thunder & hail")}


def _advice(temp, rain, code):
  tips = []
  if rain is not None and rain >= 50:
    tips.append("Pack a waterproof, and maybe pick indoor food stops.")
  elif rain is not None and rain >= 25:
    tips.append("A light rain layer wouldn't hurt.")
  if temp is not None and temp >= 24:
    tips.append("Hot one: bring 2 L of water and plan shady breaks.")
  elif temp is not None and temp <= 5:
    tips.append("Chilly: layers, gloves, and a hot-drink stop early on.")
  if code in (95, 96, 99):
    tips.append("Thunderstorms forecast. Hosts, consider rescheduling.")
  if not tips:
    tips.append("Looks like proper walking weather.")
  return " ".join(tips)


@anvil.server.callable(require_user=True)
def walk_forecast(walk_id):
  current_user()
  w = by_id(app_tables.walks, walk_id)
  if w is None or w['lat'] is None or w['start'] is None:
    return None
  start = aware(w['start']).astimezone(anvil.tz.tzutc())
  days = (start - now()).total_seconds() / 86400.0
  if days > 15 or days < -1:
    return None
  day = start.strftime('%Y-%m-%d')
  url = ("https://api.open-meteo.com/v1/forecast?latitude=%.4f&longitude=%.4f"
         "&hourly=temperature_2m,precipitation_probability,weather_code&timezone=UTC"
         "&start_date=%s&end_date=%s" % (w['lat'], w['lng'], day, day))
  try:
    data = anvil.http.request(url, json=True, timeout=8)
  except Exception as e:
    print("forecast failed", e)
    return None
  hourly = data.get('hourly') or {}
  times = hourly.get('time') or []
  target = start.strftime('%Y-%m-%dT%H:00')
  idx = times.index(target) if target in times else (start.hour if start.hour < len(times) else 0)
  try:
    temp = hourly['temperature_2m'][idx]
    rain = hourly['precipitation_probability'][idx]
    code = hourly['weather_code'][idx]
    temps = [t for t in hourly['temperature_2m'][idx:idx + 8] if t is not None]
  except (KeyError, IndexError, TypeError):
    return None
  emoji, label = CODES.get(code, ("🌡️", "Mixed weather"))
  return {'emoji': emoji, 'label': label, 'temp': temp, 'rain': rain,
          'high': max(temps) if temps else temp, 'low': min(temps) if temps else temp,
          'advice': _advice(temp, rain, code)}
