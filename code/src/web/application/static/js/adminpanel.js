const API_ROUTE = 'http://localhost:3000/api';
const LOGIN = 'http://localhost:8080/login';
const CHAT_ROUTE = 'http://localhost:3300/chat';

let toUpdateReports = [];

const token = localStorage.getItem("token");
if (!token) {
  console.error("No hay token guardado en localStorage");
}

// <-------------------- SHOW ALERT BANNER --------------------->
function showAlertBanner(message, type = 'danger') {
  const alertBanner = document.getElementById('alert-banner');
  alertBanner.classList.remove('d-none');
  alertBanner.classList.remove('alert-success', 'alert-danger', 'alert-info');
  alertBanner.classList.add(`alert-${type}`);
  let headerText = "";
  if (type === 'success') {
    headerText = "Información";
  } else {
    headerText = "¡Error!";
  }
  alertBanner.querySelector('.alert-heading').innerText = headerText;
  alertBanner.querySelector('#alert-banner-text').innerText = message;
  setTimeout(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, 200);
};
// <-------------------- SHOW ALERT BANNER --------------------->

// <-------------------- RENDER BOT CONTENT --------------------->
function renderBotContent(markdown) {
  const container = document.createElement("div");

  container.style.overflowWrap = "break-word";
  container.style.wordWrap = "break-word";
  container.style.whiteSpace = "normal";

  container.innerHTML = marked.parse(markdown);
  renderMathInElement(container, {
    delimiters: [
      { left: "$$", right: "$$", display: true },
      { left: "$", right: "$", display: false }
    ],
    throwOnError: false
  });
  return container;
}
// <-------------------- RENDER BOT CONTENT --------------------->

// <-------------------- LOAD ALL PROJECTS --------------------->
async function loadAllProjects() {
  try {
    const response = await fetch(API_ROUTE + "/get-all-projects", {
      method: "GET",
      credentials: 'include',
    });
    if (response.status === 401) {
      window.location.href = LOGIN;
      return;
    }

    const data = await response.json();

    if (response.ok) {

      const tableBody = document.querySelector("#Projects tbody");
      tableBody.innerHTML = "";

      const select = document.getElementById("project_selector");
      const firstOption = select.options[0];
      select.innerHTML = "";
      select.appendChild(firstOption);

      data.sort((a, b) => new Date(b.creation_date) - new Date(a.creation_date));

      data.forEach(project => {
        const newRow = document.createElement("tr");
        newRow.dataset.project = project.project_name;
        newRow.dataset.email = project.email;
        newRow.innerHTML = `
          <td><input type="checkbox" class="project-checkbox" data-email="${project.email}" data-project = "${project.project_name}"></td>
          <td>${project.email}</td>
          <td style="max-width: 10em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${project.project_name}</td>
          <td style="max-width: 20em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${project.about}</td>
          <td>${project.creation_date}</td>
          <td>${project.modification_date}</td>
          <td>
            ${project.file_name && project.file_data
            ? `<button class="btn btn-sm btn-secondary view-json-btn" data-file-name="${project.file_name}" data-file-data="${project.file_data}">Ver SBOM</button>`
            : "Sin archivo"}
          </td>
          <td>
            ${project.report_name && project.report_data
            ? `<button class="btn btn-sm btn-secondary view-report-btn">Ver Reporte</button>`
            : (project.file_name && project.file_data
              ? `<button class="btn btn-sm btn-secondary generate-report-btn">Generar Reporte</button>`
              : "Sin reporte")
          }
          </td>
        `;

        const viewButton = newRow.querySelector(".view-json-btn");
        if (viewButton) {

          viewButton.addEventListener("click", () => {
            const fileName = project.file_name;
            const fileData = project.file_data;

            document.getElementById("jsonFileName").textContent = fileName;

            try {
              const parsed = JSON.parse(fileData);
              document.getElementById("jsonFileContent").textContent = JSON.stringify(parsed, null, 2);
            } catch (error) {
              console.error("Error al procesar el JSON:", error);
              document.getElementById("jsonFileContent").textContent = "Error al mostrar el contenido JSON.";
            }

            const modal = new bootstrap.Modal(document.getElementById("jsonModal"));
            modal.show();
          });
        }

        const viewReportButton = newRow.querySelector(".view-report-btn");
        if (viewReportButton) {

          const reportName = project.report_name;
          const reportData = project.report_data;
          const reportReasoning = project.report_reasoning;


          viewReportButton.addEventListener("click", () => {
            document.getElementById("reportModalTitle").textContent = reportName;

            const reportDescriptionContainer = document.getElementById("reportDescription");
            const renderedContent = renderBotContent(reportData)

            reportDescriptionContainer.replaceChildren(renderedContent);

            const copyBtn = document.getElementById("copyReportBtn");
            copyBtn.onclick = () => {
              navigator.clipboard.writeText(reportData)
                .then(() => {
                  copyBtn.textContent = "Copiado ✔️";
                })
                .catch(err => {
                  console.error("Error al copiar:", err);
                  copyBtn.textContent = "Error ❌";
                });
            };

            if (reportReasoning) {
              const reasoningBtn = document.getElementById("reportReasoningBtn");
              reasoningBtn.classList.remove("d-none");
              const reasoningDiv = document.getElementById("reportReasoning");

              const content = document.getElementById("reportReasoningContent");
              const renderedReasoning = renderBotContent(reportReasoning);
              content.replaceChildren(renderedReasoning);

              reasoningBtn.onclick = () => {
                reasoningDiv.classList.toggle("d-none");
                if (reasoningDiv.classList.contains("d-none")) {
                  reasoningBtn.textContent = "Mostrar razonamiento";
                } else {
                  reasoningBtn.textContent = "Ocultar razonamiento";
                }
              };
            } else {
              const reasoningBtn = document.getElementById("reportReasoningBtn");
              reasoningBtn.classList.add("d-none");
            }
            const reportModal = new bootstrap.Modal(document.getElementById('reportModal'));
            reportModal.show();
          });
        }

        const generateReportButton = newRow.querySelector(".generate-report-btn");
        if (generateReportButton) {
          generateReportButton.onclick = () => createReport(project.email, project.project_name);
        }

        tableBody.appendChild(newRow);

        const newOption = document.createElement("option");
        newOption.value = project.project_name;
        newOption.textContent = `${project.project_name} - ${project.email}`;
        newOption.dataset.email = project.email;
        newOption.dataset.about = project.about;
        newOption.dataset.modification_date = project.modification_date;
        newOption.dataset.creation_date = project.creation_date;
        newOption.dataset.file_name = project.file_name || "";

        select.appendChild(newOption);
      });

    } else {
      showAlertBanner("Error al cargar los proyectos");
      console.error("Error al cargar proyectos:", data);
    }
  } catch (error) {
    showAlertBanner("Error de conexión al intentar cargar los proyectos");
    console.error("Error en la solicitud");
  }
}
// <-------------------- LOAD ALL PROJECTS --------------------->

