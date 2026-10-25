# Documentación de implementación de SDLC-AI

## 1. Propósito

SDLC-AI transforma una necesidad escrita en lenguaje natural en requisitos estructurados y, después de una aprobación humana, en casos de prueba trazables.

La regla principal es: **la IA propone; el sistema valida, persiste, relaciona y registra**.

## 2. Componentes

```text
cliente HTTP
        │ JSON
API FastAPI :8000
        ├── API REST
        ├── orquestación del flujo
        ├── LLMService y agentes
        └── SQLAlchemy/Alembic
                │
           PostgreSQL :5432
```

El backend usa un proveedor demo determinista cuando `AI_API_KEY` está vacío. Esto permite ejecutar el MVP sin depender de un proveedor externo. Con una clave configurada, `LLMService` usa el endpoint compatible con OpenAI definido por `AI_BASE_URL`.

## 3. Flujo funcional

1. Se crea un proyecto.
2. Se registra una necesidad.
3. El Agente de Requisitos consulta `LLMService`.
4. La respuesta JSON se persiste como requisitos y criterios de aceptación.
5. La persona revisora edita, aprueba o rechaza cada requisito.
6. El Agente de Pruebas solo recibe requisitos aprobados.
7. Los casos y sus pasos se persisten.
8. Cada caso se enlaza con uno o más criterios de aceptación existentes.
9. La API expone trazabilidad y calcula indicadores de tiempo, completitud y cobertura.

## 4. Estructura de código

```text
backend/
├── app/
│   ├── api.py       # endpoints y flujo de aplicación
│   ├── models.py    # modelo relacional SQLAlchemy
│   ├── schemas.py   # entrada y validación Pydantic
│   ├── llm.py       # adaptador de proveedor IA
│   ├── db.py        # engine y sesiones
│   └── main.py      # aplicación FastAPI
├── migrations/      # versiones Alembic
├── prompts/         # plantillas versionadas
└── Dockerfile
docs/
├── DATA_MODEL.md    # modelo entidad-relación
└── IMPLEMENTATION.md
```

## 5. Persistencia y migraciones

La base de datos se crea con Alembic, no con cambios implícitos del ORM. Al iniciar el contenedor backend se ejecuta:

```bash
alembic upgrade head
```

Para crear una nueva migración durante desarrollo:

```bash
cd backend
alembic revision --autogenerate -m "describe el cambio"
alembic upgrade head
```

La migración inicial es `0001_initial_schema.py`. La migración
`0002_test_case_criteria.py` agrega la relación explícita entre criterios y pruebas.

## 6. API principal

| Método | Ruta | Responsabilidad |
|---|---|---|
| POST | `/api/projects` | Crear proyecto |
| POST | `/api/projects/{id}/needs` | Registrar necesidad |
| POST | `/api/needs/{id}/generate-requirements` | Generar requisitos |
| PUT | `/api/requirements/{id}` | Editar requisito |
| POST | `/api/requirements/{id}/decision/{approve\|reject}` | Aprobar o rechazar requisito |
| POST | `/api/requirements/{id}/generate-tests` | Generar pruebas aprobadas |
| GET | `/api/projects/{id}/traceability` | Consultar trazabilidad |
| GET | `/api/projects/{id}/metrics` | Consultar métricas |

Los indicadores incluyen tiempo promedio de generación, completitud de requisitos,
trazabilidad de requisitos aprobados y cobertura de criterios de aceptación.

## 7. Configuración

Copiar `.env.example` como `.env` y configurar, si se desea un proveedor real:

```text
AI_API_KEY=...
AI_MODEL=gpt-4o-mini
AI_BASE_URL=https://api.openai.com/v1
```

Las credenciales solo se leen en la API y nunca se retornan al cliente.

## 8. Arranque y verificación

```powershell
docker compose up --build
```

Verificaciones:

```powershell
Invoke-WebRequest http://localhost:8000/health
```

La documentación interactiva queda disponible en `http://localhost:8000/docs`.

## 9. Verificación del corte de semana 8

- compilación del código Python: correcta;
- migraciones Alembic hasta `0002_test_case_criteria`: correctas;
- validación de Docker Compose: correcta;
- suite automatizada: `3 passed`;
- comprobación HTTP de `/health`: correcta.
