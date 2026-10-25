# SDLC-AI API

API REST mínima para transformar una necesidad en requisitos revisables y, después de una aprobación humana, en casos de prueba trazables.

## Alcance del MVP

Incluye:

- proyectos y necesidades en lenguaje natural;
- generación y validación estructural de requisitos;
- edición, aprobación o rechazo con auditoría humana;
- generación de casos de prueba solo desde requisitos aprobados;
- trazabilidad necesidad → requisito → caso de prueba;
- trazabilidad explícita criterio de aceptación → caso de prueba;
- indicadores de tiempo, completitud, trazabilidad y cobertura;
- registro de cada ejecución de IA;
- proveedor demo determinista cuando no existe `AI_API_KEY`.

No incluye autenticación, roles, interfaz web, generación de código, ejecución automática de pruebas, despliegue de aplicaciones ni automatización de otras fases del SDLC.

## Ejecutar

Requiere Docker Desktop con los puertos `5432` y `8000` disponibles.

```bash
cp .env.example .env
docker compose up --build
```

La clave de IA es opcional. Sin ella, el flujo completo funciona en modo demo.

- OpenAPI/Swagger: http://localhost:8000/docs
- Salud: http://localhost:8000/health

## Flujo mínimo

```bash
# 1. Crear proyecto
curl -X POST http://localhost:8000/api/projects \
  -H 'Content-Type: application/json' \
  -d '{"name":"Portal de clientes","description":"Caso de estudio"}'

# 2. Registrar necesidad
curl -X POST http://localhost:8000/api/projects/1/needs \
  -H 'Content-Type: application/json' \
  -d '{"description":"Como cliente quiero recuperar mi contraseña por correo electrónico."}'

# 3. Generar requisitos
curl -X POST http://localhost:8000/api/needs/1/generate-requirements

# 4. Aprobar un requisito
curl -X POST http://localhost:8000/api/requirements/1/decision/approve \
  -H 'Content-Type: application/json' \
  -d '{"reviewer":"analista@ejemplo.com","reason":"Cumple los criterios"}'

# 5. Generar pruebas y consultar trazabilidad
curl -X POST http://localhost:8000/api/requirements/1/generate-tests
curl http://localhost:8000/api/projects/1/traceability
curl http://localhost:8000/api/projects/1/metrics
```

Las generaciones repetidas responden `409` para evitar duplicados. Las respuestas del proveedor de IA se validan antes de persistirse; una salida inválida responde `502` y queda registrada como ejecución fallida.

## Pruebas

Desde `backend/`, con las dependencias instaladas:

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
```

Resultado verificado para el corte de la semana 8: `3 passed`.

## Estructura relevante

```text
backend/app/       API FastAPI, persistencia y adaptador IA
backend/prompts/   prompts versionados
backend/tests/     prueba integral del flujo MVP
backend/migrations migración inicial Alembic
docs/              decisiones de implementación y modelo de datos
```

## Entrega acumulada de la semana 8

La documentación específica del corte se encuentra en:

- `docs/ENTREGA_SEMANA_8.md`: alcance, código entregado, método de construcción y estado de verificación;
- `docs/GUIA_TECNICA_Y_EJECUCION.md`: instalación, demostración y pruebas;
- `docs/MATRIZ_ENTREGABLES_SEMANAS_1_8.md`: correspondencia entre cronograma, evidencia y archivos.
