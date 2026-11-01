"""shadcn-style Gradio components, built on gr.HTML (Gradio 6's custom HTML components).

Each component splits the work the same way:
- Python renders the markup (view.py and primitives.py), escaping every piece of backend text.
  The template is only "${value}", so the markup is shown exactly as Python made it. (Gradio runs
  templates as JavaScript template strings, so backend text must never go into one.)
- The component owns its CSS, scoped to itself by Gradio, and its behaviour in `js_on_load`.
- Events go back to Python the same way everywhere: click an element that has data-event="name",
  and the component fires `name`, with the element's data-* attributes as gr.EventData. So
  <button data-event="open" data-id="t1"> runs `history.open(fn)`, and fn reads `event.id`.
"""

import json
from html import escape

import gradio as gr

from ui.icons import icon
from ui.primitives import attributes, button

# Shared by every component. gr.HTML only lets Python listen to a custom event whose name appears
# in quotes in js_on_load, which the EVENTS line does.
EVENTS_JS = """
const EVENTS = __EVENTS__;
element.addEventListener('click', (event) => {
  const target = event.target.closest('[data-event]');
  if (!target || !element.contains(target) || !EVENTS.includes(target.dataset.event)) return;
  if (target.dataset.confirm && !window.confirm(target.dataset.confirm)) return;
  trigger(target.dataset.event, { ...target.dataset });
});
"""


class Component(gr.HTML):
    """The base: markup from Python, CSS and behaviour from the subclass, data-event clicks as events."""

    EVENTS: tuple[str, ...] = ()
    CSS = ""
    JS = ""

    def __init__(self, value: str = "", **kwargs):
        super().__init__(
            value,
            html_template="${value}",
            css_template=self.CSS,
            js_on_load=EVENTS_JS.replace("__EVENTS__", json.dumps(list(self.EVENTS))) + self.JS,
            apply_default_css=False,
            container=False,
            **kwargs,
        )


class Button(Component):
    """shadcn's <Button> as a Gradio component: `ui.Button("New chat", icon_name="square-pen").click(fn)`."""

    EVENTS = ("click",)
    CSS = ".ui-button { width: 100%; justify-content: flex-start; }"

    def __init__(self, label: str, *, icon_name: str | None = None, variant: str = "default", size: str = "default", **kwargs):
        super().__init__(button(label, icon_name=icon_name, variant=variant, size=size, data_event="click"), **kwargs)


