"""The design system: a Gradio theme with shadcn/ui's palette, and shadcn's token names on top of it.

Three layers, each built on the one before:

1. THEME sets Gradio's own variables (--body-background-fill, --border-color-primary, …) to the
   neutral palette of shadcn's AI chat template (vercel/ai-chatbot), light and dark.
2. TOKENS gives those variables shadcn's names (--background, --muted-foreground, --border, …).
   Every style below uses only these names, so a component never hard-codes a colour, and
   dark mode needs no rules of its own: Gradio swaps its variables and the tokens follow.
3. PRIMITIVES styles the shadcn primitives in primitives.py (button, badge, avatar, collapsible,
   alert). Each Gradio component in components.py adds its own scoped CSS on top.
"""

import gradio as gr

from ui.icons import mask

THEME = gr.themes.Base(
    primary_hue=gr.themes.colors.emerald,  # read as --success
    secondary_hue=gr.themes.colors.amber,  # read as --warning
    neutral_hue=gr.themes.colors.neutral,  # shadcn's "neutral" base colour: pure grey, no tint
    # lg is shadcn's --radius (0.625rem); the rest step around it as Tailwind's do.
    radius_size=gr.themes.Size(xxs="2px", xs="4px", sm="6px", md="8px", lg="10px", xl="12px", xxl="16px"),
    font=[gr.themes.GoogleFont("Geist"), "ui-sans-serif", "system-ui", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("Geist Mono"), "ui-monospace", "SFMono-Regular", "monospace"],
).set(
    body_background_fill="#fafafa",
    body_background_fill_dark="#1a1a1a",
    body_text_color="#0a0a0a",
    body_text_color_dark="#ededed",
    body_text_color_subdued="#737373",
    body_text_color_subdued_dark="#8f8f8f",
    background_fill_primary="#ffffff",  # cards and the composer
    background_fill_primary_dark="#212121",
    background_fill_secondary="#f0f0f0",  # muted surfaces: the farmer's message, badges
    background_fill_secondary_dark="#262626",
    panel_background_fill="#f5f5f5",  # the sidebar
    panel_background_fill_dark="#141414",
    border_color_primary="#e5e5e5",
    border_color_primary_dark="#2a2a2a",
    color_accent_soft="rgb(10 10 10 / 0.05)",  # hover on ghost buttons and sidebar items
    color_accent_soft_dark="rgb(237 237 237 / 0.06)",
    button_primary_background_fill="#0a0a0a",
    button_primary_background_fill_dark="#ededed",
    button_primary_text_color="#fafafa",
    button_primary_text_color_dark="#1a1a1a",
    block_background_fill="transparent",
    block_background_fill_dark="transparent",
    block_border_width="0px",
    block_shadow="none",
    block_padding="0px",
    layout_gap="0px",
)

TOKENS = """
.gradio-container {
  --background: var(--body-background-fill);
  --foreground: var(--body-text-color);
  --card: var(--background-fill-primary);
  --muted: var(--background-fill-secondary);
  --muted-foreground: var(--body-text-color-subdued);
  --accent: var(--color-accent-soft);
  --border: var(--border-color-primary);
  --primary: var(--button-primary-background-fill);
  --primary-foreground: var(--button-primary-text-color);
  --sidebar: var(--panel-background-fill);
  --success: var(--primary-500);
  --warning: var(--secondary-500);
  --radius: var(--radius-lg);
  --ring: color-mix(in oklab, var(--foreground) 20%, transparent);
  --shadow-card: 0 1px 3px rgb(0 0 0 / 0.05), 0 1px 1px rgb(0 0 0 / 0.03);
  --shadow-composer: 0 1px 2px rgb(0 0 0 / 0.04);
  --shadow-composer-focus: 0 0 0 1px rgb(0 0 0 / 0.06), 0 2px 8px -2px rgb(0 0 0 / 0.06);
  --ease-spring: cubic-bezier(0.22, 1, 0.36, 1);
}
"""

