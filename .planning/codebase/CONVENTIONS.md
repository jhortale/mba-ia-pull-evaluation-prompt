# Coding Conventions

**Analysis Date:** 2026-05-06

## Naming Patterns

**Files:**
- Lowercase with underscores: `src/utils.py`, `src/evaluate.py`, `src/metrics.py`
- YAML prompts: `prompts/bug_to_user_story_v1.yml`, `prompts/bug_to_user_story_v2.yml` (version suffix format)

**Functions:**
- Snake_case throughout: `load_yaml()`, `save_yaml()`, `check_env_vars()`, `format_score()`, `print_section_header()`, `validate_prompt_structure()`, `extract_json_from_response()`, `get_llm()`, `pull_prompts_from_langsmith()`, `push_prompt_to_langsmith()`
- Private helpers: Not used (no leading underscore convention observed)
- Full English words, no abbreviations in new code

**Variables:**
- Snake_case: `prompt_template`, `llm_model`, `eval_model`, `api_key`, `missing_vars`, `json_str`
- Portuguese descriptive names in docstrings/comments
- Loop counters: `i` (common), `example`, `ds` (for datasets)

**Types:**
- Type hints used throughout: `Dict[str, Any]`, `List[Dict[str, Any]]`, `Optional[Dict[str, Any]]`, `tuple[bool, list]`, `Any`, `bool`, `float`, `str`
- Return type hints for all functions: `-> Optional[Dict[str, Any]]`, `-> bool`, `-> tuple[bool, list]`
- Uses `typing` module imports from standard library

**Classes:**
- PascalCase for test classes: `TestPrompts` in `tests/test_prompts.py`
- No non-test classes currently defined

## Code Style

**Formatting:**
- 4-space indentation (Python standard)
- Line length: appears to follow PEP 8 (≤ 79-99 characters in most cases)
- No explicit formatter configured (no `.black`, `.ruff`, or `.pylintrc` detected)

**Linting:**
- No linting configuration found (no `.eslintrc`, `eslint.config.js`, `.pylintrc`, `biome.json`)
- Relies on manual code review and PEP 8 compliance

**String Formatting:**
- Double-quoted strings dominant: `"Campo obrigatório faltando: {field}"`, `"❌ Arquivo não encontrado: {file_path}"`
- F-strings used for interpolation: `f"❌ Arquivo não encontrado: {file_path}"`
- Multiline strings (docstrings, prompts): Triple-quoted: `"""Docstring"""`, `f"""{prompt_content}"""`

## Import Organization

**Order:**
1. Standard library imports (`os`, `sys`, `json`, `re`, `pathlib`)
2. Third-party imports (`yaml`, `dotenv`, `langchain`, `langsmith`, `pydantic`)
3. Local imports (`from utils import ...`)

**Path Aliases:**
- No path aliases configured (no `jsconfig.json` or `tsconfig.json` equivalent)
- Relative imports from sibling modules: `from utils import validate_prompt_structure`
- Explicit `sys.path.insert(0, str(Path(__file__).parent.parent / "src"))` in test files to enable imports from `src/`

**Pattern Example** (`tests/test_prompts.py`):
```python
import pytest
import yaml
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure
```

## Error Handling

**Defensive Try/Except Pattern:**
- All I/O operations wrapped in try/except with friendly Portuguese error messages
- Uses emoji indicators: `❌` (error), `⚠️` (warning), `✓` (success), `✅` (completion)
- Returns default dicts on exception (non-raising) in metrics functions (`src/metrics.py` lines 150-157, 238-243, etc.)
- Example from `src/utils.py` (lines 25-37):
```python
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data
except FileNotFoundError:
    print(f"❌ Arquivo não encontrado: {file_path}")
    return None
except yaml.YAMLError as e:
    print(f"❌ Erro ao parsear YAML: {e}")
    return None
except Exception as e:
    print(f"❌ Erro ao carregar arquivo: {e}")
    return None
```

**Special Case: Re-raising in `pull_prompt_from_langsmith()`:**
- Unlike metrics, `src/evaluate.py` (lines 105-140) explicitly re-raises after verbose diagnostic output
- Provides detailed troubleshooting instructions before raising

**JSON Extraction Fallback Pattern:**
- LLM responses may contain text around JSON
- `extract_json_from_response()` in `src/utils.py` and `src/metrics.py` searches for `{...}` bounds and tries to parse
- Returns None (utils) or default dict (metrics) if extraction fails

## Environment Configuration

**Pattern: `python-dotenv` with optional env vars:**
- All modules call `load_dotenv()` at top level (e.g., line 10 in `src/utils.py`, line 32 in `src/metrics.py`)
- Required vars checked via `check_env_vars()` before main work
- Config flow: `src/evaluate.py` line 288-294 checks required_vars based on `LLM_PROVIDER`

