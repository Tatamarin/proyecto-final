import json
import time
from pathlib import Path

import httpx

from .config import settings


PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
PROMPTS = {
    "REQUIREMENTS": ("requirements_v1.0", PROMPTS_DIR / "requirements" / "requirements_v1.0.txt"),
    "TESTING": ("testing_v1.0", PROMPTS_DIR / "testing" / "testing_v1.0.txt"),
}


class LLMService:
    def prompt(self, agent: str) -> tuple[str, str]:
        try:
            version, path = PROMPTS[agent]
        except KeyError as exc:
            raise ValueError(f"Agente no soportado: {agent}") from exc
        return version, path.read_text(encoding="utf-8").strip()

    def generate(self, agent: str, payload: dict) -> tuple[dict, int, str]:
        started = time.perf_counter()
        if not settings.ai_api_key:
            result = self.demo(agent, payload)
            return result, round((time.perf_counter()-started)*1000), "demo"
        _, instructions = self.prompt(agent)
        system = f"{instructions}\nReturn only valid JSON."
        prompt = json.dumps(payload, ensure_ascii=False)
        with httpx.Client(timeout=90) as client:
            response = client.post(
                f"{settings.ai_base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {settings.ai_api_key}"},
                json={
                    "model": settings.ai_model,
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                },
            )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content), round((time.perf_counter()-started)*1000), settings.ai_model

    def demo(self, agent, payload):
        if agent == "REQUIREMENTS":
            return {"requirements": [{"code":"REQ-001","type":"functional","title":"Implementar la necesidad","description":payload["description"],"priority":"high","acceptance_criteria":[{"code":"AC-001","description":"La funcionalidad cumple la necesidad descrita."},{"code":"AC-002","description":"Se informa claramente cualquier error."}]}],"ambiguities":[],"missing_information":[]}
        if agent == "TESTING":
            r = payload["requirement"]
            criterion_codes = [item["code"] for item in r["acceptance_criteria"]]
            return {"test_cases":[{"code":"TC-001","title":f"Flujo válido: {r['title']}","type":"positive","preconditions":["El usuario tiene acceso al sistema"],"steps":["Abrir la funcionalidad","Ingresar datos válidos","Confirmar la operación"],"expected_result":"La operación se completa correctamente.","acceptance_criteria_codes":criterion_codes},{"code":"TC-002","title":f"Validación: {r['title']}","type":"negative","preconditions":[],"steps":["Abrir la funcionalidad","Ingresar datos inválidos"],"expected_result":"El sistema muestra un mensaje de validación.","acceptance_criteria_codes":criterion_codes}]}
        raise ValueError(f"Agente no soportado: {agent}")