class Conversation(Component):
    """The message list, in the style of the template's <Messages> and AI Elements' <Message>.

    Events: `suggest` (a suggestion was clicked; event.text). Copy buttons work in the browser alone.
    """

    EVENTS = ("suggest",)
    JS = """
element.addEventListener('click', async (event) => {
  const copy = event.target.closest('[data-copy]');
  if (!copy) return;
  await navigator.clipboard.writeText(copy.dataset.copy);
  copy.dataset.copied = '';
  setTimeout(() => delete copy.dataset.copied, 1500);
});
// After each update, bring the newest question to the top of the screen, as chat apps do.
watch('value', () => {
  const questions = element.querySelectorAll('[data-role="user"]');
  questions[questions.length - 1]?.scrollIntoView({ block: 'start', behavior: 'smooth' });
});
"""
    CSS = """
display: block;

.conversation {
  max-width: 48rem; margin: 0 auto; padding: 1.5rem 1rem 2.5rem;
  display: flex; flex-direction: column; gap: 1.75rem;
}
.message { animation: ui-fade-up 0.25s var(--ease-spring); }
.message[data-role="user"] { display: flex; justify-content: flex-end; scroll-margin-top: 4.5rem; }
.bubble {
  width: fit-content; max-width: min(80%, 56ch); padding: 0.5rem 0.875rem;
  border-radius: 1rem 1rem 0.5rem 1rem; border: 1px solid color-mix(in oklab, var(--border) 30%, transparent);
  background: linear-gradient(to bottom right, var(--muted), color-mix(in oklab, var(--muted) 70%, var(--card)));
  box-shadow: var(--shadow-card); color: var(--foreground);
  font-size: 0.875rem; line-height: 1.65; white-space: pre-wrap; overflow-wrap: anywhere;
}
.message[data-role="assistant"] { display: flex; align-items: flex-start; gap: 0.75rem; }
.message[data-role="assistant"] > .ui-avatar { margin-top: -0.0625rem; }
.message-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 0.75rem; padding-top: 0.125rem; }

.prose { font-size: 0.875rem; line-height: 1.7; color: var(--foreground); overflow-wrap: anywhere; }
.prose > :first-child { margin-top: 0; }
.prose > :last-child { margin-bottom: 0; }
.prose p { margin: 0 0 0.75em; }
.prose ul, .prose ol { margin: 0.5em 0 0.75em; padding-left: 1.25rem; }
.prose ul { list-style: disc; }
.prose ol { list-style: decimal; }
.prose li { margin: 0.25em 0; }
.prose li::marker { color: var(--muted-foreground); }
.prose strong { font-weight: 600; }
.prose h1, .prose h2, .prose h3, .prose h4 { margin: 1.25em 0 0.5em; font-size: 0.9375rem; font-weight: 600; letter-spacing: -0.01em; }
.prose code { font-family: var(--font-mono); font-size: 0.8125em; padding: 0.1em 0.35em; border-radius: 0.25rem; background: var(--muted); }
.prose a { color: inherit; text-underline-offset: 2px; }
.prose table { width: 100%; margin: 0.75em 0; border-collapse: collapse; font-size: 0.8125rem; }
.prose th, .prose td { padding: 0.375rem 0.625rem; border-bottom: 1px solid var(--border); text-align: left; }
.prose th { font-weight: 500; color: var(--muted-foreground); }

.actions { display: flex; gap: 0.125rem; margin: -0.25rem 0 0 -0.375rem; opacity: 0; transition: opacity 150ms; }
.message:hover .actions, .actions:focus-within { opacity: 1; }
.actions .ui-button { color: color-mix(in oklab, var(--muted-foreground) 70%, transparent); }
.actions .ui-button:hover { color: var(--foreground); }
[data-copy] .icon-check, [data-copy][data-copied] .icon-copy { display: none; }
[data-copy][data-copied] .icon-check { display: block; }

.trace > summary, .sources > summary {
  width: fit-content; font-size: 0.8125rem; color: var(--muted-foreground); transition: color 150ms;
}
.trace > summary:hover, .sources > summary:hover { color: var(--foreground); }
.trace > summary .ui-chevron, .sources > summary .ui-chevron { margin-left: 0; }
.trace-time { color: color-mix(in oklab, var(--muted-foreground) 70%, transparent); font-variant-numeric: tabular-nums; }
.steps { list-style: none; margin: 0.875rem 0 0.25rem; padding: 0; }
.step { position: relative; display: grid; grid-template-columns: 1rem 1fr; column-gap: 0.75rem; padding-bottom: 1rem; }
.step:last-child { padding-bottom: 0; }
.step::before {
  content: ""; position: absolute; left: calc(0.5rem - 0.5px); top: 1.5rem; bottom: 0.25rem;
  width: 1px; background: var(--border);
}
.step:last-child::before { display: none; }
.step-icon { display: flex; align-items: center; height: 1.25rem; color: var(--muted-foreground); }
.step-head { display: flex; align-items: center; gap: 0.5rem; min-height: 1.25rem; font-size: 0.8125rem; font-weight: 500; }
.step-tool { font-family: var(--font-mono); font-size: 0.75rem; font-weight: 400; color: var(--muted-foreground); }
.step-desc { margin-top: 0.25rem; font-size: 0.8125rem; line-height: 1.6; color: var(--muted-foreground); }
.step-desc p { margin: 0; }
.step-desc strong { color: var(--foreground); font-weight: 500; }
.metrics { display: flex; flex-wrap: wrap; gap: 0.375rem; margin: 0.5rem 0 0; }
.metric {
  display: inline-flex; align-items: baseline; gap: 0.375rem; padding: 0.1875rem 0.5rem;
  border: 1px solid var(--border); border-radius: calc(var(--radius) - 4px); background: var(--card); font-size: 0.75rem;
}
.metric dt { color: var(--muted-foreground); }
.metric dd { margin: 0; font-weight: 500; font-variant-numeric: tabular-nums; color: var(--foreground); }

.sources > summary { font-size: 0.75rem; font-weight: 500; }
.source-list { list-style: none; margin: 0.5rem 0 0; padding: 0; display: flex; flex-direction: column; gap: 0.375rem; }
.source {
  display: grid; grid-template-columns: 1.125rem 1fr auto; align-items: center; gap: 0.25rem 0.5rem;
  padding: 0.5rem 0.75rem; border: 1px solid var(--border); border-radius: var(--radius); background: var(--card);
  font-size: 0.8125rem; color: var(--muted-foreground);
}
.source-index, .citation {
  display: inline-flex; align-items: center; justify-content: center; min-width: 1.125rem; height: 1.125rem; padding: 0 0.3rem;
  border-radius: 9999px; background: var(--muted); color: var(--muted-foreground);
  font: 500 0.625rem/1 var(--font); font-variant-numeric: tabular-nums;
}
.citation { margin-left: 0.25rem; vertical-align: 0.125em; cursor: default; transition: background-color 150ms, color 150ms; }
.citation + .citation { margin-left: 0.125rem; }
.citation:hover { background: var(--primary); color: var(--primary-foreground); }
.source-name { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--foreground); font-weight: 500; }
.source-page { color: var(--muted-foreground); font-weight: 400; }
.source-score { font-family: var(--font-mono); font-size: 0.6875rem; font-variant-numeric: tabular-nums; }
.source-quote {
  grid-column: 2 / -1; font-size: 0.75rem; line-height: 1.55;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}

.message[data-role="assistant"][data-pending] { min-height: 50vh; }
.thinking { display: flex; align-items: center; min-height: 1.5rem; font-size: 0.875rem; font-weight: 500; }

.empty {
  max-width: 48rem; margin: 0 auto; padding: 0 1rem 1.25rem;
  min-height: calc(100vh - 13rem); display: flex; flex-direction: column;
}
.greeting { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 3rem 1rem; text-align: center; }
.greeting h2 { margin: 0; font-size: 1.875rem; font-weight: 600; letter-spacing: -0.025em; color: var(--foreground); }
.greeting p { margin: 0.75rem 0 0; max-width: 30rem; font-size: 0.875rem; line-height: 1.6; color: color-mix(in oklab, var(--muted-foreground) 85%, transparent); }
.suggestions { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.625rem; }
.suggestion {
  display: flex; flex-direction: column; gap: 0.125rem; padding: 0.875rem 1rem; text-align: left; cursor: pointer;
  border: 1px solid color-mix(in oklab, var(--border) 70%, transparent); border-radius: 0.75rem;
  background: color-mix(in oklab, var(--card) 50%, transparent); font: 400 0.8125rem/1.55 var(--font);
  color: var(--foreground); transition: transform 200ms, background-color 200ms, box-shadow 200ms;
}
.suggestion:hover { transform: translateY(-2px); background: var(--card); box-shadow: var(--shadow-card); }
.suggestion span { font-size: 0.75rem; color: var(--muted-foreground); }
@media (max-width: 640px) { .suggestions { grid-template-columns: 1fr; } }
"""


