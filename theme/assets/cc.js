/* CityCrossers browser helpers: swipe cards, emoji confetti, clipboard. */
window.cc = (function () {
  function swipe(el, cb) {
    var startX = 0, startY = 0, dx = 0, dragging = false;
    el.style.touchAction = 'pan-y';
    el.addEventListener('pointerdown', function (e) {
      if (e.target.closest('button, a, input, textarea, select')) return;
      dragging = true; startX = e.clientX; startY = e.clientY; dx = 0;
      try { el.setPointerCapture(e.pointerId); } catch (err) {}
      el.style.transition = 'none';
    });
    el.addEventListener('pointermove', function (e) {
      if (!dragging) return;
      dx = e.clientX - startX;
      var dy = (e.clientY - startY) * 0.15;
      el.style.transform = 'translate(' + dx + 'px,' + dy + 'px) rotate(' + (dx / 20) + 'deg)';
      el.classList.toggle('lean-right', dx > 50);
      el.classList.toggle('lean-left', dx < -50);
    });
    function end() {
      if (!dragging) return;
      dragging = false;
      el.style.transition = '';
      if (Math.abs(dx) > 110) {
        fly(el, dx > 0 ? 'right' : 'left', cb);
      } else {
        el.style.transform = '';
        el.classList.remove('lean-right', 'lean-left');
      }
    }
    el.addEventListener('pointerup', end);
    el.addEventListener('pointercancel', end);
  }

  function fly(el, dir, cb) {
    el.classList.add(dir === 'right' ? 'lean-right' : 'lean-left');
    el.style.transition = 'transform .38s cubic-bezier(.3,.7,.4,1), opacity .38s ease';
    el.style.transform = 'translate(' + (dir === 'right' ? 700 : -700) + 'px, 40px) rotate(' + (dir === 'right' ? 26 : -26) + 'deg)';
    el.style.opacity = '0';
    setTimeout(function () { if (cb) cb(dir); }, 340);
  }

  function confetti(emojis) {
    emojis = emojis || ['🥐', '☕', '🍦', '🎉', '🥾', '🌳'];
    var layer = document.createElement('div');
    layer.className = 'cc-confetti';
    for (var i = 0; i < 28; i++) {
      var s = document.createElement('span');
      s.textContent = emojis[i % emojis.length];
      var angle = Math.random() * Math.PI * 2;
      var dist = 120 + Math.random() * 260;
      s.style.setProperty('--x', Math.cos(angle) * dist + 'px');
      s.style.setProperty('--y', (Math.sin(angle) * dist - 120) + 'px');
      s.style.setProperty('--r', (Math.random() * 720 - 360) + 'deg');
      s.style.animationDelay = (Math.random() * 0.15) + 's';
      layer.appendChild(s);
    }
    document.body.appendChild(layer);
    setTimeout(function () { layer.remove(); }, 1800);
  }

  function fallbackCopy(text) {
    var t = document.createElement('textarea');
    t.value = text; t.style.position = 'fixed'; t.style.opacity = '0';
    document.body.appendChild(t); t.select();
    var ok = false;
    try { ok = document.execCommand('copy'); } catch (e) {}
    document.body.removeChild(t);
    return ok;
  }

  function copy(text) {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).catch(function () { fallbackCopy(text); });
      return true;
    }
    return fallbackCopy(text);
  }

  function scrollTo(id) {
    var el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  return { swipe: swipe, fly: fly, confetti: confetti, copy: copy, scrollTo: scrollTo };
})();
