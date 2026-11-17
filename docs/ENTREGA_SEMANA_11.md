# Entrega hasta la semana 11

Corte del 16 de noviembre de 2026. Las actividades 10 a 13 abarcan el desarrollo de los agentes, la trazabilidad y el prototipo integrado. La actividad 14 continúa en la semana 12. La actividad 15 entrega el escenario, los artefactos de referencia y el instrumento. La medición manual está pendiente.

## Demostración

Desde la raíz, ejecutar `docker compose up --build` y abrir [la interfaz](http://localhost:8000/). Con `AI_API_KEY` vacía se activa el modo demostrativo.

1. Crear un proyecto y seleccionar **Usar caso de ejemplo**.
2. Registrar la necesidad y generar sus dos requisitos. Los requisitos generados pueden editarse, aprobarse o rechazarse.
3. Aprobar ambos requisitos y generar los casos de cada uno. El requisito sobre la solicitud tiene dos casos y el de restablecimiento tiene cuatro.
4. Abrir un caso para consultar precondiciones, datos, pasos, resultado y criterios. Registrar la aprobación o el rechazo.
5. Verificar las cinco filas de la matriz y la cobertura de requisitos de 2/2. En el ejemplo, los seis casos enlazan un requisito aprobado y cubren los cinco criterios.

La documentación interactiva está en [Swagger](http://localhost:8000/docs). La interfaz usa las mismas rutas API. La nueva operación de revisión se encuentra en `POST /api/tests/{test_id}/decision/{action}`, con acciones `approve` y `reject` y cuerpo opcional con `reviewer` y `reason`.

La migración `0003_test_case_data` añade los datos de prueba y asigna una lista vacía a casos preexistentes. El prompt `testing_v1.1` incorpora el nuevo campo y solicita escenarios verificables de frontera cuando la regla los define. La generación vuelve a verificar que el requisito siga aprobado y que su contenido coincida con lo enviado al agente antes de persistir casos.

## Pruebas

Desde `backend` y con un entorno de Python activo:

```powershell
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
```

Resultado del corte: **10 pruebas aprobadas**. Se verificaron el flujo completo, los estados de revisión, la persistencia de datos de prueba, los casos de frontera, las referencias inválidas, los reintentos, los cambios de estado durante la generación y la entrega de la interfaz. La prueba de integración en PostgreSQL 16 con Docker Compose confirmó la migración y la persistencia de seis casos y seis enlaces a criterios. La prueba de navegador comprobó el caso sintético y la matriz en escritorio y en un ancho de 390 píxeles.

Las métricas de la interfaz verifican relaciones y recuentos del prototipo. Para la comparación del estudio se utiliza el [instrumento de línea base](LINEA_BASE_SEMANA_11.md), con tiempos observados y revisión de artefactos.
