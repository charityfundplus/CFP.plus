from typing import Any, Dict

from app.adapters.base import BaseProviderAdapter


class GeminiProviderAdapter(BaseProviderAdapter):
    """P0 Gemini adapter skeleton.

    No simulated provider success is permitted. Real execution must be wired to
    an approved Gemini API client and produce retrievable execution evidence
    before CFP+ can mark technical integration or automation as verified.
    """

    def __init__(self, model_name: str, config: Dict[str, Any]):
        super().__init__(provider_name="gemini", model_name=model_name, config=config)

    def normalize_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prompt = payload.get("prompt", "")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Gemini payload requires a non-empty prompt")

        return {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": payload.get("temperature", 0.2),
            },
        }

    def execute(self, normalized_request: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError(
            "Gemini API execution is not yet wired. "
            "TECHNICAL INTEGRATION VERIFIED: NO; AUTOMATION VERIFIED: NO."
        )

    def normalize_response(self, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        candidates = raw_response.get("candidates", [])
        if not candidates:
            return {"output_text": "", "finish_reason": None}

        candidate = candidates[0]
        parts = candidate.get("content", {}).get("parts", [])
        text_output = parts[0].get("text", "") if parts else ""
        return {
            "output_text": text_output,
            "finish_reason": candidate.get("finishReason"),
        }

    def verify_response(self, normalized_response: Dict[str, Any]) -> bool:
        return bool(normalized_response.get("output_text"))
