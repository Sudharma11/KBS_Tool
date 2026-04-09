import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    value = os.getenv(key, "").strip()
    if not value:
        raise EnvironmentError(f"Missing required environment variable: {key}")
    return value


def _optional(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


# ---------------------------------------------------------------------------
# Universal LLM — supports OpenAI, Gemini, Groq, Anthropic, etc.
# Set LLM_API_KEY to your key (any provider).
# Set LLM_MODEL to the LiteLLM model string, e.g.:
#   gpt-4o-mini                        (OpenAI)
#   gemini/gemini-2.0-flash            (Google Gemini)
#   groq/llama-3.3-70b-versatile       (Groq)
#   claude-3-haiku-20240307            (Anthropic)
# If LLM_MODEL is not set, it is auto-inferred from the key prefix.
# ---------------------------------------------------------------------------
# Backward compat: fall back to GOOGLE_API_KEY if LLM_API_KEY not set
LLM_API_KEY: str = _optional("LLM_API_KEY") or _optional("GOOGLE_API_KEY")
if not LLM_API_KEY:
    raise EnvironmentError("Missing LLM_API_KEY (or GOOGLE_API_KEY) environment variable")

LLM_MODEL: str = _optional("LLM_MODEL")  # empty = auto-inferred by LLMClient

# Keep GEMINI_API_KEYS for any legacy code that still references it directly
_raw_gemini = _optional("GOOGLE_API_KEY")
GEMINI_API_KEYS: list[str] = [k.strip() for k in _raw_gemini.split(",") if k.strip()]

# ---------------------------------------------------------------------------
# Groq — used for leader/executive name extraction (llm_extractor)
# ---------------------------------------------------------------------------
GROQ_API_KEY: str = _require("GROQ_API_KEY")

# ---------------------------------------------------------------------------
# Serper — Google Search API fallback for LinkedIn enrichment
# ---------------------------------------------------------------------------
SERPER_API_KEY: str = _optional("SERPER_API_KEY")

# ---------------------------------------------------------------------------
# Alpha Vantage — financial data scraping
# ---------------------------------------------------------------------------
ALPHA_VANTAGE_API_KEY: str = _optional("ALPHA_VANTAGE_API_KEY")
