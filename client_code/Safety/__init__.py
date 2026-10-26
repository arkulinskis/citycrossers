from ._anvil_designer import SafetyTemplate
from anvil import *

from .. import ui, state, dialogs

SECTIONS = [
  ("🧭", "Before you join", [
    "Read the walk page: distance, pace, stops and finish time. Pick walks within your comfort zone.",
    "Check the host's profile: walks completed, endorsements, verified badge.",
    "Say hi in the group chat. A quick hello makes meeting in person easier.",
    "Public walks are groups of 3 or more, and hosts approve who joins.",
  ]),
  ("📲", "Before you set off", [
    "Tap “Share my plan” on the walk page and send it to someone you trust.",
    "Add an emergency contact in your profile (only you can see it).",
    "Charge your phone and bring a small battery pack for long days.",
    "Pack water (roughly 1 L per 8 km), snacks, plasters, a layer and sun protection.",
  ]),
  ("👥", "On the walk", [
    "Meet at the public meeting point, never at someone's home or car.",
    "Stay with the group. Hosts regroup at every stop.",
    "You can leave at any time, no explanation needed. Just tell the host or the chat so nobody worries.",
    "Watch out for each other at road crossings, in crowds and after dark.",
    "Keep your home address and personal details to yourself until you know people well.",
  ]),
  ("🌗", "Weather & daylight", [
    "Check the walk-day forecast on the walk page. Hosts may reschedule for storms or extreme heat.",
    "In heat: start early, plan shady stops and drink before you're thirsty.",
    "In cold or rain: layers, waterproofs and an early hot-drink stop.",
    "Check sunset time and carry a light on long autumn and winter walks.",
  ]),
  ("🤝", "Community guidelines", [
    "Be kind, be inclusive, be on time (ish).",
    "Consent matters: ask before taking or sharing photos of people.",
    "No harassment, discrimination, unwanted advances or selling. Zero tolerance.",
    "Leave places better than you found them, and tip the cafés that host us.",
  ]),
  ("🚩", "If something goes wrong", [
    "In an emergency, call your local emergency number first: 999 (UK), 112 (EU), 911 (US).",
    "Use “Report” on any profile or walk page. Reports are confidential and reviewed by our team.",
    "Hosts can decline requests, and admins can suspend accounts that break the guidelines.",
  ]),
]


class Safety(SafetyTemplate):
  def __init__(self, public=False, **properties):
    self.init_components(**properties)
    pledged = bool((state.me or {}).get('safety_pledge')) if not public else False
    sections = ''
    for emo, title, tips in SECTIONS:
      items = ''.join(f'<li><span class="i">•</span><span>{ui.esc(t)}</span></li>' for t in tips)
      sections += f'<div class="cc-card"><h3>{emo} {ui.esc(title)}</h3><ul class="cc-safety-list">{items}</ul></div>'
    if public:
      cta = ('<div class="cc-card tint-green"><h3>Ready to walk?</h3><p>Join free and take the 20-second safety pledge before your first walk.</p>'
             '<a class="cc-btn" href="#landing">← Back to CityCrossers</a></div>')
      back = '<a href="#landing" class="small">← Back to CityCrossers</a>'
    elif pledged:
      cta = '<div class="cc-card tint-green"><h3>✅ You took the pledge</h3><p style="margin:0">Thanks for helping keep CityCrossers friendly and safe.</p></div>'
      back = ''
    else:
      cta = ('<div class="cc-card tint-sun"><h3>🛟 Take the safety pledge</h3><p>Six short promises. Takes 20 seconds, earns 10 points.</p>'
             + ui.btn('Take the pledge', 'pledge') + '</div>')
      back = ''
    self.html = f'''
    <div class="cc-page narrow">
      {back}
      <div class="cc-hello" style="background:linear-gradient(130deg,#E1F4FF,#E6F8EF);margin:10px 0 20px">
        <h1>🛟 Safety center</h1>
        <p style="margin:0;font-size:1.08rem">Walking with new people is the whole point of CityCrossers, so safety is part of every route.
          Here's how we look after each other.</p>
      </div>
      <div class="cc-alert danger" style="margin-bottom:18px"><span class="ico">🚨</span><span><b>In immediate danger?</b>
        Call your local emergency number now: 999 / 112 / 911.</span></div>
      <div class="cc-stack">{sections}{cta}
        <p class="small muted">CityCrossers doesn't run background checks on members. Use your own judgement, and leave any
          situation that doesn't feel right.</p></div>
    </div>'''
    ui.bind(self, {'pledge': self.pledge})

  def pledge(self, _=None):
    if dialogs.safety_pledge():
      state.go('discover')
