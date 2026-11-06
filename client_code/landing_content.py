"""Landing page markup. Buttons use data-act (handled in the Landing form). The hero is a live map: a walking route
marches across the whole city corner, the crew walks it, and the pitch sits in a card on the left."""

ROUTE = "M560 120 C 640 90, 700 170, 760 170 S 860 110, 920 160 S 980 290, 900 330 S 780 380, 840 470 S 1010 520, 1080 460 S 1160 330, 1220 300"

# The hero map: a whole city corner. A walking route marches across it (start, coffee, pastry, park, gelato, finish) and the
# crew (three avatars) walk it on a loop (SMIL animateMotion). Anchored right so phones still see the route.
HERO_SVG = f'''
<svg viewBox="0 0 1280 620" preserveAspectRatio="xMaxYMid slice" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <g stroke="#fff" stroke-width="12" stroke-linecap="round" fill="none" opacity=".95">
    <path d="M-20 120 L1300 40"/><path d="M-20 260 L1300 200"/><path d="M-20 420 L1300 380"/><path d="M-20 560 L1300 540"/>
    <path d="M140 -20 L200 640"/><path d="M420 -20 L450 640"/><path d="M700 -20 L690 640"/><path d="M980 -20 L1010 640"/><path d="M1200 -20 L1180 640"/>
  </g>
  <g stroke="#fff" stroke-width="5" stroke-linecap="round" fill="none" opacity=".8">
    <path d="M-20 190 L1300 120"/><path d="M-20 340 L1300 290"/><path d="M-20 490 L1300 460"/><path d="M280 -20 L320 640"/><path d="M560 -20 L570 640"/><path d="M840 -20 L850 640"/><path d="M1100 -20 L1090 640"/>
  </g>
  <ellipse cx="900" cy="250" rx="110" ry="64" fill="#BDEFD3"/><ellipse cx="300" cy="470" rx="120" ry="60" fill="#BDEFD3"/><ellipse cx="1180" cy="120" rx="80" ry="50" fill="#BDEFD3"/>
  <circle cx="880" cy="236" r="12" fill="#8EDDB3"/><circle cx="920" cy="264" r="15" fill="#8EDDB3"/><circle cx="280" cy="462" r="13" fill="#8EDDB3"/>
  <path d="M-20 400 C 200 360, 380 450, 600 410 S 900 330, 1300 380" stroke="#A6DDF7" stroke-width="34" fill="none" stroke-linecap="round"/>
  <g transform="translate(730 80) scale(.74) translate(-560 -90)">
  <path d="{ROUTE}" stroke="#fff" stroke-width="13" fill="none" stroke-linecap="round" opacity=".9"/>
  <path class="lp-route" d="{ROUTE}" stroke="#17A673" stroke-width="7" fill="none"/>
  <g font-size="22" text-anchor="middle" dominant-baseline="central">
    <g><circle cx="560" cy="120" r="23" fill="#DFF6EB" stroke="#17A673" stroke-width="3"/><text x="560" y="121">🚩</text></g>
    <g><circle cx="760" cy="170" r="23" fill="#FFE8DB" stroke="#FF7A3D" stroke-width="3"/><text x="760" y="171">☕</text></g>
    <g><circle cx="920" cy="160" r="23" fill="#FFE8DB" stroke="#FF7A3D" stroke-width="3"/><text x="920" y="161">🥐</text></g>
    <g><circle cx="900" cy="330" r="23" fill="#fff" stroke="#34B06A" stroke-width="3"/><text x="900" y="331">🌳</text></g>
    <g><circle cx="840" cy="470" r="23" fill="#FFE8DB" stroke="#FF7A3D" stroke-width="3"/><text x="840" y="471">🍦</text></g>
    <g><circle cx="1220" cy="300" r="23" fill="#DFF6EB" stroke="#17A673" stroke-width="3"/><text x="1220" y="301">🏁</text></g>
  </g>
  <g font-family="DM Sans, sans-serif" font-size="12" font-weight="700" fill="#33433E">
    <text x="736" y="210">coffee · 15% off</text><text x="944" y="146">lunch!</text><text x="810" y="512">treat stop</text><text x="1150" y="346">18 km done</text>
  </g>
  <g>
    <circle r="15" fill="#17A673" stroke="#fff" stroke-width="3"/><text font-family="DM Sans, sans-serif" font-size="10" font-weight="700" fill="#fff" text-anchor="middle" dy="4">MO</text>
    <circle r="15" cx="-22" cy="12" fill="#FF7A3D" stroke="#fff" stroke-width="3"/><text x="-22" y="12" font-family="DM Sans, sans-serif" font-size="10" font-weight="700" fill="#fff" text-anchor="middle" dy="4">TL</text>
    <circle r="15" cx="-6" cy="-24" fill="#3BB3F5" stroke="#fff" stroke-width="3"/><text x="-6" y="-24" font-family="DM Sans, sans-serif" font-size="10" font-weight="700" fill="#fff" text-anchor="middle" dy="4">PR</text>
    <animateMotion dur="24s" repeatCount="indefinite" path="{ROUTE}"/>
  </g>
  </g>
</svg>'''


