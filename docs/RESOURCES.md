# Gradio + API development Resources

## Knowledge

- [Gradio guide: Blocks and Event Listeners](https://www.gradio.app/guides/blocks-and-event-listeners)
  How Blocks lay out components and how events map inputs to outputs. Use for: anything in `app.py`.
- [Gradio guide: State in Blocks](https://www.gradio.app/guides/state-in-blocks)
  Session state, browser state and what lives where. Use for: `gr.State` vs the hidden Textbox.
- [Gradio docs: gr.Request](https://www.gradio.app/docs/gradio/request)
  The request behind an event, including `query_params`. Use for: reading `?thread=` in `on_load`.
- [Gradio docs: Chatbot](https://www.gradio.app/docs/gradio/chatbot) and [guide: Agents and tool usage](https://www.gradio.app/guides/agents-and-tool-usage)
  Messages, metadata "thoughts", examples. Use for: the agent trace in the chat.
- [Gradio guide: Theming](https://www.gradio.app/guides/theming-guide)
  `gr.themes.Base(...).set(...)`. Use for: `theme/theme.py`.
- [FastAPI: Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/) and [Testing dependencies with overrides](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
  `Depends`, and swapping dependencies in tests. Use for: `current_farmer`, `get_chat_service`.
- [FastAPI: Lifespan events](https://fastapi.tiangolo.com/advanced/events/)
  Building shared objects at startup. Use for: where the services and the Postgres pool are created.
- [LangGraph: Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
  Checkpointers (per-thread graph state) and stores (long-term memory). Use for: what Postgres holds.
- [Pydantic: Models](https://docs.pydantic.dev/latest/concepts/models/)
  BaseModel, inheritance, `model_dump`. Use for: Turn, ChatResponse, ThreadSummary, Thread.
- [Sam Newman: Backends for Frontends](https://samnewman.io/patterns/architectural/bff/)
  The original write-up of the BFF pattern. Use for: why Gradio sits between the browser and the API.
- [Roy Fielding, ch. 5: REST](https://ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm)
  The primary source for the stateless constraint (5.1.3). Use for: "the API keeps nothing in memory".
- [The Twelve-Factor App: Processes](https://12factor.net/processes)
  Stateless, share-nothing processes; state in a backing service. Use for: why state goes to Postgres.
- [Designing Data-Intensive Applications — Kleppmann](https://dataintensive.net/)
  The book Manu named. Use for: scaling reads, caches, indexes, data models.
- [OWASP: Insecure Direct Object Reference Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet.html)
  Why a client-supplied user id is unsafe. Use for: "identity never comes from the frontend".
- [RFC 7519: JSON Web Token](https://datatracker.ietf.org/doc/html/rfc7519)
  The JWT standard. Use for: the auth-service sketch.
- [Neon: Connect from any app](https://neon.com/docs/connect/connect-from-any-app)
  Getting a connection string. Use for: `DATABASE_URL`.
- [MDN: History.pushState](https://developer.mozilla.org/en-US/docs/Web/API/History/pushState)
  Changing the URL without reloading. Use for: the thread id in the URL.
- [PostgreSQL: Indexes](https://www.postgresql.org/docs/current/indexes-intro.html) and [Redis patterns](https://redis.io/docs/latest/develop/use/patterns/)
  Use for: the "make it a data problem" answer to slow reads.
- [Martin Fowler: GUI Architectures](https://martinfowler.com/eaaDev/uiArchs.html)
  MVC, MVP and friends. Use for: "is Gradio MVC?".
- The code: [agrivibe-be (feat/fullstack-prototype)](https://github.com/STEM-Link-AI-Engineer-3-0-Workspace/agrivibe-be/tree/feat/fullstack-prototype), [agrivibe-fe](https://github.com/STEM-Link-AI-Engineer-3-0-Workspace/agrivibe-fe), [fieldsat-mcp-server](https://github.com/STEM-Link-AI-Engineer-3-0-Workspace/fieldsat-mcp-server)

## Wisdom (Communities)

- [Hugging Face forums — Gradio](https://discuss.huggingface.co/c/gradio/26)
  The Gradio team answers here. Use for: component quirks and "how do I…" questions.
- [FastAPI GitHub Discussions](https://github.com/fastapi/fastapi/discussions)
  Use for: dependency injection and API design questions.
- [LangChain Forum](https://forum.langchain.com/)
  Use for: LangGraph checkpointer and store questions.
- The AIE 3.0 cohort channel, with Manu and Sachith.

## Gaps
- No single high-trust source compares Gradio, React and Next.js as frontends for an agent API; the lesson builds that comparison from the BFF write-up and the Gradio docs.
