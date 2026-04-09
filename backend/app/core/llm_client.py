"""
Universal LLM client using native SDKs only — no LiteLLM required.
Supports OpenAI, Gemini, and Groq based on API key prefix.

Key prefix detection:
  sk-...      -> OpenAI
  AIza...     -> Google Gemini
  gsk_...     -> Groq (uses OpenAI-compatible API)
  sk-ant-...  -> Anthropic (not supported yet)
"""

import os


def _detect_provider(api_key: str) -> str:
    if api_key.startswith("sk-ant-"):
        raise ValueError("Anthropic is not supported yet.")
    if api_key.startswith("gsk_"):
        return "groq"
    if api_key.startswith("AIza"):
        return "gemini"
    if api_key.startswith("sk-"):
        return "openai"
    raise ValueError(
        f"Cannot detect provider from API key. "
        f"Expected prefix: sk- (OpenAI), AIza (Gemini), gsk_ (Groq)."
    )


def _default_model(provider: str) -> str:
    return {
        "openai": "gpt-4o-mini",
        "gemini": "gemini-2.0-flash",
        "groq":   "llama-3.3-70b-versatile",
    }[provider]


class LLMClient:
    def __init__(self, api_key: str | None = None, model: str | None = None, temperature: float = 0.2):
        from app.core.config import LLM_API_KEY, LLM_MODEL
        self.api_key = (api_key or LLM_API_KEY or "").strip()
        if not self.api_key:
            raise ValueError("No API key provided. Set LLM_API_KEY in your .env file.")
        self.provider = _detect_provider(self.api_key)
        self.model = (model or LLM_MODEL or "").strip() or _default_model(self.provider)
        self.temperature = temperature
        print(f"LLMClient: provider={self.provider}, model={self.model}")

    def generate(self, prompt: str) -> str:
        if self.provider == "gemini":
            return self._call_gemini(prompt)
        else:
            return self._call_openai_compatible(prompt)

    def _call_gemini(self, prompt: str) -> str:
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(
            self.model,
            generation_config={"temperature": self.temperature, "top_p": 0.8, "top_k": 40},
        )
        response = model.generate_content(prompt)
        return response.text or ""

    def _call_openai_compatible(self, prompt: str) -> str:
        from openai import OpenAI
        base_urls = {
            "groq":   "https://api.groq.com/openai/v1",
            "openai": None,  # default OpenAI base URL
        }
        client = OpenAI(
            api_key=self.api_key,
            base_url=base_urls.get(self.provider),
        )
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
        )
        return response.choices[0].message.content or ""