def _av(initials, color):
  return (f'<span class="cc-av" style="width:30px;height:30px;font-size:11px;background-color:{color}">{initials}</span>')


AVATARS = (_av('MO', '#17A673') + _av('TL', '#FF7A3D') + _av('PR', '#3BB3F5') + _av('JW', '#E84A7F') +
           '<span class="cc-av cc-av-more" style="width:30px;height:30px">+4</span>')


def _demo_card(cls, grad, emoji, vibe, when, title, facts, match):
  return f'''
  <div class="cc-swipe {cls}" style="cursor:default">
    <div class="cover {grad}"><span class="vibe">{vibe}</span><span class="cc-match">{match}</span>
      <span class="when">{when}</span><span class="emo">{emoji}</span></div>
    <div class="body"><h3 style="margin-bottom:6px">{title}</h3><div class="facts">{facts}</div>
      <div class="cc-row" style="gap:8px"><span class="cc-av-stack">{AVATARS}</span><span class="small muted">8 going</span></div></div>
  </div>'''


DEMO_CARDS = (
  _demo_card('c1', 'grad-sun', '🌅', 'Sunrise stride', 'Sat · 05:45', 'Heath &amp; Hills', '<span class="cc-pill">12 km</span>', '78%') +
  _demo_card('c2', 'grad-mint', '🌳', 'Park hopper', 'Sun · 10:00', 'Five Parks, One Picnic', '<span class="cc-pill">16 km</span>', '84%') +
  _demo_card('c3', 'grad-peach', '🥐', 'Pastry pilgrimage', 'Sat · 09:30', 'South Bank Pastry Pilgrimage',
             '<span class="cc-pill">18 km</span><span class="cc-pill orange">🥐 3 food stops</span><span class="cc-pill">🐢 Stroll</span>', '92% match')
)

MARQUEE_ITEMS = ["Pastry pilgrimages", "Sunrise strides", "Canal crawls", "Bridge-to-bridge", "Market Saturdays",
                 "Park hoppers", "Night walks", "Coast-to-coast (of the city)", "History hunts", "Gelato detours"]
MARQUEE = ''.join(f'<span>{t} <i>✺</i></span>' for t in MARQUEE_ITEMS * 2)

