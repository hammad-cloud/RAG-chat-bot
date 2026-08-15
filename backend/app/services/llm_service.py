"""LLM providers for answer generation."""

from __future__ import annotations

from app.core.config import settings
from app.core.constants import SYSTEM_PROMPT, UNKNOWN_ANSWER

# Prefer configured model, then newer Flash aliases for new Gemini API keys.
GEMINI_MODEL_FALLBACKS = (
    "gemini-3.5-flash",
    "gemini-3-flash-preview",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
)


class LLMService:
    def generate_answer(self, question: str, context: str) -> str:
        provider = settings.llm_provider.lower().strip()

        if provider == "openai":
            return self._generate_openai(question, context)
        if provider == "gemini":
            return self._generate_gemini(question, context)

        raise ValueError(
            f"Unsupported LLM provider '{settings.llm_provider}'. Use 'gemini' or 'openai'."
        )

    def _generate_gemini(self, question: str, context: str) -> str:
        if not settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is missing. Add it to backend/.env to enable answers."
            )

        from google import genai
        from google.genai import types
        from google.genai import errors as genai_errors

        client = genai.Client(api_key=settings.gemini_api_key)
        prompt = (
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            "Answer using only the context."
        )
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.1,
        )

        candidates = self._gemini_model_candidates()
        last_error: Exception | None = None

        for model_name in candidates:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )
                text = (getattr(response, "text", None) or "").strip()
                return text or UNKNOWN_ANSWER
            except genai_errors.ClientError as exc:
                last_error = exc
                message = str(exc).lower()
                if exc.code in {401, 403} or "api key" in message:
                    raise RuntimeError(
                        "Gemini API key is invalid or unauthorized. "
                        "Create a new key at https://aistudio.google.com/apikey"
                    ) from exc
                # Try next model when current one is retired/unavailable.
                if exc.code == 404 or "not found" in message or "no longer available" in message:
                    continue
                raise RuntimeError(f"Gemini request failed: {exc}") from exc
            except Exception as exc:
                last_error = exc
                message = str(exc).lower()
                if "404" in message or "not found" in message or "no longer available" in message:
                    continue
                if "401" in message or "403" in message or "api key" in message:
                    raise RuntimeError(
                        "Gemini API key is invalid or unauthorized. "
                        "Create a new key at https://aistudio.google.com/apikey"
                    ) from exc
                raise RuntimeError(f"Gemini request failed: {exc}") from exc

        raise RuntimeError(
            "No available Gemini model worked for this API key. "
            f"Tried: {', '.join(candidates)}. Last error: {last_error}"
        )

    @staticmethod
    def _gemini_model_candidates() -> list[str]:
        preferred = settings.gemini_model.removeprefix("models/").strip()
        ordered: list[str] = []
        for name in (preferred, *GEMINI_MODEL_FALLBACKS):
            if name and name not in ordered:
                ordered.append(name)
        return ordered

    def _generate_openai(self, question: str, context: str) -> str:
        if not settings.openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is missing. Add it to backend/.env to enable answers."
            )

        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        completion = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Context:\n{context}\n\n"
                        f"Question: {question}\n\n"
                        "Answer using only the context."
                    ),
                },
            ],
            temperature=0.1,
        )
        text = (completion.choices[0].message.content or "").strip()
        return text or UNKNOWN_ANSWER