// <-------------------- LOAD ALL DELETED PROJECTS --------------------->
// Función para cargar todos los proyectos eliminados
async function loadAllDeletedProjects() {
  try {
    const response = await fetch(API_ROUTE + "/get-all-deleted-projects", {
      method: "GET",
      credentials: 'include',
    });
    if (response.status === 401) {
      window.location.href = LOGIN;
      return;
    }

    const data = await response.json();

    if (response.ok) {
      // Limpiar la tabla de proyectos eliminados antes de agregar los nuevos
      const deletedTableBody = document.querySelector("#DeletedProjects tbody");
      deletedTableBody.innerHTML = "";

      // Agregar cada proyecto eliminado a la tabla
      data.forEach(project => {
        const newRow = document.createElement("tr");
        newRow.innerHTML = `
          <td>${project.email}</td>
          <td style="max-width: 10em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${project.project_name}</td>
          <td style="max-width: 20em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${project.about}</td>
          <td>${project.creation_date}</td>
          <td>${project.deletion_date}</td>
          <td>
            ${project.file_name && project.file_data
            ? `<button class="btn btn-sm btn-secondary view-json-btn" data-file-name="${project.file_name}" data-file-data="${project.file_data}">Ver SBOM</button>`
            : "Sin archivo"}
          </td>
          <td>
            ${project.report_name && project.report_data
            ? `<button class="btn btn-sm btn-secondary view-report-btn">Ver Reporte</button>`
            : "Sin reporte"}
          </td>
        `;
        deletedTableBody.appendChild(newRow);

        const viewButton = newRow.querySelector(".view-json-btn");
        if (viewButton) {

          viewButton.addEventListener("click", () => {
            const fileName = project.file_name;
            const fileData = project.file_data;

            document.getElementById("jsonFileName").textContent = fileName;

            try {
              const parsed = JSON.parse(fileData);
              document.getElementById("jsonFileContent").textContent = JSON.stringify(parsed, null, 2);
            } catch (error) {
              console.error("Error al procesar el JSON:", error);
              document.getElementById("jsonFileContent").textContent = "Error al mostrar el contenido JSON.";
            }

            const modal = new bootstrap.Modal(document.getElementById("jsonModal"));
            modal.show();
          });
        }

        const viewReportButton = newRow.querySelector(".view-report-btn");
        if (viewReportButton) {

          const reportName = project.report_name;
          const reportData = project.report_data;
          const reportReasoning = project.report_reasoning;

          viewReportButton.addEventListener("click", () => {
            document.getElementById("reportModalTitle").textContent = reportName;

            const reportDescriptionContainer = document.getElementById("reportDescription");
            const renderedContent = renderBotContent(reportData);

            reportDescriptionContainer.replaceChildren(renderedContent);

            const copyBtn = document.getElementById("copyReportBtn");
            copyBtn.onclick = () => {
              navigator.clipboard.writeText(reportData)
                .then(() => {
                  copyBtn.textContent = "Copiado ✔️";
                })
                .catch(err => {
                  console.error("Error al copiar:", err);
                  copyBtn.textContent = "Error ❌";
                });
            };

            if (reportReasoning) {
              const reasoningBtn = document.getElementById("reportReasoningBtn");
              reasoningBtn.classList.remove("d-none");
              const reasoningDiv = document.getElementById("reportReasoning");

              const content = document.getElementById("reportReasoningContent");
              const renderedReasoning = renderBotContent(reportReasoning);
              content.replaceChildren(renderedReasoning);

              reasoningBtn.onclick = () => {
                reasoningDiv.classList.toggle("d-none");
                if (reasoningDiv.classList.contains("d-none")) {
                  reasoningBtn.textContent = "Mostrar razonamiento";
                } else {
                  reasoningBtn.textContent = "Ocultar razonamiento";
                }
              };
            } else {
              const reasoningBtn = document.getElementById("reportReasoningBtn");
              reasoningBtn.classList.add("d-none");
            }
            const reportModal = new bootstrap.Modal(document.getElementById('reportModal'));
            reportModal.show();
          });
        }

      });

    } else {
      showAlertBanner("Error al cargar los proyectos eliminados");
      console.error("Error al cargar proyectos eliminados");
    }
  } catch (error) {
    showAlertBanner("Error de conexión al intentar cargar los proyectos eliminados");
    console.error("Error en la solicitud de proyectos eliminados");
  }
}

document.addEventListener("DOMContentLoaded", async function () {
  await loadAllProjects();
  loadAllDeletedProjects();
  checkAndSchedule(true);
});
// <-------------------- LOAD ALL DELETED PROJECTS --------------------->

// <-------------------- UPDATE FILES --------------------->
async function updateFiles(projects) {
  for (const project of projects) {
    fetch(API_ROUTE + '/get-report-data', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({ project_name: project[1], email: project[0] })
    })
      .then(response => {
        if (response.status === 401) {
          window.location.href = "http://localhost:8080/login";
          return;
        }
        return response.json();
      })
      .then(data => {
        if (data.ok) {
          showAlertBanner("Reporte generado exitosamente.", "success");
          localStorage.removeItem("CurrentReportGenerate");
          const projectName = project[1];
          const userEmail = project[0];
          const reportName = data.content.report_name;
          const reportData = data.content.report_data;
          const reportReasoning = data.content.report_reasoning;

          const selectedRow = document.querySelector(`#Projects tbody tr[data-project="${projectName}"][data-email="${userEmail}"]`);
          if (selectedRow) {
            const reportButton = selectedRow.querySelector(".generate-report-btn");
            if (reportButton) {
              reportButton.onclick = null;
              reportButton.disabled = false;

              reportButton.classList.remove("generate-report-btn");
              reportButton.classList.add("view-report-btn");
              reportButton.textContent = "Ver Reporte";

              reportButton.addEventListener("click", () => {
                document.getElementById("reportModalTitle").textContent = reportName;

                const reportDescriptionContainer = document.getElementById("reportDescription");
                const renderedContent = renderBotContent(reportData);

                reportDescriptionContainer.replaceChildren(renderedContent);

                const copyBtn = document.getElementById("copyReportBtn");
                copyBtn.onclick = () => {
                  navigator.clipboard.writeText(reportData)
                    .then(() => {
                      copyBtn.textContent = "Copiado ✔️";
                    })
                    .catch(err => {
                      console.error("Error al copiar:", err);
                      copyBtn.textContent = "Error ❌";
                    });
                };

                if (reportReasoning) {
                  const reasoningBtn = document.getElementById("reportReasoningBtn");
                  reasoningBtn.classList.remove("d-none");
                  const reasoningDiv = document.getElementById("reportReasoning");

                  const content = document.getElementById("reportReasoningContent");
                  const renderedReasoning = renderBotContent(reportReasoning);
                  content.replaceChildren(renderedReasoning);

                  reasoningBtn.onclick = () => {
                    reasoningDiv.classList.toggle("d-none");
                    if (reasoningDiv.classList.contains("d-none")) {
                      reasoningBtn.textContent = "Mostrar razonamiento";
                    } else {
                      reasoningBtn.textContent = "Ocultar razonamiento";
                    }
                  };
                } else {
                  const reasoningBtn = document.getElementById("reportReasoningBtn");
                  reasoningBtn.classList.add("d-none");
                }
                const reportModal = new bootstrap.Modal(document.getElementById('reportModal'));
                reportModal.show();
              });
            }
          }

        } else {
          showAlertBanner("Error al generar el reporte: " + data.message);
        }
      })
      .catch(error => {
        console.error("Error al generar el reporte:", error);
        showAlertBanner("Error al generar el reporte.");
      });
  }
}
// <-------------------- UPDATE FILES --------------------->

