"""AgriVibe's look: shadcn/ui's neutral palette, set through Gradio's own theme.

Almost everything is a theme variable, so light and dark mode both follow from this one definition
and every stock component picks it up. style.css adds the layout and a few finishing touches.
"""

from pathlib import Path

import gradio as gr

THEME = gr.themes.Base(
    primary_hue=gr.themes.colors.neutral,
    secondary_hue=gr.themes.colors.neutral,
    neutral_hue=gr.themes.colors.neutral,  # shadcn's "neutral" base colour: pure grey, no tint
    radius_size=gr.themes.Size(xxs="2px", xs="4px", sm="6px", md="8px", lg="10px", xl="12px", xxl="16px"),
    font=[gr.themes.GoogleFont("Geist"), "ui-sans-serif", "system-ui", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("Geist Mono"), "ui-monospace", "SFMono-Regular", "monospace"],
).set(
    # Surfaces: white and near-black; the sidebar is one step darker or lighter.
    body_background_fill="#ffffff",
    body_background_fill_dark="#0a0a0a",
    body_text_color="#0a0a0a",
    body_text_color_dark="#fafafa",
    body_text_color_subdued="#737373",
    body_text_color_subdued_dark="#a3a3a3",
    background_fill_primary="#ffffff",
    background_fill_primary_dark="#0a0a0a",
    background_fill_secondary="#ffffff",  # Gradio paints the chat panel and its reply bubbles with this:
    background_fill_secondary_dark="#0a0a0a",  # the page colour, so replies sit on the page as in shadcn
    border_color_primary="#e5e5e5",
    border_color_primary_dark="#262626",
    # Blocks: no boxes around components, as in shadcn's chat template. They take the page's colour,
    # which also covers the grey Gradio paints behind grouped inputs (--border-color-primary).
    block_background_fill="#ffffff",
    block_background_fill_dark="#0a0a0a",
    block_border_width="0px",
    block_shadow="none",
    block_label_text_color="#737373",
    block_label_text_color_dark="#a3a3a3",
    block_title_text_weight="500",
    # The message box: the field is see-through; .app-composer below draws the card around it.
    input_background_fill="transparent",
    input_background_fill_dark="transparent",
    input_border_color="#e5e5e5",
    input_border_color_dark="#262626",
    input_border_color_focus="#a3a3a3",
    input_border_color_focus_dark="#525252",
    input_border_width="1px",
    input_radius="*radius_xl",
    input_shadow="none",
    input_shadow_focus="none",
    # Chat: the farmer's messages are a muted fill; AgriVibe's sit on the page.
    color_accent_soft="#f5f5f5",
    color_accent_soft_dark="#262626",
    border_color_accent_subdued="#f5f5f5",
    border_color_accent_subdued_dark="#262626",
    chatbot_text_size="0.875rem",
    # The conversation list (a gr.Radio): plain rows, the selected one filled.
    checkbox_label_background_fill="transparent",
    checkbox_label_background_fill_dark="transparent",
    checkbox_label_background_fill_hover="#f0f0f0",
    checkbox_label_background_fill_hover_dark="#262626",
    checkbox_label_background_fill_selected="#ebebeb",
    checkbox_label_background_fill_selected_dark="#262626",
    checkbox_label_border_width="0px",
    checkbox_label_border_width_dark="0px",
    checkbox_label_shadow="none",
    checkbox_label_text_size="0.8125rem",
    # Buttons: solid black primary, outline secondary, quiet red for delete.
    button_border_width="1px",
    button_small_radius="*radius_md",
    button_large_radius="*radius_md",
    button_small_text_weight="500",
    button_large_text_weight="500",
    button_primary_background_fill="#0a0a0a",
    button_primary_background_fill_hover="#262626",
    button_primary_background_fill_dark="#fafafa",
    button_primary_background_fill_hover_dark="#e5e5e5",
    button_primary_text_color="#fafafa",
    button_primary_text_color_dark="#0a0a0a",
    button_primary_border_color="#0a0a0a",
    button_primary_border_color_dark="#fafafa",
    button_secondary_background_fill="#ffffff",
    button_secondary_background_fill_hover="#f5f5f5",
    button_secondary_background_fill_dark="#0a0a0a",
    button_secondary_background_fill_hover_dark="#262626",
    button_secondary_border_color="#e5e5e5",
    button_secondary_border_color_dark="#262626",
    button_cancel_background_fill="transparent",
    button_cancel_background_fill_hover="#fef2f2",
    button_cancel_background_fill_dark="transparent",
    button_cancel_background_fill_hover_dark="#450a0a",
    button_cancel_text_color="#dc2626",
    button_cancel_text_color_dark="#f87171",
    button_cancel_border_color="transparent",
    button_cancel_border_color_dark="transparent",
    button_primary_shadow="none",
    button_secondary_shadow="none",
    button_cancel_shadow="none",
)

# The CSS sits beside this file as a real stylesheet. Gradio 6 takes both in launch().
STYLE = Path(__file__).with_name("style.css")
AVATAR = Path(__file__).with_name("agrivibe.svg")  # AgriVibe's picture next to its replies

LAUNCH = {"theme": THEME, "css_paths": [STYLE]}
