from anvil import *

from ._anvil_designer import JourneyTemplate
from ... import dialogs, state, ui

FILTERS = [('all', '✨ Everything'), ('entry', '📔 Entries'), ('review', '⭐ Reviews'), ('walk', '🥾 Walks'),
           ('public', '🌍 Public')]


class Journey(JourneyTemplate):
    """#journey: my life, one walk at a time. Totals, then a timeline of journal entries, reviews and completed
    walks (filter: everything / entries / reviews / walks / public). New entry, Review a place, and per item edit,
    delete, make public/private."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.filter = 'all'
        self.filters_panel.add_event_handler('x-pick', self._filter)
        self.items_panel.add_event_handler('x-j', self._item)
        self.load()

    def load(self):
        d = state.call('journey')
        self.data = state.loose(d if d is not state.FAIL else {'items': [], 'stats': {}, 'public_default': False})
        self.render()

    def _find(self, kind, iid):
        for i in self.data['items']:
            if i['type'] == kind and i['id'] == iid:
                return i
        return None

    def render(self):
        st, items, f, d = self.data['stats'], self.data['items'], self.filter, self.dom_nodes
        state.text(d['s_km'], ui.km(st.get('km', 0)))
        state.text(d['s_walks'], st.get('walks', 0))
        state.text(d['s_people'], st.get('people', 0))
        state.text(d['s_reviews'], st.get('reviews', 0))
        state.text(d['s_entries'], st.get('entries', 0))
        if f == 'public':
            shown = [i for i in items if i.get('is_public')]
        elif f != 'all':
            shown = [i for i in items if i['type'] == f]
        else:
            shown = items
        self.filters_panel.items = [{'key': k, 'label': l, 'on': k == f} for k, l in FILTERS]
        self.items_panel.items = shown
        self.timeline.visible = bool(shown)
        self.empty_box.visible = not shown

    def _filter(self, key='all', **event_args):
        self.filter = key
        self.render()

    def _new_entry(self):
        if dialogs.entry():
            state.refresh_me()
            self.load()

    def _new_review(self):
        if dialogs.review_any():
            state.refresh_me()
            self.load()

    @handle('entry_button', 'click')
    def entry_button_click(self, **event_args):
        self._new_entry()

    @handle('entry2_button', 'click')
    def entry2_button_click(self, **event_args):
        self._new_entry()

    @handle('review_button', 'click')
    def review_button_click(self, **event_args):
        self._new_review()

    @handle('review2_button', 'click')
    def review2_button_click(self, **event_args):
        self._new_review()

    def _item(self, action=None, kind=None, iid=None, **event_args):
        i = self._find(kind, iid)
        if i is None:
            return
        if kind == 'entry':
            if action == 'edit' and dialogs.entry(existing=i):
                self.load()
            elif action == 'delete' and state.ask("Delete this entry? This can't be undone.", yes="Delete") \
                    and state.call('delete_entry', iid) is not state.FAIL:
                self.load()
        elif kind == 'review':
            if action == 'edit' and dialogs.review((i.get('place') or {}).get('name', 'this place'), existing=i):
                self.load()
            elif action == 'delete' and state.ask("Delete this review?", yes="Delete") \
                    and state.call('delete_review', iid) is not state.FAIL:
                self.load()
            elif action == 'toggle' and state.call('set_review_public', iid, not i.get('is_public')) is not state.FAIL:
                state.toast("Review is now public 🌍" if not i.get('is_public') else "Review is now private 🔒")
                self.load()
