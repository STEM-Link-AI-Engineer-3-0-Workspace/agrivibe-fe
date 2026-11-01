"""shadcn/ui primitives as HTML: button, badge, avatar, collapsible, alert. Plain functions, no Gradio.

They take the same variants as shadcn's React components and are styled by PRIMITIVES in theme.py.
One rule keeps them safe: a parameter that ends in `_html` takes markup and is inserted as it is;
every other text parameter is escaped. Text from the backend must never go into an `_html` one.
"""

from html import escape

from ui.icons import icon


def attributes(**attrs: str | None) -> str:
    """Escaped HTML attributes. data_id="x" becomes data-id="x"; None leaves the attribute out."""
    return "".join(f' {name.replace("_", "-")}="{escape(value)}"' for name, value in attrs.items() if value is not None)


def button(
    label: str = "",
    *,
    icon_name: str | None = None,
    variant: str = "default",
    size: str = "default",
    cls: str = "",
    **attrs: str | None,
) -> str:
    """shadcn's <Button>. Variants: default, outline, ghost. Sizes: default, sm, icon, icon-sm.

    Give it data_event="name" to fire that event on the Gradio component it is inside (see components.py).
    """
    svg = icon(icon_name, 14 if size in ("sm", "icon-sm") else 16) if icon_name else ""
    text = f"<span>{escape(label)}</span>" if label and size not in ("icon", "icon-sm") else ""
    if size in ("icon", "icon-sm") and label:
        attrs.setdefault("aria_label", label)
        attrs.setdefault("title", label)
    classes = f"ui-button {cls}".strip()
    return (
        f'<button type="button" class="{classes}" data-variant="{variant}" data-size="{size}"'
        f"{attributes(**attrs)}>{svg}{text}</button>"
    )


def badge(label: str, *, variant: str = "secondary", icon_name: str | None = None, **attrs: str | None) -> str:
    """shadcn's <Badge>, as a pill. Variants: secondary, outline, success, warning."""
    svg = icon(icon_name, 12) if icon_name else ""
    return f'<span class="ui-badge" data-variant="{variant}"{attributes(**attrs)}>{svg}{escape(label)}</span>'


def avatar(*, initials: str = "", icon_name: str | None = None, variant: str = "muted", shape: str = "square") -> str:
    """shadcn's <Avatar>: initials, or an icon, in a small rounded square or circle."""
    inside = icon(icon_name, 14) if icon_name else escape(initials)
    return f'<span class="ui-avatar" data-variant="{variant}" data-shape="{shape}" aria-hidden="true">{inside}</span>'


def collapsible(trigger_html: str, content_html: str, *, open: bool = False, cls: str = "") -> str:
    """shadcn's <Collapsible>, on the browser's own <details>, so it opens and closes without JavaScript."""
    return (
        f'<details class="ui-collapsible {cls}"{" open" if open else ""}>'
        f'<summary>{trigger_html}{icon("chevron-down", 14, "ui-chevron")}</summary>'
        f'<div class="ui-collapsible-content">{content_html}</div></details>'
    )


def alert(title: str, description_html: str = "", *, variant: str = "default", icon_name: str = "circle-alert") -> str:
    """shadcn's <Alert>: an icon, a title and a description. Variants: default, warning."""
    description = f'<div class="ui-alert-description">{description_html}</div>' if description_html else ""
    return (
        f'<div class="ui-alert" role="alert" data-variant="{variant}">{icon(icon_name)}'
        f'<div class="ui-alert-title">{escape(title)}</div>{description}</div>'
    )
