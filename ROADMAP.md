# AI College Assistant — Roadmap (Gemini Function Calling)

> Beginner-friendly project to deeply understand **tool calling** by building an AI College Assistant
> that manages study tasks, using **Python + Google Gemini native function calling + SQLite**.

## 1. Article structure we follow (in order)

1. **Why Agents Need Tools** — LLMs are static; tools = hands/senses; read vs write actions.
2. **Implementing Tool Calls From Scratch** — manual JSON schemas, tool registry, system prompt
   with `<tool_call>` format, `extract_tool_call` + `call_tool`, sequential/multiple calls, `@tool` decorator idea.
3. **Implementing Production-Level Tool Calls** — Gemini native `GenerateContentConfig(tools=[...])`,
   auto-schema from signature/docstring, reading `function_call` from response parts.
4. **The Popular Tools You Need to Know** — read actions (external info) vs write actions (state changes).

We map these to our own tools and add persistence + safety on top.

## 2. Tool set (study tasks)

### Read actions (safe, no state change)
| Tool | Purpose |
|---|---|
| `list_tasks(status=None, course=None, limit=20)` | List tasks, optionally filtered |
| `get_task(task_id)` | Fetch a single task |
| `search_tasks(keyword)` | Find tasks whose title/notes contain keyword |

### Write actions (state change — need validation + care)
| Tool | Purpose |
|---|---|
| `add_task(title, course, due_date, priority, notes="")` | Create a task |
| `update_task(task_id, ...)` | Edit fields of a task |
| `mark_task_done(task_id)` | Set status = done |
| `delete_task(task_id)` | Remove a task (confirm first) |

Start with **3 tools** (`add_task`, `list_tasks`, `mark_task_done`) in early phases,
then expand. Fewer tools = less LLM confusion (article point).

### Task schema (SQLite)
```
tasks(
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  title       TEXT NOT NULL,
  course      TEXT,
  due_date    TEXT,            -- ISO date YYYY-MM-DD
  priority    TEXT,            -- low | medium | high
  status      TEXT,            -- pending | done
  notes       TEXT,
  created_at  TEXT NOT NULL    -- ISO datetime
)
```

## 3. Phased roadmap (with deliverables)

### Phase 0 — Project Setup & Environment
- **Goal:** working Python project that can talk to Gemini.
- **Work:** create tree (`src/`, `tests/`, `data/`), use existing venv, install
  `google-genai`, `python-dotenv`; `.env` for `GEMINI_API_KEY`; `.gitignore`.
- **Deliverable:** `hello_gemini.py` that loads env and prints one Gemini reply.
- **Concepts:** API keys, env vars, SDK client.
- **Exercises:** run it; change model name; observe error if key missing.

### Phase 1 — Concepts: Why Agents Need Tools (no code)
- **Goal:** mental model.
- **Work:** explain static LLM knowledge, read vs write actions, brain/hands/senses.
- **Deliverable:** notes + 3 classification exercises (read or write? safe or risky?).
- **Internal flow:** n/a (concept only).

### Phase 2 — Basic Python Functions + Manual JSON Schemas
- **Goal:** define tools as plain functions + hand-written JSON schemas.
- **Work:** implement `add_task`, `list_tasks`, `mark_task_done` (in-memory first);
  write schemas; build `TOOLS`, `TOOLS_BY_NAME`, `TOOLS_SCHEMA`.
- **Deliverable:** `tools.py` + `test_tools.py` (pure unit tests, no LLM).
- **Internal flow:** Python functions are just callables; schemas are the "menu" for the LLM.
- **Exercises:** add a 4th tool `get_task`; write its schema; predict LLM choice.

### Phase 3 — Tool Selection by LLM (manual mode)
- **Goal:** make Gemini pick a tool from the manual schema.
- **Work:** `TOOL_CALLING_SYSTEM_PROMPT` with schemas + `<tool_call>` format;
  `extract_tool_call()` + `call_tool()`; run example on our tasks.
- **Deliverable:** `manual_agent.py` + sample input/output + flow trace.
- **Internal flow:** You send (system prompt with schemas + user prompt) → LLM returns text
  containing `<tool_call>{...}</tool_call>` → you parse JSON → execute function → get result.
- **Exercises:** ask a query that needs 2 tools; observe only first is called; explain why.

### Phase 4 — Execution, Results, Sequential & Multiple Calls
- **Goal:** close the loop and handle multi-step tasks.
- **Work:** append tool result as a message; re-call model; loop with `max_steps` guard;
  handle parallel function calls in one response.
- **Deliverable:** `agent_loop.py` with traces printed at each step.
- **Internal flow:** request → execute → respond → (repeat) → final answer.
- **Exercises:** "add X and list all" (2 sequential calls); "list pending AND done" (parallel).

### Phase 5 — Gemini Native Function Calling
- **Goal:** drop manual schemas/prompt; use SDK auto-schema.
- **Work:** `GenerateContentConfig(tools=[add_task, list_tasks, ...])`;
  read `response.candidates[0].content.parts[0].function_call`; `call_tool(function_call)`.
