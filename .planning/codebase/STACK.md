# Technology Stack

**Analysis Date:** 2026-05-06

## Languages

**Primary:**
- Python 3.9+ - All source code, scripts, and tests

## Runtime

**Environment:**
- Python 3.9+ (as specified in README.md)

**Package Manager:**
- pip (via requirements.txt)
- Lockfile: Present (`requirements.txt` with pinned versions)

## Frameworks

**Core:**
- LangChain 0.3.13 - Prompt management, chain orchestration, LLM abstraction
- LangChain Core 0.3.28 - Base abstractions (ChatPromptTemplate, messages)
- LangChain Community 0.3.13 - Community integrations

**LLM Providers:**
- LangChain OpenAI 0.2.14 - OpenAI API integration (ChatOpenAI class)
- LangChain Google GenAI 2.0.8 - Google Gemini integration (ChatGoogleGenerativeAI class)

**Prompt Management:**
- LangSmith 0.2.7 - Prompt Hub (hub.pull / hub.push), dataset management, tracing

**Utilities:**
- PyYAML 6.0.2 - YAML parsing for prompt files
- Pydantic 2.10.4 - Data validation (prompt structure validation)
- python-dotenv 1.0.1 - Environment variable loading from `.env`

**Testing:**
- pytest 8.3.4 - Test runner and framework

## Configuration

**Environment:**
- Configured via `.env` file (loaded by `python-dotenv`)
- Template provided in `.env.example`
- Key required vars: `LANGSMITH_API_KEY`, `LLM_PROVIDER`, `OPENAI_API_KEY` or `GOOGLE_API_KEY`

**Build:**
- No build process. Codebase is interpreted Python executed directly via `python src/evaluate.py` etc.
- Virtual environment recommended: `python3 -m venv venv && source venv/bin/activate`

## Platform Requirements

**Development:**
- Python 3.9+ installed locally
- Virtual environment (recommended)
- `.env` file configured with API credentials
- Internet connection for LLM API calls

**Production:**
- Same as development (Python runtime)
- API credentials for OpenAI or Google Gemini
- LangSmith workspace credentials

## Dependency Versions (Pinned)

| Package | Version | Purpose |
|---------|---------|---------|
| langchain | 0.3.13 | Core LLM orchestration |
| langchain-core | 0.3.28 | Base classes and types |
| langchain-community | 0.3.13 | Community utilities |
| langchain-openai | 0.2.14 | OpenAI ChatOpenAI integration |
| langchain-google-genai | 2.0.8 | Google Gemini ChatGoogleGenerativeAI integration |
| langsmith | 0.2.7 | Prompt Hub, dataset management, tracing |
| pyyaml | 6.0.2 | YAML file I/O for prompts |
| pydantic | 2.10.4 | Data validation |
| python-dotenv | 1.0.1 | .env configuration loading |
| pytest | 8.3.4 | Testing framework |

---

*Stack analysis: 2026-05-06*
