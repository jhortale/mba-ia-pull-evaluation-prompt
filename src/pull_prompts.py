"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

PROMPT_TO_PULL = "leonanluppi/bug_to_user_story_v1"
OUTPUT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v1.yml"
PROMPT_KEY = "bug_to_user_story_v1"


def pull_prompts_from_langsmith():
    """
    Faz pull do prompt do LangSmith Hub e salva localmente em YAML.

    Returns:
        True se sucesso, False caso contrário
    """
    print(f"Puxando prompt do LangSmith Hub: {PROMPT_TO_PULL}")

    try:
        prompt = hub.pull(PROMPT_TO_PULL)
    except Exception as e:
        print(f"❌ Erro ao fazer pull do prompt '{PROMPT_TO_PULL}': {e}")
        print("\nVerifique:")
        print("- LANGSMITH_API_KEY está configurada corretamente no .env")
        print("- O prompt existe e é público no LangSmith Hub")
        print("- Sua conexão com a internet está funcionando")
        return False

    if not isinstance(prompt, ChatPromptTemplate):
        print(f"❌ Tipo de prompt inesperado: {type(prompt)}")
        return False

    print("   ✓ Prompt carregado com sucesso")

    # Extrair system e user prompts das mensagens do template
    system_prompt = ""
    user_prompt = ""

    for message in prompt.messages:
        if isinstance(message, SystemMessagePromptTemplate):
            system_prompt = message.prompt.template
        elif isinstance(message, HumanMessagePromptTemplate):
            user_prompt = message.prompt.template

    if not system_prompt and not user_prompt:
        print("❌ Nenhuma mensagem system/user encontrada no prompt")
        return False

    data = {
        PROMPT_KEY: {
            "description": "Prompt para converter relatos de bugs em User Stories",
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "version": "v1",
            "source": PROMPT_TO_PULL,
            "tags": ["bug-analysis", "user-story", "product-management"],
        }
    }

    if not save_yaml(data, str(OUTPUT_FILE)):
        return False

    print(f"   ✓ Prompt salvo em: {OUTPUT_FILE}")
    return True


def main():
    """Função principal"""
    print_section_header("PULL DE PROMPTS DO LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    if not pull_prompts_from_langsmith():
        return 1

    print("\n✅ Pull concluído com sucesso!")
    print("\nPróximos passos:")
    print("1. Analise o prompt em prompts/bug_to_user_story_v1.yml")
    print("2. Crie sua versão otimizada em prompts/bug_to_user_story_v2.yml")
    print("3. Faça push com: python src/push_prompts.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
