# Codebase Concerns

**Analysis Date:** 2026-05-06

## Unimplemented Skeletons (Blocking)

**Pipeline cannot run without completing these:**

### Missing Prompt File (v2)
- **Files:** `prompts/bug_to_user_story_v2.yml` (does not exist)
- **Impact:** `src/evaluate.py` line 324 tries to evaluate `{USERNAME_LANGSMITH_HUB}/bug_to_user_story_v2` from the LangSmith Hub, which requires `src/push_prompts.py` to have published it first. Without this file, no evaluation can occur.
- **Blocker:** Complete entire pipeline (pull → optimize → push → evaluate).
- **Fix approach:** Student must create `prompts/bug_to_user_story_v2.yml` with optimized prompt, then run `src/push_prompts.py` (which is also a skeleton).

### Unimplemented pull_prompts.py
- **Files:** `src/pull_prompts.py` lines 22–32 (empty function bodies with `...`)
- **Impact:** Student cannot pull the v1 prompt from LangSmith Hub to understand the starting point. The README (lines 104–116) explicitly requires this as step 1 of the workflow.
- **Blocker:** Initial prompt analysis phase.
- **Fix approach:** Implement `pull_prompts_from_langsmith()` to call `hub.pull(prompt_name)` and save to YAML using `utils.save_yaml()`. See `src/evaluate.py` lines 105–140 for hub.pull pattern.

### Unimplemented push_prompts.py
- **Files:** `src/push_prompts.py` lines 23–52 (empty function bodies with `...`)
- **Impact:** Optimized prompt (v2) cannot be published to the LangSmith Hub, so `src/evaluate.py` will fail to find the prompt (line 189). Without this, the full iteration cycle is blocked.
- **Blocker:** Push-and-evaluate loop.
- **Fix approach:** Implement `push_prompt_to_langsmith()` to read v2 YAML, validate structure, construct ChatPromptTemplate, and call `hub.push()`. Pattern exists in LangChain docs; see evaluation feedback in `src/evaluate.py` lines 115–132 for error handling guidance.

### Empty Test Bodies
- **Files:** `tests/test_prompts.py` lines 20–42 (six `pass` statements)
- **Impact:** Tests do not validate prompt quality. README (lines 184–191) explicitly requires 6 tests. Pytest will pass vacuously; student has no validation harness.
- **Blocker:** Validation phase completeness.
- **Fix approach:** Implement using `utils.validate_prompt_structure()` (lines 119–147) as reference. Each test should:
  - Load YAML from `prompts/bug_to_user_story_v2.yml`
  - Check: system_prompt exists, role definition present ("Você é..."), format mentions ("User Story", "Markdown"), few-shot examples included, no [TODO] markers, techniques_applied list has ≥2 entries.

---

## Hub-vs-File Divergence Trap (Highest Impact Gotcha)

**Single highest risk for confusion:**

### Problem
- **Files:** `src/evaluate.py` line 189 (`hub.pull(prompt_name)`), line 324 (evaluates from Hub, not from local YAML)
- **Evidence:** Lines 1–12 state "Puxa prompts otimizados do LangSmith Hub (fonte única de verdade)" but student edits `prompts/bug_to_user_story_v2.yml` locally. Any local YAML edit **is invisible to scoring** until published via `src/push_prompts.py`.
- **Scenario:** Student edits `prompts/bug_to_user_story_v2.yml` locally and runs `python src/evaluate.py` expecting to see new scores. Receives old scores (from previously pushed v2) or 404 error (if v2 not yet pushed). Confusion ensues: "Why don't my local changes matter?"
- **Why it matters:** This is the single most likely way a student gets stuck in the challenge.

### Fix approach
1. README lines 145–158 should explicitly warn: "Local YAML edits are NOT evaluated until you run `python src/push_prompts.py`."
2. `src/evaluate.py` line 315 could output a reminder: "Tip: If you edited prompts/bug_to_user_story_v2.yml, remember to run `python src/push_prompts.py` first."
3. Student must internalize workflow: edit YAML → push → evaluate, not edit YAML → evaluate.

---

## Derived-Metric Coupling (Precision is Disproportionate)

**Design smell: derived metrics are tightly coupled to one base metric:**

### Problem
- **Files:** `src/evaluate.py` lines 220–221
  ```python
  avg_helpfulness = (avg_clarity + avg_precision) / 2
  avg_correctness = (avg_f1 + avg_precision) / 2
  ```
