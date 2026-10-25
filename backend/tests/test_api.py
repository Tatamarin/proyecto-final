import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_sdlc_ai.db"
os.environ["AI_API_KEY"] = ""

from fastapi.testclient import TestClient

from app import api as api_module
from app.db import Base, SessionLocal, engine
from app.main import app
from app.models import AIExecution, HumanReview


DB_PATH = Path("test_sdlc_ai.db")
client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module():
    engine.dispose()
    DB_PATH.unlink(missing_ok=True)


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
