import asyncio
import json
import logging
from pathlib import Path
from typing import Optional

from config import settings

try:
    from llama_cpp import Llama  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    Llama = None

try:
    import openai  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    openai = None

try:
    from huggingface_hub import InferenceClient  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    InferenceClient = None

logger = logging.getLogger(__name__)


class LLMEngine:
    """Abstraction over local gguf, OpenAI, or HuggingFace hosted models."""

    def __init__(self) -> None:
        self.provider = self._determine_provider()
        self.provider_name = self.provider or "mock"
        self._client = self._init_client()

    def _determine_provider(self) -> Optional[str]:
        if settings.LOCAL_LLM_PATH and Path(settings.LOCAL_LLM_PATH).exists() and Llama:
            return "local"
        if settings.OPENAI_API_KEY and openai:
            return "openai"
        if settings.HUGGINGFACE_API_KEY and InferenceClient:
            return "huggingface"
        return None

    def _init_client(self):
        if self.provider == "local":
            return Llama(
                model_path=settings.LOCAL_LLM_PATH,
                n_ctx=settings.LOCAL_LLM_N_CTX,
                n_threads=settings.LOCAL_LLM_N_THREADS,
                logits_all=False,
                verbose=False,
            )
        if self.provider == "openai":
            openai.api_key = settings.OPENAI_API_KEY
            return openai
        if self.provider == "huggingface":
            return InferenceClient(
                model=settings.HUGGINGFACE_MODEL,
                token=settings.HUGGINGFACE_API_KEY,
            )
        return None

    def is_available(self) -> bool:
        return self._client is not None

    async def generate_structured_analysis(self, context: str) -> str:
        prompt = self._build_structured_prompt(context)

        if not self.is_available():
            return json.dumps(self._mock_payload())

        if self.provider == "local":
            return await asyncio.to_thread(self._invoke_local, prompt)
        if self.provider == "openai":
            return await asyncio.to_thread(self._invoke_openai, prompt)
        if self.provider == "huggingface":
            return await asyncio.to_thread(self._invoke_huggingface, prompt)

        return json.dumps(self._mock_payload())

    def _invoke_local(self, prompt: str) -> str:
        response = self._client(
            prompt=prompt,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            top_p=settings.LLM_TOP_P,
            stop=["</analysis>"],
        )
        return response["choices"][0]["text"].strip()

    def _invoke_openai(self, prompt: str) -> str:
        completion = self._client.ChatCompletion.create(  # type: ignore[attr-defined]
            model=settings.OPENAI_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            messages=[
                {"role": "system", "content": "You are a precise auditor. Respond with JSON only."},
                {"role": "user", "content": prompt},
            ],
        )
        return completion["choices"][0]["message"]["content"].strip()

    def _invoke_huggingface(self, prompt: str) -> str:
        return self._client.text_generation(  # type: ignore[call-arg]
            prompt=prompt,
            max_new_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
            repetition_penalty=1.1,
            return_full_text=False,
        ).strip()

    @staticmethod
    def _build_structured_prompt(context: str) -> str:
        return f"""
<analysis>
You are AutoDeployX, an auditor that must return JSON only.
Use the provided context and cite reference ids (ref-*) for every claim.
Output schema:
{{
  "summary": "...",
  "summary_references": ["ref-1"],
  "tech_stack": {{"languages": [], "frameworks": [], "databases": [], "tools": [], "reference_ids": []}},
  "security_findings": [{{"title": "", "severity": "low|medium|high|critical", "description": "", "reference_id": "ref-1"}}],
  "code_smells": [{{"title": "", "impact": "low|medium|high", "description": "", "reference_id": "ref-2"}}],
  "improvement_plan": [{{"title": "", "impact": "low|medium|high", "effort": "low|medium|high", "details": "", "reference_id": "ref-3"}}],
  "devops_recommendations": [{{"title": "", "impact": "low|medium|high", "effort": "low|medium|high", "details": "", "reference_id": "ref-4"}}]
}}

Context:
{context}

Return valid JSON only. Do not add commentary.
</analysis>
""".strip()

    @staticmethod
    def _mock_payload():
        return {
            "summary": "Static response because no LLM provider is configured.",
            "summary_references": [],
            "tech_stack": {"languages": [], "frameworks": [], "databases": [], "tools": [], "reference_ids": []},
            "security_findings": [],
            "code_smells": [],
            "improvement_plan": [],
            "devops_recommendations": [],
        }