// <-------------------- CHECK AND SCHEDULE ---------------------->
async function checkGenerationStatus() {
  try {
    const response = await fetch(API_ROUTE + "/check-generation-status/admin", {
      method: "GET",
      credentials: "include",
    });

    if (!response.ok) {
      console.error("Error en el fetch:", response.status);
      return null;
    }

    const result = await response.json();
    return result.projects || [];
  } catch (error) {
    console.error("Error al consultar el estado de generación:", error);
    return null;
  }
}

async function checkAndSchedule(isFirstRun = false) {
  const projects = await checkGenerationStatus();

  if (projects && projects.length > 0) {
    localStorage.setItem("CurrentReportGenerate", JSON.stringify(projects));
    for (const project of projects) {
      if (!toUpdateReports.includes(project)) {
        toUpdateReports.push(project);
      }
      const projectName = project[1];
      const userEmail = project[0];
      const selectedRow = document.querySelector(`#Projects tbody tr[data-project="${projectName}"][data-email="${userEmail}"]`);
      if (selectedRow) {
        const generateBtn = selectedRow.querySelector(".generate-report-btn");
        if (generateBtn) {
          generateBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generando...`;
          generateBtn.disabled = true;
        };
      };
    }

    if (isFirstRun) {
      showAlertBanner("Ya hay un reporte en proceso de generación. Por favor, espera a que se complete antes de generar otro.", "success");
    }

    setTimeout(() => checkAndSchedule(false), 10000); // Reintentar en 10s
  } else {
    localStorage.removeItem("CurrentReportGenerate");
    if (!isFirstRun) {
      showAlertBanner("Reporte generado exitosamente.", "success");
      updateFiles(toUpdateReports);
    }
  }
}
// <-------------------- CHECK AND SCHEDULE ---------------------->

// <-------------------- LOAD ALL USERS --------------------->
async function loadAllUsers() {
  try {
    const response = await fetch(API_ROUTE + "/get-all-users", {
      method: "GET",
      credentials: 'include',
    });
    if (response.status === 401) {
      window.location.href = LOGIN;
      return;
    }

    const data = await response.json();

    if (response.ok) {

      const tableBody = document.querySelector("#User tbody");
      tableBody.innerHTML = "";

      const select = document.getElementById("user_selector_user");
      const firstOption = select.options[0];
      select.innerHTML = "";
      select.appendChild(firstOption);

      //data.sort((a, b) => new Date(b.creation_date) - new Date(a.creation_date));

      data.forEach(user => {
        const isActive = true

        const newRow = document.createElement("tr");
        newRow.dataset.email = user.email;
        newRow.innerHTML = `
          <td><input type="checkbox" class="user-checkbox" data-email="${user.email}" data-active="${isActive}"></td>
          <td>${user.email}</td>
          <td>${user.name}</td>
          <td>${user.surname}</td>
          <td>${user.role}</td>
          <td>${isActive ? "✓" : "✗"}</td>
        `;
        tableBody.appendChild(newRow);

        const newOption = document.createElement("option");
        newOption.value = user.email;
        newOption.textContent = `${user.email} - ${user.name} ${user.surname}`;
        newOption.dataset.name = user.name;
        newOption.dataset.surname = user.surname;
        newOption.dataset.role = user.role;
        newOption.dataset.active = "True";

        select.insertBefore(newOption, select.children[1]);
      });

    } else {
      showAlertBanner("Error al cargar los proyectos");
      console.error("Error al cargar proyectos:", data);
    }
  } catch (error) {
    showAlertBanner("Error de conexión al intentar cargar los proyectos");
    console.error("Error en la solicitud");
  }
}
// <-------------------- LOAD ALL USERS --------------------->

// <-------------------- SHOW MODAL CREATE --------------------->
createProjectModal.addEventListener('show.bs.modal', () => {
  document.getElementById('max_total_vulns').value = 20;
  document.getElementById('min_fixable_ratio').value = 80;
  document.getElementById('max_severity_level').value = 7.0;
  document.getElementById('composite_score').value = 75;
});
// <-------------------- SHOW MODAL CREATE --------------------->

// <-------------------- RESET MODAL --------------------->
crearUsuarioModal.addEventListener('hidden.bs.modal', () => {
  const inputs = createProjectModal.querySelectorAll('input, textarea');
  inputs.forEach(input => input.value = '');
});

createProjectModal.addEventListener('hidden.bs.modal', () => {
  const inputs = createProjectModal.querySelectorAll('input, textarea');
  inputs.forEach(input => input.value = '');
});

editUsuarioModal.addEventListener('hidden.bs.modal', () => {
  const form = editUsuarioModal.querySelector('form');
  const inputs = form.querySelectorAll('input, textarea, select');

  inputs.forEach(input => {
    if (input.type === 'checkbox' || input.type === 'radio') {
      input.checked = false;
    } else {
      input.value = '';
    }
  });
});

editProjectModal.addEventListener('hidden.bs.modal', () => {
  const form = editProjectModal.querySelector('form');
  const inputs = form.querySelectorAll('input, textarea, select');

  inputs.forEach(input => {
    if (input.type === 'checkbox' || input.type === 'radio') {
      input.checked = false;
    } else {
      input.value = '';
    }
  });
});
// <-------------------- RESET MODAL --------------------->

// <-------------------- HIDE MODAL REPORT --------------------->
document.getElementById('reportModal').addEventListener('hidden.bs.modal', () => {
  const reasoningBtn = document.getElementById("reportReasoningBtn");
  reasoningBtn.textContent = "Mostrar razonamiento";
  const reasoningDiv = document.getElementById("reportReasoning");
  reasoningDiv.classList.add("d-none");
  const copyBtn = document.getElementById("copyReportBtn");
  copyBtn.textContent = "Copiar";
});
// <-------------------- HIDE MODAL REPORT --------------------->

// <-------------------- CREATE PROJECT --------------------->
document.getElementById("registerProject").addEventListener("submit", async function (e) {
  e.preventDefault();

  const projectData = new FormData(this);
  const fileInput = document.getElementById("project_file");
  const file = fileInput.files[0];

  let fileName = "";
  let fileData = "";

  if (file) {
    fileName = file.name;

    // Leer archivo como texto
    const reader = new FileReader();

    // Retorna una promesa que resuelve cuando el archivo esté leído
    const readFileAsText = (file) => {
      return new Promise((resolve, reject) => {
        reader.onload = () => resolve(reader.result);
        reader.onerror = () => reject(reader.error);
        reader.readAsText(file);
      });
    };

    try {
      fileData = await readFileAsText(file);
    } catch (error) {
      console.error("Error al leer el archivo:", error);
      return; // salir si falla la lectura del archivo
    }
  }
  try {
    const response = await fetch(API_ROUTE + "/create-project", {
      method: "POST",
      body: projectData,
      credentials: 'include',
    });
    if (response.status === 401) {
      window.location.href = LOGIN;
      return;
    }

    const data = await response.json();

    if (data.status === "success") {
      const modal = bootstrap.Modal.getInstance(document.getElementById("createProjectModal"));
      modal.hide();

      const fechaFormateada = data.creation_date;

      const tableBody = document.querySelector("#Projects tbody");

      const newRow = document.createElement("tr");
      newRow.dataset.project = projectData.get("project_name");
      newRow.dataset.email = currentUserEmail;
      newRow.innerHTML = `
        <td><input type="checkbox" class="project-checkbox" data-email="${currentUserEmail}" data-project="${projectData.get("project_name")}"></td>
        <td>${currentUserEmail}</td>
        <td style="max-width: 10em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${projectData.get("project_name")}</td>
        <td style="max-width: 20em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${projectData.get("about")}</td>
        <td>${fechaFormateada}</td>
        <td>${fechaFormateada}</td>
        <td>
          ${fileName && fileData
          ? `<button class="btn btn-sm btn-secondary view-json-btn" data-file-name="${fileName}" data-file-data="${fileData}">Ver SBOM</button>`
          : "Sin archivo"}
        </td>
        <td>
          ${fileName && fileData
          ? `<button class="btn btn-sm btn-secondary generate-report-btn">Generar Reporte</button>`
          : "Sin reporte"}
        </td>
      `;

      const viewButton = newRow.querySelector(".view-json-btn");
      if (viewButton) {


        viewButton.addEventListener("click", () => {

          document.getElementById("jsonFileName").textContent = fileName;

          try {
            const parsed = JSON.parse(fileData);
            document.getElementById("jsonFileContent").textContent = JSON.stringify(parsed, null, 2);
          } catch (error) {
            console.error("Error al procesar el JSON:", error);
            document.getElementById("jsonFileContent").textContent = "Error al mostrar el contenido JSON.";
          }

          const modal = new bootstrap.Modal(document.getElementById("jsonModal"));
          modal.show();
        });
      }

      const ReportButton = newRow.querySelector(".generate-report-btn");
      if (ReportButton) {
        ReportButton.onclick = () => createReport(currentUserEmail, projectData.get("project_name"));
      };


      tableBody.insertBefore(newRow, tableBody.firstChild);

      const select = document.getElementById("project_selector");

      const newOption = document.createElement("option");
      newOption.value = projectData.get("project_name");
      newOption.textContent = `${projectData.get("project_name")} - ${currentUserEmail}`;
      newOption.dataset.email = currentUserEmail;
      newOption.dataset.about = projectData.get("about");
      newOption.dataset.modification_date = fechaFormateada;
      newOption.dataset.creation_date = fechaFormateada;
      newOption.dataset.file_name = fileName || "";


      select.insertBefore(newOption, select.children[1]);


      this.reset();

    } else {
      const modal = bootstrap.Modal.getInstance(document.getElementById("createProjectModal"));
      modal.hide();
      showAlertBanner("Error while creating project");
    }
  } catch (error) {
    console.error("Error");
  }
});
// <-------------------- CREATE PROJECT --------------------->

// <-------------------- CREATE USER --------------------->
document.getElementById("registerForm").addEventListener("submit", async function (e) {
  e.preventDefault();

  const formData = new FormData(this);

  try {
    const response = await fetch(API_ROUTE + "/register-user", {
      method: "POST",
      body: formData,
      credentials: 'include',
    });
    if (response.status === 401) {
      window.location.href = LOGIN;
      return;
    }

    const data = await response.json();

    if (data.status === "success") {

      const modal = bootstrap.Modal.getInstance(document.getElementById("crearUsuarioModal"));
      modal.hide();

      const isActive = true

      const tableBody = document.querySelector("#User tbody");
      const newRow = document.createElement("tr");
      newRow.dataset.email = formData.get("email");
      newRow.innerHTML = `
          <td><input type="checkbox" class="user-checkbox" data-email="${formData.get("email")}" data-active="${isActive}"></td>
          <td>${formData.get("email")}</td>
          <td>${formData.get("user_name")}</td>
          <td>${formData.get("user_surname")}</td>
          <td>${formData.get("role")}</td>
          <td>${isActive ? "✓" : "✗"}</td>
        `;
      tableBody.appendChild(newRow);

      const select = document.getElementById("user_selector_user");
      const newOption = document.createElement("option");
      newOption.value = formData.get("email");
      newOption.textContent = `${formData.get("email")} - ${formData.get("user_name")} ${formData.get("user_surname")}`;
      newOption.dataset.name = formData.get("user_name");
      newOption.dataset.surname = formData.get("user_surname");
      newOption.dataset.role = formData.get("role");
      newOption.dataset.active = "True";

      select.insertBefore(newOption, select.children[1]);

      this.reset();

    } else {
      const modal = bootstrap.Modal.getInstance(document.getElementById("crearUsuarioModal"));
      modal.hide();
      showAlertBanner("Error al crear usuario");
    }
  } catch (error) {
    console.error("Error en la solicitud");
  }
});
// <-------------------- CREATE USER --------------------->

// <-------------------- CREATE REPORT --------------------->
function createReport(userEmail, projectName) {
  if (!confirm("Aviso, generar un reporte puede tardar unos minutos, durante los cuales el chat estaría inactivo durante ese tiempo. ¿Deseas continuar?")) {
    return;
  }

  if (!localStorage.getItem("CurrentReportGenerate")) {
    localStorage.setItem("CurrentReportGenerate", [userEmail, projectName]);
  } else {
    showAlertBanner("Ya hay un reporte en proceso de generación. Por favor, espera a que se complete antes de generar otro.");
    return;
  }

  const rows = document.querySelectorAll('#Projects tbody tr');
  for (let row of rows) {
    const rowEmail = row.getAttribute('data-email');
    const rowProject = row.getAttribute('data-project');

    if (rowEmail === userEmail && rowProject === projectName) {
      const generateBtn = row.querySelector(".generate-report-btn");
      if (generateBtn) {
        generateBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generando...`;
        generateBtn.disabled = true;
      };
    }
  }

  fetch(CHAT_ROUTE + '/generate-report', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    credentials: 'include',
    body: JSON.stringify({
      user_email: userEmail,
      project_name: projectName,
    })
  })
    .then(response => {
      if (response.status === 401) {
        window.location.href = "http://localhost:8080/login";
        return;
      }
      return response.json();
    })
    .then(data => {
      if (data.ok) {
        showAlertBanner("Reporte generado exitosamente.", "success");
        localStorage.removeItem("CurrentReportGenerate");
        const projectName = data.content.project_name;
        const reportName = data.content.report_name;
        const reportData = data.content.report_data;
        const reportReasoning = data.content.report_reasoning;

        const selectedRow = document.querySelector(`#Projects tbody tr[data-project="${projectName}"][data-email="${userEmail}"]`);
        if (selectedRow) {
          const reportButton = selectedRow.querySelector(".generate-report-btn");
          if (reportButton) {
            reportButton.onclick = null;
            reportButton.disabled = false;

            reportButton.classList.remove("generate-report-btn");
            reportButton.classList.add("view-report-btn");
            reportButton.textContent = "Ver Reporte";

            reportButton.addEventListener("click", () => {
              document.getElementById("reportModalTitle").textContent = reportName;

              const reportDescriptionContainer = document.getElementById("reportDescription");
              const renderedContent = renderBotContent(reportData);

              reportDescriptionContainer.replaceChildren(renderedContent);

              const copyBtn = document.getElementById("copyReportBtn");
              copyBtn.onclick = () => {
                navigator.clipboard.writeText(reportData)
                  .then(() => {
                    copyBtn.textContent = "Copiado ✔️";
                  })
                  .catch(err => {
                    console.error("Error al copiar:", err);
                    copyBtn.textContent = "Error ❌";
                  });
              };

              if (reportReasoning) {
                const reasoningBtn = document.getElementById("reportReasoningBtn");
                reasoningBtn.classList.remove("d-none");
                const reasoningDiv = document.getElementById("reportReasoning");

                const content = document.getElementById("reportReasoningContent");
                const renderedReasoning = renderBotContent(reportReasoning);
                content.replaceChildren(renderedReasoning);

                reasoningBtn.onclick = () => {
                  reasoningDiv.classList.toggle("d-none");
                  if (reasoningDiv.classList.contains("d-none")) {
                    reasoningBtn.textContent = "Mostrar razonamiento";
                  } else {
                    reasoningBtn.textContent = "Ocultar razonamiento";
                  }
                };
              } else {
                const reasoningBtn = document.getElementById("reportReasoningBtn");
                reasoningBtn.classList.add("d-none");
              }
              const reportModal = new bootstrap.Modal(document.getElementById('reportModal'));
              reportModal.show();
            });
          }
        }

      } else {
        showAlertBanner("Error al generar el reporte: " + data.message);
      }
    })
    .catch(error => {
      console.error("Error al generar el reporte:", error);
      showAlertBanner("Error al generar el reporte.");
    });
}
// <-------------------- CREATE REPORT --------------------->

