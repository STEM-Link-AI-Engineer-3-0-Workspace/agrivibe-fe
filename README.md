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

Learning from this repo? The review pack for AIE 3.0 Level 6 Lesson 5 is in [`docs/`](docs/README.md), and
[online](https://stem-link-ai-engineer-3-0-workspace.github.io/agrivibe-fe/lessons/0001-gradio-api-full-stack.html).

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

Everything on the page is a stock Gradio component, themed. There is no custom HTML; the only
JavaScript keeps the URL in step with the open conversation and confirms a delete.

- **Conversations in the sidebar** (`gr.Sidebar`, `gr.Radio`). Every conversation is saved by the
  backend in Postgres; click one to reopen it. **Delete conversation** asks to confirm first.
- **The URL names the open conversation** (`/?thread=<id>`). It is the only place the id is
  kept, so a refresh, a bookmark or a shared link reopens the conversation, and Back and Forward
  step between conversations. `on_load` reads it with `gr.Request`; a few lines of JS in `app.py`
  write it whenever the conversation changes.
- **Each answer carries its own evidence**, as collapsible "thoughts" in the `gr.Chatbot`
  (a message with `metadata`):
  - *Worked with 4 agents (45s)* opens into one nested thought per step the orchestrator took:
    the fields it looked up, what it saved to memory, and each specialist with its summary and
    numbers. A specialist that failed is named next to the title: *No data from Farm context*.
  - *Used 3 sources* lists the cited passages with their page, rerank score and a quote.
    Citations in the answer become `[1]`, `[2]`, matching that list.
- **While the agents work**, a pending thought with a spinner shows in the chat.
- **Suggestions** (`gr.Chatbot(examples=...)`) on the empty chat send a question straight away,
  including the demo fields that fail on purpose.
- **Light and dark mode** follow the system.

The terminal gets one JSON line per turn:

```
INFO:     agrivibe.ui: {"event": "chat_turn", "farmer_id": "frm_7f3a9c2e", "thread_id": "c3badd50-…", "status": "ok", "seconds": 43.7, "field_id": "SL-PADDY-MINNERIYA", "tools_called": ["save_requirements", "ask_weather_agent", "ask_farm_context_agent", "ask_knowledge_agent", "ask_advisory_agent"], "specialists": {"weather": "ok", "farm_context": "ok", "knowledge": "ok"}}
```

## How the code is laid out

The code is grouped by job, the way Gradio works: events run handlers, handlers ask the API, and
presenters turn the answer into what each component shows.

```
agrivibe-fe/
├── app.py                  the page: layout, and which handler runs for each event
├── settings.py             .env values and the suggestions
├── api/                    the backend
│   ├── models.py           its contract: Turn, Finding, Source, Thread…, with facts as properties
│   └── client.py           the HTTP calls, the two errors, and the one shared client (`agrivibe`)
├── handlers/               what each event does
│   ├── conversations.py    opening the page, opening, starting and deleting conversations
│   └── chat.py             asking and answering, and the turn log
├── contracts/              backend data → what each component shows (Markdown, never HTML)
│   ├── messages.py         turns as chat messages: the trace, the answer, the sources
│   ├── evidence.py         how evidence reads: tool names, citations, numbers, statuses
│   └── page.py             the header, greeting, farmer, offline alert, thread list
├── theme/
│   ├── theme.py            shadcn/ui's neutral palette as a Gradio theme
│   ├── style.css           layout and a few finishing touches
│   └── agrivibe.svg        AgriVibe's avatar
└── tests/                  one file per module; no backend and no keys needed
```

Imports run one way: `app → handlers → api + contracts`. Nothing imports `app`, and only
`api/client.py` makes HTTP calls.

- **`api/models.py`** copies only the fields of the backend's contract that the UI reads
  (`src/agrivibe/models/` in agrivibe-be). A field the backend adds later is ignored. Facts about
  the data are properties (`turn.field_id`, `turn.sources`, `finding.ok`, `finding.covered`); how
  they read on the page is the presenters' job.
- **`api/client.py`** turns every failure into one of two errors with a message a farmer can read.
  A 404 becomes `ConversationNotFound`, so the page can start fresh when a conversation was deleted
  in another tab. Handlers call `client.agrivibe` when they run, so tests swap it for a fake.
- **The presenters return Markdown, never HTML.** `gr.Chatbot` sanitises any HTML inside a message
  (`sanitize_html=True`, its default), so text from the agents and documents is safe to show.
- **Two events per question.** `ask` shows the question and a pending thought at once, without the
  queue; `.success(answer)` then waits for the backend. Gradio's progress overlay is turned off
  (`show_progress="hidden"`) because the pending thought does that job.
- **State.** The URL holds the open conversation's id; in the page, `thread_id` is a hidden
  `gr.Textbox`, not `gr.State`, because a `gr.State` never reaches the browser and the URL-writing
  JS must read it. The open conversation's turns live in `gr.State`, and the chat is rebuilt from
  them after every change.
- **The look is mostly theme.** `gr.themes.Base(...).set(...)` sets Gradio's own variables, for
  light and dark, so every stock component follows. `theme/style.css` (about 30 rules) does layout
  and a few finishing touches. It names our own `elem_classes` (`.app-*`) and a handful of Gradio's
  semantic classes (`.message.bot`, `.example`, `.icon-button`), never its generated `svelte-*` ones. Gradio 6 takes the theme and CSS in `launch()`, passed as
  `demo.launch(**LAUNCH)`, which loads the theme and `css_paths=[style.css]`.
- **An earlier version** built shadcn-style components on `gr.HTML` (custom templates, scoped CSS,
  JavaScript events). It looks closer to shadcn's template but takes twice the code. It is kept at
  the git tag `ui-custom-components`.

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
