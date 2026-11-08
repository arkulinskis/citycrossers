from anvil import *

from ._anvil_designer import JournalCardTemplate
from ... import state, ui


class JournalCard(JournalCardTemplate):
    """A journey highlight on a profile: date, km, mood + title, the start of the story, the photo.
    item = a journal entry from get_profile."""

    def __init__(self, **properties):
        super().__init__(**properties)
        j, d = self.item, self.dom_nodes
        date = ui.fmt_date(j["entry_date"], True) if j.get("entry_date") else ""
        state.text(d["date"], date + ((" · " + ui.km(j["km"])) if j.get("km") else ""))
        lock = "" if j.get("is_public") else "  🔒 private"
        state.text(d["title"], "%s %s%s" % (j.get("mood") or "", j.get("title") or "", lock))
        body = j.get("body") or ""
        state.text(d["body"], body[:280] + ("…" if len(body) > 280 else ""))
        url = ui.media_url(j.get("photo"))
        if url:
            d["photo"].setAttribute("src", url)
            d["photo"].setAttribute("alt", "Photo: %s" % (j.get("title") or "journey entry"))
        state.show(d["photo"], bool(url))