// <-------------------- DELETE PROJECTS --------------------->
document.getElementById("selectAllProjects").addEventListener("change", function () {
  const deleteButton = document.getElementById("confirmDeleteProjects");
  const checkboxes = document.querySelectorAll(".project-checkbox");
  checkboxes.forEach(cb => cb.checked = this.checked);
});

confirmDeleteProjects.addEventListener('click', async function (e) {
  e.preventDefault();

  const checkboxes = document.querySelectorAll('.project-checkbox:checked');
  if (checkboxes.length === 0) {
    showAlertBanner('Selecciona al menos un proyecto para eliminar.');
    console.error('❌ No se seleccionó ningún proyecto para eliminar.');
    return;
  }

  for (let checkbox of checkboxes) {
    const email = checkbox.dataset.email;
    const project_name = checkbox.dataset.project;

    try {
      const response = await fetch(API_ROUTE + "/delete-project", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        credentials: 'include',
        body: JSON.stringify({ email, project_name })
      });
      const result = await response.json();
      if (response.status === 401) {
        window.location.href = LOGIN;
        return;
      }
      if (response.ok) {

        const row = checkbox.closest('tr');

        if (row) {
          const deletedTableBody = document.querySelector('#DeletedProjects tbody');
          const newRow = document.createElement('tr');
          newRow.innerHTML = `
            <td>${result.email}</td>
            <td style="max-width: 10em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${result.project_name}</td>
            <td style="max-width: 20em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${result.about}</td>
            <td>${result.creation_date}</td>
            <td>${result.deletion_date}</td>
            <td>
              ${result.file_name && result.file_data
              ? `<button class="btn btn-sm btn-secondary view-json-btn" data-file-name="${result.file_name}" data-file-data="${result.file_data}">Ver SBOM</button>`
              : "Sin archivo"}
            </td>
            <td>
              ${result.report_name && result.report_data
              ? `<button class="btn btn-sm btn-secondary view-report-btn">Ver Reporte</button>`
              : "Sin reporte"
            }
            </td>
          `;
          deletedTableBody.insertBefore(newRow, deletedTableBody.firstChild);

          row.remove();

          const viewButton = newRow.querySelector(".view-json-btn");
          if (viewButton) {

            viewButton.addEventListener("click", () => {
              const fileName = result.file_name;
              const fileData = result.file_data;

              document.getElementById("jsonFileName").textContent = fileName;

              try {
                const parsed = JSON.parse(fileData);
                document.getElementById("jsonFileContent").textContent = JSON.stringify(parsed, null, 2);
              } catch (error) {
                console.error("Error al procesar el JSON:", error);
                document.getElementById("jsonFileContent").textContent = "Error al mostrar el contenido JSON.";
              }

              const modal = new bootstrap.Modal(document.getElementById("jsonModal"));
              modal.show();
            });
          }

          const viewReportButton = newRow.querySelector(".view-report-btn");
          if (viewReportButton) {
            const reportName = result.report_name;
            const reportData = result.report_data;
            const reportReasoning = result.report_reasoning;

            viewReportButton.addEventListener("click", () => {
              document.getElementById("reportModalTitle").textContent = reportName;

              const reportDescriptionContainer = document.getElementById("reportDescription");
              const renderedContent = renderBotContent(reportData);

              reportDescriptionContainer.replaceChildren(renderedContent);

              const copyBtn = document.getElementById("copyReportBtn");
              copyBtn.onclick = () => {
                navigator.clipboard.writeText(reportData)
                  .then(() => {
                    copyBtn.textContent = "Copiado ✔️";
                  })
                  .catch(err => {
                    console.error("Error al copiar:", err);
                    copyBtn.textContent = "Error ❌";
                  });
              };

              if (reportReasoning) {
                const reasoningBtn = document.getElementById("reportReasoningBtn");
                reasoningBtn.classList.remove("d-none");
                const reasoningDiv = document.getElementById("reportReasoning");

                const content = document.getElementById("reportReasoningContent");
                const renderedReasoning = renderBotContent(reportReasoning);
                content.replaceChildren(renderedReasoning);

                reasoningBtn.onclick = () => {
                  reasoningDiv.classList.toggle("d-none");
                  if (reasoningDiv.classList.contains("d-none")) {
                    reasoningBtn.textContent = "Mostrar razonamiento";
                  } else {
                    reasoningBtn.textContent = "Ocultar razonamiento";
                  }
                };
              } else {
                const reasoningBtn = document.getElementById("reportReasoningBtn");
                reasoningBtn.classList.add("d-none");
              }
              const reportModal = new bootstrap.Modal(document.getElementById('reportModal'));
              reportModal.show();
            });

          }

          const select = document.getElementById('project_selector');
          const options = select.options;

          for (let i = 0; i < options.length; i++) {
            const option = options[i];
            if (
              option.value === result.project_name &&
              option.getAttribute('data-email') === result.email
            ) {
              select.removeChild(option);
              break;
            }
          }

        } else {
          showAlertBanner(`Error eliminando ${project_name}: ${result.message}`);
          console.error(`❌ Error eliminando ${project_name}: ${result.message}`);
        }

      } else {
        showAlertBanner(`Error eliminando ${project_name}: ${result.message}`);
        console.error(`❌ Error eliminando ${project_name}: ${result.message}`);
      }
    } catch (error) {
      showAlertBanner(`Error de red al eliminar ${project_name}`);
      console.error(`❌ Error de red al eliminar ${project_name}`);
    }
  }
});
// <-------------------- DELETE PROJECTS --------------------->

