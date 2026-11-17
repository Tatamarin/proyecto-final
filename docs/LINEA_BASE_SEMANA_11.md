# Línea base del proceso manual

**Actividad 15, semanas 11 y 12, del 9 al 22 de noviembre de 2026.** Estado al corte de la semana 11: escenario, artefactos de referencia e instrumento preparados. Medición cronometrada pendiente.

## Enunciado que recibe el participante

El portal de clientes debe permitir solicitar un enlace de recuperación por correo. Para una cuenta registrada envía un enlace y muestra la misma confirmación que para una cuenta inexistente, sin enviar correo a esta última. El enlace es de un solo uso y solo es válido antes de que transcurran 30 minutos desde su emisión. Con un enlace válido se puede fijar una nueva contraseña y registrar el resultado sin guardar el enlace ni la contraseña en el registro.

## Procedimiento

1. Entregar el enunciado y las plantillas vacías al participante. Reservar los artefactos esperados para la revisión.
2. En la condición manual, redactar los requisitos y diseñar los casos con un editor, sin consultar las salidas de SDLC-AI. En la condición asistida, utilizar el mismo enunciado, registrar el modelo y la versión del prompt y conservar las salidas iniciales.
3. Iniciar el cronómetro con la entrega del enunciado. Registrar por separado el tiempo de especificación, diseño y revisión. Incluir espera de generación e interacción en la condición asistida. Registrar y descontar las pausas ajenas al ejercicio.
4. Guardar la primera versión antes de revisar. Aplicar la misma rúbrica en las dos condiciones, registrar cada corrección y conservar la versión validada y la matriz. Registrar quién ejerció cada rol mediante códigos.
5. Si la misma persona participa en ambas condiciones, anotar el orden y considerar el efecto de familiaridad al interpretar el tiempo. Registrar resultados con una condición o muestra faltante como pendientes.

## Registro por corrida

| Campo | Valor |
|---|---|
| Código de corrida y fecha | |
| Condición (manual o asistida) y orden | |
| Código de participante y de revisor | |
| Editor o versión del prototipo, modelo y prompt | |
| Especificación de requisitos, inicio, fin y duración efectiva (min:s) | |
| Diseño de casos, inicio, fin y duración efectiva (min:s) | |
| Revisión y correcciones, inicio, fin y duración efectiva (min:s) | |
| Pausas excluidas y motivo | |
| Tiempo efectivo total (min:s) | |
| Archivos de la primera versión, versión validada y matriz | |
| Incidencias o desviaciones del protocolo | |

**Plantilla de requisito**

| ID | Tipo | Título | Descripción | Prioridad | Criterios verificables con ID | Estado |
|---|---|---|---|---|---|---|
| | | | | | | |

**Plantilla de caso de prueba**

| ID | Requisito | Criterios | Título y tipo | Precondiciones | Datos sintéticos | Pasos | Resultado esperado | Estado |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |

**Registro de revisión**

| ID de artefacto | Campo o relación revisada | Valor inicial | Decisión y justificación | Corrección | Sustancial (sí/no) |
|---|---|---|---|---|---|
| | | | | | |

Cambiar el comportamiento, el resultado esperado, el criterio o el enlace se considera corrección sustancial. La corrección ortográfica sin cambio semántico es menor. Registrar los artefactos faltantes identificados por el revisor.

## Rúbrica y cálculo

| Indicador | Registro | Meta |
|---|---|---|
| Tiempo | Sumar minutos efectivos de las tres fases. Reducción = 100 × (manual − asistido) / manual. | ≥ 25 % |
| Completitud | Campos obligatorios válidos en la primera versión / campos obligatorios esperados. Registrar ausencia explícita de precondiciones o datos como «no aplica» solo si se justifica. | ≥ 90 % |
| Cobertura de trazabilidad | Requisitos aprobados con uno o más casos asociados / requisitos aprobados. | ≥ 95 % |
| Integridad de trazabilidad | Casos vinculados a un requisito existente y aprobado / casos generados. | 100 % |
| Consistencia | Artefactos revisados sin contradicciones internas o entre requisito, criterio y caso / artefactos revisados. | ≥ 90 % |
| Intervención humana | Artefactos revisados con corrección sustancial / artefactos revisados. Contar cada artefacto una vez. | ≤ 20 % |

Conservar numerador, denominador y porcentaje de cada indicador. Un denominador nulo se registra como no calculable. La latencia de la API es un dato técnico y la medición del ejercicio usa tiempo efectivo de principio a fin.

## Artefactos esperados para revisión

El [escenario demostrativo](../backend/app/static/scenario.json) contiene el enunciado, dos requisitos de referencia, cinco criterios y seis casos reproducibles. El revisor admite identificadores y formulaciones equivalentes siempre que los comportamientos y vínculos sean verificables. Los casos cubren cuenta registrada, cuenta inexistente, uso a 29:59, vencimiento a 30:00, enlace reutilizado y omisión de secretos en el registro. Esta referencia sirve para revisar los artefactos del participante.

## Tratamiento de datos

Utilizar direcciones, credenciales y enlaces sintéticos. Conservar la evidencia en una ubicación de acceso restringido. Si se incorporan datos personales reales, documentar finalidad y autorización cuando corresponda, según los artículos 4, 8 y 9 de la [Ley 1581 de 2012](https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=49981).