- **Evidence:** Precision feeds into **two of five gated metrics** (helpfulness, correctness). Base metrics are F1, Clarity, Precision (line 10 comments claim five base metrics; only three are implemented in evaluate.py).
- **Impact:** Raising or dropping precision by 0.1 affects:
  - helpfulness: ±0.05
  - correctness: ±0.05
  - precision direct: ±0.10
  - Overall pass/fail disproportionately hinges on precision score.
- **Why it matters:** If `metrics.py` evaluate_precision() has a bug or bias (e.g., LLM-as-Judge prompt is too harsh), the entire evaluation cascades. The four unused metrics in `metrics.py` (tone, acceptance_criteria, user_story_format, completeness) are never called by evaluate.py, so students may assume they are part of scoring when they are not.

### Fix approach
1. Document in README: "Derived metrics (Helpfulness, Correctness) are calculated from base metrics (F1, Clarity, Precision). Formulas: Helpfulness = (Clarity + Precision) / 2; Correctness = (F1 + Precision) / 2. Precision has 3x weight in pass/fail logic."
2. In `src/metrics.py`, move formulas to a docstring comment so they are visible to maintainers.
3. Consider if the weighting is intentional; if not, document why precision is overweighted.

---

## Live-LLM Exposure (Cost & API Dependency)

**Every metric invocation hits a paid API:**

### Problem
- **Files:** `src/metrics.py` lines 67, 160, 246 (evaluate_f1_score, evaluate_clarity, evaluate_precision all call `get_evaluator_llm()` and invoke LLM)
- **Evidence:** `src/utils.py` lines 232–243 shows `get_eval_llm()` returns a live ChatOpenAI or ChatGoogleGenerativeAI instance. Line 30 in metrics.py imports `from utils import get_eval_llm`. Each call to evaluate_f1_score, evaluate_clarity, or evaluate_precision sends a network request.
- **Cost:** README lines 86–98 estimates ~$1–5 per evaluation cycle for OpenAI (gpt-4o). With 3–5 expected iterations, cost can accumulate quickly.
- **Gotcha:** Running `python src/metrics.py` directly (lines 697–773 includes __main__ test block) will invoke the LLM and charge the account, even as a smoke test.
- **Why it matters:** Student may accidentally run metrics.py multiple times for debugging and incur unexpected costs. Gemini free tier hits 15 req/min rate limit (line 98).

### Fix approach
1. README should add warning section: "⚠️ Cost Warning: Every call to `python src/evaluate.py` hits the LLM API. With 15 examples in the dataset and 3 metrics per example, expect ~$0.30–1.00 per evaluation run on gpt-4o. Plan 3–5 iterations."
2. Add environment variable `DRY_RUN=true` to metrics.py to return mock scores without hitting API, for testing.
3. Prompt the user at the start of evaluate.py: "About to evaluate {N} examples with {M} metrics. Estimated cost: ${X}. Continue? (y/n)".

---

## Judge JSON-Parse Fragility (Silent Failures)

**Parse failures silently drag averages down:**

### Problem
- **Files:** `src/metrics.py` lines 43–64 (extract_json_from_response in metrics.py); `src/utils.py` lines 150–173 (extract_json_from_response in utils.py)
- **Evidence:** Both functions catch `json.JSONDecodeError` and return fallback dicts:
  - metrics.py line 64: `return {"score": 0.0, "reasoning": "Erro ao processar resposta"}`
  - utils.py line 173: `return None` (more graceful)
  - metrics.py line 63 prints a warning, but utils.py does not.
- **Impact:** If an LLM response is malformed or the JSON extraction logic fails, the metric silently returns 0.0, dragging the average down. Example:
  - If 1 of 15 examples gets a malformed response, that example scores 0.0, pulling average from 0.95 to 0.933, causing failure (threshold is 0.9000).
  - Student sees "Precision: 0.93 ✗" with no indication why one example dropped to zero.
- **Why it matters:** Debugging becomes hard. No detailed error log shows which example(s) had parse failures.

### Fix approach
1. Collect parse failures in a list during evaluate_prompt() (line 181–239 in evaluate.py).
2. At end of display_results() (line 242–274), if any failures occurred, print:
   ```
   ⚠️  {N} examples had JSON parse errors and defaulted to 0.0 score.
   Review LLM responses in the LangSmith trace dashboard.
   ```
