from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .llm import LLMService
from .models import (
    AcceptanceCriteria,
    AIExecution,
    HumanReview,
    Need,
    Project,
    PromptVersion,
    Requirement,
    TestCase,
    TestCaseStep,
)
from .schemas import (
    NeedIn,
    NeedOut,
    ProjectIn,
    ProjectOut,
    RequirementUpdate,
    RequirementsGeneration,
    ReviewDecision,
    TestsGeneration,
)

router = APIRouter()
llm = LLMService()


def project_or_404(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proyecto no encontrado")
    return project


def requirement_or_404(db: Session, requirement_id: int) -> Requirement:
    requirement = db.get(Requirement, requirement_id)
    if not requirement:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Requisito no encontrado")
    return requirement


def requirement_payload(requirement: Requirement) -> dict:
    return {
        "id": requirement.id,
        "need_id": requirement.need_id,
        "code": requirement.code,
        "type": requirement.type,
        "title": requirement.title,
        "description": requirement.description,
        "priority": requirement.priority,
        "status": requirement.status,
        "acceptance_criteria": [
            {"id": item.id, "code": item.code, "description": item.description}
            for item in requirement.acceptance_criteria
        ],
    }


def test_payload(test: TestCase) -> dict:
    return {
        "id": test.id,
        "requirement_id": test.requirement_id,
        "code": test.code,
        "title": test.title,
        "type": test.type,
        "preconditions": test.preconditions,
        "steps": [
            {"order": step.step_order, "description": step.description}
            for step in test.steps
        ],
        "expected_result": test.expected_result,
        "acceptance_criteria_codes": [
            criterion.code for criterion in test.acceptance_criteria
        ],
        "status": test.status,
    }


def prompt_version(db: Session, agent: str) -> PromptVersion:
    version_name, template = llm.prompt(agent)
    version = db.query(PromptVersion).filter_by(
        agent_type=agent, version=version_name
    ).first()
    if not version:
        version = PromptVersion(
            agent_type=agent,
            version=version_name,
            template=template,
        )
        db.add(version)
        db.flush()
    return version


def start_execution(db: Session, agent: str, payload: dict) -> AIExecution:
    execution = AIExecution(
        prompt_version=prompt_version(db, agent),
        agent_type=agent,
        model=settings.ai_model if settings.ai_api_key else "demo",
        input_json=payload,
        status="RUNNING",
        execution_time_ms=0,
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    return execution


def mark_execution_failed(db: Session, execution_id: int, exc: Exception) -> None:
    db.rollback()
    execution = db.get(AIExecution, execution_id)
    if execution:
        execution.status = "FAILURE"
        execution.error_message = str(exc)[:2000]
        db.commit()


@router.post("/projects", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(data: ProjectIn, db: Session = Depends(get_db)):
    project = Project(**data.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.id.desc()).all()


@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    return project_or_404(db, project_id)


@router.post(
    "/projects/{project_id}/needs",
    response_model=NeedOut,
    status_code=status.HTTP_201_CREATED,
)
def create_need(project_id: int, data: NeedIn, db: Session = Depends(get_db)):
    project_or_404(db, project_id)
    need = Need(project_id=project_id, **data.model_dump())
    db.add(need)
    db.commit()
    db.refresh(need)
    return need


@router.get("/projects/{project_id}/needs", response_model=list[NeedOut])
def list_needs(project_id: int, db: Session = Depends(get_db)):
    project_or_404(db, project_id)
    return db.query(Need).filter_by(project_id=project_id).order_by(Need.id).all()


@router.get("/projects/{project_id}/requirements")
def list_requirements(project_id: int, db: Session = Depends(get_db)):
    project = project_or_404(db, project_id)
    return [
        requirement_payload(requirement)
        for need in project.needs
        for requirement in need.requirements
    ]


@router.post("/needs/{need_id}/generate-requirements")
def generate_requirements(need_id: int, db: Session = Depends(get_db)):
    need = db.get(Need, need_id)
    if not need:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Necesidad no encontrada")
    if need.requirements:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "La necesidad ya tiene requisitos generados",
        )

    input_payload = {"description": need.description}
    execution = start_execution(db, "REQUIREMENTS", input_payload)
    try:
        raw_output, elapsed_ms, model = llm.generate("REQUIREMENTS", input_payload)
        output = RequirementsGeneration.model_validate(raw_output)
        execution.model = model
        execution.output_json = output.model_dump()
        execution.execution_time_ms = elapsed_ms
        execution.status = "SUCCESS"
        for row in output.requirements:
            requirement = Requirement(
                need_id=need.id,
                ai_execution_id=execution.id,
                code=row.code,
                type=row.type,
                title=row.title,
                description=row.description,
                priority=row.priority,
            )
            requirement.acceptance_criteria = [
                AcceptanceCriteria(code=item.code, description=item.description)
                for item in row.acceptance_criteria
            ]
            db.add(requirement)
        db.commit()
    except Exception as exc:
        mark_execution_failed(db, execution.id, exc)
        detail = "El agente de requisitos no produjo una respuesta válida"
        if not isinstance(exc, ValidationError):
            detail = "No fue posible ejecutar el agente de requisitos"
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail) from exc

    return {
        "count": len(output.requirements),
        "execution_id": execution.id,
        "execution_ms": elapsed_ms,
        "model": model,
        "ambiguities": output.ambiguities,
        "missing_information": output.missing_information,
    }


@router.put("/requirements/{requirement_id}")
def update_requirement(
    requirement_id: int,
    data: RequirementUpdate,
    db: Session = Depends(get_db),
):
    requirement = requirement_or_404(db, requirement_id)
    if requirement.tests:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "No se puede editar un requisito que ya tiene casos de prueba",
        )
    original = requirement_payload(requirement)
    fields = data.model_dump(exclude={"acceptance_criteria"})
    for field, value in fields.items():
        setattr(requirement, field, value)
    requirement.acceptance_criteria.clear()
    db.flush()
    requirement.acceptance_criteria = [
        AcceptanceCriteria(code=item.code, description=item.description)
        for item in data.acceptance_criteria
    ]
    requirement.status = "IN_REVIEW"
    db.flush()
    updated = requirement_payload(requirement)
    db.add(
        HumanReview(
            requirement=requirement,
            reviewer="user",
            action="EDIT",
            original_value=original,
            new_value=updated,
        )
    )
    db.commit()
    return updated


