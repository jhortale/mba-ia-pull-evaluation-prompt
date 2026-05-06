<!-- refreshed: 2026-05-06 -->
# Architecture

**Analysis Date:** 2026-05-06

## System Overview

```text
┌─────────────────────────────────────────────────────────────────────┐
│                    CLI ENTRY POINTS (User Tier)                     │
│  pull_prompts.py | push_prompts.py | evaluate.py | metrics.py       │
│  `src/*.py` — Run manually by user from repo root                   │
└──────────┬──────────────┬──────────────┬──────────────┬─────────────┘
           │              │              │              │
           ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Provider-Agnostic LLM Layer (Abstraction)              │
│            `src/utils.py` — get_llm() / get_eval_llm()             │
│  Supports: OpenAI (gpt-4o-mini) | Google Gemini (gemini-2.5-flash)│
│  Temperature: 0.0 (deterministic) | Configurable via .env          │
└──────────┬──────────────────────────┬─────────────────────────────┘
           │                          │
           ▼                          ▼
┌────────────────────────┐  ┌─────────────────────────────────────────┐
│  Evaluation Metrics    │  │  Orchestration & Chain Invocation       │
│  `src/metrics.py`      │  │  `src/evaluate.py`                      │
│                        │  │                                          │
│ • F1-Score            │  │ • Chain composition (prompt | llm)       │
│ • Clarity             │  │ • Dataset loading (bug_to_user_story.js) │
│ • Precision           │  │ • Score aggregation & formatting         │
│ • Tone Score          │  │ • LangSmith integration                  │
│ • Acceptance Criteria │  │ • Terminal output & status reporting     │
│ • User Story Format   │  │                                          │
│ • Completeness        │  │                                          │
│                        │  │                                          │
│ All: LLM-as-Judge     │  │                                          │
│ JSON extraction       │  │                                          │
│ Error handling        │  │                                          │
└────────────────────────┘  └─────────────────────────────────────────┘
           │                          │
           └──────────────┬───────────┘
                         ▼
┌────────────────────────────────────────────────────────────────────┐
│           External Services & Data Stores                           │
│                                                                     │
│ LangSmith Hub API    LangSmith Tracing   File System               │
│ ├─ pull(prompt)      └─ Project tracing  ├─ prompts/*.yml        │
│ └─ push(prompt)                          ├─ datasets/*.jsonl     │
│                                          ├─ .env (config)        │
│                                          └─ tests/test_*.py      │
└────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| **pull_prompts.py** | Fetch prompts from LangSmith Hub, save to local YAML | `src/pull_prompts.py` |
| **push_prompts.py** | Read local YAML, validate structure, push to LangSmith Hub | `src/push_prompts.py` |
| **evaluate.py** | Orchestrate full evaluation: load dataset, invoke prompt chain, calculate metrics, display results | `src/evaluate.py` |
| **metrics.py** | Implement 7 metric functions (F1, Clarity, Precision, Tone, Acceptance, Format, Completeness) using LLM-as-Judge pattern | `src/metrics.py` |
| **utils.py** | Shared helpers: `get_llm()`, `get_eval_llm()`, YAML I/O, env validation, JSON extraction, prompt validation | `src/utils.py` |
| **test_prompts.py** | Pytest suite: validate system_prompt, role definition, format requirements, few-shot examples, no TODOs, minimum techniques | `tests/test_prompts.py` |

## Pattern Overview

**Overall:** Procedural CLI pipeline — no framework, no MVC. Four independent entry-point scripts orchestrate a linear workflow.

**Key Characteristics:**
- **No framework:** Plain Python scripts, no FastAPI/Django/Click (user runs `python src/script.py` directly)
- **Data-driven:** Prompts as YAML, dataset as JSONL, configuration via .env
- **Multi-provider:** Abstracted LLM selection (OpenAI vs Google) at utility layer
- **Stateless:** Each script reads environment, loads data, performs action, outputs
- **Async-free:** Synchronous only (no asyncio, no background jobs)

## Layers

**Layer 1: CLI Entry Points**
- Purpose: User-facing command entry points
- Location: `src/pull_prompts.py`, `src/push_prompts.py`, `src/evaluate.py`, `src/metrics.py` (also smoke test)
- Contains: Main functions that parse args, validate env vars, orchestrate workflows
- Depends on: utils.py (for LLM, YAML, validation), metrics.py (evaluate.py only)
- Used by: Direct user invocation (`python src/script.py`)

**Layer 2: Provider-Agnostic LLM Abstraction**
- Purpose: Centralize multi-provider LLM instantiation
- Location: `src/utils.py` — functions `get_llm()` and `get_eval_llm()`
- Contains: Dynamic provider detection (OpenAI vs Google), API key validation, temperature control
- Depends on: `langchain_openai`, `langchain_google_genai`, `os` (env vars)
- Used by: `evaluate.py` (main chain execution), `metrics.py` (judge model)

**Layer 3: Evaluation Metrics**
- Purpose: Score generation via LLM-as-Judge
- Location: `src/metrics.py`
- Contains: 7 metric functions that each construct a judge prompt, invoke evaluator LLM, extract JSON result
- Depends on: `get_eval_llm()` from utils, `extract_json_from_response()` for parsing
- Used by: `evaluate.py` (for scoring each example)

**Layer 4: Orchestration & Chain Invocation**
- Purpose: Workflow coordination — dataset loading, prompt composition, metric aggregation, reporting
- Location: `src/evaluate.py`
- Contains: Dataset JSONL loading, LangSmith Hub prompt pulling, chain execution (prompt | llm), score averaging, formatted terminal output
- Depends on: `get_llm()` from utils, metric functions from metrics.py, LangSmith Client, LangChain hub
- Used by: User directly

**Layer 5: Data Storage & Configuration**
- Purpose: Prompt versions, evaluation dataset, environment config
- Location: `prompts/bug_to_user_story_v*.yml`, `datasets/bug_to_user_story.jsonl`, `.env`, `requirements.txt`
- Contains: YAML prompt templates with system_prompt and user_prompt keys, JSONL evaluation examples with inputs/outputs/metadata
- Depends on: File system
- Used by: All scripts (via utils.py YAML loader, direct JSONL parsing in evaluate.py)

## Data Flow

### Primary Request Path: Evaluate Prompts

1. **Initialization** (`src/evaluate.py:main()`)
   - Check env vars: `LANGSMITH_API_KEY`, `LLM_PROVIDER`, `USERNAME_LANGSMITH_HUB`, provider-specific API key
   - Initialize LangSmith Client with API key

2. **Dataset Setup** (`src/evaluate.py:create_evaluation_dataset()`)
   - Load `datasets/bug_to_user_story.jsonl` (15 examples)
   - Create/reuse LangSmith dataset (named `{project_name}-eval`)
   - Each example has `inputs` (bug_report) and `outputs` (reference user story)

3. **Prompt Retrieval** (`src/evaluate.py:pull_prompt_from_langsmith()`)
   - Call `hub.pull(f"{username}/bug_to_user_story_v2")` → fetches ChatPromptTemplate from LangSmith Hub
   - Template contains system_prompt and user_prompt placeholders

4. **Chain Composition** (`src/evaluate.py:evaluate_prompt()`)
   - Compose: `prompt_template | get_llm()` → creates chain
   - Get LLM via `get_llm(temperature=0)` → resolves provider from `LLM_PROVIDER` env var

5. **Example Evaluation Loop** (`src/evaluate.py:evaluate_prompt_on_example()`)
   - For each of 15 examples:
     - Extract inputs: `question = bug_report` (or PR title or variant)
     - Invoke chain: `chain.invoke({"bug_report": "..."})` → returns LLM response
     - Extract output: `answer = response.content`
     - Get reference: `reference = example.outputs["reference"]`

6. **Metric Scoring** (`src/metrics.py:evaluate_*()`)
   - For each example result (question, answer, reference):
     - Call `evaluate_f1_score()` → constructs judge prompt, calls `get_eval_llm()`, extracts JSON, computes F1 = 2*(P*R)/(P+R)
     - Call `evaluate_clarity()` → scores 4 dimensions (organization, language, ambiguity, concision)
     - Call `evaluate_precision()` → scores 3 dimensions (no hallucination, focus, factual correctness)
     - Call `evaluate_tone_score()`, `evaluate_acceptance_criteria_score()`, `evaluate_user_story_format_score()`, `evaluate_completeness_score()` for specialized metrics
   - Each metric function:
     - Builds prompt with instructions and example context
     - Calls LLM: `get_eval_llm().invoke([HumanMessage(content=prompt)])`
     - Parses response: `extract_json_from_response(response.content)` → extracts score from JSON

7. **Score Aggregation** (`src/evaluate.py:evaluate_prompt()`)
   - Collect scores from all 15 examples
   - Compute averages:
     - `avg_helpfulness = (avg_clarity + avg_precision) / 2`
     - `avg_correctness = (avg_f1 + avg_precision) / 2`
     - `avg_f1_score = mean(f1_scores)`
     - `avg_clarity = mean(clarity_scores)`
     - `avg_precision = mean(precision_scores)`

8. **Results Display** (`src/evaluate.py:display_results()`)
   - Print formatted output:
     - Derived metrics (Helpfulness, Correctness)
     - Base metrics (F1-Score, Clarity, Precision)
     - Pass/fail status (all >= 0.9?)
     - Average score and alerts for failures

### Secondary Flow: Pull & Push Prompts

**Pull Flow** (`src/pull_prompts.py`)
1. Check env vars (LANGSMITH_API_KEY, USERNAME_LANGSMITH_HUB)
2. Call `hub.pull(f"{username}/bug_to_user_story_v1")`
3. Extract prompt data (system_prompt, user_prompt, metadata)
4. Save to `prompts/bug_to_user_story_v1.yml` via `save_yaml()` in utils

**Push Flow** (`src/push_prompts.py`)
1. Load `prompts/bug_to_user_story_v2.yml` via `load_yaml()` from utils
2. Validate structure: required fields, no TODOs, min 2 techniques via `validate_prompt()` (or `validate_prompt_structure()` from utils)
3. Create ChatPromptTemplate: `ChatPromptTemplate.from_messages([SystemMessage(content=system_prompt), HumanMessagePromptTemplate(...)])`
4. Push to Hub: `hub.push(f"{username}/bug_to_user_story_v2", prompt_object, tags=[...], metadata=[...])`

### State Management

- **No persistent state** — each script is independent stateless process
- **LangSmith as source of truth** for published prompts (pull source)
- **Local filesystem for iteration** (v1.yml is given, v2.yml is edited by user)
- **Environment variables** for credentials (never stored in code)
- **Dataset is static** (15 JSONL examples, not updated during evaluation)

## Key Abstractions

**`get_llm(model=None, temperature=0.0)` in `src/utils.py`**
- Purpose: Resolve LLM provider and instantiate model
- Pattern: Factory function with provider switch
- Provider detection: reads `LLM_PROVIDER` env var
- Returns: `ChatOpenAI` or `ChatGoogleGenerativeAI` instance
- Temperature: 0.0 default for deterministic output
- Used by: `evaluate.py` (chain execution), custom code

**`get_eval_llm(temperature=0.0)` in `src/utils.py`**
- Purpose: Specialized LLM for metric scoring (separate model config)
- Pattern: Wrapper around `get_llm()` that uses `EVAL_MODEL` env var instead of `LLM_MODEL`
- Returns: Same LLM types as `get_llm()`, but model name from `EVAL_MODEL`
- Used by: `metrics.py` (all 7 metric functions)

**`extract_json_from_response(response_text)` in `src/utils.py` and `src/metrics.py`**
- Purpose: Parse LLM responses that contain JSON but may have surrounding text
- Pattern: Try direct JSON parse, fallback to finding `{...}` substring
- Robustness: Handles incomplete responses, extra markdown fences
- Returns: Dict (parsed JSON) or None (fallback returns default dict in metrics.py)
- Used by: `metrics.py` (every metric function to parse judge responses)

**`validate_prompt_structure(prompt_data)` in `src/utils.py`**
- Purpose: Check required YAML fields and content validity
- Validates: description, system_prompt, version fields present; system_prompt non-empty; no [TODO] markers; min 2 techniques_applied
- Returns: `(bool, list[str])` — valid flag and error list
- Used by: `push_prompts.py` (pre-push validation), `test_prompts.py` (pytest suite)

**Metrics functions in `src/metrics.py`**
- Pattern: Each function is a specialized LLM-as-Judge scorer
- Input: (question, answer, reference) or (bug_report, user_story, reference)
- Process: Build eval prompt → call `get_eval_llm()` → extract JSON → validate score range
- Output: `{"score": float, "reasoning": str, ...}` (additional fields vary by metric)
- Examples:
  - `evaluate_f1_score()` → `{score, precision, recall, reasoning}`
  - `evaluate_clarity()` → `{score, reasoning}`
  - `evaluate_tone_score()` → `{score, reasoning}`

## Entry Points

**`src/pull_prompts.py`**
- Location: `src/pull_prompts.py`
- Triggers: `python src/pull_prompts.py` (run from repo root, CWD-relative paths)
- Responsibilities: Connect to LangSmith, fetch prompt by name, save locally as YAML
- Output: Creates/updates `prompts/bug_to_user_story_v1.yml`
- Exit code: 0 on success, 1 on failure

**`src/push_prompts.py`**
- Location: `src/push_prompts.py`
- Triggers: `python src/push_prompts.py`
- Responsibilities: Read local YAML, validate, push to Hub with metadata
- Input: Reads `prompts/bug_to_user_story_v2.yml`
- Side effect: Publishes prompt to LangSmith (accessible via hub.pull() afterward)
- Exit code: 0 on success, 1 on failure

**`src/evaluate.py`**
- Location: `src/evaluate.py`
- Triggers: `python src/evaluate.py`
- Responsibilities: Main evaluation orchestrator — loads dataset, pulls prompt, executes chain on all examples, scores with metrics, reports results
- Input: `datasets/bug_to_user_story.jsonl`, prompt from LangSmith Hub
- Output: Terminal formatted results (scores, pass/fail, next steps)
- Exit code: 0 if all metrics >= 0.9, 1 otherwise

**`src/metrics.py` (with `__main__`)**
- Location: `src/metrics.py`
- Triggers: `python src/metrics.py` (smoke test in `if __name__ == "__main__"` block)
- Responsibilities: Test all 7 metric functions with hardcoded examples, print results
- No input files — self-contained test data
- Output: Demonstrates metric output format, verifies provider config and LLM connectivity
- Exit code: Not checked (is a demo)

**pytest suite**
- Location: `tests/test_prompts.py`
- Triggers: `pytest tests/test_prompts.py` (from repo root)
- Responsibilities: Validate prompt YAML structure and content quality
- Tests: 6 assertions (system_prompt exists, role definition, format mention, few-shot examples, no TODOs, min techniques)
- Input: `prompts/bug_to_user_story_v2.yml` (expects it exists)
- Exit code: 0 if all tests pass, 1 if any fail

## Architectural Constraints

- **Threading:** Single-threaded, synchronous execution only. No asyncio, no parallel metric evaluation. Each example is scored sequentially (15 examples × 7 metrics per example = ~105 LLM calls, takes ~5-10 minutes for full run).
- **Global state:** Minimal. Environment variables loaded at script start via `load_dotenv()` in each module. No module-level singletons except implicit ones in LangChain (Client connection pooling).
- **Circular imports:** Not present — utils.py is imported by all others; metrics.py imports utils; evaluate.py imports utils and metrics.
- **Cwd-relative paths:** All data paths (`prompts/`, `datasets/`) are relative to repo root. Scripts must be run from repo root: `python src/evaluate.py` not `cd src && python evaluate.py`.
- **Environment-driven:** No hardcoded credentials, model names, or URLs. All configurable via `.env` (see `.env.example`).
- **Stateless script design:** Each script is idempotent where possible (pull/push) or additive (evaluate writes to terminal only, not files).

## Anti-Patterns

### Module-level `load_dotenv()` Calls

**What happens:** `load_dotenv()` is called at module top-level in `utils.py`, `evaluate.py`, `metrics.py`. If .env is not found, silently continues (dotenv default behavior). If .env is found, loads all vars into `os.environ`.

**Why it's wrong:** Environment vars are loaded multiple times (once per imported module). If .env changes during script execution, the change is not reflected. No clear point of env initialization.

**Do this instead:** Consolidate `load_dotenv()` call in `src/__init__.py` or at the very start of each entry-point script (pull_prompts.py, push_prompts.py, evaluate.py). Keep it out of utils.py. Validate required vars immediately after loading, not lazily in utility functions.

### Direct LLM Instantiation in Metrics

**What happens:** `metrics.py` imports `get_eval_llm` from utils, but also duplicates `extract_json_from_response()` locally (exists in both utils.py and metrics.py).

**Why it's wrong:** Code duplication. If JSON extraction logic changes, must update in two places. Risk of drift.

**Do this instead:** Export `extract_json_from_response()` from utils.py as the single source of truth. metrics.py should import it, not redefine it.

### Hardcoded Metric Weights

**What happens:** In `evaluate.py`, derived metrics are computed as:
- `avg_helpfulness = (avg_clarity + avg_precision) / 2`
- `avg_correctness = (avg_f1 + avg_precision) / 2`

These are fixed ratios with no documentation of why.

**Why it's wrong:** Weights are arbitrary and not configurable. If business requirements change (e.g., clarity should count more than precision), code must change. Requirements are embedded in logic, not documented.

**Do this instead:** Define metric weights in `.env` or a config section:
```python
METRIC_WEIGHTS = {
    "helpfulness": {"clarity": 0.5, "precision": 0.5},
    "correctness": {"f1_score": 0.5, "precision": 0.5},
}
```
Or at least document in comments: "Helpfulness is average of Clarity and Precision (50/50 weight) because..."

### No Idempotency Check in Push

**What happens:** `push_prompts.py` always pushes, even if the same version is being pushed again.

**Why it's wrong:** Repeated pushes overwrite the Hub version with identical data. Wastes API calls. No warning if prompt hasn't changed.

**Do this instead:** Compute hash of `prompts/bug_to_user_story_v2.yml` content. Compare with hash of previously pushed version (store in `.prompt_hash` file or metadata in Hub). Only push if hash differs. Log: "Prompt unchanged, skipping push" if no diff.

## Error Handling

**Strategy:** Defensive validation with early exit. Check requirements (env vars, file existence) at script start. Fail fast with clear error messages.

**Patterns:**
- **Env var validation** (`check_env_vars()` in utils.py): List missing vars, explain where to find them (URLs in error message)
- **File I/O** (`load_yaml()`, `save_yaml()`): Try/except with specific error messages (FileNotFoundError vs YAMLError vs generic Exception)
- **LLM calls**: Catch exceptions, return error dict with 0 score + error message string, continue to next example (no fatal crash)
- **JSON extraction** (`extract_json_from_response()`): Graceful fallback — if no JSON found, log warning and return default `{"score": 0.0}`
- **Dataset loading** (`load_dataset_from_jsonl()`): Check file exists before opening, skip empty/invalid JSONL lines with warning, continue with valid lines

## Cross-Cutting Concerns

**Logging:** Console-based (no log files). Uses `print()` with emoji prefixes:
- `✓` — success
- `✗` — failure (metric < 0.9)
- `❌` — error (exception, missing file, failed API call)
- `⚠️` — warning (skipped test, default value used)
- `=` lines for section headers

No structured logging (no JSON logs, no log levels). All output to stdout.

**Validation:** Happens at multiple points:
- Script start: env vars (fail fast)
- File loading: YAML structure, JSONL JSON validity
- Prompt: required fields, non-empty system_prompt, no [TODO], min techniques
- Metrics: score range (0.0 to 1.0), JSON format

**Authentication:** All via .env variables:
- `LANGSMITH_API_KEY` — API key for LangSmith (required for all ops)
- `OPENAI_API_KEY` or `GOOGLE_API_KEY` — LLM provider key (based on `LLM_PROVIDER`)
- No intermediate token storage, no session management

---

*Architecture analysis: 2026-05-06*
