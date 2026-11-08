/* Smoke test (tools/ui_test.py runs it at 1280 px and at 390 px): every page address opens without errors, is not
   empty and doesn't scroll sideways. Signed out (landing + Watch section + footer links, the public safety page, a
   member page = the landing page), then as a new walker signed up through the dialog (welcome, discover + the pledge
   dialog, map, plan, a walk + its host's profile, someone else's walk in the editor, my walks, people, me, edit,
   journey + the entry dialog, perks, safety, notifications, admin = "Admins only"), then as admin (every Admin tab).
   Python/JS errors are caught by ui_test.py from the browser log. Resolves to {ok, log}. */
(async function () {
  const log = [], bad = [];
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  async function until(fn, what, ms) {
    const end = Date.now() + (ms || 20000);
    while (Date.now() < end) { try { const v = fn(); if (v) return v; } catch (e) {} await sleep(150); }
    throw new Error('timed out waiting for: ' + what);
  }
  const $ = (s) => document.querySelector(s), $$ = (s) => Array.from(document.querySelectorAll(s));
  const errs = [];
  window.addEventListener('error', (e) => errs.push(String(e.message || e)));
  const visible = (el) => !!el && el.getClientRects().length > 0;
  function type(input, value) {
    input.focus(); input.value = value;
    input.dispatchEvent(new Event('input', { bubbles: true })); input.dispatchEvent(new Event('change', { bubbles: true }));
  }
  function button(re, root) {
    const sel = (root || '').split(',').map((r) => (r.trim() + ' button').trim()).join(', ');
    return $$(sel).find((b) => re.test(b.textContent.trim()) && visible(b));
  }
  const modal = () => $$('.modal, .anvil-modal').find((m) => visible(m) && m.innerText.trim().length > 5);
  const mainText = () => ($('.cc-main') ? $('.cc-main').innerText.trim() : '');
  function check(name, expect) {
    const text = mainText();
    const w = document.documentElement.scrollWidth, vw = screen.width <= 500 ? screen.width : window.innerWidth;
    const problems = [];
    if (text.length < 40) problems.push('empty page');
    if (expect && !new RegExp(expect.source, 'i').test(text)) problems.push('missing ' + expect);
    if (w > vw + 1) {
      const wide = $$('body *').filter((e) => { const r = e.getBoundingClientRect(); return r.width && r.right > vw + 1; })
        .slice(0, 3).map((e) => e.tagName.toLowerCase() + '.' + String(e.className).split(' ').slice(0, 2).join('.'));
      problems.push('scrolls sideways (' + w + ' > ' + vw + ') ' + wide.join(' '));
    }
    if (errs.length) problems.push('errors: ' + errs.splice(0).join(' / '));
    if (problems.length) bad.push(name + ': ' + problems.join('; '));
    log.push((problems.length ? 'BAD  ' : 'ok   ') + name);
  }
  async function open(hash, expect, ready) {
    if (location.hash !== hash) window.UI_READY = false;
    location.hash = hash;
    await until(() => window.UI_READY && location.hash === hash, hash, 30000);
    if (ready) await until(ready, hash + ' content', 30000);
    await sleep(800);
    check(hash, expect);
  }
  async function closeModal() {
    const m = modal();
    if (!m) return;
    const close = $$('.modal button, .anvil-modal button').find((b) => /^(Cancel|Close|Done|Not now|OK|×)$/.test(b.textContent.trim()) && visible(b));
    if (close) close.click();
    else document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    await until(() => !modal(), 'dialog closed', 10000);
    await sleep(300);
  }
  async function dialog(name, opener, expect) {
    if (!opener) { bad.push('dialog ' + name + ': no button to open it'); return; }
    opener.click();
    const dlg = await until(modal, 'dialog ' + name, 15000);
    await sleep(700);
    const problems = [];
    if (expect && !expect.test(dlg.innerText)) problems.push('missing ' + expect);
    if (errs.length) problems.push('errors: ' + errs.splice(0).join(' / '));
    if (problems.length) bad.push('dialog ' + name + ': ' + problems.join('; '));
    log.push((problems.length ? 'BAD  ' : 'ok   ') + 'dialog ' + name);
    await closeModal();
  }
  const signedIn = () => visible($('.cc-me-btn'));
  async function authDialog(mode, name, email, password) {
    // the landing page's "Log in" opens the dialog; returns true once signed in
    await open('#landing', /Long walks/);
    $$('[data-act=login]').find(visible).click();
    const dlg = await until(modal, 'sign-in dialog');
    await sleep(400);
    if (mode === 'signup') { button(/^Create an account$/, '.anvil-modal, .modal').click(); await sleep(300); }
    const inputs = Array.from(dlg.querySelectorAll('input:not([type=checkbox]):not([type=hidden]):not([type=radio]):not([type=file])')).filter(visible);
    if (mode === 'signup') { type(inputs[0], name); type(inputs[1], email); type(inputs[2], password); }
    else { type(inputs[0], email); type(inputs[1], password); }
    const tick = Array.from(dlg.querySelectorAll('input[type=checkbox]')).find(visible);
    if (mode === 'signup' && tick && !tick.checked) tick.click();
    button(mode === 'signup' ? /^Create my account$/ : /^Log in$/, '.anvil-modal, .modal').click();
    const end = Date.now() + 30000;
    while (Date.now() < end) {
      if (!modal() && window.UI_READY && signedIn()) return true;
      const msg = dlg.querySelector('.anvil-role-msg-error');
      if (msg && visible(msg) && msg.textContent.trim()) { log.push(mode + ' said: ' + msg.textContent.trim()); await closeModal(); return false; }
      await sleep(200);
    }
    log.push(mode + ': no sign-in after 30 s');
    return false;
  }
  async function signOut() {
    $('.cc-me-btn').click();
    await sleep(300);
    button(/Log out/, '.cc-menu').click();
    await until(() => location.hash === '#landing' && window.UI_READY && !signedIn(), 'signed out');
    await sleep(500);
  }
  try {
    // ---- signed out
    await open('#landing', /Long walks/);
    if (!$('.ytf-cover[data-yt-film]')) bad.push('no Watch section');
    const foot = $('.lp-footer').innerText;
    for (const t of ['Submit feedback', 'Privacy & Terms', 'arkvital.com', 'addanapp.com']) if (foot.indexOf(t) < 0) bad.push('landing footer misses ' + t);
    await open('#safety', /Safety center/);
    await open('#walks', /Long walks/);
    log.push('     #walks shows the landing page to visitors');

    // ---- a new walker, signed up through the dialog
    const ok = await authDialog('signup', 'Smoke Walker', 'smoke' + Date.now() + '@example.com', 'Cc-' + Math.random().toString(36).slice(2) + '-Wk7');
    if (!ok) throw new Error('sign-up failed');
    await until(() => location.hash === '#walks' && window.UI_READY, 'went on to the page asked for');
    check('#walks after sign-up', /My walks/);
    await open('#welcome', /Welcome/);
    await open('#discover', /Walks for you/, () => /walk/.test(mainText()));
    const sfoot = $('.cc-footer').innerText;
    for (const t of ['Submit feedback', 'Privacy & Terms', 'arkvital.com', 'addanapp.com']) if (sfoot.indexOf(t) < 0) bad.push('footer misses ' + t);
    await dialog('safety pledge', button(/^Take it$/), /safety pledge/i);
    await open('#map', /snack map/, () => $('.cc-map.leaflet-container'));
    const walkLink = await until(() => $$('a.cc-walk-row').find((a) => /#walk\//.test(a.getAttribute('href'))), 'a walk on the map page');
    const walkHash = walkLink.getAttribute('href');
    await open('#plan', /The route/, () => $('.cc-map.leaflet-container'));
    await open(walkHash, /Route & stops/, () => /The crew/.test(mainText()));
    const hostLink = $$('.cc-main .cc-person a.name').find(visible);
    const hostHash = hostLink ? hostLink.getAttribute('href') : null;
    if (hostHash) await open(hostHash, /Endorsements/);
    await open(walkHash.replace('#walk/', '#edit/'), /Can't edit this walk/);
    await open('#walks', /My walks/);
    await open('#walks/past', /My walks/);
    await open('#people', /People/);
    await open('#me', /Endorsements/);
    await open('#me/edit', /Edit profile/);
    await open('#journey', /My journey/);
    await dialog('journey entry', button(/New entry/, '.cc-main'), /New journey entry/);
    await open('#perks', /points to spend/);
    await open('#safety', /Safety center/);
    await open('#notifications', /Notifications/);
    await open('#admin', /Admins only/);
    await signOut();

    // ---- admin (ADMIN_EMAILS in server_code/common.py): sign up the first time, log in after that
    const adminPw = 'Cc-smoke-adm-93Kx-7q';
    if (!(await authDialog('signup', 'Admin Tester', 'arkulinskis@gmail.com', adminPw))) {
      if (!(await authDialog('login', '', 'arkulinskis@gmail.com', adminPw))) throw new Error('admin sign-in failed');
    }
    await open('#admin', /Run the club/, () => $$('.cc-main .cc-tabs button').length >= 6);
    for (const t of [/Places/, /Safety reports/, /Users/, /Perks/, /Demo data/, /Deals/]) {
      button(t, '.cc-main .cc-tabs').click();
      await sleep(1200);
      check('#admin tab ' + t.source, /Run the club/);
    }
    await signOut();
    log.push(bad.length ? 'PROBLEMS: ' + bad.join(' | ') : 'PASSED');
    return { ok: !bad.length, log: log };
  } catch (e) {
    log.push(String(e && e.message || e));
    log.push('at ' + location.hash + ': ' + mainText().replace(/\s+/g, ' ').slice(0, 400));
    if (errs.length) log.push('errors: ' + errs.join(' / '));
    if (bad.length) log.push('PROBLEMS: ' + bad.join(' | '));
    return { ok: false, log: log };
  }
})();