// <-------------------- DELETE USERS --------------------->
document.addEventListener("DOMContentLoaded", function () {
  const deleteButton = document.getElementById("confirmDeleteUsers");
  const selectAllCheckbox = document.getElementById("selectAllUsers");

  if (!deleteButton || !selectAllCheckbox) return;

  // Marcar o desmarcar todos los checkboxes de usuario
  selectAllCheckbox.addEventListener("change", function () {
    const checkboxes = document.querySelectorAll(".user-checkbox");
    checkboxes.forEach(cb => cb.checked = this.checked);
  });

  // Botón eliminar usuarios
  deleteButton.addEventListener("click", async function (e) {
    e.preventDefault();

    const selectedCheckboxes = document.querySelectorAll(".user-checkbox:checked");

    if (selectedCheckboxes.length === 0) {
      showAlertBanner("Selecciona al menos un usuario para eliminar.");
      return;
    }

    for (let checkbox of selectedCheckboxes) {
      const email = checkbox.dataset.email;

      const projectRows = document.querySelectorAll(`#Projects tbody tr[data-email="${email}"]`);

      for (let row of projectRows) {
        const project_name = row.dataset.project;

        try {
          const response = await fetch(API_ROUTE + "/delete-project", {
            method: "POST",
            headers: {
              "Content-Type": "application/json"
            },
            credentials: 'include',
            body: JSON.stringify({ email, project_name })
          });
          if (response.status === 401) {
            window.location.href = LOGIN;
            return;
          }

          const result = await response.json();

          if (response.ok) {

            const deletedTableBody = document.querySelector('#DeletedProjects tbody');
            const newRow = document.createElement('tr');
            newRow.innerHTML = `
              <td>${result.email}</td>
              <td style="max-width: 10em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${result.project_name}</td>
              <td style="max-width: 20em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${result.about}</td>
              <td>${result.creation_date}</td>
              <td>${result.deletion_date}</td>
              <td>
                ${result.file_name && result.file_data
                ? `<button class="btn btn-sm btn-secondary view-json-btn" data-file-name="${result.file_name}" data-file-data="${result.file_data}">Ver SBOM</button>`
                : "Sin archivo"}
              </td>
              <td>
                ${result.report_name && result.report_data
                ? `<button class="btn btn-sm btn-secondary view-report-btn">Ver Reporte</button>`
                : "Sin reporte"
              }
              </td>
            `;
            deletedTableBody.insertBefore(newRow, deletedTableBody.firstChild);

            row.remove();

            const viewButton = newRow.querySelector(".view-json-btn");
            if (viewButton) {

              viewButton.addEventListener("click", () => {
                const fileName = result.file_name;
                const fileData = result.file_data;

                document.getElementById("jsonFileName").textContent = fileName;

                try {
                  const parsed = JSON.parse(fileData);
                  document.getElementById("jsonFileContent").textContent = JSON.stringify(parsed, null, 2);
                } catch (error) {
                  console.error("Error al procesar el JSON:", error);
                  document.getElementById("jsonFileContent").textContent = "Error al mostrar el contenido JSON.";
                }

                const modal = new bootstrap.Modal(document.getElementById("jsonModal"));
                modal.show();
              });
            }

            const viewReportButton = newRow.querySelector(".view-report-btn");
            if (viewReportButton) {
              const reportName = result.report_name;
              const reportData = result.report_data;
              const reportReasoning = result.report_reasoning;

              viewReportButton.addEventListener("click", () => {
                document.getElementById("reportModalTitle").textContent = reportName;

                const reportDescriptionContainer = document.getElementById("reportDescription");
                const renderedContent = renderBotContent(reportData);

                reportDescriptionContainer.replaceChildren(renderedContent);

                const copyBtn = document.getElementById("copyReportBtn");
                copyBtn.onclick = () => {
                  navigator.clipboard.writeText(reportData)
                    .then(() => {
                      copyBtn.textContent = "Copiado ✔️";
                    })
                    .catch(err => {
                      console.error("Error al copiar:", err);
                      copyBtn.textContent = "Error ❌";
                    });
                };

                if (reportReasoning) {
                  const reasoningBtn = document.getElementById("reportReasoningBtn");
                  reasoningBtn.classList.remove("d-none");
                  const reasoningDiv = document.getElementById("reportReasoning");

                  const content = document.getElementById("reportReasoningContent");
                  const renderedReasoning = renderBotContent(reportReasoning);
                  content.replaceChildren(renderedReasoning);

                  reasoningBtn.onclick = () => {
                    reasoningDiv.classList.toggle("d-none");
                    if (reasoningDiv.classList.contains("d-none")) {
                      reasoningBtn.textContent = "Mostrar razonamiento";
                    } else {
                      reasoningBtn.textContent = "Ocultar razonamiento";
                    }
                  };
                } else {
                  const reasoningBtn = document.getElementById("reportReasoningBtn");
                  reasoningBtn.classList.add("d-none");
                }
                const reportModal = new bootstrap.Modal(document.getElementById('reportModal'));
                reportModal.show();
              });

            }

            const select = document.getElementById('project_selector');
            const options = select.options;

            for (let i = 0; i < options.length; i++) {
              const option = options[i];
              if (
                option.value === result.project_name &&
                option.getAttribute('data-email') === result.email
              ) {
                select.removeChild(option);
                break;
              }
            }

          } else {
            showAlertBanner(`Error eliminando ${project_name}: ${result.message}`);
            console.error(`❌ Error eliminando proyecto ${project_name}: ${result.message}`);
          }
        } catch (error) {
          showAlertBanner(`Error de red al eliminar ${project_name}`);
          console.error(`❌ Error de red al eliminar proyecto ${project_name}`);
        }
      }

      try {
        const response = await fetch(API_ROUTE + "/delete-user", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          credentials: 'include',
          body: JSON.stringify({ email: email })
        });
        if (response.status === 401) {
          window.location.href = LOGIN;
          return;
        }

        const result = await response.json();

        if (response.ok) {
          const row = checkbox.closest('tr');

          const colActive = row.children[row.children.length - 1];

          const isActive = false;

          colActive.innerHTML = `${isActive ? "✓" : "✗"}`;

          const selectOptions = document.querySelectorAll('#user_selector_user option');
          selectOptions.forEach(option => {
            if (option.value === email) {
              option.dataset.active = "False";
            }
          });

        } else {
          showAlertBanner(`Error eliminando ${email}: ${result.message}`);
          console.error(`❌ Error eliminando ${email}: ${result.message}`);
        }
      } catch (error) {
        showAlertBanner(`Error de red al eliminar ${email}`);
        console.error(`❌ Error de red al eliminar ${email}`);
      }
    }
  });
});
// <-------------------- DELETE USERS --------------------->