**Key env vars:**
- `LLM_PROVIDER`: "openai" (default) or "google"
- `LLM_MODEL`: Model name (e.g., "gpt-4o-mini", defaults to "gpt-4o-mini")
- `EVAL_MODEL`: Model for evaluation (defaults to "gpt-4o")
- `OPENAI_API_KEY`: Required if LLM_PROVIDER is "openai"
- `GOOGLE_API_KEY`: Required if LLM_PROVIDER is "google"
- `LANGSMITH_API_KEY`: Required for prompt management
- `USERNAME_LANGSMITH_HUB`: Username for publishing to public Hub (src/evaluate.py line 317-320)
- `LANGSMITH_PROJECT`: Project name (defaults to "prompt-optimization-challenge-resolved")

## UI and Logging Helpers

**Print Formatting:**
- `print_section_header(title, char="=", width=50)` — line separator with title, used in `src/evaluate.py` line 278
- `format_score(score, threshold=0.9)` — returns `"{score:.2f} {symbol}"` where symbol is `✓` (pass) or `✗` (fail), used in `src/evaluate.py` lines 249-254

**Logging:**
- Console output via `print()` with emoji prefixes (❌, ✓, ⚠️, ✅)
- No structured logging (no `logging` module usage detected)
- Portuguese user-facing messages; English code/variable names

## Comments and Documentation

**Docstring Style:**
- Module-level docstrings describe purpose and usage (e.g., `src/metrics.py` lines 1-22)
- Function docstrings include Args, Returns sections (Google/NumPy-style):
```python
def validate_prompt_structure(prompt_data: Dict[str, Any]) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt.

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
```

**Inline Comments:**
- Portuguese comments explaining non-obvious logic (e.g., `src/metrics.py` line 48: "Tentar parsear diretamente")
- Sparse use—code is generally self-documenting

**TODO/FIXME:**
- Not observed in instructor-written files (`src/utils.py`, `src/metrics.py`, `src/evaluate.py`)
- Student skeletons use `...` (ellipsis) for unimplemented functions (e.g., `src/pull_prompts.py` line 23)

## Prompt YAML Schema

**Top-level Key Format:**
- `bug_to_user_story_v{N}:` — version-specific key (e.g., `bug_to_user_story_v1:`, `bug_to_user_story_v2:`)

**Required Fields:**
- `description`: Short text describing the prompt purpose
- `system_prompt`: System instructions with placeholders like `{bug_report}`
- `user_prompt`: User input template (may reference placeholder vars)
- `version`: Version string (e.g., "v1", "v2")

**Optional Metadata Fields:**
- `tags`: List of tags for categorization (e.g., `["bug-analysis", "user-story", "product-management"]`)
- `created_at`: ISO date (e.g., "2025-01-15")
- `techniques_applied`: List of prompt engineering techniques used (enforced by `validate_prompt_structure()` — minimum 2 required)

**Example Structure** (`prompts/bug_to_user_story_v1.yml`, lines 6-26):
```yaml
bug_to_user_story_v1:
  description: "Prompt para converter relatos de bugs em User Stories"
  system_prompt: |
    Você é um assistente que ajuda a transformar relatos de bugs...
    {bug_report}
    ---
    User Story gerada:
  user_prompt: "{bug_report}"
  version: "v1"
  created_at: "2025-01-15"
  tags: ["bug-analysis", "user-story", "product-management"]
```

## Module-Level Initialization

**`load_dotenv()` Pattern:**
- Called once at module top-level (not in functions) to ensure env vars are loaded before any code executes
- Location: Line 10 in `src/utils.py`, line 32 in `src/metrics.py`, line 32 in `src/evaluate.py`
- Critical for env-dependent code paths

## Function Signature Consistency

**Naming Consistency:**
- Getter functions: `get_llm()`, `get_eval_llm()`, `get_evaluator_llm()` — all return LLM instances
- Validator functions: `validate_prompt_structure()`, `validate_prompt()` (skeleton)
- File I/O: `load_yaml()`, `save_yaml()`
- LangSmith integration: `pull_prompts_from_langsmith()`, `push_prompt_to_langsmith()`, `pull_prompt_from_langsmith()`

**Return Patterns:**
- Tuple unpacking: `is_valid, errors = validate_prompt_structure(data)` (line 119-147 in `src/utils.py`)
- Dict with keys like `{"score": 0.95, "reasoning": "..."}` for metric functions
- Optional returns: `Optional[Dict[str, Any]]` for file loading that may fail
- Boolean success: `-> bool` for file save operations

---

*Convention analysis: 2026-05-06*
