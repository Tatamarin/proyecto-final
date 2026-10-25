# Matriz de entregables — semanas 1 a 8

| Semana | Fase | Actividad | Entregable verificable | Archivo o componente |
|---:|---|---|---|---|
| 1 | Investigación | Revisión bibliográfica y formulación | Base documental revisada | Anteproyecto y referencias del proyecto |
| 2 | Análisis | Selección y descripción del escenario | Caso de estudio del portal de clientes | Documento de caso de estudio |
| 3 | Análisis | Definición de alcance, actores y requisitos | Especificación funcional inicial | `docs/ENTREGA_SEMANA_8.md` y caso de estudio |
| 4 | Análisis | Definición de indicadores | Metas de tiempo, completitud y trazabilidad | Informe de avance semanas 1–8 |
| 5 | Diseño | Arquitectura de agentes y backend | Especificación técnica | `docs/IMPLEMENTATION.md`, `backend/app/` |
| 6 | Diseño | Modelo de datos y trazabilidad | Modelo relacional y migración | `docs/DATA_MODEL.md`, `backend/app/models.py`, `backend/migrations/` |
| 7 | Diseño | Preparación del entorno y prompts | Entorno reproducible y agentes versionados | `Dockerfile`, `docker-compose.yml`, `.env.example`, `backend/prompts/` |
| 8 | Implementación | Inicio del prototipo y Agente de Requisitos | API inicial, persistencia y prueba definida | `backend/app/`, `backend/tests/test_api.py` |

## Estado de evidencia

| Evidencia | Estado al corte | Observación |
|---|---|---|
| Código Python compila | Verificado | `compileall` finalizó sin errores. |
| Compose es válido | Verificado | `docker compose config -q` finalizó sin errores. |
| Pruebas automatizadas | Verificadas | `3 passed` en el entorno aislado de validación. |
| Revisión humana | Implementada | Edición, aprobación y rechazo quedan auditados. |
| Trazabilidad | Implementada a nivel requisito | Necesidad → requisito → caso de prueba. |
| Cobertura criterio–prueba | Implementada | Tabla `test_case_criteria`, validación de códigos e indicador porcentual. |

