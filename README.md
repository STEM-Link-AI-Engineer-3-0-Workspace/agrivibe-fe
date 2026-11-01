# AgriVibe UI

The Gradio frontend for AgriVibe, a multi-agent farm advisor for paddy farmers in Sri Lanka.
It is a separate repo and a separate process from the backend, and it talks to the backend
**only over HTTP**: it never imports `agrivibe`. If the UI needs something the API does not
offer, the fix is a new endpoint in the backend, not an import here.

```
browser ──▶ agrivibe-fe (Gradio, :7860) ──HTTP──▶ agrivibe-be (FastAPI, :8000) ──┬─▶ Postgres (threads, memory, evidence)
                                                                                    ├─▶ Pinecone (documents)
                                                                                    └─▶ fieldsat-mcp-server (:8001)
```

Gradio calls the backend from Python on the server, not from the browser, so there is no CORS to
set up. In that sense this app is a backend-for-frontend: a small server whose only job is the UI.

## Setup

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # skip if you already have uv
uv sync
cp .env.example .env
```

The UI needs no API keys; the backend holds them. `.env` has:

| Variable | Default | What it does |
|---|---|---|
| `AGRIVIBE_API` | `http://127.0.0.1:8000` | Where the backend runs |
| `AGRIVIBE_TIMEOUT` | `180` | Seconds to wait for one chat turn. Decision questions can take two minutes |
| `FARMER_ID`, `FARMER_NAME` | `frm_7f3a9c2e`, `Nimal Perera` | **Keep these the same as in `agrivibe-be`'s `.env`.** Shown on the page and written to the log, never sent |
| `GRADIO_SERVER_NAME` | `127.0.0.1` | Read by Gradio itself. Set `0.0.0.0` inside a container |

### Who the farmer is

The UI never tells the backend who is asking. The backend decides that on the server, from its
own `.env`, in one function (`current_farmer()`) where a real auth service would plug in later.
This repo keeps a copy of the same `FARMER_ID`, synced by hand, only to show the farmer's name on
the page and to label its logs. If the two drift, only this page's label is wrong: every thread
and every memory is still keyed correctly by the backend.

## Run

Clone the three repos side by side, then start them in three terminals, in this order:

```bash
# 1. FieldSat on demo data, in fieldsat-mcp-server (port 8001, because the backend uses 8000)
uv run fieldsat --demo --transport http --port 8001

# 2. The backend, in agrivibe-be (it needs OPENAI_API_KEY, PINECONE_API_KEY and DATABASE_URL,
#    and refuses to start if FieldSat or Postgres cannot be reached)
uv run fastapi dev

# 3. The UI, in this repo
uv run python app.py          # http://127.0.0.1:7860
```

While you edit the UI, run `uv run gradio app.py` instead: Gradio reloads the page every time you
save. Both commands apply the same theme.

## What the page does

The layout follows shadcn/ui's AI chat template ([vercel/ai-chatbot](https://github.com/vercel/ai-chatbot)):
a sidebar, a centred conversation, and a message box docked at the bottom.

- **Conversations in the sidebar**, grouped by day. Every conversation is saved by the backend in
  Postgres; click one to reopen it. Hover one for its delete button, which asks to confirm first.
- **A refresh keeps your place.** The open conversation's id is kept in the browser
  (`gr.BrowserState`), so reloading the page reopens it.
- **Each answer carries its own evidence**, in the message, as modern chat apps do:
  - *Worked with 4 agents · 45s* opens into the chain of steps the orchestrator took: the fields it
    looked up, what it saved to memory, and each specialist with its status, summary and numbers.
    A specialist that failed is flagged on the closed line too (*No data from Farm context*).
  - Citations in the answer become small numbered chips. *Used 3 sources* lists the cited
    passages with their page, rerank score and a quote.
  - A copy button copies the answer without its citation ids.
- **A thinking message** shows while the agents work, and the send button rests until the answer is in.
- **Suggestions** on the empty page send a question straight away, including the demo fields that
  fail on purpose. The header shows the field in memory and whether the backend is online.
- **Light and dark mode** follow the system.

The terminal gets one JSON line per turn:

