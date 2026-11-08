from anvil import *

from ._anvil_designer import JourneyItemTemplate
from ... import state, ui


class JourneyItem(JourneyItemTemplate):
    """One moment on my journey timeline: a journal entry (mood, story, photo; Edit / Delete), a review (place,
    stars, note to future me; Make public/private / Edit / Delete) or a completed walk (vibe colours, links to it).
    item = an item from journey(); buttons raise x-j(action=..., kind=..., iid=...)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        i, d = self.item, self.dom_nodes
        kind = i['type']
        d['item'].className = 'cc-j-item ' + kind
        date = ui.fmt_date(i['date'], True) if i.get('date') else ''
        public = bool(i.get('is_public'))
        d['vis'].className = 'cc-pill ' + ('sky' if public else '')
        state.text(d['vis'], '🌍 Public' if public else '🔒 Private')
        for k in ('walk_link', 'title_link', 'stars', 'rtitle', 'future', 'back', 'photo', 'walk_sum'):
            state.show(d[k], False)
        self.toggle_button.visible = kind == 'review'
        self.acts.visible = kind != 'walk'
        if kind == 'entry':
            state.text(d['marker'], i.get('mood'))
            state.text(d['date'], date + ((' · ' + ui.km(i['km'])) if i.get('km') else ''))
            if i.get('walk_id'):
                state.text(d['walk_link'], ' · ' + (i.get('walk_title') or 'the walk'))
                state.href(d['walk_link'], '#walk/%s' % i['walk_id'])
                state.show(d['walk_link'], True)
            state.text(d['title'], i.get('title'))
            state.text(d['body'], i.get('body'))
            url = ui.media_url(i.get('photo'))
            if url:
                d['photo'].setAttribute('src', url)
                d['photo'].setAttribute('alt', 'Photo: %s' % (i.get('title') or 'journey entry'))
                state.show(d['photo'], True)
        elif kind == 'review':
            place = i.get('place') or {}
            state.text(d['marker'], '⭐')
            state.text(d['date'], '%s · review' % date)
            state.text(d['title'], '%s %s' % (ui.emoji(place.get('kind')), place.get('name', 'A place')))
            state.text(d['stars'], ui.stars(i.get('rating')))
            d['stars'].setAttribute('aria-label', '%s out of 5 stars' % int(round(i.get('rating') or 0)))
            state.show(d['stars'], True)
            if i.get('title'):
                state.text(d['rtitle'], i['title'])
                state.show(d['rtitle'], True)
            state.text(d['body'], i.get('body'))
            if i.get('future_note'):
                state.text(d['future'], '💌 Note to future me: ' + i['future_note'])
                state.show(d['future'], True)
            state.show(d['back'], bool(i.get('would_return')))
            self.toggle_button.text = 'Make private' if public else 'Make public'
        else:
            v = ui.vibe_of(i.get('vibe'))
            host = i.get('host') or {}
            state.text(d['marker'], '🥾')
            d['card'].className = 'cc-card cc-j-walk ' + v[3]
            state.show(d['vis'], False)
            state.text(d['date'], '%s · walk completed' % date)
            state.show(d['title'], False)
            state.text(d['title_link'], '%s %s' % (v[1], i.get('title')))
            state.href(d['title_link'], '#walk/%s' % i['id'])
            state.show(d['title_link'], True)
            state.show(d['body'], False)
            state.text(d['walk_sum'], "🏁 %s with %s's crew" % (ui.km(i.get('km')), host.get('name', 'the crew')))
            state.show(d['walk_sum'], True)

    def _raise(self, action):
        self.parent.raise_event('x-j', action=action, kind=self.item['type'], iid=self.item['id'])

    @handle('toggle_button', 'click')
    def toggle_button_click(self, **event_args):
        self._raise('toggle')

    @handle('edit_button', 'click')
    def edit_button_click(self, **event_args):
        self._raise('edit')

    @handle('delete_button', 'click')
    def delete_button_click(self, **event_args):
        self._raise('delete')
