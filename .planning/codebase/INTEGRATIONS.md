# External Integrations

**Analysis Date:** 2026-05-06

## APIs & External Services

**LLM Generation & Evaluation:**
- OpenAI API - LLM provider for prompt execution and evaluation
  - SDK: `langchain-openai` (ChatOpenAI class in `src/utils.py:193-207`)
  - Models: `gpt-4o-mini` for generation (default), `gpt-4o` for evaluation
  - Auth: Environment variable `OPENAI_API_KEY`
  - Configuration location: `.env.example` (lines 10-11)
  - Used by: `src/utils.py` (get_llm, get_eval_llm), `src/evaluate.py`, `src/metrics.py`

- Google Gemini API - LLM provider for prompt execution and evaluation (free tier)
  - SDK: `langchain-google-genai` (ChatGoogleGenerativeAI class in `src/utils.py:209-223`)
  - Models: `gemini-2.5-flash` for both generation and evaluation
  - Auth: Environment variable `GOOGLE_API_KEY`
  - Rate limits: 15 req/min, 1500 req/day (documented in README.md:98)
  - Configuration location: `.env.example` (lines 13-14)
  - Used by: `src/utils.py` (get_llm, get_eval_llm), `src/evaluate.py`, `src/metrics.py`

**Prompt Management:**
- LangSmith Prompt Hub - Central repository for prompt versions
  - SDK: `langsmith` (hub.pull, hub.push methods)
  - Endpoint: `https://api.smith.langchain.com` (configured in `.env.example`:3)
  - Auth: Environment variable `LANGSMITH_API_KEY`
  - Auth: Environment variable `USERNAME_LANGSMITH_HUB` (for Hub namespace/username)
  - Project configuration: `LANGSMITH_PROJECT` environment variable (default: "prompt-optimization-challenge-resolved")
  - Features:
    - **Pull** (read): `hub.pull("{username}/bug_to_user_story_v2")` in `src/evaluate.py:108`
    - **Push** (write): `hub.push()` in `src/push_prompts.py` (skeleton)
    - Prompts are public by default after push
    - Hub is the **source of truth** for evaluation (not local YAML files)
  - Configuration location: `.env.example` (lines 1-8)
  - Used by: `src/evaluate.py`, `src/pull_prompts.py`, `src/push_prompts.py`

- LangSmith Tracing & Datasets - Monitoring and evaluation infrastructure
  - SDK: `langsmith` (Client class)
  - Features:
    - Dataset creation and management (see `src/evaluate.py:64-102`)
    - Example management (`client.list_examples`, `client.create_example`)
    - Automatic tracing of LLM calls when `LANGSMITH_TRACING=true`
  - Configuration: `LANGSMITH_TRACING`, `LANGSMITH_ENDPOINT`, `LANGSMITH_API_KEY`
  - Location: `.env.example` (lines 1-5)
  - Used by: `src/evaluate.py` for creating evaluation datasets and recording results

## Data Storage

**Databases:**
- None - This is a CLI tool without persistent database

**File Storage:**
- Local filesystem only
  - Prompts: `prompts/bug_to_user_story_v1.yml` (initial), `prompts/bug_to_user_story_v2.yml` (optimized)
  - Datasets: `datasets/bug_to_user_story.jsonl` (15 evaluation examples, pre-loaded)
  - Configuration: `.env` (created locally from `.env.example`)

**Caching:**
- None - Each evaluation run pulls fresh prompts from LangSmith Hub

## Authentication & Identity

**Auth Provider:**
- Custom (API key-based)
  - OpenAI: API key authentication via `OPENAI_API_KEY` environment variable
  - Google Gemini: API key authentication via `GOOGLE_API_KEY` environment variable
  - LangSmith: API key authentication via `LANGSMITH_API_KEY` environment variable
  - LangSmith Hub username: `USERNAME_LANGSMITH_HUB` (identifies user namespace in Hub)

**Implementation:**
- Environment variable loading via `python-dotenv` in `src/utils.py:12`
- Validation in `src/utils.py:check_env_vars()` function
- Lazy loading of credentials in `get_llm()` and `get_eval_llm()` functions
- Error handling with helpful messages (lines 196-229)

## LLM Provider Selection

**Multi-provider architecture** in `src/utils.py:176-229`:

```python
# get_llm() function selects provider based on LLM_PROVIDER env var
provider = os.getenv('LLM_PROVIDER', 'openai').lower()

if provider == 'openai':
    return ChatOpenAI(...)
elif provider == 'google':
    return ChatGoogleGenerativeAI(...)
```

