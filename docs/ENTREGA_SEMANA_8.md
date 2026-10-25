# Entrega técnica acumulada — semanas 1 a 8

## 1. Identificación

- **Proyecto:** SDLC-AI
- **Estudiante:** Tatiana Marín Rivera
- **Corte:** semana 8
- **Programa:** Ingeniería de Software
- **Objetivo:** automatizar la estructuración de requisitos y la generación de casos de prueba mediante agentes de inteligencia artificial, conservando revisión humana y trazabilidad.

## 2. Resultado del corte

Al cierre de la semana 8 se entrega un prototipo de backend que transforma una necesidad escrita en lenguaje natural en requisitos estructurados. Después de una aprobación humana, el mismo flujo puede generar casos de prueba vinculados al requisito. El prototipo registra el prompt, la ejecución de IA, los artefactos generados y las decisiones de revisión.

El código incluye trabajo adelantado del Agente de Pruebas para facilitar la integración posterior. Este adelanto no sustituye la evaluación experimental programada para las semanas siguientes.

## 3. Entregables de código

| Entregable | Ubicación | Resultado |
|---|---|---|
| API REST | `backend/app/api.py` | Endpoints para proyectos, necesidades, requisitos, aprobaciones, pruebas, trazabilidad y métricas. |
| Validación | `backend/app/schemas.py` | Contratos Pydantic para entradas y respuestas de agentes. |
| Modelo de datos | `backend/app/models.py` | Entidades y relaciones de trazabilidad y auditoría. |
| Persistencia | `backend/app/db.py` | Motor y sesiones SQLAlchemy. |
| Integración IA | `backend/app/llm.py` | Proveedor configurable y modo demo determinista. |
| Aplicación | `backend/app/main.py` | Inicialización FastAPI y ruta de salud. |
| Migración | `backend/migrations/versions/0001_initial_schema.py` | Creación controlada del esquema inicial. |
| Agente de Requisitos | `backend/prompts/requirements/requirements_v1.0.txt` | Prompt versionado con salida JSON. |
| Agente de Pruebas | `backend/prompts/testing/testing_v1.0.txt` | Prompt versionado para casos positivos, negativos y de límite. |
| Pruebas automatizadas | `backend/tests/test_api.py` | Flujo MVP, auditoría, rechazo, trazabilidad criterio-prueba y manejo de errores verificados. |
| Entorno | `Dockerfile`, `docker-compose.yml`, `.env.example` | Ejecución reproducible con API y PostgreSQL. |

## 4. Cómo se construyó

1. Se delimitó el problema de pérdida de trazabilidad entre necesidad, requisito y prueba.
2. Se seleccionó como caso de estudio la recuperación de contraseña de un portal de clientes.
3. Se definió una arquitectura de dos agentes con una puerta de aprobación humana.
4. Se diseñó un modelo relacional con necesidades, requisitos, criterios, pruebas, pasos, prompts, ejecuciones y revisiones.
5. Se implementaron los contratos de entrada y salida antes de conectar el modelo de IA.
6. Se creó un modo demo determinista para verificar el flujo sin depender de una API externa.
7. Se incorporó un proveedor compatible con OpenAI mediante variables de entorno.
8. Se agregaron controles para impedir duplicados y bloquear pruebas de requisitos no aprobados.
9. Se documentaron la arquitectura, el modelo de datos, la ejecución y la evidencia del corte.

## 5. Flujo funcional implementado

```text
Proyecto
   └── Necesidad en lenguaje natural
          └── Agente de Requisitos
                 └── Requisito + criterios
                        └── Edición y aprobación humana
                               └── Agente de Pruebas
                                      └── Casos + pasos
```

La API permite consultar la cadena completa mediante `GET /api/projects/{id}/traceability` y los conteos operativos mediante `GET /api/projects/{id}/metrics`.

## 6. Correspondencia con las semanas 1 a 8

| Semana | Actividad | Evidencia entregada |
|---:|---|---|
| 1 | Revisión documental y definición inicial | Anteproyecto revisado y referencias. |
| 2 | Selección del caso de estudio | Documento del portal de clientes. |
| 3 | Requisitos y alcance | Requisitos candidatos, criterios y restricciones. |
| 4 | Indicadores | Metas iniciales de tiempo, completitud y trazabilidad. |
| 5 | Arquitectura | Especificación técnica y componentes del backend. |
| 6 | Modelo de datos | Entidades, relaciones, estados y migración inicial. |
| 7 | Preparación tecnológica | Docker, Compose, variables de entorno y prompts. |
| 8 | Inicio de implementación | API, Agente de Requisitos, persistencia y prueba integral definida. |

## 7. Verificación realizada para la entrega

- Compilación estática de `app`, `migrations` y `tests`: **correcta**.
- Validación de `docker-compose.yml` mediante `docker compose config -q`: **correcta**.
- Migraciones Alembic sobre una base limpia: **correctas hasta `0002_test_case_criteria`**.
- Ejecución de pytest: **3 pruebas aprobadas**.
- Comprobación HTTP de `/health`: **correcta**.
- Inspección de rutas, relaciones, validaciones y prompts: **realizada**.

## 8. Alcance pendiente

- implementar una interfaz de usuario para la demostración;
- realizar la comparación manual frente a SDLC-AI;
- analizar indicadores y redactar conclusiones;
- agregar autenticación y controles de producción si se despliega fuera de un entorno académico.

Los elementos pendientes pertenecen a fases posteriores a la semana 8 y no impiden considerar completo este corte.

## 9. Documentos relacionados

- `README.md`: inicio rápido y flujo mínimo.
- `docs/IMPLEMENTATION.md`: decisiones de implementación.
- `docs/DATA_MODEL.md`: modelo relacional.
- `docs/GUIA_TECNICA_Y_EJECUCION.md`: instalación, estructura y verificación.
- `docs/MATRIZ_ENTREGABLES_SEMANAS_1_8.md`: relación semana–actividad–archivo.

