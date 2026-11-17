"""Caso reproducible del portal. Los datos del escenario son sintéticos."""
import json
from pathlib import Path

SCENARIO = json.loads(
    (Path(__file__).parent / "static" / "scenario.json").read_text(encoding="utf-8")
)


def demo_requirements(payload: dict) -> dict:
    description = payload["description"]
    matches = description.strip() == SCENARIO["description"]
    requirements = SCENARIO["requirements"] if matches else [{
        "code": "REQ-001",
        "type": "functional",
        "title": "Implementar la necesidad",
        "description": description,
        "priority": "high",
        "acceptance_criteria": [
            {"code": "AC-001", "description": "La funcionalidad cumple la necesidad descrita."},
            {"code": "AC-002", "description": "Se informa claramente cualquier error."},
        ],
    }]
    return {"requirements": requirements, "ambiguities": [], "missing_information": []}


def demo_tests(payload: dict) -> dict:
    requirement = payload["requirement"]
    reference = next(
        (row for row in SCENARIO["requirements"] if row["code"] == requirement["code"]), None
    )
    criteria = requirement["acceptance_criteria"]
    if reference and (
        requirement["description"] == reference["description"]
        and sorted(criteria, key=lambda row: row["code"])
        == sorted(reference["acceptance_criteria"], key=lambda row: row["code"])
    ):
        cases = [
            {**case, "acceptance_criteria_codes": [criterion["code"]]}
            for criterion in criteria
            for case in SCENARIO["cases"][criterion["code"]]
        ]
    else:
        codes = [item["code"] for item in criteria]
        cases = [
            {
                "title": "Operación con datos válidos",
                "type": "positive",
                "preconditions": ["La funcionalidad está disponible."],
                "test_data": ["Datos válidos para el requisito revisado."],
                "steps": ["Abrir la funcionalidad.", "Aplicar datos válidos y confirmar."],
                "expected_result": "Se cumple el comportamiento especificado en el requisito.",
                "acceptance_criteria_codes": codes,
            },
            {
                "title": "Operación con datos inválidos",
                "type": "negative",
                "preconditions": [],
                "test_data": ["Datos inválidos para el requisito revisado."],
                "steps": ["Abrir la funcionalidad.", "Ingresar datos inválidos y confirmar."],
                "expected_result": "La funcionalidad informa la validación sin completar la operación.",
                "acceptance_criteria_codes": codes,
            },
        ]
    return {
        "test_cases": [
            {"code": f"TC-{index:03}", **case}
            for index, case in enumerate(cases, start=1)
        ]
    }