@router.post("/requirements/{requirement_id}/decision/{action}")
def decide_requirement(
    requirement_id: int,
    action: str,
    decision: ReviewDecision | None = None,
    db: Session = Depends(get_db),
):
    requirement = requirement_or_404(db, requirement_id)
    if action not in {"approve", "reject"}:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Acción no válida")
    decision = decision or ReviewDecision()
    requirement.status = "APPROVED" if action == "approve" else "REJECTED"
    db.flush()
    db.add(
        HumanReview(
            requirement=requirement,
            reviewer=decision.reviewer,
            action=requirement.status,
            new_value=requirement_payload(requirement),
            reason=decision.reason,
        )
    )
    db.commit()
    return {"id": requirement_id, "status": requirement.status}


@router.post("/requirements/{requirement_id}/approve", include_in_schema=False)
def approve_requirement(requirement_id: int, db: Session = Depends(get_db)):
    return decide_requirement(requirement_id, "approve", None, db)


@router.post("/requirements/{requirement_id}/reject", include_in_schema=False)
def reject_requirement(requirement_id: int, db: Session = Depends(get_db)):
    return decide_requirement(requirement_id, "reject", None, db)


@router.post("/requirements/{requirement_id}/generate-tests")
def generate_tests(requirement_id: int, db: Session = Depends(get_db)):
    requirement = requirement_or_404(db, requirement_id)
    if requirement.status != "APPROVED":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Solo se pueden generar pruebas para requisitos aprobados",
        )
    if requirement.tests:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "El requisito ya tiene casos de prueba generados",
        )

    criteria = [
        {"code": item.code, "description": item.description}
        for item in requirement.acceptance_criteria
    ]
    criteria_by_code = {item.code: item for item in requirement.acceptance_criteria}
    input_payload = {
        "requirement": {
            "code": requirement.code,
            "title": requirement.title,
            "description": requirement.description,
            "acceptance_criteria": criteria,
        }
    }
    execution = start_execution(db, "TESTING", input_payload)
    try:
        raw_output, elapsed_ms, model = llm.generate("TESTING", input_payload)
        output = TestsGeneration.model_validate(raw_output)
        execution.model = model
        execution.output_json = output.model_dump()
        execution.execution_time_ms = elapsed_ms
        execution.status = "SUCCESS"
        for row in output.test_cases:
            unknown_codes = set(row.acceptance_criteria_codes) - set(criteria_by_code)
            if unknown_codes:
                raise ValueError(
                    "Criterios de aceptación desconocidos: "
                    + ", ".join(sorted(unknown_codes))
                )
            test = TestCase(
                requirement_id=requirement.id,
                ai_execution_id=execution.id,
                code=row.code,
                title=row.title,
                type=row.type,
                preconditions=row.preconditions,
                expected_result=row.expected_result,
            )
            test.steps = [
                TestCaseStep(step_order=index, description=step)
                for index, step in enumerate(row.steps, 1)
            ]
            test.acceptance_criteria = [
                criteria_by_code[code] for code in row.acceptance_criteria_codes
            ]
            db.add(test)
        db.commit()
    except Exception as exc:
        mark_execution_failed(db, execution.id, exc)
        detail = "El agente de pruebas no produjo una respuesta válida"
        if not isinstance(exc, ValidationError):
            detail = "No fue posible ejecutar el agente de pruebas"
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail) from exc

    return {
        "count": len(output.test_cases),
        "execution_id": execution.id,
        "execution_ms": elapsed_ms,
        "model": model,
    }