// <-------------------- EDIT USERS --------------------->
const userSelector = document.getElementById("user_selector_user");
const nameInput = document.getElementById("edit_user_name_user");
const surnameInput = document.getElementById("edit_user_surname_user");
const emailInput = document.getElementById("edit_email_user");
const passwordInput = document.getElementById("edit_password_user");
const roleSelect = document.getElementById("edit_role_user");
const activeSelect = document.getElementById("edit_active_user");
const originalEmailInput = document.getElementById("original_email_user");

userSelector.addEventListener("change", function () {
  const selectedOption = this.options[this.selectedIndex];
  nameInput.value = selectedOption.dataset.name || "";
  surnameInput.value = selectedOption.dataset.surname || "";
  emailInput.value = selectedOption.value || "";
  roleSelect.value = selectedOption.dataset.role || "";
  activeSelect.value = selectedOption.dataset.active || "";
  originalEmailInput.value = selectedOption.value || "";
});

document.getElementById("editForm").addEventListener("submit", async function (e) {
  e.preventDefault();
  const data = {
    original_email: originalEmailInput.value,
    user_name: nameInput.value,
    user_surname: surnameInput.value,
    email: emailInput.value,
    password: passwordInput.value,
    role: roleSelect.value,
    active: activeSelect.value
  };


  const response = await fetch(API_ROUTE + "/edit-user", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    credentials: 'include',
    body: JSON.stringify(data)
  });
  if (response.status === 401) {
    window.location.href = LOGIN;
    return;
  }


  const result = await response.json();

  try {
    if (result.status === "success") {
      // Seleccionamos la fila que tiene el data-email igual al original
      const tableRows = document.querySelectorAll('#User tbody tr');
      tableRows.forEach(row => {
        if (row.dataset.email === data.original_email) {
          // Actualizamos los valores de las celdas
          const cells = row.querySelectorAll('td');
          row.dataset.email = data.email; // Actualizamos el atributo data-email

          cells[1].textContent = data.email;
          cells[2].textContent = data.user_name;
          cells[3].textContent = data.user_surname;
          cells[4].textContent = data.role;
          cells[5].innerHTML = data.active === "True" || data.active === true ? "&#x2713;" : "&#x2717;";

          // También actualizamos el checkbox si lo deseas
          const checkbox = row.querySelector('.user-checkbox');
          if (checkbox) {
            checkbox.dataset.email = data.email;
            checkbox.dataset.active = data.active;
          }
        }
      });
      const selectOptions = document.querySelectorAll('#user_selector_user option');
      selectOptions.forEach(option => {
        if (option.value === data.original_email) {
          option.value = data.email;
          option.textContent = `${data.email} - ${data.user_name} ${data.user_surname}`;
          option.dataset.name = data.user_name;
          option.dataset.surname = data.user_surname;
          option.dataset.role = data.role;
          option.dataset.active = data.active === "True" || data.active === true ? "True" : "False";
        }
      });

      if (result.active == "false") {
        const old_email = originalEmailInput.value;
        const projectRows = document.querySelectorAll(`#Projects tbody tr[data-email="${old_email}"]`);

        for (let row of projectRows) {
          const project_name = row.dataset.project;

          try {
            const response = await fetch(API_ROUTE + "/delete-project", {
              method: "POST",
              headers: {
                "Content-Type": "application/json"
              },
              credentials: 'include',
              body: JSON.stringify({ old_email, project_name })
            });
            if (response.status === 401) {
              window.location.href = LOGIN;
              return;
            }

            const result = await response.json();

            if (response.ok) {
              const deletedTableBody = document.querySelector('#DeletedProjects tbody');
              const newRow = document.createElement('tr');
              newRow.innerHTML = `
              <td>${result.email}</td>
              <td>${result.project_name}</td>
              <td>${result.about}</td>
              <td>${result.creation_date}</td>
              <td>${result.deletion_date}</td>
            `;
              deletedTableBody.insertBefore(newRow, deletedTableBody.firstChild);
              row.remove();

              const select = document.getElementById('project_selector');
              const options = select.options;

              for (let i = 0; i < options.length; i++) {
                const option = options[i];
                if (
                  option.value === result.project_name &&
                  option.getAttribute('data-email') === result.email
                ) {
                  select.removeChild(option);
                  break;
                }
              }

            } else {
              showAlertBanner(`Error eliminando ${project_name}: ${result.message}`);
              console.error(`❌ Error eliminando proyecto ${project_name}: ${result.message}`);
            }
          } catch (error) {
            showAlertBanner(`Error de red al eliminar ${project_name}`);
            console.error(`❌ Error de red al eliminar proyecto ${project_name}`);
          }
        }
      }

      if (data.original_email !== data.email) {
        const projectRows = document.querySelectorAll(`#Projects tbody tr[data-email="${data.original_email}"]`);
        projectRows.forEach(row => {
          row.setAttribute('data-email', data.email);
          const emailCell = row.querySelector('td:nth-child(2)');
          if (emailCell) {
            emailCell.textContent = data.email;
          }
          const checkbox = row.querySelector('input.project-checkbox');
          if (checkbox) {
            checkbox.setAttribute('data-email', data.email);
          }
        });
        const projectOptions = document.querySelectorAll(`#project_selector option[data-email="${data.original_email}"]`);
        projectOptions.forEach(option => {
          option.setAttribute('data-email', data.email);
          const projectName = option.value;
          option.textContent = `${projectName} - ${data.email}`;
        });
        const originalEmailProjectField = document.getElementById('original_email_project_project');
        if (originalEmailProjectField) {
          originalEmailProjectField.value = data.email;
        }
      }
    } else {
      showAlertBanner(`Error al editar ${data.original_email}: ${result.message}`);
      console.error(`❌ Error al editar ${data.original_email}: ${result.message}`);
    }
  } catch (error) {
    showAlertBanner(`Error de red al editar ${data.original_email}`);
    console.error(`❌ Error de red al editar ${data.original_email}`);
  }


  const modalElement = document.getElementById("editUsuarioModal");
  const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
  modal.hide();
});
// <-------------------- EDIT USERS --------------------->

