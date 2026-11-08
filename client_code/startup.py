"""The app starts here (anvil.yaml: startup module). The Privacy & Terms kit, one server call to learn who is signed
in (Anvil's loading spinner shows meanwhile), then the page for the address in the browser bar."""
import anvil.server

from . import legal, router, state

LEGAL_THEME = {"accent": "#0E8A5D"}  # colours for the Privacy & Terms page (CityCrossers green, --green-d in app.css)

legal.setup(LEGAL_THEME)
if state.logged_in():
    me = state.call("get_me", quiet=True)
    state.set_me(None if me is state.FAIL else me)
    legal.refresh_soon()
router.start()
