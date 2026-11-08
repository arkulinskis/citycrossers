import random

from anvil import *
from anvil.js import window

from ._anvil_designer import DiscoverTemplate
from ... import dialogs, router, state, ui

TAGLINES = ["Ready for a long one?", "Somewhere out there is a cinnamon bun with your name on it.",
            "Every 5 km deserves a snack.", "Your next crew is one swipe away.",
            "Walk far, eat well, meet people."]
EMPTY = {'deck': [], 'upcoming': [], 'invites': [], 'suggestions': [], 'counts': {}}


class Discover(DiscoverTemplate):
    """#discover, home for members: a hello band with my numbers, nudges (invites, friend requests, the safety
    pledge, an unfinished profile), then two tabs. "Walks for you" = the swipe deck (cc.js drags the card; right =
    join_walk, left = pass_walk) next to my invites and coming-up walks; "Walkers to meet" = suggested people."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.tab, self.idx = "walks", 0
        data = state.call("home_feed")
        self.data = state.loose(data if data is not state.FAIL else dict(EMPTY))
        if data is not state.FAIL:
            state.set_counts(data.get("counts") or {})
        self.deck = self.data["deck"]
        self._swipe_bound = False
        self.tabs_panel.add_event_handler("x-pick", self._tab)
        self.invites_panel.add_event_handler("x-invite", self._invite)
        self.people_panel.add_event_handler("x-person", self._person)
        self.dom_nodes["tagline"].textContent = random.choice(TAGLINES)
        self.render()

    # ------------------------------------------------------------ page
    def greeting(self):
        h = ui.now_local().hour
        if h < 5:
            return "Night owl mode", "🌙"
        if h < 12:
            return "Good morning", "☀️"
        if h < 18:
            return "Good afternoon", "🌤️"
        return "Good evening", "🌆"

    def render(self):
        me, d = state.me() or {}, self.dom_nodes
        hello, emo = self.greeting()
        first = (me.get("name") or "walker").split(" ")[0]
        state.text(d["hello"], "%s, %s %s" % (hello, first, emo))
        lvl = me.get("level") or {}
        state.text(d["points"], "⭐ %s" % me.get("points", 0))
        state.text(d["level"], "%s %s" % (lvl.get("emoji", "🚶"), lvl.get("name", "Stroller")))
        state.text(d["level_sub"], "%d%% to %s" % (int(lvl.get("progress", 0) * 100), lvl.get("next_name") or "the top"))
        state.text(d["km"], ui.km(me.get("km_total", 0)))
        nxt = (self.data["upcoming"] or [None])[0]
        state.text(d["next"], ui.fmt_rel(nxt["start"]) if nxt else "No plans")
        state.text(d["next_sub"], ("Next: " + nxt["title"][:26]) if nxt else "Swipe below 👇")
        inv = len(self.data["invites"])
        self.invite_alert.visible = bool(inv)
        state.text(d["invite_text"], "You have %d walk invite%s." % (inv, "s" if inv != 1 else ""))
        fr = (self.data.get("counts") or {}).get("friend_requests", 0)
        self.friend_alert.visible = bool(fr)
        state.text(d["friend_text"], "%d walker%s want%s to connect." % (fr, "s" if fr != 1 else "", "s" if fr == 1 else ""))
        self.pledge_alert.visible = bool(me) and not me.get("safety_pledge")
        self.profile_alert.visible = bool(me) and bool(me.get("safety_pledge")) and me.get("completeness", 100) < 75
        state.text(d["profile_text"], "Your profile is %s%% done." % me.get("completeness", 0))
        self.tabs_panel.items = [
            {"key": "walks", "label": "🔥 Walks for you", "on": self.tab == "walks", "cls": "", "count": len(self.deck) - self.idx},
            {"key": "people", "label": "👋 Walkers to meet", "on": self.tab == "people", "cls": ""}]
        self.walks_tab.visible = self.tab == "walks"
        self.people_tab.visible = self.tab == "people"
        if self.tab == "walks":
            self.render_side()
            self.render_deck()
        else:
            people = self.data["suggestions"]
            self.people_panel.items = [{"p": p, "mode": "suggest"} for p in people]
            self.people_panel.visible = bool(people)
            self.people_empty.visible = not people

    def _tab(self, key='walks', **event_args):
        self.tab = key
        self.render()

    def render_side(self):
        invites = self.data["invites"]
        self.invites_card.visible = bool(invites)
        self.invites_panel.items = invites
        up = self.data["upcoming"]
        self.upcoming_card.visible = bool(up)
        self.nothing_card.visible = not up
        self.upcoming_panel.items = [{"walk": w, "sub": "%s · %s · %s going" % (ui.fmt_rel(w["start"]), ui.fmt_time(w["start"]),
                                                                              w.get("going", 0))} for w in up[:4]]

    # ------------------------------------------------------------ the deck
    def render_deck(self):
        left = len(self.deck) - self.idx
        self.deck_box.visible = left > 0
        self.deck_empty.visible = left <= 0
        if left <= 0:
            return
        w, d = self.deck[self.idx], self.dom_nodes
        v = ui.vibe_of(w.get("vibe"))
        pace = ui.pace_of(w.get("pace"))
        host = w.get("host") or {}
        card = d["card"]
        card.style.transition = "none"
        card.style.transform = ""
        card.style.opacity = ""
        card.classList.remove("lean-right", "lean-left", "cc-fade-in")
        getattr(card, "offsetWidth")  # restart the arrival animation
        card.classList.add("cc-fade-in")
        card.style.transition = ""
        state.show(d["shadow2"], left > 2)
        state.show(d["shadow1"], left > 1)
        d["cover"].className = "cover " + v[3]
        state.text(d["vibe"], "%s %s" % (v[1], v[2]))
        friend = bool(w.get("from_friend"))
        state.cls(d["match"], "friend", friend)
        state.text(d["match"], ("💞 Friend's walk · %s%%" if friend else "%s%% match") % w.get("match", 0))
        state.text(d["rel"], ui.fmt_rel(w.get("start")))
        state.text(d["when"], ui.fmt_when(w.get("start")))
        state.text(d["emo"], v[1])
        state.text(d["title"], w.get("title"))
        state.text(d["f_dist"], "📏 " + ui.km(w.get("distance_km")))
        state.text(d["f_dur"], "⏱️ " + ui.fmt_dur(w.get("duration_min")))
        state.text(d["f_pace"], "%s %s" % (pace[0], pace[1]))
        state.text(d["f_food"], "🥐 %s food stops" % w.get("food_stops", 0))
        state.text(d["f_spots"], "👥 %s spots left" % w.get("spots_left", 0))
        self.strip.show(w.get("stops") or [])
        state.text(d["desc"], w.get("description"))
        self.tags_panel.items = [{"text": t, "color": "outline"} for t in (w.get("tags") or [])[:4]]
        hl = host.get("level") or {}
        self.host.show(host, sub="%s %s · %s walks" % (hl.get("emoji", ""), hl.get("name", ""), host.get("walks_count", 0)), size=42)
        state.text(d["approval"], "🙋 Host approves requests" if w.get("approval_required") else "⚡ Instant join")
        state.text(d["hint"], "Drag the card, or use the buttons · %d walk%s in your deck" % (left, "s" if left != 1 else ""))

    @handle("", "show")
    def form_show(self, **event_args):
        if not self._swipe_bound:
            self._swipe_bound = True
            try:
                window.cc.swipe(self.dom_nodes["card"], self._swiped)
            except Exception:
                pass

    def _fly(self, direction):
        if self.idx >= len(self.deck):
            return
        try:
            window.cc.fly(self.dom_nodes["card"], direction, self._swiped)
        except Exception:
            self._swiped(direction)

    def pass_click(self, event):
        self._fly("left")

    def join_click(self, event):
        self._fly("right")

    def details_click(self, event):
        if self.idx < len(self.deck):
            router.go("walk/" + self.deck[self.idx]["id"])

    def _swiped(self, direction):
        if self.idx >= len(self.deck):
            return
        w = self.deck[self.idx]
        if direction == "right":
            status = state.call("join_walk", w["id"])
            if status is state.FAIL:
                self.render_deck()  # put the card back
                return
            msgs = {"going": "You're in! 🎉 See you at the meeting point.",
                    "requested": "Request sent! 🙋 We'll ping you when the host says yes.",
                    "waitlist": "It's full, so you're on the waitlist. Fingers crossed 🤞"}
            state.toast(msgs.get(status, "Done!"))
            if status == "going":
                state.confetti()
        else:
            state.call("pass_walk", w["id"], quiet=True)
        self.idx += 1
        self.render()

    # ------------------------------------------------------------ actions
    def _person(self, action='', uid='', **event_args):
        res = state.call("send_friend_request", uid)
        if res is state.FAIL:
            return
        state.toast("Connected! 🤝" if res == "friends" else "Request sent 👋")
        self.data["suggestions"] = [p for p in self.data["suggestions"] if p["id"] != uid]
        self.render()

    def _invite(self, wid='', accept=False, **event_args):
        status = state.call("respond_invite", wid, accept)
        if status is state.FAIL:
            return
        if accept:
            state.toast("You're in! 🎉" if status == "going" else "Added to the waitlist 🤞")
            if status == "going":
                state.confetti()
            router.go("walk/" + wid)
            return
        self.data["invites"] = [w for w in self.data["invites"] if w["id"] != wid]
        state.toast("No worries, maybe next time.", "info")
        self.render()

    @handle("pledge_button", "click")
    def pledge_button_click(self, **event_args):
        if dialogs.safety_pledge():
            self.render()
