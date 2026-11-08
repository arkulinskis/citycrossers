from anvil import *

from ._anvil_designer import ReviewCardTemplate
from ... import state, ui


class ReviewCard(ReviewCardTemplate):
    """A review. item = {review, mode}: mode "place" (in the place dialog: who wrote it and when) or "profile" (the
    taste map on a profile: which place, private or not, the note to future me, would go back)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        r, d = self.item["review"], self.dom_nodes
        on_place = self.item.get("mode") == "place"
        self.person_part.visible = on_place
        stars = ui.stars(r.get("rating"))
        if on_place:
            self.person.show(r.get("user"), sub=ui.ago(r.get("created")), size=34)
            state.text(d["place"], "")
        else:
            p = r.get("place") or {}
            lock = "" if r.get("is_public") else "  🔒 private"
            state.text(d["place"], "%s %s%s" % (ui.emoji(p.get("kind")), p.get("name", "A place"), lock))
        state.text(d["stars"], stars)
        d["stars"].setAttribute("aria-label", "%s out of 5 stars" % int(round(r.get("rating") or 0)))
        state.text(d["title"], r.get("title"))
        state.show(d["title"], bool(r.get("title")))
        state.text(d["body"], r.get("body"))
        fut = r.get("future_note") if not on_place else None
        state.text(d["future"], "💌 Note to future me: %s" % fut if fut else "")
        state.show(d["future"], bool(fut))
        state.show(d["back"], bool(r.get("would_return")) and not on_place)
