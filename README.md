# Phormeta

A deliberately small agentic AI hackathon starter. No case-specific solution yet.

```text
Streamlit (app.py)
    -> one OpenAI Agent + Runner (agent.py)
    -> agent tools (tools/demo_tools.py)
    -> application logic / SQLite (db.py)
```

- `agent_sessions.db`: conversation memory managed by the SDK's `SQLiteSession`.
- `app.db`: application data, currently three placeholder items and a notes table.

Both files live beside the source files and are ignored by Git. Reset conversation
starts a new session ID; it does not erase earlier sessions or application data.
The browser session keeps its ID across Streamlit reruns. A new browser session
starts fresh; there is intentionally no session picker or login.

## Windows setup (PowerShell)

Use Python 3.13 (the tested version), with this repository as the current directory.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

Fill in `OPENAI_API_KEY` and `OPENAI_MODEL` locally. Choose a model your API project
can access that supports function tools through the Responses API. Neither value
has a default. Existing environment variables take precedence over `.env`.

```powershell
python -m streamlit run app.py
```

If PowerShell blocks activation, use the interpreter directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open http://localhost:8501. The application initializes its database automatically.
Restart Streamlit after changing `.env`.

## Try it

> Show me the available demo items, multiply Demo Alpha's value by 3, and save a
> short note about the result.

Expect the list, calculation (`37.5`), a saved note ID, and a final explanation.
Expand **Agent Activity** to inspect SDK tool calls, arguments, and results.
Then ask "What result did we just calculate?" to check conversation memory.
Use **Reset conversation** and verify the new conversation does not recall it.

The SDK runs the tool loop with a limit of 8 model turns. Failed runs can already
have saved notes; inspect activity before retrying a write. Errors are shown
without raw exception bodies, which could contain credentials or request data.
SDK tracing stays enabled with its default behavior; traces may include prompts
and tool data. Activity is a compact view of SDK run items, not a separate tracer.

## How to adapt this tomorrow

1. `agent.py`: change the instructions and tool list.
2. `tools/demo_tools.py`: replace the demo tools with case-specific functions.
3. `db.py`: replace the placeholder schema, queries, and seeds.
4. `app.py`: adapt the Streamlit UI.

Keep the core `Agent` + `Runner` architecture. Schema changes belong in `db.py`,
not the agent. `CREATE TABLE IF NOT EXISTS` does not migrate existing tables;
if all local data is disposable, stop the app and remove `app.db` before trying
a replacement schema. Otherwise write a small explicit migration.

## Potential additions depending on the case

Add SDK tools to the agent's tool list in `agent.py` only when needed:

- `WebSearchTool`: live external information.
- `CodeInterpreterTool`: file/data analysis.
- `FileSearchTool`: document retrieval (requires a configured vector store).
- Approval gates: use SDK `needs_approval=True` for irreversible tools such as
  `place_order`, `issue_refund`, `delete_record`, or `send_message`. Add UI handling
  for SDK interruptions and approve/reject/resume before enabling those tools.
- Additional agents: only if the case clearly benefits from separation.

## Hackathon constraints

Only three direct dependencies are pinned in `requirements.txt`; their transitive
dependencies are resolved by pip. Set up every teammate's environment before the
event. Internet access, API quota, model access, and API latency remain external
dependencies. The turn limit bounds model turns, not total time or spending.
The calculator uses ordinary floating-point arithmetic; replace it with decimal
arithmetic if the actual case requires exact monetary calculations.
SQLite is intended for this small local demo; run from a local unsynced folder if
OneDrive or concurrent writers cause file locking.

Official reference: [OpenAI Agents SDK](https://developers.openai.com/api/docs/guides/agents/sdk).

## Verification performed

Verified on Python 3.13.7: dependency consistency, imports, database initialization,
reads/writes, tools and invalid arguments, SDK execution with simulated model
responses, persistent session history and isolation, turn limits, Streamlit UI
submit/reset/error paths, and a running server's HTTP health endpoint. Git ignore
rules and source secret patterns were checked. Live model behavior and trace
export remain untested because neither API credentials nor a model were configured.