class Composer(Component):
    """The message box, in the style of the template's <MultimodalInput>.

    Events: `send` (event.text). Enter sends, Shift+Enter adds a line. While an answer is pending
    (a [data-pending] message is on the page) it will not send again.
    """

    EVENTS = ("send",)
    JS = """
const form = element.querySelector('form');
const box = element.querySelector('textarea');
const busy = () => document.querySelector('[data-pending]') !== null;
const fit = () => { box.style.height = 'auto'; box.style.height = Math.min(box.scrollHeight, 240) + 'px'; };
const send = () => {
  const text = box.value.trim();
  if (!text || busy()) return;
  trigger('send', { text });
  box.value = '';
  fit();
};
form.addEventListener('submit', (event) => { event.preventDefault(); send(); });
box.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); send(); }
});
box.addEventListener('input', fit);
"""
    CSS = """
display: block;

.composer {
  max-width: 46rem; margin: 0 auto; border-radius: 1rem;
  border: 1px solid color-mix(in oklab, var(--border) 80%, transparent); background: var(--card);
  box-shadow: var(--shadow-composer); transition: box-shadow 300ms, border-color 300ms;
}
.composer:focus-within { box-shadow: var(--shadow-composer-focus); border-color: var(--border); }
textarea {
  display: block; width: 100%; min-height: 4.5rem; max-height: 15rem; resize: none; overflow-y: auto;
  padding: 0.875rem 1rem 0.375rem; border: 0; outline: none; background: transparent; box-shadow: none;
  font: 400 0.875rem/1.6 var(--font); color: var(--foreground);
}
textarea::placeholder { color: color-mix(in oklab, var(--muted-foreground) 60%, transparent); }
.composer-footer { display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; padding: 0 0.75rem 0.75rem; }
.composer-hint { display: flex; align-items: center; gap: 0.375rem; min-width: 0; font-size: 0.75rem; color: var(--muted-foreground); }
.send {
  display: inline-flex; align-items: center; justify-content: center; width: 1.75rem; height: 1.75rem;
  border: 0; border-radius: 0.75rem; background: var(--primary); color: var(--primary-foreground); cursor: pointer;
  transition: opacity 200ms, transform 200ms;
}
.send:hover { opacity: 0.85; }
.send:active { transform: scale(0.95); }
:root:has([data-pending]) & .send { opacity: 0.25; cursor: not-allowed; }
.disclaimer { max-width: 46rem; margin: 0.5rem auto 0; text-align: center; font-size: 0.6875rem; color: color-mix(in oklab, var(--muted-foreground) 80%, transparent); }
"""

    def __init__(self, *, placeholder: str, hint_html: str = "", disclaimer: str = "", **kwargs):
        markup = (
            '<form class="composer">'
            f'<textarea rows="2"{attributes(placeholder=placeholder, aria_label=placeholder)}></textarea>'
            f'<div class="composer-footer"><div class="composer-hint">{hint_html}</div>'
            f'<button type="submit" class="send" aria-label="Send">{icon("arrow-up", 16)}</button></div></form>'
        )
        if disclaimer:
            markup += f'<p class="disclaimer">{escape(disclaimer)}</p>'
        super().__init__(markup, **kwargs)