// <-------------------- EDIT PROJECTS --------------------->
document.getElementById('project_selector').addEventListener('change', function () {
  const selectedOption = this.options[this.selectedIndex];

  // Llenamos los campos del modal con los datos del proyecto seleccionado
  document.getElementById('original_project_name_project').value = selectedOption.value;
  document.getElementById('edit_project_name_project').value = selectedOption.value;

  const email = selectedOption.getAttribute('data-email');
  document.getElementById('original_email_project_project').value = email;
  document.getElementById('edit_email_project').value = email;

  document.getElementById('edit_about_project').value = selectedOption.getAttribute('data-about');

  const projectFileName = selectedOption.getAttribute("data-file_name");

  fetch(API_ROUTE + '/get-criteria', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    credentials: 'include',
    body: JSON.stringify({ project_name: selectedOption.value, email: email })
  })
    .then(response => {
      if (response.status === 401) {
        window.location.href = "http://localhost:8080/login";
        return;
      }
      return response.json();
    })
    .then(data => {
      document.getElementById('edit_max_total_vulns').value = data.content.max_total_vulns;
      document.getElementById('edit_min_fixable_ratio').value = data.content.min_fixable_ratio;
      document.getElementById('edit_max_severity_level').value = data.content.max_severity_level;
      document.getElementById('edit_composite_score').value = data.content.composite_score;
    })
    .catch(error => {
      console.error("Error al mostrar el modal:", error);
      showAlertBanner("Error al mostrar el modal.");
    });

  const fileInfoElement = document.getElementById('currentFileInfo');
  if (projectFileName) {
    fileInfoElement.textContent = `Archivo actual: ${projectFileName}`;
  } else {
    fileInfoElement.textContent = `No hay archivo actualmente cargado.`;
  }
});