3. In metrics.py, raise a custom exception instead of silently defaulting, so it propagates as a visible error rather than a silent 0.0.

---

## Hardcoded/CWD-Dependent Paths

**Relative paths break if run from wrong directory:**

### Problem
- **Files:** `src/evaluate.py` line 300 (`datasets/bug_to_user_story.jsonl` is relative); `tests/test_prompts.py` line 10 (`sys.path.insert(0, str(Path(__file__).parent.parent / "src"))` assumes test runs from project root)
- **Evidence:** If student runs `python src/evaluate.py` from inside the `src/` directory, line 39 in evaluate.py will try to open `datasets/bug_to_user_story.jsonl` relative to `src/`, not the project root, causing FileNotFoundError (line 52).
- **Similar issue:** If running tests with `pytest` from inside `tests/`, the sys.path hack at line 10 may resolve incorrectly.
- **Why it matters:** Instructional clarity suffers. README says "python src/evaluate.py" (line 285) without noting the working directory must be project root.

### Fix approach
1. In `src/evaluate.py`, replace line 300:
   ```python
   jsonl_path = "datasets/bug_to_user_story.jsonl"
   ```
   with:
   ```python
   jsonl_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datasets", "bug_to_user_story.jsonl")
   ```
   This makes the path absolute relative to the script location, not CWD.
2. In `tests/test_prompts.py`, use `Path(__file__).parent.parent / "prompts"` consistently for YAML loading.
3. README: "Run all commands from the project root directory."

---

## Dead-Code Metric Helpers (Misleading)

**Four metric functions exist but are never called:**

### Problem
- **Files:** `src/metrics.py` lines 333–416 (evaluate_tone_score), 418–503 (evaluate_acceptance_criteria_score), 506–593 (evaluate_user_story_format_score), 596–693 (evaluate_completeness_score)
- **Evidence:** These functions are fully implemented with detailed prompts, but grep for calls to them:
  ```bash
  grep -n "evaluate_tone_score\|evaluate_acceptance_criteria_score\|evaluate_user_story_format_score\|evaluate_completeness_score" src/evaluate.py
  ```
  returns no results. They are never invoked by `evaluate_prompt()` (line 181–239).
- **Impact:** Future maintainers may assume these metrics affect the pass/fail gate (lines 262–274 in evaluate.py), when in fact only F1, Clarity, and Precision are gated. Student might optimize for tone, acceptance_criteria, or format (which are good practices!) but not see those scores improve, causing confusion.
- **Why it matters:** Code smell. Either these functions should be removed, or they should be integrated into the evaluation pipeline.

### Fix approach
1. Document clearly in `src/metrics.py` top comment (line 6–14): "MÉTRICAS GERAIS (3 used for scoring): ... | MÉTRICAS ESPECÍFICAS (4 NOT used in current pipeline): ..." to make the distinction explicit.
2. Add a comment in `src/evaluate.py` around line 196:
   ```python
   # Only these three metrics are used for the final gate (lines 220–221)
   # See metrics.py for additional unused metrics (tone, acceptance_criteria, etc.)
   ```
3. Consider if these four metrics should be integrated into the pipeline. If not, relocate them to a separate `src/bonus_metrics.py` to avoid confusion.

---

## Idempotency of Dataset Creation (Manual Cleanup Required)

**Dataset reuse requires manual intervention if student wants to change input data:**

### Problem
- **Files:** `src/evaluate.py` lines 76–102 (create_evaluation_dataset)
- **Evidence:** Lines 79–82 check if a dataset with the same name exists; if it does, the function reuses it (line 85–86). If student wants to update the dataset (e.g., add more examples to `datasets/bug_to_user_story.jsonl`), the old dataset is not refreshed.
- **Impact:** Student edits `datasets/bug_to_user_story.jsonl` locally, runs `python src/evaluate.py`, but the old dataset is used, so changes don't affect evaluation. Silent failure.
- **Why it matters:** Workflow ambiguity. README (line 334) says "Não altere os datasets de avaliação", but if student discovers a bug in the dataset or wants to add examples, they have no way to do so via the CLI.