HTML = f'''
<div class="lp">
  <div class="lp-wrap">
    <nav class="lp-nav">
      <a class="cc-logo" href="#landing"><img class="cc-logo-img" src="_/theme/logo.svg" alt=""><span>City<b>Crossers</b></span></a>
      <div class="links">
        <button data-act="scroll" data-arg="how">How it works</button>
        <button data-act="scroll" data-arg="manifesto">The break manifesto</button>
        <button data-act="scroll" data-arg="perks">Points &amp; perks</button>
        <button data-act="scroll" data-arg="safety">Safety</button>
        <button data-act="scroll" data-arg="faq">FAQ</button>
      </div>
      <div class="cc-row lp-auth">
        <button class="cc-btn ghost" data-act="login">Log in</button>
        <button class="cc-btn" data-act="signup">Join free</button>
      </div>
    </nav>
  </div>

  <section class="lp-hero">
    <div class="lp-mapbg">{HERO_SVG}</div>
    <div class="lp-wrap">
      <div class="lp-card">
        <div class="lp-eyebrow"><span class="new">NEW</span> Walking clubs, minus the sprinting</div>
        <h1>Long walks.<br><span class="hl">New people.</span><br><span class="snack">Snack stops</span> guaranteed.</h1>
        <p class="lead">CityCrossers is the walking club for people who'd rather stroll 20 km than sprint 5.
          Plan epic city crossings, drop pins for coffee and pastry stops, and fill your crew with friends, or
          friendly strangers who walk at your pace.</p>
        <div class="ctas">
          <button class="cc-btn lg" data-act="signup">Start walking. It's free</button>
          <button class="cc-btn ghost lg" data-act="scroll" data-arg="how">See how it works</button>
        </div>
        <div class="facts">
          <span class="cc-pill green">🥾 Walks of 10 to 30 km</span>
          <span class="cc-pill orange">☕ A break at least every 5 km</span>
          <span class="cc-pill sky">🐢 Nobody gets left behind</span>
        </div>
      </div>
    </div>
    <div class="lp-float a">☕ Coffee break in 1.2 km<span class="sub">Kettle &amp; Crumb · 15% off for crossers</span></div>
    <div class="lp-float b"><div class="cc-row" style="gap:8px"><span class="cc-av-stack">{AVATARS}</span></div>
      <span class="sub" style="margin-top:4px">Maya + 7 others are going</span></div>
    <div class="lp-float c">🏁 Walk complete · +48 pts<span class="sub">You met 4 new people today</span></div>
  </section>

  <div class="lp-marquee"><div class="track">{MARQUEE}</div></div>

  <section class="lp-section ytf" id="watch">
    <div class="lp-wrap"><div class="ytf-in">
      <div class="ytf-copy">
        <div class="lp-kicker ytf-kick"><svg viewBox="0 0 28 20" width="20" height="14" aria-hidden="true"><rect width="28" height="20" rx="5" fill="#FF0033"/><path d="M11.2 5.8v8.4l7.3-4.2z" fill="#fff"/></svg>Watch</div>
        <h2>See CityCrossers in about a minute.</h2>
        <p class="intro">A short video tour: swipe on group walks, plan a route with food stops, and meet your crew.</p>
        <a class="ytf-link" href="https://www.youtube.com/watch?v=iIDuAWF-BzI" target="_blank" rel="noopener">Watch on YouTube &#8599;</a>
      </div>
      <div>
        <div class="ytf-frame"><button type="button" class="ytf-cover" data-yt-film="iIDuAWF-BzI" data-yt-title="CityCrossers video" aria-label="Play the CityCrossers video (1:14)"><img src="_/theme/yt-cover.jpg" alt="" loading="lazy" decoding="async" width="960" height="540"><span class="ytf-play" aria-hidden="true"><svg viewBox="0 0 68 48" width="68" height="48"><path d="M66.5 7.7a8.5 8.5 0 0 0-6-6C55.3.3 34 .3 34 .3s-21.3 0-26.5 1.4a8.5 8.5 0 0 0-6 6C.1 13 .1 24 .1 24s0 11 1.4 16.3a8.5 8.5 0 0 0 6 6c5.2 1.4 26.5 1.4 26.5 1.4s21.3 0 26.5-1.4a8.5 8.5 0 0 0 6-6C67.9 35 67.9 24 67.9 24s0-11-1.4-16.3z" fill="#FF0033"/><path d="M45 24 27 14v20z" fill="#fff"/></svg></span><span class="ytf-len">1:14</span></button></div>
        <p class="ytf-note">The video loads from YouTube when you press play.</p>
      </div>
    </div></div>
  </section>

  <section class="lp-section" id="how">
    <div class="lp-wrap">
      <div class="lp-kicker">How it works</div>
      <h2>A running club for people who prefer walking (and second breakfast).</h2>
      <p class="intro">Every CityCrossers walk is a small adventure planned by someone like you: a route, a handful of
        stops worth stopping for, and a group that grows as people say yes.</p>
      <div class="lp-steps">
        <div class="lp-step"><span class="e">🗺️</span><h3>Plan the route</h3><p>Drop your meeting point, coffee stops,
          lunch spot and finish line on the map. We estimate distance, time and breaks.</p></div>
        <div class="lp-step"><span class="e">💌</span><h3>Invite your crew</h3><p>Ping your friends first. Not enough takers?
          Open the walk to the public and let like-minded walkers request a spot.</p></div>
        <div class="lp-step"><span class="e">💚</span><h3>Swipe to join</h3><p>Browse walks like you'd browse dates. Swipe right
          on the ones that match your pace, distance and snack philosophy.</p></div>
        <div class="lp-step"><span class="e">🥐</span><h3>Walk, snack, repeat</h3><p>Earn points for every kilometre, every review
          and every new face. Write it all down in your personal Journey.</p></div>
      </div>
    </div>
  </section>

  <section class="lp-section alt" id="manifesto">
    <div class="lp-wrap lp-manifesto">
      <div>
        <div class="lp-kicker">The break manifesto</div>
        <h2>We don't do suffering. We do pastries at kilometre seven.</h2>
        <div class="lp-rules">
          <div class="lp-rule"><span class="e">⏸️</span><div><b>A pause at least every 5 km</b><span>Routes are planned with breaks
            baked in. Literally, in most cases.</span></div></div>
          <div class="lp-rule"><span class="e">🍽️</span><div><b>Every walk has a food stop</b><span>Coffee, lunch, gelato. Hosts plan them,
            walkers vote on extras.</span></div></div>
          <div class="lp-rule"><span class="e">🐢</span><div><b>The group walks at the pace of its slowest snacker</b>
            <span>Pace is set upfront: Stroll, Steady or Brisk. No surprises, no sprint finishes.</span></div></div>
          <div class="lp-rule"><span class="e">🚪</span><div><b>Leave whenever you like</b><span>Bail at the bakery, no explanation
            needed. Every stop is an exit.</span></div></div>
        </div>
      </div>
      <div class="lp-day">
        <h3>☀️ A typical Saturday crossing</h3>
        <ul class="cc-timeline">
          <li><span class="bubble start">🚩</span><div class="what"><b>09:00 · Meet at Little Venice</b><span class="eta">Name tags, sunscreen, hellos</span></div></li>
          <li><span class="bubble cafe">☕</span><div class="what"><b>09:50 · Coffee on a boat</b><span class="eta">3.1 km in</span><span class="break">25 min break</span></div></li>
          <li><span class="bubble culture">🏛️</span><div class="what"><b>11:00 · Camden Lock</b><span class="eta">People-watching, obviously</span></div></li>
          <li><span class="bubble food">🥐</span><div class="what"><b>12:15 · Second breakfast</b><span class="eta">8.4 km in · 15% off for crossers</span><span class="break">40 min</span></div></li>
          <li><span class="bubble treat">🍦</span><div class="what"><b>15:10 · Gelato detour</b><span class="eta">Group vote: 6 to 1</span><span class="break">15 min</span></div></li>
          <li><span class="bubble finish">🏁</span><div class="what"><b>16:30 · Limehouse Basin</b><span class="eta">14.6 km · 8 new friends · 61 pts</span></div></li>
        </ul>
      </div>
    </div>
  </section>

  <section class="lp-section">
    <div class="lp-wrap">
      <div class="lp-kicker">Everything you need</div>
      <h2>Part map, part club, part diary.</h2>
      <div class="lp-features">
        <div class="lp-feature wide grad-mint"><span class="e">🗺️</span><h3>A living map of good stops</h3>
          <p>Cafés, bakeries, viewpoints, benches with a view and water refills, pinned by walkers who've been there.
          Propose new spots, vote on stops for upcoming walks, and spot the 🏷️ partner deals.</p></div>
        <div class="lp-feature grad-peach"><span class="e">💚</span><h3>Group dates, not dates</h3>
          <p>Swipe through walks that fit your pace. The match isn't one person, it's a whole crew.</p></div>
        <div class="lp-feature grad-sky"><span class="e">🪪</span><h3>Walker profiles</h3>
          <p>Headlines, stats and endorsements like “Pace keeper” or “Snack scout”. Think LinkedIn, if LinkedIn had pastries.</p></div>
        <div class="lp-feature grad-sun"><span class="e">📔</span><h3>Your life journey</h3>
          <p>Every walk, place and person in one timeline. Keep it private, or let people see what you love.</p></div>
        <div class="lp-feature grad-berry"><span class="e">💌</span><h3>Reviews for future you</h3>
          <p>Rate places and leave notes for yourself: “Order the cardamom bun. Sit upstairs.” Share the best ones publicly.</p></div>
      </div>
    </div>
  </section>

  <section class="lp-section">
    <div class="lp-wrap lp-split">
      <div class="lp-cards-demo">{DEMO_CARDS}</div>
      <div>
        <div class="lp-kicker">Swipe right on a Saturday</div>
        <h2>It's a match! With eight people and a croissant.</h2>
        <p class="intro">Your Discover deck is full of walks near you, ranked by how well they match your pace,
          preferred distance and interests. Swipe right to request a spot; the host says yes; you've got plans.</p>
        <p class="intro">No friends free this weekend? That's literally what we're for.</p>
        <button class="cc-btn orange lg" data-act="signup" style="margin-top:10px">Find my first walk</button>
      </div>
    </div>
  </section>

  <section class="lp-section alt" id="perks">
    <div class="lp-wrap lp-split">
      <div>
        <div class="lp-kicker">Points &amp; perks</div>
        <h2>Every kilometre counts. So does every croissant review.</h2>
        <p class="intro">Earn points for walking, hosting, meeting new people and helping others find great stops.
          Level up from Stroller to City Crosser and trade points for real perks.</p>
        <div class="lp-earn">
          <div><span>🥾 Finish a walk</span><b>15 pts + 2/km</b></div>
          <div><span>🎪 Host a walk</span><b>+25 pts</b></div>
          <div><span>👋 Each new person you meet</span><b>+5 pts</b></div>
          <div><span>⭐ Review a place</span><b>+8 to 12 pts</b></div>
          <div><span>📍 Your stop makes the route</span><b>+5 pts</b></div>
          <div><span>📔 Write in your journey</span><b>+5 pts</b></div>
        </div>
      </div>
      <div>
        <div class="lp-levels">
          <div class="lp-level"><span class="e">🚶</span><b>Stroller</b><span>0 pts</span></div>
          <div class="lp-level"><span class="e">🥾</span><b>Wanderer</b><span>100</span></div>
          <div class="lp-level"><span class="e">🌿</span><b>Rambler</b><span>300</span></div>
          <div class="lp-level"><span class="e">🧭</span><b>Pathfinder</b><span>700</span></div>
          <div class="lp-level"><span class="e">🔥</span><b>Trailblazer</b><span>1,500</span></div>
          <div class="lp-level"><span class="e">🏙️</span><b>City Crosser</b><span>3,000</span></div>
        </div>
        <div class="cc-card" style="margin-top:16px">
          <h4>🎁 Perks you can unlock</h4>
          <div class="cc-pills" style="margin-top:8px">
            <span class="cc-pill">☕ Free coffee at partner cafés</span><span class="cc-pill">🧦 Walking socks</span>
            <span class="cc-pill">🥐 Pastry passport</span><span class="cc-pill">⭐ Spotlight your walk</span>
            <span class="cc-pill">🎟️ Big Crossing early access</span><span class="cc-pill">🩹 Blister rescue kit</span>
          </div>
        </div>
      </div>
    </div>
  </section>

  <section class="lp-section">
    <div class="lp-wrap">
      <div class="lp-partner">
        <div>
          <div class="lp-kicker" style="color:#fff;opacity:.85">For cafés, bakeries &amp; delis</div>
          <h2>Hungry groups walk past your door every weekend.</h2>
          <p>Partner places show up on the CityCrossers map with a deal badge. Hosts plan routes around them, and walkers
            arrive in groups of eight, hungry, at a predictable time.</p>
          <button class="cc-btn sun lg" data-act="partner">Become a partner stop</button>
        </div>
        <div class="tags">
          <div class="tag"><span class="pct">15%</span>off pastries for crossers</div>
          <div class="tag"><span class="pct">2-for-1</span>gelato after 15 km</div>
          <div class="tag"><span class="pct">FREE</span>water refill, always</div>
        </div>
      </div>
    </div>
  </section>

  <section class="lp-section" id="safety">
    <div class="lp-wrap">
      <div class="lp-safety">
        <div class="lp-kicker" style="color:#13719F">Safety first, snacks second</div>
        <h2>Walking with new people should feel easy and safe.</h2>
        <p class="intro">Meeting strangers is the whole point, so we've built safety into every step. Please read these, and
          take our 20-second safety pledge before your first walk.</p>
        <div class="lp-safety-grid">
          <div><span class="e">📍</span><b>Public meeting points</b><span>Walks start at busy, public places. Never at someone's home.</span></div>
          <div><span class="e">👥</span><b>Groups, not one-on-ones</b><span>Public walks need room for 3+ walkers. Hosts approve requests.</span></div>
          <div><span class="e">🪪</span><b>Real profiles</b><span>Stats, endorsements from people who've walked together, and verified badges.</span></div>
          <div><span class="e">📲</span><b>Share your plans</b><span>One tap shares your route, timings and group with someone you trust.</span></div>
          <div><span class="e">🚩</span><b>Report &amp; get help</b><span>Report a walker or walk in two taps. Our team reviews every report.</span></div>
          <div><span class="e">🌤️</span><b>Daylight &amp; weather</b><span>Walk-day forecasts, daylight-friendly routes, and tips for heat, cold and rain.</span></div>
        </div>
        <p class="lp-disclaimer">⚠️ CityCrossers doesn't run background checks on members. Use your judgement, stay in
          the group, and leave whenever you like. In an emergency, call your local emergency number (999 / 112 / 911) first.</p>
        <button class="cc-btn ghost" data-act="safety" style="margin-top:8px">Read the full safety guide</button>
      </div>
    </div>
  </section>

  <section class="lp-section" id="faq">
    <div class="lp-wrap">
      <div class="lp-kicker">Questions</div>
      <h2>Good questions, asked while walking.</h2>
      <div class="lp-faq">
        <details><summary>How long are the walks?</summary><p>Most are 10 to 30 km and last a few hours to a full day, breaks
          included. Each walk shows distance, pace and estimated time before you join, so there are no surprises.</p></details>
        <details><summary>Do I need to be fit?</summary><p>If you can walk for an hour, you can join a Stroll-pace walk. Breaks
          every few kilometres keep it comfortable. Pick Steady or Brisk once you're hooked.</p></details>
        <details><summary>What if I want to leave early?</summary><p>Go for it. Every stop is an exit. Just let the host or the
          group chat know you've headed off so nobody worries.</p></details>
        <details><summary>Is it safe to walk with strangers?</summary><p>We do a lot to help: public meeting points, groups of
          3+, host approval, profiles with endorsements, reporting tools and a safety pledge. But we don't vet every member, so
          trust your instincts and share your plans with someone you know.</p></details>
        <details><summary>How do points and perks work?</summary><p>You earn points for walking, hosting, meeting new people,
          reviewing places and journaling. Points unlock levels and can be traded for perks like free coffee at partner cafés.</p></details>
        <details><summary>Can I bring my dog?</summary><p>On walks tagged “Dog friendly”, yes. Biscuit approves.</p></details>
        <details><summary>How much does it cost?</summary><p>Nothing. CityCrossers is free while we're growing. Partner cafés
          and future optional extras keep the lights on.</p></details>
      </div>
    </div>
  </section>

  <div class="lp-wrap">
    <div class="lp-final">
      <span class="deco" style="left:6%;top:18%">🥐</span><span class="deco" style="right:8%;top:22%">☕</span>
      <span class="deco" style="left:12%;bottom:14%">🌳</span><span class="deco" style="right:12%;bottom:12%">🍦</span>
      <h2>Your next 20 km starts with a coffee.</h2>
      <p>Join free, plan your first crossing, or swipe right on someone else's.</p>
      <button class="cc-btn sun lg" data-act="signup">Join CityCrossers</button>
    </div>
    <footer class="lp-footer">
      <div><b>CityCrossers</b> · walk like the ancestors, snack like the moderns.</div>
      <div><button data-act="safety">Safety</button><button data-act="scroll" data-arg="faq">FAQ</button>
        <button data-act="partner">Partners</button><a class="lp-idea" href="https://prepsto.com/#f/wzrzr2f" target="_blank" rel="noopener" data-prepsto-open>Submit feedback</a><button data-lk-open="overview">Privacy &amp; Terms</button><button data-act="login">Log in</button></div>
      <div class="lp-org">Contact developer: <a href="https://arkvital.com" target="_blank" rel="noopener">arkvital.com</a> · Parent company: <a href="https://addanapp.com" target="_blank" rel="noopener">addanapp.com</a></div>
    </footer>
  </div>
</div>
'''