@router.get("/requirements/{requirement_id}/tests")
def list_tests(requirement_id: int, db: Session = Depends(get_db)):
    requirement_or_404(db, requirement_id)
    tests = db.query(TestCase).filter_by(requirement_id=requirement_id).order_by(TestCase.id)
    return [test_payload(test) for test in tests]


@router.get("/projects/{project_id}/traceability")
def traceability(project_id: int, db: Session = Depends(get_db)):
    project = project_or_404(db, project_id)
    return [
        {
            "need_id": need.id,
            "need": need.description,
            "requirements": [
                {
                    "id": requirement.id,
                    "code": requirement.code,
                    "title": requirement.title,
                    "status": requirement.status,
                    "acceptance_criteria": [
                        {
                            "code": criterion.code,
                            "description": criterion.description,
                        }
                        for criterion in requirement.acceptance_criteria
                    ],
                    "tests": [
                        {
                            "id": test.id,
                            "code": test.code,
                            "title": test.title,
                            "type": test.type,
                            "acceptance_criteria_codes": [
                                criterion.code
                                for criterion in test.acceptance_criteria
                            ],
                        }
                        for test in requirement.tests
                    ],
                }
                for requirement in need.requirements
            ],
        }
        for need in project.needs
    ]


@router.get("/projects/{project_id}/metrics")
def metrics(project_id: int, db: Session = Depends(get_db)):
    project = project_or_404(db, project_id)
    requirements = [item for need in project.needs for item in need.requirements]
    execution_ids = {
        execution_id
        for requirement in requirements
        for execution_id in [
            requirement.ai_execution_id,
            *(test.ai_execution_id for test in requirement.tests),
        ]
        if execution_id is not None
    }
    executions = (
        db.query(AIExecution).filter(AIExecution.id.in_(execution_ids)).all()
        if execution_ids
        else []
    )
    criteria = [
        criterion
        for requirement in requirements
        for criterion in requirement.acceptance_criteria
    ]
    approved = [item for item in requirements if item.status == "APPROVED"]
    complete = [
        item
        for item in requirements
        if item.title.strip()
        and item.description.strip()
        and item.acceptance_criteria
    ]
    traced = [item for item in approved if item.tests]
    covered_criteria = [criterion for criterion in criteria if criterion.tests]

    def percentage(part: int, total: int) -> float:
        return round((part / total) * 100, 2) if total else 0.0

    average_time = (
        round(sum(item.execution_time_ms for item in executions) / len(executions), 2)
        if executions
        else 0.0
    )
    return {
        "needs": len(project.needs),
        "requirements": len(requirements),
        "approved_requirements": len(approved),
        "test_cases": sum(len(requirement.tests) for requirement in requirements),
        "ai_executions": len(execution_ids),
        "quality_indicators": {
            "average_generation_time_ms": average_time,
            "requirements_completeness_pct": percentage(
                len(complete), len(requirements)
            ),
            "requirement_traceability_pct": percentage(len(traced), len(approved)),
            "acceptance_criteria_coverage_pct": percentage(
                len(covered_criteria), len(criteria)
            ),
        },
        "targets": {
            "time_reduction_pct": 25.0,
            "requirements_completeness_pct": 90.0,
            "requirement_traceability_pct": 95.0,
            "acceptance_criteria_coverage_pct": 95.0,
            "time_reduction_requires_manual_baseline": True,
        },
    }
