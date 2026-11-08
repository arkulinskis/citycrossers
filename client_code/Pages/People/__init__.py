from anvil import *

from ._anvil_designer import PeopleTemplate
from ... import state

EMPTY = {'friends': [], 'incoming': [], 'outgoing': [], 'suggestions': []}


class People(PeopleTemplate):
    """#people: search walkers, answer connection requests, my crew (connections), suggested walkers, and the
    requests I sent."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.results = None
        for p in (self.results_panel, self.incoming_panel, self.friends_panel, self.suggest_panel):
            p.add_event_handler('x-person', self._person)
        self.load()

    def load(self):
        d = state.call('people_page')
        self.data = state.loose(d if d is not state.FAIL else dict(EMPTY))
        self.render()

    def render(self):
        d = self.data
        searching = self.results is not None
        self.results_part.visible = searching
        if searching:
            self.results_panel.items = [{'p': p, 'mode': 'search'} for p in self.results]
            self.results_panel.visible = bool(self.results)
            self.no_results.visible = not self.results
        self.incoming_part.visible = bool(d['incoming'])
        self.incoming_panel.items = [{'p': p, 'mode': 'incoming'} for p in d['incoming']]
        n = len(d['friends'])
        state.text(self.dom_nodes['crew_h'], '🤝 Your crew (%d)' % n if n else '🤝 Your crew')
        self.friends_panel.items = [{'p': p, 'mode': 'friend'} for p in d['friends']]
        self.friends_panel.visible = bool(n)
        self.no_friends.visible = not n
        self.suggest_part.visible = bool(d['suggestions'])
        self.suggest_panel.items = [{'p': p, 'mode': 'suggest'} for p in d['suggestions']]
        self.outgoing_part.visible = bool(d['outgoing'])
        self.outgoing_panel.items = [{'card': p, 'sub': 'Waiting…', 'size': 34} for p in d['outgoing']]

    def search(self):
        text = (self.search_box.text or '').strip()
        if len(text) < 2:
            state.toast("Type at least 2 letters.", 'warning')
            return
        res = state.call('search_people', text)
        if res is not state.FAIL:
            self.results = res
            self.render()

    @handle('search_button', 'click')
    def search_button_click(self, **event_args):
        self.search()

    @handle('search_box', 'pressed_enter')
    def search_box_pressed_enter(self, **event_args):
        self.search()

    @handle('clear_button', 'click')
    def clear_button_click(self, **event_args):
        self.results = None
        self.search_box.text = ''
        self.render()

    def _person(self, action='', uid='', **event_args):
        if action == 'connect':
            res = state.call('send_friend_request', uid)
            if res is state.FAIL:
                return
            state.toast("Connected! 🤝" if res == 'friends' else "Request sent 👋")
            for p in self.results or []:
                if p['id'] == uid:
                    p['relationship'] = res
        else:
            accept = action == 'accept'
            if state.call('respond_friend_request', uid, accept) is state.FAIL:
                return
            state.toast("You're connected! Time to plan a walk 🥾" if accept else "Request ignored", 'ok' if accept else 'info')
            for p in self.results or []:
                if p['id'] == uid and accept:
                    p['relationship'] = 'friends'
        self.load()
