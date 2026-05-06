# Testing Patterns

**Analysis Date:** 2026-05-06

## Test Framework

**Runner:**
- pytest 8.3.4 (from `requirements.txt` line 19)
- Config: No explicit `pytest.ini` or `pyproject.toml` config detected
- Default discovery: `tests/test_*.py` files with `Test*` classes and `test_*` methods

**Assertion Library:**
- pytest built-in assertions (no explicit `assert` statements yet — test bodies are stubs with `pass`)

**Run Commands:**
```bash
pytest tests/test_prompts.py                    # Run all tests
pytest tests/test_prompts.py -v                # Verbose output
pytest tests/test_prompts.py -v --tb=short     # Short traceback (as seen in test file line 45)
python -m pytest tests/test_prompts.py          # Alternative invocation
```

## Test File Organization

**Location:**
- Single test file: `tests/test_prompts.py`
- Tests live in `tests/` directory, source in `src/` (separate directories, not co-located)

**Naming Convention:**
- Test class: `TestPrompts` (PascalCase with `Test` prefix)
- Test methods: `test_*` (snake_case, descriptive names like `test_prompt_has_system_prompt`)
- File: `test_prompts.py` (matches subject `prompts`, not module-specific)

**Initialization Pattern** (`tests/test_prompts.py`, lines 1-12):
```python
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure
```

This pattern:
1. Imports pytest and required libraries
2. Manually inserts parent `src/` into `sys.path` for imports
3. Imports the function under test from `src/utils.py`

## Test Structure

**Suite Organization:**
```python
class TestPrompts:
    def test_prompt_has_system_prompt(self):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        pass

    def test_prompt_has_role_definition(self):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        pass
```

**Test Method Mandates (from README §5):**
Exactly 6 test methods required (currently all stubs with `pass`):
1. `test_prompt_has_system_prompt` — Field existence check
2. `test_prompt_has_role_definition` — Persona definition presence
3. `test_prompt_mentions_format` — Format requirement validation
4. `test_prompt_has_few_shot_examples` — Few-shot examples presence
5. `test_prompt_no_todos` — Absence of `[TODO]` markers
6. `test_minimum_techniques` — Metadata: ≥2 techniques_applied

**Helper Function Available:**
- `load_prompts(file_path: str)` — Loads YAML prompt file and returns parsed dict (line 14-17)
- `validate_prompt_structure(prompt_data)` from `src/utils.py` — Enforces requirements (imported line 12)

**What `validate_prompt_structure()` Enforces** (`src/utils.py`, lines 119-147):
```python
def validate_prompt_structure(prompt_data: Dict[str, Any]) -> tuple[bool, list]:
    errors = []
    
    required_fields = ['description', 'system_prompt', 'version']
    for field in required_fields:
        if field not in prompt_data:
            errors.append(f"Campo obrigatório faltando: {field}")
    
    system_prompt = prompt_data.get('system_prompt', '').strip()
    if not system_prompt:
        errors.append("system_prompt está vazio")
    
    if 'TODO' in system_prompt:
        errors.append("system_prompt ainda contém TODOs")
    
    techniques = prompt_data.get('techniques_applied', [])
    if len(techniques) < 2:
        errors.append(f"Mínimo de 2 técnicas requeridas, encontradas: {len(techniques)}")
    
    return (len(errors) == 0, errors)
```

Returns tuple: `(is_valid: bool, errors: list)`

## Test Flow (Expected Student Implementation Pattern)

**Typical test flow for test_prompt_no_todos:**
```python
def test_prompt_no_todos(self):
    """Garante que você não esqueceu nenhum `[TODO]` no texto."""
    # Load prompt YAML
    prompt_data = load_prompts("prompts/bug_to_user_story_v2.yml")
    
    # Validate using helper
    is_valid, errors = validate_prompt_structure(prompt_data)
    
    # Assert validation passes (no TODO errors)
    assert is_valid, f"Prompt validation failed: {errors}"
    
    # Or extract specific error check
    assert not any("TODO" in error for error in errors), "Prompt contains TODO markers"
```

## Test Data & Fixtures

**Test Data Location:**
- Prompts loaded from YAML files: `prompts/bug_to_user_story_v1.yml`, `prompts/bug_to_user_story_v2.yml`
- No separate fixture files created yet
- Tests load data on-the-fly via `load_prompts()` helper (line 14-17 in test file)

