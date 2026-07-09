"""
Testes automatizados para validação de prompts.
"""
import re
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt_data():
    """Carrega os dados do prompt v2 otimizado."""
    data = load_prompts(str(PROMPT_FILE))
    assert data is not None, f"Arquivo YAML vazio ou inválido: {PROMPT_FILE}"
    assert PROMPT_KEY in data, f"Chave '{PROMPT_KEY}' não encontrada no YAML"
    return data[PROMPT_KEY]


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt_data):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt_data, "Campo 'system_prompt' não existe"
        system_prompt = prompt_data["system_prompt"]
        assert isinstance(system_prompt, str), "'system_prompt' deve ser uma string"
        assert system_prompt.strip(), "'system_prompt' está vazio"

    def test_prompt_has_role_definition(self, prompt_data):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system_prompt = prompt_data["system_prompt"].lower()
        role_patterns = [
            r"você é um[a]?\s+\w+",
            r"you are a[n]?\s+\w+",
            r"atue como\s+\w+",
        ]
        has_role = any(re.search(p, system_prompt) for p in role_patterns)
        assert has_role, "Prompt não define uma persona (ex: 'Você é um Product Manager')"

    def test_prompt_mentions_format(self, prompt_data):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system_prompt = prompt_data["system_prompt"].lower()
        format_keywords = [
            "user story",
            "como um",       # formato padrão "Como um..., eu quero..., para que..."
            "eu quero",
            "markdown",
        ]
        mentions_format = any(k in system_prompt for k in format_keywords)
        assert mentions_format, "Prompt não exige formato Markdown ou User Story padrão"
        # O formato completo da User Story padrão deve estar especificado
        assert "como um" in system_prompt and "eu quero" in system_prompt and "para que" in system_prompt, \
            "Prompt não especifica o formato completo 'Como um..., eu quero..., para que...'"

    def test_prompt_has_few_shot_examples(self, prompt_data):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = prompt_data["system_prompt"].lower()
        assert "exemplo" in system_prompt, "Prompt não contém exemplos (Few-shot Learning)"
        assert "entrada" in system_prompt and "saída" in system_prompt, \
            "Exemplos devem conter pares de Entrada/Saída explícitos"
        # Deve haver pelo menos 2 exemplos
        example_count = len(re.findall(r"exemplo\s+\d", system_prompt))
        assert example_count >= 2, f"Mínimo de 2 exemplos few-shot esperados, encontrados: {example_count}"

    def test_prompt_no_todos(self, prompt_data):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        full_text = yaml.dump(prompt_data, allow_unicode=True)
        assert "[TODO]" not in full_text, "Prompt ainda contém marcadores [TODO]"
        assert "TODO" not in prompt_data.get("system_prompt", ""), "system_prompt contém TODO"
        assert "TODO" not in prompt_data.get("user_prompt", ""), "user_prompt contém TODO"

    def test_minimum_techniques(self, prompt_data):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt_data.get("techniques_applied", [])
        assert isinstance(techniques, list), "'techniques_applied' deve ser uma lista"
        assert len(techniques) >= 2, \
            f"Mínimo de 2 técnicas requeridas nos metadados, encontradas: {len(techniques)}"
        # Validação completa da estrutura (usa o helper compartilhado)
        is_valid, errors = validate_prompt_structure(prompt_data)
        assert is_valid, f"Estrutura do prompt inválida: {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
