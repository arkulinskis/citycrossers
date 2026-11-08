from anvil import *

from ._anvil_designer import WalkCardTemplate
from ... import state, ui


class WalkCard(WalkCardTemplate):
    """A walk card (My walks): vibe cover with my status, when, distance, time, pace, who can see it, the stop strip,
    the host and how many are going. The whole card links to #walk/<id>. A note under it asks the host to mark a
    past walk complete, or says how many join requests are waiting. item = a walk summary from my_walks."""

    def __init__(self, **properties):
        super().__init__(**properties)
        w, d = self.item, self.dom_nodes
        v = ui.vibe_of(w.get("vibe"))
        pace = ui.pace_of(w.get("pace"))
        state.href(d["link"], "#walk/%s" % w["id"])
        d["cover"].className = "cover " + v[3]
        status, color = "", ""
        if w.get("status") == "completed":
            status, color = "🏁 Completed", "dark"
        elif w.get("status") == "cancelled":
            status, color = "Cancelled", "dark"
        elif w.get("is_host"):
            status, color = "⭐ Hosting", "dark"
        elif w.get("my_status") in ui.STATUS_PILLS:
            status, color = ui.STATUS_PILLS[w["my_status"]]
        d["status"].className = "cc-pill " + color
        state.text(d["status"], status)
        state.show(d["status"], bool(status))
        state.text(d["emo"], v[1])
        state.text(d["rel"], ui.fmt_rel(w.get("start")))
        state.text(d["when"], ui.fmt_when(w.get("start")))
        state.text(d["title"], w.get("title"))
        state.text(d["dist"], "📏 " + ui.km(w.get("distance_km")))
        state.text(d["dur"], "⏱️ " + ui.fmt_dur(w.get("duration_min")))
        state.text(d["pace"], "%s %s" % (pace[0], pace[1]))
        state.text(d["vis"], "🌍 Public" if w.get("visibility") == "public" else "👯 Friends")
        self.strip.show(w.get("stops") or [])
        host = w.get("host") or {}
        self.host_av.show(host, 28)
        state.text(d["host"], "by %s" % host.get("name", "someone"))
        state.text(d["going"], "%s/%s going" % (w.get("going", 0), w.get("max_walkers", 0)))
        note = ""
        if w.get("needs_completion"):
            ico, note = "🏁", "Did it happen? Mark it complete to award points."
            state.cls(d["note"], "orange", False)
        elif w.get("requests"):
            n = w["requests"]
            ico, note = "🙋", "%d request%s waiting for you" % (n, "s" if n != 1 else "")
            state.cls(d["note"], "orange", True)
        else:
            ico = ""
        state.text(d["note_ico"], ico)
        state.text(d["note_text"], note)
        state.show(d["note"], bool(note))
