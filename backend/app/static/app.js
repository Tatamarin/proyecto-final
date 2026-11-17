const $ = (id) => document.getElementById(id);
const projects = $("projects");
const needs = $("needs");
const stateLabels = {
  GENERATED: "Generado", IN_REVIEW: "En revisión", APPROVED: "Aprobado", REJECTED: "Rechazado",
};
const typeLabels = {positive: "Positivo", negative: "Negativo", boundary: "De frontera"};
let busy = false;

async function request(path, method = "GET", body) {
  const response = await fetch(path, {
    method,
    ...(body && {headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)}),
  });
  if (response.ok) return response.json();
  const payload = await response.json().catch(() => ({}));
  const detail = typeof payload.detail === "string" ? payload.detail
    : payload.detail?.map?.(entry => entry.msg).join(". ");
  throw new Error(detail || "La solicitud no pudo completarse.");
}

function node(tag, text, className) {
  const element = document.createElement(tag);
  element.textContent = text ?? "";
  if (className) element.className = className;
  return element;
}

function button(label, action, secondary = false) {
  const element = node("button", label, secondary ? "secondary" : undefined);
  element.type = "button";
  element.addEventListener("click", () => run(action));
  return element;
}

async function run(action) {
  if (busy) return;
  busy = true;
  const feedback = $("feedback");
  feedback.classList.remove("error");
  feedback.textContent = "Procesando…";
  document.querySelector("main").setAttribute("aria-busy", "true");
  const disabled = [...document.querySelectorAll("button:not(:disabled), select:not(:disabled)")];
  disabled.forEach(control => { control.disabled = true; });
  try {
    feedback.textContent = (await action()) || "";
  } catch (error) {
    feedback.classList.add("error");
    feedback.textContent = error.message;
  } finally {
    disabled.forEach(control => { control.disabled = false; });
    syncControls();
    document.querySelector("main").removeAttribute("aria-busy");
    busy = false;
  }
}

function syncControls() {
  const hasProject = Boolean(projects.value);
  $("save-need").disabled = !hasProject;
  needs.disabled = !hasProject;
  $("generate").disabled = !needs.value || $("requirements").dataset.hasRequirements === "true";
}

function fillSelect(select, rows, placeholder, selectedId, label) {
  select.replaceChildren(new Option(placeholder, ""));
  rows.forEach(row => select.add(new Option(label(row), row.id)));
  select.value = selectedId || "";
}

async function loadProjects(selectedId) {
  const rows = await request("/api/projects");
  fillSelect(projects, rows, "Selecciona un proyecto", selectedId, row => row.name);
  await loadNeeds();
}

async function loadNeeds(selectedId) {
  const rows = projects.value ? await request(`/api/projects/${projects.value}/needs`) : [];
  fillSelect(needs, rows, "Selecciona una necesidad", selectedId,
    row => `#${row.id} · ${row.description.slice(0, 75)}`);
  await refresh();
}

function list(tag, rows) {
  const element = node(tag);
  rows.forEach(row => element.append(node("li", row)));
  return element;
}

async function decide(url, action, reason) {
  await request(`${url}/decision/${action}`, "POST", {reviewer: "analista-demo", reason: reason || null});
  await refresh();
  return action === "approve" ? "Aprobación registrada." : "Rechazo registrado.";
}

function renderCase(test) {
  const entry = node("details", "", "case");
  entry.append(
    node("summary", `${test.code} · ${test.title}`),
    node("p", `${typeLabels[test.type]} · ${stateLabels[test.status]} · ${test.acceptance_criteria_codes.join(", ")}`, "state"),
  );
  if (test.preconditions.length) entry.append(node("p", "Precondiciones"), list("ul", test.preconditions));
  if (test.test_data.length) entry.append(node("p", "Datos de prueba"), list("ul", test.test_data));
  entry.append(node("p", "Pasos"), list("ol", test.steps.map(step => step.description)),
    node("p", `Resultado esperado · ${test.expected_result}`));
  const actions = node("div", "", "actions");
  const url = `/api/tests/${test.id}`;
  if (test.status !== "APPROVED") actions.append(button("Aprobar caso", () => decide(url, "approve")));
  if (test.status !== "REJECTED") actions.append(button("Rechazar caso", () => decide(url, "reject"), true));
  entry.append(actions);
  return entry;
}

function inputField(label, control, value, options = {}) {
  const wrapper = node("label", label);
  control.value = value;
  Object.assign(control, options);
  wrapper.append(control);
  return wrapper;
}

function editor(requirement) {
  const details = node("details");
  details.append(node("summary", "Editar requisito"));
  const title = node("input");
  const description = node("textarea");
  const criteria = requirement.acceptance_criteria.map(item => ({...item, input: node("textarea")}));
  const form = node("form");
  const save = node("button", "Guardar cambios");
  form.append(
    inputField("Título", title, requirement.title, {required: true, minLength: 3, maxLength: 200}),
    inputField("Descripción", description, requirement.description, {required: true, minLength: 10, maxLength: 10000, rows: 3}),
    ...criteria.map(item => inputField(item.code, item.input, item.description,
      {required: true, minLength: 5, maxLength: 2000, rows: 2})),
    save,
  );
  form.addEventListener("submit", event => {
    event.preventDefault();
    run(async () => {
      await request(`/api/requirements/${requirement.id}`, "PUT", {
        type: requirement.type, priority: requirement.priority,
        title: title.value, description: description.value,
        acceptance_criteria: criteria.map(item => ({code: item.code, description: item.input.value})),
      });
      await refresh();
      return "Cambios guardados. Revisa el requisito antes de aprobarlo.";
    });
  });
  details.append(form);
  return details;
}

