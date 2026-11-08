"""Draw a walker's avatar into a DOM node: their photo, or their initials on their colour. Used by the header,
Components/Avatar and Components/AvatarStack (display only, no user text is parsed as HTML)."""
from . import ui


def paint(node, card, size=40):
    card = card or {}
    node.className = "cc-av"
    s = node.style
    s.width = s.height = "%dpx" % size
    s.fontSize = "%dpx" % max(11, int(size * 0.38))
    s.backgroundColor = card.get("avatar_color") or "#17A673"
    url = ui.media_url(card.get("avatar"))
    if url:
        s.backgroundImage = "url('%s')" % str(url).replace("'", "%27")
        node.textContent = ""
    else:
        s.backgroundImage = ""
        node.textContent = card.get("initials") or "?"
    if card.get("name"):
        node.setAttribute("title", card["name"])
    node.setAttribute("aria-hidden", "true")
