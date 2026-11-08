"""App-wide client state and small helpers every form uses.

    state.me()                 the signed-in walker as a dict from get_me() (name, points, level, is_admin ...), or None
    state.set_me(me) / refresh_me()   refresh_me also redraws the header
    state.counts() / set_counts(c)    unread notifications, invites, friend requests, points (the header's badge)
    state.call(fn, *args, quiet=False, **kw)
                               server call with friendly errors: anything that goes wrong shows a toast (unless quiet)
                               and returns state.FAIL. "SAFETY_PLEDGE_REQUIRED" opens the pledge and retries once;
                               "Please sign in" opens the sign-in dialog and retries once. quiet=True = no spinner.
    state.ask_login(mode)      the sign-in / sign-up dialog (Dialogs/AuthDialog); True once signed in
    state.toast(msg, kind)     kind None / "ok" (ink), "error" (red), "info", "warning"
    state.ask(text, yes)       a yes/no question
    state.set_attr / set_control_attr / heading / live / text / show / cls   DOM helpers
"""
import anvil
import anvil.js
import anvil.server
import anvil.users
from anvil import Notification
from anvil.js import window

FAIL = object()

_state: dict = {"me": None, "counts": {}, "after": None}


# ---------------------------------------------------------------- who is signed in
def me():
    return _state["me"]


def set_me(value):
    _state["me"] = value or None
    redraw_shell()


def logged_in():
    return anvil.users.get_user() is not None


def is_admin():
    m = _state["me"]
    return bool(m and m.get("is_admin"))


def refresh_me():
    res = call("get_me", quiet=True)
    if res is not FAIL:
        _state["me"] = res
    from . import legal
    legal.refresh_soon()  # Privacy & Terms: records the sign-up tick, or reminds people to review
    redraw_shell()
    return _state["me"]


def redraw_shell():
    """The header shows the avatar, points and menu from state.me(): redraw it after a change."""
    from . import router
    router.refresh_shell()


def counts():
    return _state["counts"]


def set_counts(value):
    c = dict(_state["counts"])
    c.update(value or {})
    _state["counts"] = c
    m = _state["me"]
    if m is not None and "points" in c:
        m["points"] = c["points"]
    redraw_shell()


def after_login(value=False):
    """Where to go once someone signs in (a member page a visitor asked for). No argument = read and forget it."""
    if value is False:
        v = _state["after"]
        _state["after"] = None
        return v
    _state["after"] = value
    return value


def peek_after():
    return _state["after"]


def ask_login(mode="login"):
    """Open the sign-in dialog. True once signed in (state.me() is filled)."""
    from .Dialogs.AuthDialog import AuthDialog
    return bool(anvil.alert(AuthDialog(mode=mode), buttons=[], role="app-dialog", dismissible=True))


# ---------------------------------------------------------------- server calls
def clean_msg(e):
    msg = str(e)
    for prefix in ("PermissionDenied: ", "anvil.server.PermissionDenied: ", "Exception: ", "anvil.server.InternalError: ",
                   "anvil.users."):
        if msg.startswith(prefix):
            msg = msg[len(prefix):]
    return msg


def call(fn, *args, quiet=False, **kwargs):
    """Server call with friendly errors. Returns FAIL (and shows a toast unless quiet) when anything goes wrong."""
    try:
        if quiet:
            return anvil.server.call_s(fn, *args, **kwargs)
        return anvil.server.call(fn, *args, **kwargs)
    except Exception as e:
        if type(e).__name__ == "SessionExpiredError":
            toast("Your session timed out. Reloading…", "error")
            window.setTimeout(lambda: window.location.reload(), 1200)
            return FAIL
        msg = clean_msg(e)
        if "SAFETY_PLEDGE_REQUIRED" in msg:
            from . import dialogs
            if dialogs.safety_pledge():
                return call(fn, *args, quiet=quiet, **kwargs)
            return FAIL
        if "Please sign in" in msg:
            if ask_login():
                return call(fn, *args, quiet=quiet, **kwargs)
            return FAIL
        if not quiet:
            toast(msg or "Something went wrong. Try again?", "error")
        return FAIL


# ---------------------------------------------------------------- feedback
STYLES = {"ok": "success", "error": "danger", "info": "info", "warning": "warning"}


def toast(message, kind=None, timeout=None):
    t = timeout or (5 if kind == "error" else 3.5)
    try:
        n = Notification(message, timeout=t, role=kind)
    except TypeError:  # the open-source App Server 1.18 has no `role` yet: its older `style` gives the same classes
        n = Notification(message, timeout=t, style=STYLES.get(kind or "", "success"))
    n.show()


def confetti(emojis=None):
    try:
        if emojis:
            window.cc.confetti(emojis)
        else:
            window.cc.confetti()
    except Exception:
        pass


def copy_text(text):
    try:
        return bool(window.cc.copy(text))
    except Exception:
        return False


def ask(text, yes="Yes", no="Cancel", title=""):
    return bool(anvil.confirm(text, title=title, buttons=[(no, False), (yes, True)], role="app-dialog"))


def feedback():
    """Open the Prepsto feedback panel (the app's only feedback channel)."""
    if window.get("Prepsto") and window.Prepsto.open:
        window.Prepsto.open()
    else:
        window.open("https://prepsto.com/#f/wzrzr2f", "_blank", "noopener")


# ---------------------------------------------------------------- DOM helpers
def set_attr(component, name, value):
    """An HTML attribute (href, aria-label, title) on a component's root element.
    (HtmlComponent.attrs does this on hosted Anvil, but the open-source App Server 1.18 doesn't have it yet.)"""
    node = anvil.js.get_dom_node(component)
    if value is None:
        node.removeAttribute(name)
    else:
        node.setAttribute(name, str(value))


def control(component):
    """The real <input>, <textarea>, <select> or <button> inside an Anvil component (for ARIA attributes and focus)."""
    node = anvil.js.get_dom_node(component)
    if str(node.tagName) in ("INPUT", "TEXTAREA", "SELECT", "BUTTON"):
        return node
    return node.querySelector("input, textarea, select, button") or node


def focus(component):
    getattr(control(component), "focus")()


def set_control_attr(component, name, value):
    el = control(component)
    if value is None:
        el.removeAttribute(name)
    else:
        el.setAttribute(name, str(value))


def heading(component, level=1):
    """Make a Label a real heading for screen readers (an Anvil Label renders as a <div>)."""
    set_attr(component, "role", "heading")
    set_attr(component, "aria-level", level)


def live(component, urgent=False):
    set_attr(component, "role", "alert" if urgent else "status")


def busy(button, text=None):
    """Grey a Button out while it works; returns a function that puts it back."""
    old = button.text
    button.enabled = False
    if text:
        button.text = text

    def done():
        button.enabled = True
        button.text = old
    return done


def text(node, value):
    """Display-only text on an anvil:dom-node element."""
    node.textContent = "" if value is None else str(value)


def show(node, on=True):
    node.style.display = "" if on else "none"


def cls(node, name, on=True):
    if on:
        node.classList.add(name)
    else:
        node.classList.remove(name)


def href(node, value):
    node.setAttribute("href", value)


def loose(x):
    """Hands a value through untyped, so the validator doesn't pin an attribute to its first value for good.
    (The browser's Python has no `typing` module.)"""
    return x