document.getElementById('editProjectForm').addEventListener('submit', async function (e) {
  e.preventDefault();

  const originalProjectName = document.getElementById('original_project_name_project').value;
  const originalEmail = document.getElementById('original_email_project_project').value;
  const newProjectName = document.getElementById('edit_project_name_project').value.trim();
  const newAbout = document.getElementById('edit_about_project').value.trim();
  const newEmail = document.getElementById('edit_email_project').value.trim();
  const fileInput = document.getElementById("edit_project_file");
  const newMaxVulns = document.getElementById('edit_max_total_vulns').value;
  const newMinRatio = document.getElementById('edit_min_fixable_ratio').value;
  const newMaxSev = document.getElementById('edit_max_severity_level').value;
  const newCompScore = document.getElementById('edit_composite_score').value;
  const file = fileInput.files[0];

  let fileName = "";
  let fileData = "";

  const formData = new FormData();
  formData.append("new_email", newEmail);
  formData.append("project_name", originalProjectName);
  formData.append("email", originalEmail);
  formData.append("new_max_total_vulns", newMaxVulns);
  formData.append("new_min_fixable_ratio", newMinRatio);
  formData.append("new_max_severity_level", newMaxSev);
  formData.append("new_composite_score", newCompScore);

  if (newProjectName && newProjectName !== originalProjectName) {
    formData.append("new_project_name", newProjectName);
    formData.append("new-project_name", true);
  }

  if (newAbout) {
    formData.append("new_about", newAbout);
    formData.append("new-about", true);
  }

  if (file) {
    formData.append("project_file", file);
    const reader = new FileReader();
    reader.onload = async () => {
      await enviarSolicitud(formData, file); // con archivo
    };
    reader.readAsText(file); // o readAsDataURL si quieres base64
  } else {
    await enviarSolicitud(formData, null); // sin archivo
  }

  async function enviarSolicitud(formData, file) {
    try {
      const response = await fetch(API_ROUTE + "/edit-project", {
        method: "POST",
        credentials: 'include',
        body: formData,
      });
      if (response.status === 401) {
        window.location.href = LOGIN;
        return;
      }

      const result = await response.json();

      if (result.status === "success") {
        const rows = document.querySelectorAll('#Projects tbody tr');
        for (let row of rows) {
          const rowEmail = row.getAttribute('data-email');
          const rowProject = row.getAttribute('data-project');

          if (rowEmail === originalEmail && rowProject === originalProjectName) {
            // Actualiza atributos del <tr>
            row.setAttribute('data-email', newEmail || originalEmail);
            row.setAttribute('data-project', newProjectName || originalProjectName);
            row.setAttribute('data-about', newAbout);

            const cells = row.querySelectorAll('td');
            cells[1].textContent = newEmail || originalEmail;
            cells[2].textContent = newProjectName || originalProjectName;
            cells[3].textContent = newAbout;
            cells[5].textContent = result.modification_date || ""; // Actualiza la columna de modificación

            if (file) {
              const sbomCell = row.children[6];
              sbomCell.innerHTML = "";

              const reader = new FileReader();
              reader.onload = () => {
                const fileData = reader.result;

                const viewBtn = document.createElement("button");
                viewBtn.className = "btn btn-sm btn-secondary view-json-btn";
                viewBtn.textContent = "Ver SBOM";
                viewBtn.setAttribute("data-file-name", file.name);
                viewBtn.setAttribute("data-file-data", fileData);

                viewBtn.addEventListener("click", () => {
                  document.getElementById("jsonFileName").textContent = file.name;
                  try {
                    const parsed = JSON.parse(fileData);
                    document.getElementById("jsonFileContent").textContent = JSON.stringify(parsed, null, 2);
                  } catch (err) {
                    document.getElementById("jsonFileContent").textContent = "Error al mostrar el contenido JSON.";
                  }
                  const modal = new bootstrap.Modal(document.getElementById("jsonModal"));
                  modal.show();
                });

                sbomCell.appendChild(viewBtn);
              };
              reader.readAsText(file);

              const generateReportButton = row.querySelector(".generate-report-btn");
              if (generateReportButton) {
                generateReportButton.onclick = null;
                generateReportButton.onclick = () => createReport(newEmail || originalEmail, newProjectName || originalProjectName);
              }

              const viewReportButton = row.querySelector(".view-report-btn");
              if (viewReportButton) {
                const lastTd = viewReportButton.closest("td");

                // Crear nuevo botón
                const newButton = document.createElement("button");
                newButton.className = "btn btn-sm btn-secondary generate-report-btn";
                newButton.textContent = "Generar Reporte";

                // Asignar funcionalidad
                newButton.onclick = () => createReport(newEmail || originalEmail, newProjectName || originalProjectName);

                // Reemplazar el botón en el mismo TD
                lastTd.replaceChildren(newButton);
              }
            }

            // Actualiza atributos del checkbox
            const checkbox = row.querySelector('input.project-checkbox');
            checkbox.setAttribute('data-email', newEmail || originalEmail);
            checkbox.setAttribute('data-project', newProjectName || originalProjectName);
            if (newAbout) {
              checkbox.setAttribute('data-about', newAbout);
            }
            break;
          }
        }
        // Actualiza también la opción del selector de proyectos
        const select = document.getElementById('project_selector');
        const options = select.options;

        for (let i = 0; i < options.length; i++) {
          const option = options[i];
          if (
            option.value === originalProjectName &&
            option.getAttribute('data-email') === originalEmail
          ) {
            option.value = newProjectName || originalProjectName;
            option.textContent = `${newProjectName || originalProjectName} - ${newEmail || originalEmail}`;
            option.setAttribute('data-email', newEmail || originalEmail);
            if (newAbout) {
              option.setAttribute('data-about', newAbout);
            }
            document.getElementById('original_project_name_project').value = newProjectName || originalProjectName;
            document.getElementById('original_email_project_project').value = newEmail || originalEmail;
            break;
          }
        }

      } else {
        showAlertBanner(` ${result.message}`);
      }
    } catch (error) {
      showAlertBanner(" Error al enviar la solicitud.");
      console.error("Error al enviar la solicitud:");
    }
  }
});
// <-------------------- EDIT PROJECTS --------------------->