PRIMITIVES = """
.ui-button {
  display: inline-flex; align-items: center; justify-content: center; gap: 0.5rem; flex-shrink: 0;
  height: 2.25rem; padding: 0 1rem; border-radius: calc(var(--radius) - 2px);
  border: 1px solid transparent; background: transparent; color: var(--foreground);
  font: 500 0.875rem/1 var(--font); white-space: nowrap; cursor: pointer;
  transition: background-color 150ms, color 150ms, opacity 150ms, transform 150ms;
}
.ui-button:focus-visible { outline: none; box-shadow: 0 0 0 3px var(--ring); }
.ui-button:disabled { opacity: 0.5; pointer-events: none; }
.ui-button svg { flex-shrink: 0; }
.gradio-container svg[stroke="currentColor"] { stroke: currentColor; }
.ui-button[data-variant="default"] { background: var(--primary); color: var(--primary-foreground); }
.ui-button[data-variant="default"]:hover { opacity: 0.9; }
.ui-button[data-variant="outline"] { border-color: var(--border); background: var(--card); }
.ui-button[data-variant="outline"]:hover, .ui-button[data-variant="ghost"]:hover { background: var(--accent); }
.ui-button[data-variant="ghost"] { color: var(--muted-foreground); }
.ui-button[data-variant="ghost"]:hover { color: var(--foreground); }
.ui-button[data-size="sm"] { height: 2rem; padding: 0 0.75rem; gap: 0.375rem; font-size: 0.8125rem; border-radius: var(--radius); }
.ui-button[data-size="icon"] { width: 2rem; height: 2rem; padding: 0; border-radius: var(--radius); }
.ui-button[data-size="icon-sm"] { width: 1.75rem; height: 1.75rem; padding: 0; border-radius: calc(var(--radius) - 2px); }

.ui-badge {
  display: inline-flex; align-items: center; gap: 0.25rem; flex-shrink: 0;
  height: 1.25rem; padding: 0 0.5rem; border-radius: 9999px; border: 1px solid transparent;
  font: 500 0.6875rem/1 var(--font); white-space: nowrap;
}
.ui-badge svg { width: 0.75rem; height: 0.75rem; }
.ui-badge[data-variant="secondary"] { background: var(--muted); color: var(--muted-foreground); }
.ui-badge[data-variant="outline"] { border-color: var(--border); color: var(--muted-foreground); }
.ui-badge[data-variant="success"] {
  background: color-mix(in oklab, var(--success) 12%, transparent);
  color: color-mix(in oklab, var(--success) 70%, var(--foreground));
}
.ui-badge[data-variant="warning"] {
  background: color-mix(in oklab, var(--warning) 14%, transparent);
  color: color-mix(in oklab, var(--warning) 62%, var(--foreground));
}

.ui-avatar {
  display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0;
  width: 1.75rem; height: 1.75rem; border-radius: calc(var(--radius) - 2px);
  background: color-mix(in oklab, var(--muted) 60%, transparent); color: var(--muted-foreground);
  box-shadow: 0 0 0 1px color-mix(in oklab, var(--border) 50%, transparent);
  font: 600 0.6875rem/1 var(--font);
}
.ui-avatar[data-shape="circle"] { border-radius: 9999px; }
.ui-avatar[data-variant="primary"] { background: var(--primary); color: var(--primary-foreground); box-shadow: none; }

.ui-collapsible > summary {
  display: flex; align-items: center; gap: 0.5rem; list-style: none; cursor: pointer; user-select: none;
}
.ui-collapsible > summary::-webkit-details-marker { display: none; }
.ui-collapsible > summary .ui-chevron { margin-left: auto; color: var(--muted-foreground); transition: transform 200ms var(--ease-spring); }
.ui-collapsible[open] > summary .ui-chevron { transform: rotate(180deg); }
.ui-collapsible[open] > .ui-collapsible-content { animation: ui-slide-down 200ms var(--ease-spring); }

.ui-alert {
  display: grid; grid-template-columns: 1rem 1fr; gap: 0.25rem 0.75rem; align-items: start;
  padding: 0.75rem 1rem; border: 1px solid var(--border); border-radius: var(--radius);
  background: var(--card); color: var(--foreground); font-size: 0.875rem; line-height: 1.5;
}
.ui-alert svg { margin-top: 0.125rem; }
.ui-alert-title { font-weight: 500; }
.ui-alert-description { grid-column: 2; color: var(--muted-foreground); font-size: 0.8125rem; }
.ui-alert-description code { font-family: var(--font-mono); font-size: 0.75rem; }
.ui-alert[data-variant="warning"] svg { color: var(--warning); }

.ui-shimmer {
  background-image: linear-gradient(90deg, var(--muted-foreground) 40%, var(--foreground) 50%, var(--muted-foreground) 60%);
  background-size: 200% 100%; -webkit-background-clip: text; background-clip: text; color: transparent;
  animation: ui-shimmer 1.6s linear infinite;
}

@keyframes ui-shimmer { from { background-position: 100% 0; } to { background-position: -100% 0; } }
@keyframes ui-slide-down { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: none; } }
@keyframes ui-fade-up { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
"""

# Gradio's own page chrome, made to sit quietly behind the app: full width, no footer, no gaps.
CHROME = """
.gradio-container { max-width: none !important; padding: 0 !important; background: var(--background); }
/* Gradio hides overflow here, which turns the container into the scroll box of every sticky element
   inside it. clip cuts off the same overflow without that, so the header and composer stay pinned. */
.gradio-container { overflow: visible !important; overflow-x: clip !important; }
.gradio-container .main, .gradio-container .contain { padding: 0 !important; }
footer { display: none !important; }
.gradio-container .html-container { padding: 0 !important; }
.gradio-container .prose { max-width: none; }
"""

