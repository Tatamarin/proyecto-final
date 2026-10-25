# Guía técnica y de ejecución

## 1. Arquitectura

SDLC-AI utiliza una API FastAPI, modelos Pydantic, persistencia SQLAlchemy, migraciones Alembic y PostgreSQL. `LLMService` desacopla el flujo del proveedor de IA. Sin `AI_API_KEY`, el sistema utiliza respuestas deterministas de demostración; con una clave configurada, consume un endpoint compatible con OpenAI.

```text
Cliente HTTP
    │
    ▼
FastAPI ── validación Pydantic
    │
    ├── LLMService ── Agente de Requisitos / Agente de Pruebas
    │
    └── SQLAlchemy + Alembic ── PostgreSQL
```

## 2. Requisitos

- Docker Desktop o Docker Engine con Compose;
- puertos 8000 y 5432 disponibles;
- clave de proveedor únicamente si se desea salir del modo demo.

## 3. Configuración

Desde la raíz del proyecto:

```bash
cp .env.example .env
```

Variables:

```text
DATABASE_URL=postgresql+psycopg://sdlc:sdlc@db:5432/sdlc_ai
AI_API_KEY=
AI_MODEL=gpt-4o-mini
AI_BASE_URL=https://api.openai.com/v1
```

Las credenciales incluidas corresponden a desarrollo local. No deben reutilizarse en producción.

## 4. Inicio

```bash
docker compose up --build
```

El contenedor backend ejecuta `alembic upgrade head` antes de iniciar Uvicorn.

Puntos de acceso:

- salud: `http://localhost:8000/health`;
- documentación OpenAPI: `http://localhost:8000/docs`.

## 5. Flujo de demostración

### Crear proyecto

```bash
curl -X POST http://localhost:8000/api/projects \
  -H 'Content-Type: application/json' \
  -d '{"name":"Portal de clientes","description":"Caso de estudio"}'
```

### Registrar necesidad

```bash
curl -X POST http://localhost:8000/api/projects/1/needs \
  -H 'Content-Type: application/json' \
  -d '{"description":"Como cliente quiero recuperar mi contraseña por correo electrónico."}'
```

### Generar requisitos

```bash
curl -X POST http://localhost:8000/api/needs/1/generate-requirements
```

### Aprobar el requisito

```bash
curl -X POST http://localhost:8000/api/requirements/1/decision/approve \
  -H 'Content-Type: application/json' \
  -d '{"reviewer":"analista","reason":"Requisito verificado"}'
```

### Generar pruebas y consultar trazabilidad

```bash
curl -X POST http://localhost:8000/api/requirements/1/generate-tests
curl http://localhost:8000/api/projects/1/traceability
curl http://localhost:8000/api/projects/1/metrics
```

## 6. Pruebas

Con Python y las dependencias disponibles:

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
```

`test_complete_mvp_flow_and_guards` verifica:

- creación de proyecto;
- rechazo de una necesidad demasiado corta;
- generación en modo demo;
- prevención de requisitos y pruebas duplicados;
- bloqueo de pruebas antes de la aprobación;
- registro de aprobación humana;
- generación de casos de prueba;
- trazabilidad y métricas finales.

La suite también verifica el rechazo con auditoría y el manejo de criterios
desconocidos sin persistencia parcial. Resultado del corte: `3 passed`.

## 7. Cierre

```bash
docker compose down
```

Esta orden conserva el volumen local. Eliminar el volumen también elimina la base de datos y solo debe hacerse de manera intencional.