**Example Data Structure** (from `prompts/bug_to_user_story_v1.yml`):
```yaml
bug_to_user_story_v1:
  description: "Prompt para converter relatos de bugs em User Stories"
  system_prompt: |
    Você é um assistente que ajuda a transformar relatos de bugs...
    {bug_report}
  user_prompt: "{bug_report}"
  version: "v1"
  created_at: "2025-01-15"
  tags: ["bug-analysis", "user-story", "product-management"]
  techniques_applied: ["Chain-of-Thought", "Few-Shot Examples"]  # Minimum 2 required
```

## Coverage & CI/CD

**Coverage Requirements:**
- Not enforced (`coverage` not in `requirements.txt`)
- No `.coveragerc` or coverage badge detected

**CI/CD Configuration:**
- No GitHub Actions, GitLab CI, or other CI pipelines detected (no `.github/workflows/`, `.gitlab-ci.yml`)
- Tests are run manually during development

**Integration Testing:**
- Closest equivalent: `python src/metrics.py` (line 697+) runs live smoke test against configured LLM
- This is a paid operation (hits OpenAI/Google API) — not suitable for typical CI
- Demonstrates metric functions work end-to-end with real LLM responses

## Test Execution Entry Point

**Main Block** (`tests/test_prompts.py`, lines 44-45):
```python
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
```

Allows direct script execution: `python tests/test_prompts.py`

## Mocking Strategy

**Current State:**
- No mocking configured or used
- Test bodies are empty (`pass`)
- When tests are implemented, mocking likely needed for:
  - LangSmith API calls (if any integration testing added)
  - LLM responses (to avoid cost and latency)

**Example Mocking Pattern (if needed in future):**
```python
from unittest.mock import patch, Mock

@patch('utils.get_llm')
def test_with_mock_llm(self, mock_get_llm):
    mock_llm = Mock()
    mock_get_llm.return_value = mock_llm
    # Test logic
```

## Error Handling in Tests

**Expected Pattern:**
- Use `validate_prompt_structure()` for declarative validation
- Assert on tuple return: `is_valid, errors = validate_prompt_structure(prompt_data)`
- Provide error list in assertion message for debugging

**Example:**
```python
def test_prompt_has_system_prompt(self):
    prompt_data = load_prompts("prompts/bug_to_user_story_v2.yml")
    is_valid, errors = validate_prompt_structure(prompt_data)
    
    assert is_valid, f"Validation errors: {errors}"
    assert prompt_data.get('system_prompt'), "system_prompt is empty"
```

## Test Dependencies

**Imports Required:**
- `pytest` — Test runner
- `yaml` — YAML parsing
- `sys`, `pathlib` — Path manipulation for imports
- `validate_prompt_structure` from `src/utils.py` — Validation logic

**External Data:**
- `prompts/bug_to_user_story_v2.yml` — Prompt file under test (student-created)
- `prompts/bug_to_user_story_v1.yml` — Reference/example prompt (instructor-provided)

## Test Markers (Not Configured)

**Potential Future Use:**
```python
@pytest.mark.slow      # For slow tests like LLM-based evals
@pytest.mark.requires_api  # For tests needing API keys
@pytest.mark.skip("Reason")
```

Not currently used in this codebase.

## Snapshot/Golden File Testing

**Not Used:**
- No pytest-snapshot or similar library in `requirements.txt`
- Expected results are hard-coded in assertion logic

## Performance Notes

**Test Runtime:**
- Currently instant (all `pass` stubs)
- When implemented with LLM calls: ~30 seconds per metric (network latency)
- `validate_prompt_structure()` is fast (local validation only)

## Notes for Student Implementation

1. **Load prompt from YAML** using `load_prompts("prompts/bug_to_user_story_v2.yml")`
2. **Run validation** with `validate_prompt_structure(prompt_data)` — this enforces 4 checks:
   - Required fields: `description`, `system_prompt`, `version`
   - `system_prompt` not empty
   - No `TODO` in `system_prompt`
   - ≥2 entries in `techniques_applied`
3. **Assert each test condition** — tests should verify these checks pass
4. **Tests v2 prompt** — they target `prompts/bug_to_user_story_v2.yml` which the student creates
5. **Keep helper functions** — `load_prompts()` and `validate_prompt_structure()` do the heavy lifting

---

*Testing analysis: 2026-05-06*
