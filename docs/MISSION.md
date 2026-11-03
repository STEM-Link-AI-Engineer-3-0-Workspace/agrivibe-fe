# Mission: Gradio + API development for the AgriVibe full stack

## Why
The AIE 3.0 cohort has built AgriVibe's agent core with Sachith. Level 6 Lesson 5 turns it into a full-stack app: an API with persisted threads, and a Gradio frontend over it. Learners need to explain, run and extend that architecture on their own, and Manu needs a review pack that carries the session's picture.

## Success looks like
- Draw the picture from memory: browser → Gradio BFF → FastAPI (API, services, agent core) → Postgres and FieldSat.
- Trace one `POST /chat` request end to end, naming where the thread and the turn are written.
- Explain why identity never comes from the frontend, and where real auth would plug in (`current_farmer`).
- Read `agrivibe-fe` and say which folder to change for a given feature (api, contracts, handlers, theme).
- Add a small feature across both repos (an endpoint, a client call, a handler, a component).

## Constraints
- Python only; the cohort is not expected to know React or Next.js.
- Stock Gradio components; single-tenant identity from `.env`; no auth service yet.
- The emphasis is the architecture, not line-by-line code.

## Out of scope
- Building an auth service or JWT handling (a separate session, maybe).
- Docker and deployment (the next sessions).
- Streaming and Mem0. (Normalising the database was done after the session: farmers, threads, turns.)
