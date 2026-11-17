import os
from pathlib import Path
from tempfile import TemporaryDirectory

db_directory = TemporaryDirectory(prefix="sdlc-ai-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{(Path(db_directory.name) / 'test.db').as_posix()}"
os.environ["AI_API_KEY"] = ""

from fastapi.testclient import TestClient

from app import api as api_module
from app.db import Base, SessionLocal, engine
from app.main import app
from app.models import AIExecution, HumanReview



client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module():
    engine.dispose()
    db_directory.cleanup()


def test_complete_mvp_flow_and_guards():
    project = client.post(
        "/api/projects",
        json={"name": "Portal", "description": "Caso de estudio"},
    )
    assert project.status_code == 201
    project_id = project.json()["id"]

    invalid_need = client.post(
        f"/api/projects/{project_id}/needs",
        json={"description": "corta"},
    )
    assert invalid_need.status_code == 422

    need = client.post(
        f"/api/projects/{project_id}/needs",
        json={"description": "Como cliente quiero recuperar mi contraseña por correo."},
    )
    assert need.status_code == 201
    need_id = need.json()["id"]

    generated = client.post(f"/api/needs/{need_id}/generate-requirements")
    assert generated.status_code == 200
    assert generated.json()["count"] == 1
    assert generated.json()["model"] == "demo"

    duplicate = client.post(f"/api/needs/{need_id}/generate-requirements")
    assert duplicate.status_code == 409

    requirements = client.get(f"/api/projects/{project_id}/requirements").json()
    requirement_id = requirements[0]["id"]
    assert requirements[0]["status"] == "GENERATED"
    assert requirements[0]["acceptance_criteria"]

    updated = client.put(
        f"/api/requirements/{requirement_id}",
        json={
            "type": "functional",
            "title": "Recuperar contraseña por correo",
            "description": "El portal permitirá solicitar un enlace de recuperación por correo.",
            "priority": "high",
            "acceptance_criteria": [
                {
                    "code": "AC-001",
                    "description": "Se informa que la solicitud fue recibida.",
                },
                {
                    "code": "AC-002",
                    "description": "El enlace solo puede utilizarse una vez.",
                },
            ],
        },
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "IN_REVIEW"
    assert {item["code"] for item in updated.json()["acceptance_criteria"]} == {
        "AC-001",
        "AC-002",
    }

    blocked = client.post(f"/api/requirements/{requirement_id}/generate-tests")
    assert blocked.status_code == 409

    approved = client.post(
        f"/api/requirements/{requirement_id}/decision/approve",
        json={"reviewer": "analista", "reason": "Verificado"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"

    tests = client.post(f"/api/requirements/{requirement_id}/generate-tests")
    assert tests.status_code == 200
    assert tests.json()["count"] == 2

    listed_tests = client.get(f"/api/requirements/{requirement_id}/tests")
    assert listed_tests.status_code == 200
    assert all(
        set(item["acceptance_criteria_codes"]) == {"AC-001", "AC-002"}
        for item in listed_tests.json()
    )

    duplicate_tests = client.post(f"/api/requirements/{requirement_id}/generate-tests")
    assert duplicate_tests.status_code == 409

    traceability = client.get(f"/api/projects/{project_id}/traceability")
    assert traceability.status_code == 200
    assert len(traceability.json()[0]["requirements"][0]["tests"]) == 2
    assert len(traceability.json()[0]["requirements"][0]["acceptance_criteria"]) == 2

    blocked_edit = client.put(
        f"/api/requirements/{requirement_id}",
        json={
            "type": "functional",
            "title": "Cambio tardío",
            "description": "No debe modificarse después de generar las pruebas.",
            "priority": "high",
            "acceptance_criteria": [
                {"code": "AC-001", "description": "Criterio tardío inválido."}
            ],
        },
    )
    assert blocked_edit.status_code == 409

    metrics = client.get(f"/api/projects/{project_id}/metrics")
    assert metrics.status_code == 200
    data = metrics.json()
    assert data["needs"] == 1
    assert data["requirements"] == 1
    assert data["approved_requirements"] == 1
    assert data["test_cases"] == 2
    assert data["ai_executions"] == 2
    assert data["quality_indicators"]["requirements_completeness_pct"] == 100.0
    assert data["quality_indicators"]["requirement_traceability_pct"] == 100.0
    assert data["quality_indicators"]["acceptance_criteria_coverage_pct"] == 100.0
    assert data["targets"]["time_reduction_pct"] == 25.0

    with SessionLocal() as db:
        assert db.query(HumanReview).count() == 2


def test_reject_requirement_records_decision():
    project_id = client.post("/api/projects", json={"name": "Portal"}).json()["id"]
    need_id = client.post(
        f"/api/projects/{project_id}/needs",
        json={"description": "Como cliente quiero recuperar el acceso al portal."},
    ).json()["id"]
    client.post(f"/api/needs/{need_id}/generate-requirements")
    requirement_id = client.get(
        f"/api/projects/{project_id}/requirements"
    ).json()[0]["id"]

    rejected = client.post(
        f"/api/requirements/{requirement_id}/decision/reject",
        json={"reviewer": "analista", "reason": "Falta una regla de seguridad"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "REJECTED"
    assert client.post(
        f"/api/requirements/{requirement_id}/generate-tests"
    ).status_code == 409

    with SessionLocal() as db:
        review = db.query(HumanReview).one()
        assert review.action == "REJECTED"
        assert review.reason == "Falta una regla de seguridad"


def test_unknown_acceptance_criterion_fails_without_partial_tests(monkeypatch):
    project_id = client.post("/api/projects", json={"name": "Portal"}).json()["id"]
    need_id = client.post(
        f"/api/projects/{project_id}/needs",
        json={"description": "Como cliente quiero recuperar el acceso al portal."},
    ).json()["id"]
    client.post(f"/api/needs/{need_id}/generate-requirements")
    requirement_id = client.get(
        f"/api/projects/{project_id}/requirements"
    ).json()[0]["id"]
    client.post(f"/api/requirements/{requirement_id}/decision/approve")

    def invalid_testing_output(agent, payload):
        assert agent == "TESTING"
        return (
            {
                "test_cases": [
                    {
                        "code": "TC-INVALID",
                        "title": "Caso con criterio inexistente",
                        "type": "negative",
                        "preconditions": [],
                        "steps": ["Ejecutar el flujo"],
                        "expected_result": "El sistema rechaza la operación.",
                        "acceptance_criteria_codes": ["AC-NO-EXISTE"],
                    }
                ]
            },
            1,
            "demo",
        )

    monkeypatch.setattr(api_module.llm, "generate", invalid_testing_output)
    response = client.post(f"/api/requirements/{requirement_id}/generate-tests")
    assert response.status_code == 502
    assert client.get(f"/api/requirements/{requirement_id}/tests").json() == []

    with SessionLocal() as db:
        execution = (
            db.query(AIExecution)
            .filter_by(agent_type="TESTING")
            .order_by(AIExecution.id.desc())
            .first()
        )
        assert execution.status == "FAILURE"
        assert "AC-NO-EXISTE" in execution.error_message


def accepted_requirement():
    project_id = client.post("/api/projects", json={"name": "Portal"}).json()["id"]
    need_id = client.post(
        f"/api/projects/{project_id}/needs",
        json={"description": "Como cliente quiero recuperar el acceso al portal."},
    ).json()["id"]
    assert client.post(f"/api/needs/{need_id}/generate-requirements").status_code == 200
    requirement = client.get(f"/api/projects/{project_id}/requirements").json()[0]
    assert client.post(f"/api/requirements/{requirement['id']}/approve").status_code == 200
    return project_id, requirement["id"]


def test_portal_example_links_positive_negative_and_boundary_cases():
    from app.demo import SCENARIO

    project_id = client.post("/api/projects", json={"name": "Caso sintético"}).json()["id"]
    need = client.post(
        f"/api/projects/{project_id}/needs",
        json={"description": SCENARIO["description"]},
    ).json()
    result = client.post(f"/api/needs/{need['id']}/generate-requirements")
    assert result.json()["count"] == 2
    requirements = client.get(f"/api/projects/{project_id}/requirements").json()
    all_cases = []
    for requirement in requirements:
        url = f"/api/requirements/{requirement['id']}"
        assert client.post(f"{url}/approve").status_code == 200
        assert client.post(f"{url}/generate-tests").status_code == 200
        cases = client.get(f"{url}/tests").json()
        assert all(test["test_data"] for test in cases)
        assert {code for test in cases for code in test["acceptance_criteria_codes"]} == {
            item["code"] for item in requirement["acceptance_criteria"]
        }
        all_cases.extend(cases)
    assert len(all_cases) == 6
    assert {test["type"] for test in all_cases} == {"positive", "negative", "boundary"}
    assert {test["test_data"][0] for test in all_cases if test["type"] == "boundary"} == {
        "Antigüedad del enlace: 29 min 59 s.", "Antigüedad del enlace: 30 min 00 s."
    }

    metrics = client.get(f"/api/projects/{project_id}/metrics").json()
    assert metrics["test_cases"] == 6
    assert metrics["quality_indicators"]["traceability_integrity_pct"] == 100.0


def test_review_case_updates_matrix_and_keeps_audit():
    project_id, requirement_id = accepted_requirement()
    url = f"/api/requirements/{requirement_id}"
    assert client.post(f"{url}/generate-tests").status_code == 200
    test_id = client.get(f"{url}/tests").json()[0]["id"]
    assert client.post(f"/api/tests/{test_id}/decision/approve").json()["status"] == "APPROVED"
    trace = client.get(f"/api/projects/{project_id}/traceability").json()
    assert trace[0]["requirements"][0]["tests"][0]["status"] == "APPROVED"
    assert client.post(f"/api/tests/{test_id}/decision/reject", json={
        "reason": "Aclarar los datos de prueba"
    }).status_code == 200
    with SessionLocal() as db:
        review = db.query(HumanReview).filter_by(test_case_id=test_id, action="REJECTED").one()
        assert review.original_value["status"] == "APPROVED"
        assert review.new_value["status"] == "REJECTED"
        assert review.reason == "Aclarar los datos de prueba"


def test_rejecting_requirement_with_cases_preserves_integrity():
    project_id, requirement_id = accepted_requirement()
    url = f"/api/requirements/{requirement_id}"
    assert client.post(f"{url}/generate-tests").status_code == 200
    assert client.post(f"{url}/reject").status_code == 409
    metrics = client.get(f"/api/projects/{project_id}/metrics").json()
    assert metrics["quality_indicators"]["traceability_integrity_pct"] == 100.0


def test_removal_of_approval_during_generation_does_not_save_cases(monkeypatch):
    _, requirement_id = accepted_requirement()
    url = f"/api/requirements/{requirement_id}"
    generate = api_module.llm.generate

    def concurrent_rejection(agent, payload):
        assert client.post(f"{url}/reject").status_code == 200
        return generate(agent, payload)

    monkeypatch.setattr(api_module.llm, "generate", concurrent_rejection)
    assert client.post(f"{url}/generate-tests").status_code == 409
    assert client.get(f"{url}/tests").json() == []


def test_invalid_generated_requirement_criteria_can_be_retried(monkeypatch):
    from copy import deepcopy

    project_id = client.post("/api/projects", json={"name": "Portal"}).json()["id"]
    need_id = client.post(
        f"/api/projects/{project_id}/needs",
        json={"description": "El portal debe permitir recuperar el acceso."},
    ).json()["id"]
    endpoint = f"/api/needs/{need_id}/generate-requirements"
    generate = api_module.llm.generate

    def duplicate_criteria(agent, payload):
        raw, elapsed, model = generate(agent, payload)
        invalid = deepcopy(raw)
        invalid["requirements"][0]["acceptance_criteria"] *= 2
        return invalid, elapsed, model

    with monkeypatch.context() as patch:
        patch.setattr(api_module.llm, "generate", duplicate_criteria)
        assert client.post(endpoint).status_code == 502
    assert client.get(f"/api/projects/{project_id}/requirements").json() == []
    assert client.post(endpoint).status_code == 200


def test_generated_case_rejects_blank_steps(monkeypatch):
    _, requirement_id = accepted_requirement()
    url = f"/api/requirements/{requirement_id}"
    generate = api_module.llm.generate

    def blank_step(agent, payload):
        raw, elapsed, model = generate(agent, payload)
        raw["test_cases"][-1]["steps"] = ["   "]
        return raw, elapsed, model

    monkeypatch.setattr(api_module.llm, "generate", blank_step)
    assert client.post(f"{url}/generate-tests").status_code == 502
    assert client.get(f"{url}/tests").json() == []


def test_interface_and_scenario_are_served_by_fastapi():
    page = client.get("/")
    assert page.status_code == 200
    assert "Trazabilidad de requisitos" in page.text
    assert client.get("/demo/app.js").status_code == 200
    assert client.get("/demo/style.css").status_code == 200
    scenario = client.get("/demo/scenario.json").json()
    assert "30 minutos" in scenario["description"]