function renderRequirement(requirement, cases) {
  const article = node("article", "", "requirement");
  article.append(
    node("h3", `${requirement.code} · ${requirement.title}`),
    node("p", stateLabels[requirement.status], "state"),
    node("p", requirement.description),
    list("ul", requirement.acceptance_criteria.map(item => `${item.code} · ${item.description}`)),
  );
  const url = `/api/requirements/${requirement.id}`;
  const actions = node("div", "", "actions");
  if (!cases.length) {
    article.append(editor(requirement));
    if (requirement.status !== "APPROVED") actions.append(button("Aprobar requisito", () => decide(url, "approve")));
    if (requirement.status !== "REJECTED") actions.append(button("Rechazar requisito", () => decide(url, "reject"), true));
    if (requirement.status === "APPROVED") actions.append(button("Generar casos de prueba", async () => {
      const data = await request(`${url}/generate-tests`, "POST");
      await refresh();
      return `${data.count} casos generados · modelo ${data.model}.`;
    }));
  }
  article.append(actions, ...cases.map(renderCase));
  return article;
}

function renderTrace(trace, metrics) {
  const table = $("trace");
  table.replaceChildren();
  trace.forEach(need => need.requirements.forEach(requirement => {
    requirement.acceptance_criteria.forEach(criterion => {
      const row = node("tr");
      const relevant = requirement.tests.filter(test => test.acceptance_criteria_codes.includes(criterion.code));
      row.append(node("td", `#${need.need_id} · ${requirement.code} · ${stateLabels[requirement.status]}`),
        node("td", criterion.code),
        node("td", relevant.map(test => `${test.code} (${stateLabels[test.status]})`).join(", ") || "Sin caso asociado"));
      table.append(row);
    });
  }));
  if (!table.childElementCount) {
    const row = node("tr");
    const cell = node("td", "La matriz se llenará al generar requisitos.");
    cell.colSpan = 3;
    row.append(cell);
    table.append(row);
  }
  $("metrics").textContent = metrics
    ? `Cobertura de requisitos aprobados: ${metrics.quality_indicators.requirement_traceability_pct} %. Integridad de enlaces: ${metrics.quality_indicators.traceability_integrity_pct} %.`
    : "";
}

async function refresh() {
  const target = $("requirements");
  if (!projects.value) {
    target.dataset.hasRequirements = "false";
    target.replaceChildren(node("p", "Selecciona o crea un proyecto para comenzar.", "note"));
    renderTrace([], null);
    return;
  }
  const path = `/api/projects/${projects.value}`;
  const [requirements, trace, metrics] = await Promise.all([
    request(`${path}/requirements`), request(`${path}/traceability`), request(`${path}/metrics`),
  ]);
  const selected = requirements.filter(row => row.need_id === Number(needs.value));
  const cases = await Promise.all(selected.map(row => request(`/api/requirements/${row.id}/tests`)));
  target.dataset.hasRequirements = String(Boolean(selected.length));
  target.replaceChildren(...selected.map((row, index) => renderRequirement(row, cases[index])));
  if (!selected.length) target.append(node("p", "Selecciona una necesidad y genera sus requisitos.", "note"));
  renderTrace(trace, metrics);
}

projects.addEventListener("change", () => run(async () => {
  $("generation").textContent = "";
  await loadNeeds();
}));
needs.addEventListener("change", () => run(async () => {
  $("generation").textContent = "";
  await refresh();
}));
$("new-project").addEventListener("submit", event => {
  event.preventDefault();
  run(async () => {
    const name = $("project-name").value.trim();
    if (!name) throw new Error("Escribe un nombre para el proyecto.");
    const project = await request("/api/projects", "POST", {name});
    $("project-name").value = "";
    $("generation").textContent = "";
    await loadProjects(project.id);
    return "Proyecto creado.";
  });
});
$("example").addEventListener("click", () => run(async () => {
  const scenario = await request("/demo/scenario.json");
  $("description").value = scenario.description;
}));
$("new-need").addEventListener("submit", event => {
  event.preventDefault();
  run(async () => {
    const need = await request(`/api/projects/${projects.value}/needs`, "POST", {description: $("description").value});
    $("description").value = "";
    $("generation").textContent = "";
    await loadNeeds(need.id);
    return "Necesidad registrada.";
  });
});
$("generate").addEventListener("click", () => run(async () => {
  const result = await request(`/api/needs/${needs.value}/generate-requirements`, "POST");
  $("generation").replaceChildren(node("p", `Modelo de generación · ${result.model}`));
  if (result.ambiguities.length) $("generation").append(node("p", "Ambigüedades"), list("ul", result.ambiguities));
  if (result.missing_information.length) $("generation").append(node("p", "Información faltante"), list("ul", result.missing_information));
  await refresh();
  return `${result.count} requisitos generados.`;
}));
run(() => loadProjects());