### Fix approach
1. Add a `--reset-dataset` flag to `src/evaluate.py` main() that deletes the old dataset before creating a new one.
2. README: "To update the dataset after editing `datasets/bug_to_user_story.jsonl`, run `python src/evaluate.py --reset-dataset`."
3. Alternatively, compute a checksum of the JSONL file and only reuse the dataset if the checksum matches.

---

## Pinned-but-Aging Dependency Set (Future Breaks)

**Dependencies are pinned to old versions; future upgrades will likely break API signatures:**

### Problem
- **Files:** `requirements.txt` lines 2–3, 7 (langchain==0.3.13, langsmith==0.2.7, langchain-core==0.3.28)
- **Evidence:** As of 2026, LangChain releases have moved past 0.4.x and 1.x. The pinned versions are from early 2025. API changes between 0.3.x and 1.0 in LangChain are common (hub.pull, Client signatures, ChatPromptTemplate constructors).
- **Impact:** If student or future contributor runs `pip install -U`, dependencies will upgrade, and code that calls `hub.pull()` (evaluate.py line 108), `client.list_datasets()` (line 76), or `ChatPromptTemplate` construction may break.
- **Why it matters:** No lock file (pipenv.lock, poetry.lock) is present. No pin documentation (e.g., "frozen as of 2025-01-15 for stability").

### Fix approach
1. Create a `Pipfile.lock` or `poetry.lock` to freeze transitive dependencies.
2. Add a note to README: "Dependencies pinned to January 2025 versions for stability. To upgrade, test against LangChain 1.0+ release notes before updating requirements.txt."
3. Consider adding a GitHub Actions workflow that periodically tests against newer versions.

---

## Secrets Discipline

**Mixed signals on credential safety:**

### Problem
- **Files:** `.env` (in .gitignore, good), `.env.example` (lines 1–23, blank values), README (lines 110–123, missing security guidance)
- **Evidence:**
  - `.gitignore` line 29 includes `.env` (correct).
  - `.env.example` is shipped with only blank values (good practice).
  - README does NOT warn against committing screenshots showing `LANGSMITH_API_KEY` or `OPENAI_API_KEY` in console output.
  - README does NOT mention that prompts pushed to the LangSmith Hub are PUBLIC by default (line 157 says "Deixá-lo público" but provides no warning about data sensitivity).
  - If student uses a prompt containing proprietary business logic or PII-related examples, publishing to Hub is risky.
- **Why it matters:** Student might screenshot the evaluation terminal (which may show partial API keys in error traces) and post it in a GitHub issue or PR. Alternatively, the student might publish a prompt containing confidential business logic to the Hub without realizing it's public.

### Fix approach
1. Add a "Security" section to README:
   ```markdown
   ## Security & Confidentiality
   
   - **Never commit `.env`** — it's in .gitignore. Use `.env.example` as reference.
   - **Screenshots:** If sharing screenshots of evaluation output, redact any API keys, secret values, or sensitive model configurations.
   - **Public Hub:** Prompts pushed to the LangSmith Hub are PUBLIC. Do not include proprietary business logic, customer data, or sensitive examples.
   - **Example data:** The `datasets/bug_to_user_story.jsonl` is provided for testing. Do not commit real customer bug reports if they contain PII.
   ```
2. In `src/evaluate.py` line 286, avoid logging full API keys in environment display.

---

## Test Coverage Gaps

**Unimplemented tests leave critical validation unverified:**

### Problem
- **Files:** `tests/test_prompts.py` lines 20–42 (all six test bodies are `pass`)
- **Coverage gaps:**
  - No test validates that the prompt actually produces output when invoked (end-to-end test).
  - No test checks that the prompt can be parsed by LangChain's `hub.pull()` (format validation).
  - No test verifies that prompt reasoning aligns with Few-shot examples (quality validation).
- **Impact:** Student can submit a v2 prompt that looks structurally correct but fails when evaluate.py tries to invoke it (e.g., missing template variable, invalid YAML syntax).
- **Why it matters:** Silent failure upstream. Student runs evaluate.py, gets an error on first example invocation (line 154 in evaluate.py), with no clear guidance on what the prompt structure should be.

### Fix approach
1. Implement the six required tests (as specified in README lines 184–191).
2. Add an integration test: attempt to pull and invoke the v2 prompt locally before publishing to Hub.
3. Add to tests: validate that prompt has a `system_prompt` and `user_prompt` key with no unresolved template variables like `{undefined_var}`.

---

*Concerns audit: 2026-05-06*