```
INFO:     agrivibe.ui: {"event": "chat_turn", "farmer_id": "frm_7f3a9c2e", "thread_id": "c3badd50-…", "status": "ok", "seconds": 43.7, "field_id": "SL-PADDY-MINNERIYA", "tools_called": ["save_requirements", "ask_weather_agent", "ask_farm_context_agent", "ask_knowledge_agent", "ask_advisory_agent"], "specialists": {"weather": "ok", "farm_context": "ok", "knowledge": "ok"}}
```

## How the code is laid out

```
agrivibe-fe/
├── client.py         the backend as the UI sees it: the HTTP calls, the models they return, and
│                     every failure turned into one message a farmer can read
├── view.py           replies → markup: messages, the agent trace, sources, the history list.
│                     Plain functions, no Gradio. Every piece of backend text is escaped
├── app.py            the Gradio page: layout, events, state
├── ui/               the design system, reusable beyond AgriVibe
│   ├── theme.py      Gradio theme + shadcn tokens + primitive and shell CSS
│   ├── primitives.py shadcn primitives as HTML: button, badge, avatar, collapsible, alert
│   ├── components.py Gradio components built on gr.HTML: Button, Conversation, Composer, ThreadList
│   └── icons.py      Lucide icons, the set shadcn uses
└── tests/            run with no backend and no keys
```

### The design system (`ui/`)

It is built in three layers, so a colour is defined once and every piece follows light and dark mode:

1. **Theme.** `gr.themes.Base(...).set(...)` sets Gradio's own variables to shadcn's neutral palette
   and the Geist font.
2. **Tokens.** shadcn's names point at those variables: `--background: var(--body-background-fill)`,
   `--muted-foreground: var(--body-text-color-subdued)`, `--border`, `--primary`, … All other CSS uses
   only these names. Status colours come from the theme's hues (`--success` is emerald,
   `--warning` amber), and their soft versions are mixed with `color-mix()`, so dark mode needs no
   rules of its own.
3. **Primitives and components.** `primitives.py` renders shadcn's primitives as HTML with the
   same variants (`button(variant="outline", size="sm")`, `badge(variant="warning")`). `components.py`
   turns the interactive pieces into Gradio components by subclassing `gr.HTML`, Gradio 6's
   custom HTML components:

```python
class ThreadList(Component):
    EVENTS = ("open", "remove")     # Python can listen: threads.open(fn), threads.remove(fn)
    CSS = ".history-item { … }"     # scoped to this component by Gradio
```

Every component works the same way. Python renders the markup and escapes backend text; the
template is just `${value}`. Clicking an element with `data-event="open" data-id="t1"` fires the
`open` event, and the handler reads `event.id` from `gr.EventData`. The template stays `${value}`
because Gradio evaluates templates as JavaScript template strings, so text from the backend must
never become part of a template.

- **`client.py`** copies only the fields of the backend's contract that the UI reads
  (`src/agrivibe/models/` in agrivibe-be). A field the backend adds later is ignored. A 404
  becomes `ConversationNotFound`, so the page can start fresh when a conversation was deleted
  in another tab.
- **Two events per question.** `ask` shows the question and a thinking message at once, without the
  queue; `.success(answer)` then waits for the backend. Gradio's own progress overlay is turned off
  (`show_progress="hidden"`) because the thinking message does that job.
- **State.** `thread_id` lives in `gr.BrowserState` (survives a refresh); the open conversation's
  turns live in `gr.State`, and the page is re-rendered from them after every change.
- **Gradio 6 takes the theme and CSS in `launch()`**, passed as `demo.launch(**ui.LAUNCH)`.

## Try the demo fields

| Ask | What you should see |
|---|---|
| Is my Minneriya paddy field stressed? | Farm context and Weather, both OK |
| Should I spray fungicide on my Minneriya field this week? | All four specialists, Advisory last. Up to two minutes |
| Is field SL-PADDY-SAT-FAIL stressed? | Farm context: **No data**; the answer says the satellite timed out |
| Has it rained much on field SL-PADDY-WEATHER-FAIL? | Weather: **No data** |
| Should I apply urea on field SL-PADDY-SLOW this week? | Works, about 20 s slower |

Then click **New conversation** and ask "Has it rained on my field?". The backend remembers your
field from earlier conversations, so it answers without asking which field.

## Test

```bash
uv run pytest
uvx ruff check .
```

CI runs both on every pull request.