**Configuration:**
- `LLM_PROVIDER`: One of `'openai'` or `'google'` (default: 'openai')
- `LLM_MODEL`: Model name for generation (default: 'gpt-4o-mini' for OpenAI)
- `EVAL_MODEL`: Model name for evaluation (default: 'gpt-4o' for OpenAI)
- Configuration location: `.env.example` (lines 16-23)

**Runtime behavior:**
- Evaluation always uses `get_eval_llm()` which respects `EVAL_MODEL` setting
- Generation uses `get_llm()` which respects `LLM_MODEL` setting
- Both functions respect `LLM_PROVIDER` to select OpenAI or Google Gemini

## Monitoring & Observability

**Error Tracking:**
- None explicit. Errors are logged to stdout via print statements.

**Logs:**
- Console-based logging via print() statements
- Progress indicators: ✓, ✗, ❌, ✅, ⚠️
- Structured metrics output in `src/evaluate.py:242-274` (display_results function)

**LangSmith Tracing:**
- Automatic when `LANGSMITH_TRACING=true` in `.env`
- Traces all LLM calls and chain executions
- Viewable in LangSmith dashboard at `https://smith.langchain.com/projects/`
- Dataset results published to LangSmith for review

## CI/CD & Deployment

**Hosting:**
- Not deployed. Local CLI tool only.

**CI Pipeline:**
- None configured. Manual execution via:
  ```bash
  python src/pull_prompts.py      # Step 1: Pull prompts
  python src/push_prompts.py      # Step 3: Push optimized versions
  python src/evaluate.py          # Step 4: Evaluate and score
  pytest tests/test_prompts.py    # Validation tests
  ```

## Environment Configuration

**Required env vars (at minimum):**
- `LANGSMITH_API_KEY` - LangSmith workspace authentication
- `LANGSMITH_ENDPOINT` - LangSmith API endpoint (default: `https://api.smith.langchain.com`)
- `USERNAME_LANGSMITH_HUB` - Your LangSmith Hub username (for prompt namespace)
- `LLM_PROVIDER` - One of `'openai'` or `'google'` (default: `'openai'`)
- `OPENAI_API_KEY` (if LLM_PROVIDER=openai) - OpenAI authentication
- `GOOGLE_API_KEY` (if LLM_PROVIDER=google) - Google Gemini authentication

**Optional env vars:**
- `LANGSMITH_TRACING` - Enable tracing (default: true)
- `LANGSMITH_PROJECT` - Project name in LangSmith (default: "prompt-optimization-challenge-resolved")
- `LLM_MODEL` - Generation model (default: 'gpt-4o-mini' or 'gemini-2.5-flash')
- `EVAL_MODEL` - Evaluation model (default: 'gpt-4o' or 'gemini-2.5-flash')

**Secrets location:**
- `.env` file (in project root) — NEVER committed to git
- Template: `.env.example` — included in repo with empty values
- Loaded via `python-dotenv` in all entry points

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## Data Flow Summary

1. **Pull Phase**: `src/pull_prompts.py` uses `hub.pull()` to fetch `{username}/bug_to_user_story_v1` from LangSmith Hub and saves locally as YAML
2. **Local Optimization**: Developer manually edits YAML to create `prompts/bug_to_user_story_v2.yml`
3. **Push Phase**: `src/push_prompts.py` reads local YAML and uses `hub.push()` to publish to LangSmith Hub as `{username}/bug_to_user_story_v2`
4. **Evaluation Phase**: `src/evaluate.py`:
   - Loads dataset from `datasets/bug_to_user_story.jsonl`
   - Creates/updates evaluation dataset in LangSmith via `client.create_dataset()`
   - **Pulls prompt from Hub** at runtime (source of truth): `hub.pull("{username}/bug_to_user_story_v2")`
   - Invokes prompt against each dataset example using selected LLM (OpenAI or Google Gemini)
   - Calls `src/metrics.py` functions to score responses using LLM-as-Judge
   - Publishes results to LangSmith dashboard
5. **Metrics Evaluation**: `src/metrics.py` functions use the configured evaluation LLM to score:
   - F1-Score (precision + recall)
   - Clarity (structure, language, conciseness)
   - Precision (hallucinations, focus, factual correctness)
   - Helpfulness (derived from clarity + precision)
   - Correctness (derived from F1-Score + precision)

---

*Integration audit: 2026-05-06*
