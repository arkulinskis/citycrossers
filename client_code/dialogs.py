"""Open the app's dialogs (Forms in client_code/Dialogs) with one call each. Every function returns what the
dialog closed with: True/False, a dict, an id, or None when cancelled.

    safety_pledge()                        the six promises; True once taken (state.me() is refreshed)
    place_form(title, ...)                 name + kind (+ map pin, description) for a place or a route stop
    review(place_name, place_id=..)        write or edit a review; True when saved
    review_any()                           pick a place from the map, then review it
    entry(existing=None, walk=None)        a journey entry; True when saved
    report(user_id=None, walk_id=None, who='')
    invite(walk)                           invite connections or an email address to a walk
    place_details(place_id)                a place: deals, reviews, Review / Plan a walk from here
    info(title, ...)                       a message with an OK button (perk codes, share text, tips)
"""
import anvil

from . import state


def _open(form, large=False, dismissible=True):
    return anvil.alert(form, buttons=[], large=large, role="app-dialog", dismissible=dismissible)


def safety_pledge():
    from .Dialogs.SafetyPledge import SafetyPledge
    return bool(_open(SafetyPledge(), large=True))


def place_form(title, subtitle='', lat=None, lng=None, kinds=None, default_kind='cafe', with_map=False,
               context=None, ask_desc=False, name='', button='Add'):
    """Returns {'name', 'kind', 'lat', 'lng', 'description'} or None."""
    from .Dialogs.PlaceForm import PlaceForm
    return _open(PlaceForm(title=title, subtitle=subtitle, lat=lat, lng=lng, kinds=kinds, default_kind=default_kind,
                           with_map=with_map, context=context, ask_desc=ask_desc, name=name, button=button),
                 large=with_map)


def review(place_name, place_id=None, stop_id=None, walk_id=None, existing=None):
    from .Dialogs.Review import Review
    return bool(_open(Review(place_name=place_name, place_id=place_id, stop_id=stop_id, walk_id=walk_id,
                             existing=existing), large=True))


def review_any():
    places = state.call('reviewable_places')
    if places is state.FAIL:
        return False
    if not places:
        state.toast("No places on the map yet. Add one from the Map page.", 'warning')
        return False
    from .Dialogs.ReviewPick import ReviewPick
    pid = _open(ReviewPick(places=places))
    if not pid:
        return False
    name = [p['name'] for p in places if p['id'] == pid][0]
    return review(name, place_id=pid)


def entry(existing=None, walk=None):
    from .Dialogs.Entry import Entry
    return bool(_open(Entry(existing=existing, walk=walk), large=True))


def report(user_id=None, walk_id=None, who=''):
    from .Dialogs.Report import Report
    return bool(_open(Report(user_id=user_id, walk_id=walk_id, who=who), large=True))


def invite(walk):
    friends = state.call('my_friends')
    if friends is state.FAIL:
        return False
    from .Dialogs.Invite import Invite
    return bool(_open(Invite(walk=walk, friends=friends), large=True))


def place_details(place_id):
    if not place_id:
        return
    p = state.call('get_place', place_id)
    if p is state.FAIL:
        return
    from .Dialogs.PlaceDetails import PlaceDetails
    what = _open(PlaceDetails(place=p), large=True)
    if what == 'review':
        review(p['name'], place_id=p['id'])
    elif what == 'plan':
        from . import router
        router.go('plan/from/' + p['id'])


def info(title, text='', emoji='', code='', button='OK', link=None, pre=''):
    """A message with one button. link = (text, '#address') adds a link button that closes the dialog first."""
    from .Dialogs.Info import Info
    return _open(Info(title=title, text=text, emoji=emoji, code=code, button=button, link=link, pre=pre))
