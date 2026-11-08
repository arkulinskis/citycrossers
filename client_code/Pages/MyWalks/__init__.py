from anvil import *

from ._anvil_designer import MyWalksTemplate
from ... import router, state, ui

TABS = [('upcoming', '🗓️ Going'), ('hosting', '⭐ Hosting'), ('invites', '💌 Invites'),
        ('pending', '⏳ Pending'), ('past', '🏁 Past walks')]
EMPTIES = {
    'upcoming': ('🥾', "No walks lined up", "Swipe through Discover to find your next crew.", ('Find a walk', '#discover', 'cc-btn')),
    'hosting': ('⭐', "You're not hosting anything", "Hosting earns +25 pts per walk, and you choose the snacks.",
                ('Plan a walk', '#plan', 'cc-btn orange')),
    'invites': ('💌', "No invites right now", "Connect with more walkers and the invites will roll in.",
                ('Find people', '#people', 'cc-btn ghost')),
    'pending': ('⏳', "Nothing pending", "Requests you've sent and waitlists you're on will show here.", None),
    'past': ('🏁', "No finished walks yet", "Your first one is going to be great.", None),
}


class MyWalks(MyWalksTemplate):
    """#walks[/tab]: my walks in five tabs (going, hosting, invites, pending, past) as walk cards. The tab is in the
    address (#walks/hosting), so the back button and shared links keep it."""

    def __init__(self, tab=None, **properties):
        super().__init__(**properties)
        data = state.call('my_walks')
        self.data = state.loose(data if data is not state.FAIL else {k: [] for k, _ in TABS})
        if tab not in dict(TABS):
            tab = 'upcoming' if self.data['upcoming'] or not self.data['hosting'] else 'hosting'
            if self.data['invites']:
                tab = 'invites'
        self.tab = str(tab)
        self.tabs_panel.add_event_handler('x-pick', self._tab)
        past = self.data['past']
        state.text(self.dom_nodes['lead'], '%d walks done · %s together with your crews'
                   % (len(past), ui.km(sum((w.get('distance_km') or 0) for w in past))))
        self.render()

    def _tab(self, key='upcoming', **event_args):
        self.tab = key
        router.replace_hash('walks/' + key)
        self.render()

    def render(self):
        d = self.data
        self.tabs_panel.items = [{'key': k, 'label': label, 'on': k == self.tab, 'cls': '',
                                  'count': len(d[k]) if k != 'past' else 0} for k, label in TABS]
        walks = d[self.tab]
        self.walks_panel.items = walks
        self.walks_panel.visible = bool(walks)
        self.empty_box.visible = not walks
        if not walks:
            emo, title, text, link = EMPTIES[self.tab]
            state.text(self.dom_nodes['e_emoji'], emo)
            state.text(self.dom_nodes['e_title'], title)
            state.text(self.dom_nodes['e_text'], text)
            self.e_link_box.visible = bool(link)
            if link:
                node = self.dom_nodes['e_link']
                node.textContent = link[0]
                node.setAttribute('href', link[1])
                node.className = link[2]
