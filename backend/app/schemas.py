from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator


class ProjectIn(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str = Field(default="", max_length=2000)


class NeedIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    description: str = Field(min_length=10, max_length=10_000)


NonBlank = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class AcceptanceCriterionIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    code: str = Field(min_length=1, max_length=30)
    description: str = Field(min_length=5, max_length=2000)


class RequirementUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    type: Literal["functional", "non_functional"]
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=10_000)
    priority: Literal["low", "medium", "high"] = "medium"
    acceptance_criteria: list[AcceptanceCriterionIn] = Field(min_length=1)

    @field_validator("acceptance_criteria")
    @classmethod
    def unique_acceptance_codes(cls, rows: list[AcceptanceCriterionIn]):
        codes = [row.code for row in rows]
        if len(codes) != len(set(codes)):
            raise ValueError("Los códigos de criterio deben ser únicos")
        return rows


class ReviewDecision(BaseModel):
    reviewer: str = Field(default="user", min_length=1, max_length=150)
    reason: str | None = Field(default=None, max_length=2000)


class ProjectOut(ProjectIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str


class NeedOut(NeedIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int


class GeneratedRequirement(RequirementUpdate):
    code: str = Field(min_length=1, max_length=30)


class RequirementsGeneration(BaseModel):
    requirements: list[GeneratedRequirement] = Field(min_length=1, max_length=20)
    ambiguities: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)

    @field_validator("requirements")
    @classmethod
    def unique_codes(cls, rows: list[GeneratedRequirement]):
        codes = [row.code for row in rows]
        if len(codes) != len(set(codes)):
            raise ValueError("Los códigos de requisito deben ser únicos")
        return rows


class GeneratedTestCase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: str = Field(min_length=1, max_length=30)
    title: str = Field(min_length=3, max_length=200)
    type: Literal["positive", "negative", "boundary"]
    preconditions: list[str] = Field(default_factory=list)
    test_data: list[NonBlank] = Field(default_factory=list)
    steps: list[NonBlank] = Field(min_length=1)
    expected_result: str = Field(min_length=5, max_length=5000)
    acceptance_criteria_codes: list[str] = Field(min_length=1)

    @field_validator("acceptance_criteria_codes")
    @classmethod
    def unique_criteria_codes(cls, codes: list[str]):
        if len(codes) != len(set(codes)):
            raise ValueError("Los códigos de criterio asociados deben ser únicos")
        return codes


class TestsGeneration(BaseModel):
    test_cases: list[GeneratedTestCase] = Field(min_length=1, max_length=30)

    @field_validator("test_cases")
    @classmethod
    def unique_codes(cls, rows: list[GeneratedTestCase]):
        codes = [row.code for row in rows]
        if len(codes) != len(set(codes)):
            raise ValueError("Los códigos de caso de prueba deben ser únicos")
        return rows
