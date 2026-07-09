"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header, validate_prompt_structure

load_dotenv()

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_data["system_prompt"]),
        ("user", prompt_data["user_prompt"]),
    ])

    # Metadados: tags do prompt + técnicas aplicadas
    tags = list(prompt_data.get("tags", []))
    techniques = prompt_data.get("techniques_applied", [])
    all_tags = tags + [t.lower().replace(" ", "-") for t in techniques]

    description = prompt_data.get("description", "")
    if techniques:
        description += f" | Técnicas: {', '.join(techniques)}"

    try:
        client = Client()
        url = client.push_prompt(
            prompt_name,
            object=chat_prompt,
            description=description,
            tags=all_tags,
            is_public=True,
        )
        print(f"   ✓ Push realizado com sucesso: {prompt_name}")
        print(f"   ✓ URL: {url}")
        return True

    except Exception as e:
        if "has not changed" in str(e):
            print(f"   ✓ Prompt já está atualizado no Hub (nenhuma mudança desde o último commit)")
            return True

        print(f"❌ Erro ao fazer push do prompt '{prompt_name}': {e}")
        print("\nVerifique:")
        print("- LANGSMITH_API_KEY está configurada corretamente no .env")
        print("- Sua API key tem permissão de escrita no Hub")
        print("- Para push público, seu perfil do Hub precisa estar configurado:")
        print("  https://smith.langchain.com/prompts")
        return False


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    is_valid, errors = validate_prompt_structure(prompt_data)

    user_prompt = prompt_data.get("user_prompt", "")
    if "{bug_report}" not in user_prompt:
        errors.append("user_prompt deve conter a variável {bug_report}")
        is_valid = False

    return (is_valid, errors)


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPTS OTIMIZADOS AO LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    data = load_yaml(str(PROMPT_FILE))
    if not data or PROMPT_KEY not in data:
        print(f"❌ Prompt '{PROMPT_KEY}' não encontrado em {PROMPT_FILE}")
        print("\nCrie o arquivo prompts/bug_to_user_story_v2.yml antes de fazer push.")
        return 1

    prompt_data = data[PROMPT_KEY]

    print(f"Validando prompt: {PROMPT_KEY}...")
    is_valid, errors = validate_prompt(prompt_data)

    if not is_valid:
        print("❌ Prompt inválido:")
        for error in errors:
            print(f"   - {error}")
        return 1

    print("   ✓ Prompt válido\n")

    print(f"Fazendo push para o LangSmith Hub...")
    if not push_prompt_to_langsmith(PROMPT_KEY, prompt_data):
        return 1

    print("\n✅ Push concluído com sucesso!")
    print("\nPróximos passos:")
    print("1. Verifique o prompt publicado em: https://smith.langchain.com/prompts")
    print("2. Confirme que o prompt está PÚBLICO")
    print("3. Execute a avaliação: python src/evaluate.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