# The app shell, laid out as the template's: a sidebar (brand, New chat, history, the farmer), a sticky
# header, the conversation, and the composer docked at the bottom. Gradio puts elem_classes on both
# a component's outer block and its inner div, so these rules name the block: .block.app-…
SHELL = """
.app-sidebar { background: var(--sidebar) !important; border-right: 1px solid var(--border) !important; box-shadow: none !important; }
.app-sidebar .sidebar-content { display: flex; flex-direction: column; height: 100%; padding: 0.75rem 0.75rem 0 !important; }
.app-sidebar .sidebar-content > .column { flex: 1; min-height: 0; display: flex; flex-direction: column; gap: 0.25rem !important; }
.app-sidebar .toggle-button {
  top: 0.75rem !important; left: calc(100% - 2.75rem) !important; width: 2rem !important; height: 2rem !important;
  display: flex; align-items: center; justify-content: center; padding: 0 !important;
  border: 0 !important; border-radius: var(--radius) !important; background: transparent !important;
  color: var(--muted-foreground); box-shadow: none !important; transition: background-color 150ms, color 150ms;
}
.app-sidebar:not(.open) .toggle-button { left: calc(100% + 0.75rem) !important; }
.app-sidebar .toggle-button:hover { background: var(--accent) !important; color: var(--foreground); }
.app-sidebar .toggle-button .chevron { display: none; }
.app-sidebar .toggle-button::before {
  content: ""; width: 1rem; height: 1rem; background: currentColor;
  -webkit-mask: PANEL_LEFT center / contain no-repeat; mask: PANEL_LEFT center / contain no-repeat;
}
.sidebar-brand { display: flex; align-items: center; gap: 0.5rem; height: 2rem; padding: 0 0.125rem; font-size: 0.875rem; font-weight: 600; letter-spacing: -0.01em; color: var(--foreground); }
.block.app-new { margin: 0.5rem 0 0.75rem; }
.app-new .ui-button[data-variant="outline"] { background: transparent; color: var(--muted-foreground); }
.app-new .ui-button[data-variant="outline"]:hover { background: var(--accent); color: var(--foreground); }
.block.app-history { flex: 1; min-height: 0; overflow-y: auto; margin: 0 -0.25rem; padding: 0 0.25rem; }
.block.app-user { width: calc(100% + 1.5rem) !important; margin: 0 -0.75rem; padding: 0.625rem 0.875rem 0.75rem; border-top: 1px solid var(--border); }
.sidebar-user { display: flex; align-items: center; gap: 0.625rem; min-width: 0; }
.sidebar-user > div { display: flex; flex-direction: column; min-width: 0; line-height: 1.35; }
.sidebar-user b { font-size: 0.8125rem; font-weight: 500; color: var(--foreground); }
.sidebar-user code { font-family: var(--font-mono); font-size: 0.6875rem; color: var(--muted-foreground); background: none; padding: 0; }

.block.app-header {
  position: sticky; top: 0; z-index: 20;
  background: color-mix(in oklab, var(--background) 85%, transparent); backdrop-filter: blur(12px);
}
.header { display: flex; align-items: center; justify-content: space-between; gap: 1rem; height: 3.5rem; padding: 0 1rem; }
.sidebar-parent:not(:has(.sidebar.open)) .header { padding-left: 3.5rem; }
.header-title { min-width: 0; }
.header-title h1 { margin: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 0.875rem; font-weight: 500; color: var(--foreground); }
.header-title h1.untitled { color: var(--muted-foreground); font-weight: 400; }
.header-meta { display: flex; align-items: center; gap: 0.75rem; flex-shrink: 0; }
.header-meta .ui-badge { font-family: var(--font-mono); font-weight: 400; }
.status { display: inline-flex; align-items: center; gap: 0.375rem; font-size: 0.75rem; color: var(--muted-foreground); }
.status i { width: 0.375rem; height: 0.375rem; border-radius: 9999px; background: var(--success); }
.status[data-online="false"] i { background: var(--warning); }

.block.app-alert { max-width: 48rem; width: 100%; margin: 1rem auto 0; padding: 0 1rem; }
main.contain > .column { min-height: 100vh; }
.block.app-conversation { flex: 1; }
.block.app-composer {
  position: sticky; bottom: 0; z-index: 10; padding: 1rem 1rem 0.75rem;
  background: linear-gradient(to top, var(--background) 70%, transparent);
}
""".replace("PANEL_LEFT", mask("panel-left"))

CSS = TOKENS + PRIMITIVES + CHROME + SHELL