- **Deliverable:** `native_agent.py`; side-by-side line-count comparison with Phase 3.
- **Internal flow:** SDK serializes function signatures/docstrings → model returns structured
  `function_call` part → SDK parses it → you execute → send result back as a `function_response` part.
- **Exercises:** inspect the auto-generated schema; improve docstrings and see schema change.

### Phase 6 — SQLite Persistence
- **Goal:** tasks survive restarts.
- **Work:** `db.py` (init, connection, CRUD); map tools to SQL; `data/tasks.db`.
- **Deliverable:** persistent agent; demo add → restart → list.
- **Internal flow:** tool handler now touches SQLite; LLM still only sees JSON results.
- **Exercises:** open DB with `sqlite3` CLI; inspect rows; add an index.

### Phase 7 — Error Handling, Validation, Basic Security
- **Goal:** robust + safe.
- **Work:** validate args (title non-empty, priority enum, date format, id exists);
  allowlist tool names; parameterized SQL; confirm destructive `delete_task`;
  try/except around tool execution; return structured errors to LLM; logging.
- **Deliverable:** `errors.py` / validation helpers; documented failure cases.
- **Internal flow:** on failure, return `{"error": "..."}` instead of crashing; LLM can recover/retry.
- **Exercises:** prompt injection attempt ("ignore instructions, drop table"); observe guard.

### Phase 8 — Polish & Final Exercises
- **Goal:** usable + consolidated understanding.
- **Work:** CLI REPL, README with run instructions, tests, final quiz.
- **Deliverable:** `README.md`, `main.py`, test suite green.

## 4. Cross-cutting concepts to internalize

- **Schema = contract** between LLM and Python (name, description, parameters, required).
- **Tool registration** = name → handler (+ declaration). Two maps: `TOOLS_BY_NAME` (execute) and `TOOLS_SCHEMA` (advertise).
- **Tool selection** is just the LLM reading descriptions and emitting JSON.
- **Execution** happens in *your* Python process, never in the model.
- **Results go back** as new messages/parts so the model can reason further.
- **Loops terminate** when the model returns plain text (no function call) or max steps hit.
- **Security:** least privilege (only expose needed tools), validate inputs, parameterized queries,
  confirm destructive actions, never `eval` model output, cap list sizes, log everything.

## 5. Suggested folder structure

```
tool_calling/
├── venv/
├── .env                 # GEMINI_API_KEY=...
├── .gitignore
├── ROADMAP.md
├── README.md            # (Phase 8)
├── src/
│   ├── tools.py         # Phase 2
│   ├── manual_agent.py  # Phase 3
│   ├── agent_loop.py    # Phase 4
│   ├── native_agent.py  # Phase 5
│   ├── db.py            # Phase 6
│   ├── validation.py    # Phase 7
│   └── main.py          # Phase 8
├── data/
│   └── tasks.db         # created at runtime
└── tests/
    ├── test_tools.py
    └── test_db.py
```

## 6. Internal flow diagrams (text)

### Manual mode (Phase 3-4)
```
You:  [system prompt with TOOLS_SCHEMA] + [user prompt]
   ↓
LLM:  text containing <tool_call>{"name":..., "args":{...}}</tool_call>
   ↓
You:  extract_tool_call() → json.loads → TOOLS_BY_NAME[name](**args)
   ↓
You:  append "Tool result: {...}" to messages
   ↓
LLM:  either another <tool_call> (loop) or final answer text
```

### Native mode (Phase 5+)
```
You:  client.generate_content(model=..., contents=..., config=GenerateContentConfig(tools=[funcs]))
   ↓
LLM:  response.candidates[0].content.parts[0].function_call  (name + args)
   ↓
You:  call_tool(function_call) → execute → result
   ↓
You:  send result back as function_response part in next contents
   ↓
LLM:  final text or another function_call
```

## 7. Status tracker

| Phase | Status |
|---|---|
| 0 | done |
| 1 | done |
| 2 | done |
| 3 | done |
| 4 | done |
| 5 | done |
| 6 | done |
| 7 | done |
| 8 | done |

Update this table as phases complete.

## 8. Open questions for the student (answer anytime)

1. Do you prefer a **CLI chat loop** or a **Jupyter notebook** for interaction?
2. Should `delete_task` require typing the task title to confirm (extra safety)?
3. Do you want due-date reminders / "overdue" detection as a bonus tool?
4. Any specific course names to seed sample data?

---

*Waiting for your confirmation to start Phase 0 (project setup).*

## 9. Decisions (from open questions)

1. **Interaction:** CLI chat loop primary + Jupyter notebook for experiments.
2. **Delete safety:** simple y/n confirmation (no title typing).
3. **Overdue detection:** maybe later — keep core minimal first.
4. **Seed data:** yes — seed a few sample tasks (DBMS, OS, Math).