class ThreadList(Component):
    """The conversation history, in the style of the template's <SidebarHistory>.

    Events: `open` (event.id), `remove` (event.id, after the browser asks to confirm).
    """

    EVENTS = ("open", "remove")
    CSS = """
display: block;

.history { display: flex; flex-direction: column; gap: 1rem; }
.history-label {
  padding: 0.25rem 0.5rem; font-size: 0.625rem; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase;
  color: color-mix(in oklab, var(--muted-foreground) 85%, transparent);
}
.history-items { display: flex; flex-direction: column; gap: 0.125rem; }
.history-item { position: relative; display: flex; align-items: center; border-radius: var(--radius); transition: background-color 150ms; }
.history-item:hover, .history-item[data-active] { background: var(--accent); }
.history-link {
  flex: 1; min-width: 0; height: 2rem; padding: 0 0.5rem; border: 0; border-radius: var(--radius); background: none;
  text-align: left; font: 400 0.8125rem/2rem var(--font); color: var(--muted-foreground); cursor: pointer;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.history-item:hover .history-link, .history-item[data-active] .history-link { color: var(--foreground); }
.history-item:hover .history-link, .history-item:focus-within .history-link { padding-right: 2rem; }
.history-action { position: absolute; right: 0.125rem; opacity: 0; transition: opacity 150ms; }
.history-item:hover .history-action, .history-item:focus-within .history-action { opacity: 1; }
.history-action:hover { color: var(--foreground); background: transparent; }
.history-empty { padding: 0.5rem; font-size: 0.8125rem; line-height: 1.5; color: var(--muted-foreground); }
"""
