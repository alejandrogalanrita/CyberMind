const API_ROUTE = 'http://localhost:3000/api';
const CHAT_ROUTE = 'http://localhost:3300/chat';
const LOGIN = "http://localhost:8080/login";

let toUpdateReports = [];

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

/* Chat functionality */
// <-------------------- SHOW STATUS MESSAGE --------------------->
function showStatusMessage(text) {
    const statusEl = document.getElementById("statusMessage");
    const chat = document.getElementById("chat");
    if (statusEl) {
        statusEl.classList.remove("d-none");
        statusEl.textContent = text;
        chat.style.height = "37.5em";
    }
}
// <-------------------- SHOW STATUS MESSAGE --------------------->
// <-------------------- CLEAR STATUS MESSAGE --------------------->
function clearStatusMessage() {
    const statusEl = document.getElementById("statusMessage");
    const chat = document.getElementById("chat");
    if (statusEl) {
        {
            chat.style.height = "40em";
            statusEl.classList.textContent = "";
            statusEl.classList.add("d-none");
        }
    }
}
// <-------------------- CLEAR STATUS MESSAGE --------------------->

var n = 0;
var pendingResponse = false;
const chatContainer = document.getElementById("chat");
const input = document.getElementById("userInput");

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
// <-------------------- SEND BOT MESSAGE --------------------->
function sendBotMessage(text, reasoning) {
    if (!chatContainer) return;



    const messageRow = document.createElement("div");
    messageRow.classList.add("row", "d-flex", "justify-content-between", "pe-4", "py-2");
    messageRow.id = "chat-bot-message-" + n;
    n++;

    const iconCol = document.createElement("div");
    iconCol.classList.add("col-1", "ps-sm-4");

    const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    icon.setAttribute("width", "16");
    icon.setAttribute("height", "16");
    icon.setAttribute("fill", "primary");
    icon.setAttribute("viewBox", "0 0 16 16");
    icon.classList.add("text-secondary");
    icon.innerHTML = `
        <path d="M6 12.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 0 1h-3a.5.5 0 0 1-.5-.5M3 8.062C3 6.76 4.235 5.765 5.53 5.886a26.6 26.6 0 0 0 4.94 0C11.765 5.765 13 6.76 13 8.062v1.157a.93.93 0 0 1-.765.935c-.845.147-2.34.346-4.235.346s-3.39-.2-4.235-.346A.93.93 0 0 1 3 9.219zm4.542-.827a.25.25 0 0 0-.217.068l-.92.9a25 25 0 0 1-1.871-.183.25.25 0 0 0-.068.495c.55.076 1.232.149 2.02.193a.25.25 0 0 0 .189-.071l.754-.736.847 1.71a.25.25 0 0 0 .404.062l.932-.97a25 25 0 0 0 1.922-.188.25.25 0 0 0-.068-.495c-.538.074-1.207.145-1.98.189a.25.25 0 0 0-.166.076l-.754.785-.842-1.7a.25.25 0 0 0-.182-.135"/>
        <path d="M8.5 1.866a1 1 0 1 0-1 0V3h-2A4.5 4.5 0 0 0 1 7.5V8a1 1 0 0 0-1 1v2a1 1 0 0 0 1 1v1a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-1a1 1 0 0 0 1-1V9a1 1 0 0 0-1-1v-.5A4.5 4.5 0 0 0 10.5 3h-2zM14 7.5V13a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V7.5A3.5 3.5 0 0 1 5.5 4h5A3.5 3.5 0 0 1 14 7.5"/>
    `;
    iconCol.appendChild(icon);

    const messageCol = document.createElement("div");
    messageCol.classList.add("bg-secondary", "col-sm-11", "col-10", "rounded", "p-3", "text-white");

    const visibleContent = renderBotContent(text);
    messageCol.appendChild(visibleContent);

    if (reasoning) {
        const collapseId = `collapse-${n}`;
        const toggleBtn = document.createElement("button");
        toggleBtn.className = "btn btn-sm btn-outline-light mt-2";
        toggleBtn.setAttribute("data-bs-toggle", "collapse");
        toggleBtn.setAttribute("data-bs-target", `#${collapseId}`);
        toggleBtn.setAttribute("aria-expanded", "false");
        toggleBtn.setAttribute("aria-controls", collapseId);
        toggleBtn.textContent = "Mostrar razonamiento";

        const reasoningDiv = document.createElement("div");
        reasoningDiv.className = "collapse text-light bg-dark p-2 mt-2 rounded";
        reasoningDiv.id = collapseId;

        const reasoningContent = renderBotContent(reasoning);
        reasoningDiv.appendChild(reasoningContent);

        messageCol.appendChild(toggleBtn);
        messageCol.appendChild(reasoningDiv);
    }

    messageRow.appendChild(iconCol);
    messageRow.appendChild(messageCol);
    chatContainer.appendChild(messageRow);
};

// Function to get chatbot response
// In getChatbotResponse, after fetch:
async function getChatbotResponse(text) {
    let userEmail = currentUserEmail;
    let promptJSON = JSON.stringify({
        message: text,
        user_email: userEmail
    });

    try {
        let response = await fetch(CHAT_ROUTE + "/send-message", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            credentials: 'include',
            body: promptJSON
        });
        if (response.status === 401) {
            window.location.href = LOGIN;
            return null;
        }
        if (!response.ok) {
            throw new Error("Error en la petición: " + response.statusText);
        }

        let data = await response.json();
        return data;
    } catch (error) {
        console.error("Error");
        return null;
    }
}
// <-------------------- SEND BOT MESSAGE --------------------->

// Function to focus on last message
// <-------------------- SCROLL TO END --------------------->
function scrollToEnd() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}
// <-------------------- SCROLL TO END --------------------->

// Function to handle user messages
// <-------------------- SEND USER MESSAGE --------------------->
function sendUserMessage(text) {
    if (!chatContainer) return;

    // Create message container
    const messageRow = document.createElement("div");
    messageRow.classList.add("row", "d-flex", "justify-content-between", "ps-4", "py-2");
    messageRow.id = "chat-user-message-" + n;

    // Create icon column
    const iconCol = document.createElement("div");
    iconCol.classList.add("col-1", "ps-sm-4");

    // Create icon SVG
    const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    icon.setAttribute("width", "16");
    icon.setAttribute("height", "16");
    icon.setAttribute("fill", "primary");
    icon.setAttribute("viewBox", "0 0 16 16");
    icon.classList.add("text-secondary");
    icon.innerHTML = `
        <path d="M3 14s-1 0-1-1 1-4 6-4 6 3 6 4-1 1-1 1zm5-6a3 3 0 1 0 0-6 3 3 0 0 0 0 6"/>
    `;
    iconCol.appendChild(icon);

    // Create message column
    const messageCol = document.createElement("div");
    messageCol.classList.add("bg-primary", "col-10", "col-sm-11", "rounded", "p-3", "text-white");
    messageCol.textContent = text;
    messageRow.appendChild(messageCol);
    messageRow.appendChild(iconCol);

    // Append message to chat container
    chatContainer.appendChild(messageRow);
};
// <-------------------- SEND USER MESSAGE --------------------->

// Function to handle chat input
// <-------------------- CHAT HANDLER --------------------->
async function chatHandler() {
    if (pendingResponse) return;
    pendingResponse = true;

    let text = input.value.trim();
    if (text === "") {
        input.value = "";
        pendingResponse = false;
        return;
    }

    input.value = "";
    sendUserMessage(text);
    scrollToEnd();

    // Start fetching bot response (do not await yet)
    const responsePromise = getChatbotResponse(text);



    // Start updating status messages in the background
    const statusLoop = async () => {
        const messages = [
            "Procesando el mensaje...",
            "Pensando...",
            "Escribiendo..."
        ];
        let i = 0;
        while (!responseReady) {
            showStatusMessage(messages[i % messages.length]);
            await new Promise(r => setTimeout(r, 5000));
            i++;
        }
    };

    let responseReady = false;
    const statusPromise = statusLoop();

    const botResponse = await responsePromise;
    responseReady = true;

    // Wait for any pending status update (quick cleanup)
    await statusPromise;
    clearStatusMessage();

    if (botResponse && botResponse["response"]) {
        sendBotMessage(botResponse["response"], botResponse["reasoning"]);
    } else {
        sendBotMessage("Lo siento, no puedo responder a eso en este momento.");
    }

    pendingResponse = false;
    scrollToEnd();
}
// <-------------------- CHAT HANDLER --------------------->

// Initialize chat
// <-------------------- INITIALIZE CHAT --------------------->
document.addEventListener("DOMContentLoaded", () => {
    chatContainer.innerHTML = "";
    sendBotMessage("¡Bip Bop! Soy un Bot, ¿en qué puedo ayudarte?");
});

// Allow sending messages with Enter key
document.addEventListener("keypress", function (e) {
    if (e.key === "Enter" && document.activeElement === input) {
        chatHandler();
    }
});
// <-------------------- INITIALIZE CHAT --------------------->

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
            const projectName = projectData.get("project_name");
            const projectAbout = projectData.get("about");
            const newListItem = document.createElement("a");
            newListItem.href = "#";
            newListItem.className = "list-group-item list-group-item-action";
            newListItem.dataset.projectName = projectName;
            newListItem.dataset.about = projectAbout;
            newListItem.dataset.fileName = fileName;
            newListItem.dataset.fileData = fileData;

            newListItem.onclick = (e) => {
                setActiveItem(e.currentTarget);
            };

            newListItem.innerHTML = `
                ${projectName}
                <button class="trash-container deleteList" data-project-name="${projectName}" onclick="deleteProject(this)">
                    <svg xmlns="http://www.w3.org/2000/svg" class="trash-icon" viewBox="0 0 16 16">
                        <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0z"/>
                        <path d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4zM2.5 3h11V2h-11z"/>
                    </svg>
                </button>
            `;

            const listGroup = document.querySelector(".list-group.d-none.d-lg-block");
            listGroup.insertBefore(newListItem, listGroup.firstChild);

            const select = document.getElementById("projectSelect");
            const newOption = document.createElement("option");
            newOption.value = projectName;
            newOption.textContent = projectName;
            newOption.dataset.about = projectAbout;
            newOption.dataset.fileName = fileName;
            newOption.dataset.fileData = fileData;

            if (fileName && fileData) {
                newOption.setAttribute("data-file-name", fileName);
                newOption.setAttribute("data-file-data", fileData);

            } else {
                newOption.removeAttribute("data-file-name");
                newOption.removeAttribute("data-file-data");
            }

            select.insertBefore(newOption, select.firstChild);

            select.value = projectName;

            setActiveItem(newListItem);

            const modalElement = document.getElementById("createProjectModal");
            const modalInstance = bootstrap.Modal.getInstance(modalElement);
            modalInstance.hide();
        } else {
            const modalElement = document.getElementById("createProjectModal");
            const modalInstance = bootstrap.Modal.getInstance(modalElement);
            modalInstance.hide();
            showAlertBanner("Error al crear el proyecto");
        }
    } catch (error) {
        console.error("Error");
        const modalElement = document.getElementById("createProjectModal");
        const modalInstance = bootstrap.Modal.getInstance(modalElement);
        modalInstance.hide();
        showAlertBanner("Error al crear el proyecto");
    }
});
// <-------------------- CREATE PROJECT --------------------->

// <-------------------- REGISTER REPORT --------------------->
function createReport(userEmail, projectName) {
    if (!confirm("Aviso, generar un reporte puede tardar unos minutos, durante los cuales el chat estaría inactivo durante ese tiempo. ¿Deseas continuar?")) {
        return;
    }

    if (!localStorage.getItem("CurrentReportGenerate")) {
        localStorage.setItem("CurrentReportGenerate", [projectName]);
        console.log("Current Report Project Name:", projectName);
    } else {
        showAlertBanner("Ya hay un reporte en proceso de generación. Por favor, espera a que se complete antes de generar otro.");
        return;
    }

    setFiles();

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
            console.log("Respuesta del servidor:", data);
            if (data.ok) {
                showAlertBanner("Reporte generado exitosamente.", "success");
                localStorage.removeItem("CurrentReportGenerate");
                const projectName = data.content.project_name;
                const projectReportName = data.content.report_name;
                const projectReportData = data.content.report_data;
                const projectReportReasoning = data.content.report_reasoning;

                const listItems = document.querySelectorAll("#projectList .list-group-item");
                listItems.forEach(item => {
                    if (item.dataset.projectName === projectName) {
                        item.dataset.reportName = projectReportName;
                        item.dataset.reportData = projectReportData;
                    }
                });

                const options = document.querySelectorAll("#projectSelect option");
                options.forEach(option => {
                    if (option.value === projectName) {
                        option.dataset.reportName = projectReportName;
                        option.dataset.reportData = projectReportData;

                        if (projectReportName && projectReportData) {
                            option.setAttribute("data-report-name", projectReportName);
                            option.setAttribute("data-report-data", projectReportData);
                            option.setAttribute("data-report-reasoning", projectReportReasoning);
                        } else {
                            option.removeAttribute("data-report-name");
                            option.removeAttribute("data-report-data");
                            option.removeAttribute("data-report-reasoning");
                        }
                    }
                });

                setFiles();
            } else {
                console.log("Va por el else");
                showAlertBanner("Error al generar el reporte: " + data.message);
            }
        })
        .catch(error => {
            console.log("Va por el error");
            console.error("Error al generar el reporte:", error);
            showAlertBanner("Error al generar el reporte.");
        });
}
// <-------------------- REGISTER REPORT --------------------->

// <-------------------- DELETE PROJECTS SELECT --------------------->
async function deleteProjectSelect() {
    const select = document.getElementById("projectSelect");

    if (!select || select.options.length === 0) {
        showAlertBanner("No hay proyectos para eliminar.");
        return;
    }

    const projectName = select.value;

    if (!confirm("¿Estás seguro de que quieres eliminar el proyecto seleccionado?")) {
        return;
    }

    try {
        const response = await fetch(API_ROUTE + '/delete-project', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ project_name: projectName })
        });
        if (response.status === 401) {
            window.location.href = LOGIN;
            return;
        }

        if (!response.ok) {
            throw new Error("Error while deleting project");
        }

        const data = await response.json();

        const listItems = document.querySelectorAll(".list-group-item");
        listItems.forEach(item => {
            if (item.dataset.projectName === projectName) {
                item.remove();
            }
        });

        const optionToRemove = Array.from(select.options).find(option => option.value === projectName);
        if (optionToRemove) {
            optionToRemove.remove();
        }

        if (listItems.length > 0) {
            activeSelect();
        }
    } catch (error) {
        console.error("Error");
    }
}
// <-------------------- DELETE PROJECTS SELECT --------------------->

// <-------------------- DELETE PROJECTS LIST --------------------->
async function deleteProject(button) {
    const projectName = button.dataset.projectName;

    if (!confirm("¿Estás seguro de que quieres eliminar el proyecto seleccionado?")) {
        return;
    }

    try {
        const response = await fetch(API_ROUTE + '/delete-project', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ project_name: projectName })
        });
        if (response.status === 401) {
            window.location.href = LOGIN;
            return;
        }

        if (!response.ok) {
            throw new Error("Error while deleting project");
        }

        const data = await response.json();

        const projectItem = button.closest(".list-group-item");
        if (projectItem) {
            projectItem.remove();
        }

        const select = document.getElementById("projectSelect");
        if (select) {
            const optionToRemove = Array.from(select.options).find(option => option.value === projectName);
            if (optionToRemove) {
                optionToRemove.remove();
            }
        }

        const listItems = document.querySelectorAll(".list-group-item");
        if (listItems.length > 0) {
            setActiveItem(listItems[0]);
        }
    } catch (error) {
        console.error("Error");
    }
}
// <-------------------- DELETE PROJECTS LIST --------------------->

// <-------------------- MODAL REMEMBER --------------------->
function modifyProject() {
    const selectElement = document.getElementById("projectSelect");
    const selectedOption = selectElement.options[selectElement.selectedIndex];

    if (!selectedOption || !selectedOption.value || selectedOption.value === "") {
        showAlertBanner("Por favor, selecciona un proyecto primero.");
        return;
    }

    const projectName = selectedOption.value;
    const about = selectedOption.getAttribute("data-about");
    const email = currentUserEmail;
    const projectFileName = selectedOption.getAttribute("data-file-name");

    document.getElementById('original_project_name').value = projectName;
    document.getElementById('edit_project_name').value = projectName;
    document.getElementById('edit_about').value = about;

    fetch(API_ROUTE + '/get-criteria', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({ project_name: projectName })
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
            console.log("Va por el error");
            console.error("Error al mostrar el modal:", error);
            showAlertBanner("Error al mostrar el modal.");
        });


    const fileInfoElement = document.getElementById('currentFileInfo');
    if (projectFileName) {
        fileInfoElement.textContent = `Archivo actual: ${projectFileName}`;
    } else {
        fileInfoElement.textContent = `No hay archivo actualmente cargado.`;
    }

    let hiddenEmailField = document.getElementById('original_email');
    if (!hiddenEmailField) {
        hiddenEmailField = document.createElement('input');
        hiddenEmailField.type = 'hidden';
        hiddenEmailField.id = 'original_email';
        hiddenEmailField.name = 'original_email';
        document.getElementById('editProjectForm').appendChild(hiddenEmailField);
    }
    hiddenEmailField.value = email;
    const modal = new bootstrap.Modal(document.getElementById('editProjectModal'));
    modal.show();
}
// <-------------------- MODAL REMEMBER --------------------->

// <-------------------- EDIT PROJECTS --------------------->
async function submitProjectEdit(e) {
    e.preventDefault();

    const originalProjectName = document.getElementById('original_project_name').value.trim();
    const originalEmail = document.getElementById('original_email').value.trim();
    const newProjectName = document.getElementById('edit_project_name').value.trim();
    const newAbout = document.getElementById('edit_about').value.trim();
    const newMaxVulns = document.getElementById('edit_max_total_vulns').value;
    const newMinRatio = document.getElementById('edit_min_fixable_ratio').value;
    const newMaxSev = document.getElementById('edit_max_severity_level').value;
    const newCompScore = document.getElementById('edit_composite_score').value;

    const fileInput = document.getElementById("edit_project_file");
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

    const formData = new FormData();
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
    }

    try {
        console.log("Sending form data:", formData)
        const response = await fetch(API_ROUTE + "/edit-project", {
            method: "POST",
            credentials: 'include',
            body: formData
        });
        if (response.status === 401) {
            window.location.href = LOGIN;
            return;
        }

        const result = await response.json();

        if (result.status === "success") {
            const selectElement = document.getElementById("projectSelect");
            const selectedOption = selectElement.options[selectElement.selectedIndex];

            selectedOption.value = newProjectName;
            selectedOption.textContent = newProjectName;
            selectedOption.setAttribute("data-about", newAbout);
            if (fileName && fileData) {
                selectedOption.setAttribute("data-file-name", fileName);
                selectedOption.setAttribute("data-file-data", fileData);

                selectedOption.removeAttribute("data-report-name");
                selectedOption.removeAttribute("data-report-data");
                selectedOption.removeAttribute("data-report-reasoning");
            }

            const allListItems = document.querySelectorAll(".list-group-item");
            allListItems.forEach((item) => {
                if (item.dataset.projectName === originalProjectName) {
                    item.dataset.projectName = newProjectName;
                    item.dataset.about = newAbout;
                    item.innerHTML = `
                        ${newProjectName}
                        <button class="trash-container deleteList" data-project-name="${newProjectName}" onclick="deleteProject(this)">
                            <svg xmlns="http://www.w3.org/2000/svg" class="trash-icon" viewBox="0 0 16 16">
                                <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0z"/>
                                <path d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4zM2.5 3h11V2h-11z"/>
                            </svg>
                        </button>
                    `;
                }
            });
            setDescription();
            setFiles();
        } else {
            showAlertBanner("Error: " + result.message);
        }
    } catch (error) {
        showAlertBanner("Error al enviar la solicitud.");
    }
}
// <-------------------- EDIT PROJECTS --------------------->

// <-------------------- SHOW MODAL CREATE --------------------->

createProjectModal.addEventListener('show.bs.modal', () => {
    document.getElementById('max_total_vulns').value = 20;
    document.getElementById('min_fixable_ratio').value = 80;
    document.getElementById('max_severity_level').value = 7.0;
    document.getElementById('composite_score').value = 75;
});

// <-------------------- SHOW MODAL CREATE --------------------->

// <-------------------- HIDE MODAL CREATE --------------------->
createProjectModal.addEventListener('hidden.bs.modal', () => {
    const inputs = createProjectModal.querySelectorAll('input, textarea');
    inputs.forEach(input => input.value = '');
});
// <-------------------- HIDE MODAL CREATE --------------------->

// <-------------------- HIDE MODAL EDIT --------------------->
editProjectModal.addEventListener('hidden.bs.modal', () => {
    const inputs = editProjectModal.querySelectorAll('input, textarea');
    inputs.forEach(input => {
        // Asegúrate de limpiar también el tipo "file"
        if (input.type === 'file') {
            input.value = null; // o input.value = ''
        } else {
            input.value = '';
        }
    });
});
// <-------------------- HIDE MODAL EDIT --------------------->

// <-------------------- SET DESCRIPTION --------------------->
function setDescription() {
    const select = document.getElementById("projectSelect");
    const selectedOption = select.options[select.selectedIndex];
    const about = selectedOption.getAttribute("data-about");

    const aboutTitle = document.getElementById("about-name");
    const aboutDesc = document.getElementById("about-text");

    if (aboutTitle && aboutDesc) {
        aboutTitle.textContent = selectedOption.value;
        aboutDesc.textContent = about;
    }
}
// <-------------------- SET DESCRIPTION --------------------->

// <-------------------- UPDATE FILES ---------------------->

async function updateFiles(projectNames) {
    for (const projectName of projectNames) {
        fetch(API_ROUTE + '/get-report-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ project_name: projectName })
        })
            .then(response => {
                if (response.status === 401) {
                    window.location.href = "http://localhost:8080/login";
                    return;
                }
                return response.json();
            })
            .then(data => {
                if (data && data.content) {
                    const projectReportName = data.content.report_name;
                    const projectReportData = data.content.report_data;
                    const projectReportReasoning = data.content.report_reasoning;

                    const listItems = document.querySelectorAll("#projectList .list-group-item");
                    listItems.forEach(item => {
                        if (item.dataset.projectName === projectName) {
                            item.dataset.reportName = projectReportName;
                            item.dataset.reportData = projectReportData;
                        }
                    });

                    const options = document.querySelectorAll("#projectSelect option");
                    options.forEach(option => {
                        if (option.value === projectName) {
                            option.dataset.reportName = projectReportName;
                            option.dataset.reportData = projectReportData;

                            if (projectReportName && projectReportData) {
                                option.setAttribute("data-report-name", projectReportName);
                                option.setAttribute("data-report-data", projectReportData);
                                option.setAttribute("data-report-reasoning", projectReportReasoning);
                            } else {
                                option.removeAttribute("data-report-name");
                                option.removeAttribute("data-report-data");
                                option.removeAttribute("data-report-reasoning");
                            }
                        }
                    });

                    setFiles();
                } else {
                    console.log("Va por el else");
                    showAlertBanner("Error al generar el reporte: " + (data && data.message ? data.message : 'Respuesta inválida del servidor.'));
                }
            })
            .catch(error => {
                console.log("Va por el error");
                console.error("Error al generar el reporte:", error);
                showAlertBanner("Error al generar el reporte.");
            });
    }
}

// <-------------------- UPDATE FILES ---------------------->

// <-------------------- SET FILES --------------------->
function setFiles() {
    const select = document.getElementById("projectSelect");
    const selectedOption = select.options[select.selectedIndex];

    const fileName = selectedOption.getAttribute("data-file-name");
    const fileData = selectedOption.getAttribute("data-file-data");

    if (fileName && fileData) {
        const noFile = document.getElementById("no-file");
        noFile.style.display = "none";

        const fileLinks = document.getElementById("file-links");
        fileLinks.innerHTML = '';

        // Lista para los elementos de archivo y reporte
        const fileList = document.createElement("ul");
        fileList.style.listStyleType = "none";
        fileList.style.padding = "0";
        fileList.style.margin = "0";

        const createFileItem = (name, data, reasoning) => {
            const li = document.createElement("li");
            li.style.display = "flex";
            li.style.alignItems = "center";
            li.style.marginBottom = "10px";

            const button = document.createElement("button");
            button.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="white" class="bi bi-eye" viewBox="0 0 16 16">
                    <path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8M1.173 8a13 13 0 0 1 1.66-2.043C4.12 4.668 5.88 3.5 8 3.5s3.879 1.168 5.168 2.457A13 13 0 0 1 14.828 8q-.086.13-.195.288c-.335.48-.83 1.12-1.465 1.755C11.879 11.332 10.119 12.5 8 12.5s-3.879-1.168-5.168-2.457A13 13 0 0 1 1.172 8z"/>
                    <path d="M8 5.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5M4.5 8a3.5 3.5 0 1 1 7 0 3.5 3.5 0 0 1-7 0"/>
                </svg>
            `;
            Object.assign(button.style, {
                backgroundColor: "#1971B2",
                border: "none",
                borderRadius: "5px",
                padding: "2px",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: "34px",
                height: "34px"
            });

            button.onclick = () => showFile(name, data);

            const span = document.createElement("span");
            span.textContent = " " + name;
            span.style.marginLeft = "8px";

            li.appendChild(button);
            li.appendChild(span);
            return li;
        };

        // Añadir archivo principal
        fileList.appendChild(createFileItem(fileName, fileData));

        // Añadir reporte si existe
        const reportName = selectedOption.getAttribute("data-report-name");
        const reportData = selectedOption.getAttribute("data-report-data");
        const reportReasoning = selectedOption.getAttribute("data-report-reasoning");

        const createReportItem = (name, data, reasoning) => {
            const li = document.createElement("li");
            li.style.display = "flex";
            li.style.alignItems = "center";
            li.style.marginBottom = "10px";

            const button = document.createElement("button");
            button.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="white" class="bi bi-eye" viewBox="0 0 16 16">
                    <path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8M1.173 8a13 13 0 0 1 1.66-2.043C4.12 4.668 5.88 3.5 8 3.5s3.879 1.168 5.168 2.457A13 13 0 0 1 14.828 8q-.086.13-.195.288c-.335.48-.83 1.12-1.465 1.755C11.879 11.332 10.119 12.5 8 12.5s-3.879-1.168-5.168-2.457A13 13 0 0 1 1.172 8z"/>
                    <path d="M8 5.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5M4.5 8a3.5 3.5 0 1 1 7 0 3.5 3.5 0 0 1-7 0"/>
                </svg>
            `;
            Object.assign(button.style, {
                backgroundColor: "#1971B2",
                border: "none",
                borderRadius: "5px",
                padding: "2px",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: "34px",
                height: "34px"
            });

            button.onclick = () => showReport(name, data, reasoning);

            const span = document.createElement("span");
            span.textContent = " " + name;
            span.style.marginLeft = "8px";

            li.appendChild(button);
            li.appendChild(span);
            return li;
        };

        const createReportButton = () => {
            const li = document.createElement("li");
            li.style.display = "flex";
            li.style.alignItems = "center";
            li.style.marginBottom = "10px";

            const button = document.createElement("button");
            let span = document.createElement("span");
            const in_process = localStorage.getItem("CurrentReportGenerate");
            if (in_process && in_process.includes(selectedOption.value)) {
                button.innerHTML = `
                    <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true" style="color: white;"></span>
                `;
                button.disabled = true;
                span.textContent = "Generando Reporte...";
                span.style.marginLeft = "8px";
            } else {
                button.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="white" class="bi bi-file-earmark-text" viewBox="0 0 16 16">
                        <path d="M14 4.5V14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V4.5A1.5 1.5 0 0 1 3.5 3h6A1.5 1.5 0 0 1 11 4.5v.5h3zM11.5 4h-6A1.5 1.5 0 0 0 4 5.5v8A1.5 1.5 0 0 0 5.5 15h6A1.5 1.5 0 0 0 13 13.5V4.707L11.293 3H11v1zM10 .293V3h2l-2-2z"/>
                        <path d="M5 6.5a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5zm0 2a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 0 1h-3a.5.5 0 0 1-.5-.5zm0 2a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 0 1h-3a.5.5 0 0 1-.5-.5z"/>
                    </svg>
                `;
                span.textContent = "Generar Reporte";
                span.style.marginLeft = "8px";
            }
            Object.assign(button.style, {
                backgroundColor: "#1971B2",
                border: "none",
                borderRadius: "5px",
                padding: "2px",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: "34px",
                height: "34px",
            });

            button.onclick = () => createReport(currentUserEmail, selectedOption.value);

            li.appendChild(button);
            li.appendChild(span);
            return li;
        };

        if (reportName && reportData) {
            console.log("Report Name:", reportName);
            fileList.appendChild(createReportItem(reportName, reportData, reportReasoning));
        } else {
            fileList.appendChild(createReportButton());
        }

        fileLinks.appendChild(fileList);
        fileLinks.style.display = "block";

    } else {
        const noFile = document.getElementById("no-file");
        noFile.style.display = "block";

        const fileLinks = document.getElementById("file-links");
        fileLinks.innerHTML = '';
    }
}
// <-------------------- SET FILES --------------------->
// <-------------------- SHOW FILE MODAL --------------------->

function showFile(fileName, fileData) {
    document.getElementById("fileModalTitle").textContent = fileName;
    document.getElementById("fileDescription").textContent = fileData;

    const fileModal = new bootstrap.Modal(document.getElementById('fileModal'));
    fileModal.show();
}

// <-------------------- SHOW FILE MODAL --------------------->

// <-------------------- SHOW REPORT MODAL --------------------->

function showReport(reportName, reportData, reportReasoning) {

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
}

// <-------------------- SHOW FILE MODAL --------------------->

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

// <-------------------- SET ACTIVE ITEM --------------------->
function setActiveItem(targetItem) {
    const listItems = document.querySelectorAll(".list-group-item");

    listItems.forEach(item => item.classList.remove("active"));
    targetItem.classList.add("active");

    const projectName = targetItem.dataset.projectName;
    const about = targetItem.dataset.about;
    localStorage.setItem("activeProject", projectName);

    const select = document.getElementById("projectSelect");
    select.value = projectName;

    setDescription();
    setFiles();
};
// <-------------------- SET ACTIVE ITEM --------------------->

// <-------------------- ACTIVE SELECT --------------------->
function activeSelect() {
    const selectedProjectName = document.getElementById("projectSelect").value;
    const listItems = document.querySelectorAll(".list-group-item");

    listItems.forEach(item => {
        if (item.dataset.projectName === selectedProjectName) {
            setActiveItem(item);
        }
    });
};
// <-------------------- ACTIVE SELECT --------------------->

// <-------------------- LOAD ALL PROJECTS --------------------->
async function loadAllProjects() {
    try {
        const response = await fetch(API_ROUTE + "/get-projects", {
            method: "GET",
            credentials: 'include',
        });
        if (response.status === 401) {
            window.location.href = LOGIN;
            return;
        }

        const data = await response.json();

        if (response.ok) {

            data.sort((a, b) => new Date(b.creation_date) - new Date(a.creation_date));

            data.forEach(project => {
                const projectName = project.project_name;
                const projectAbout = project.about;
                const projectFileName = project.file_name;
                const projectFileData = project.file_data;
                const projectReportName = project.report_name;
                const projectReportData = project.report_data;
                const newListItem = document.createElement("a");
                newListItem.href = "#";
                newListItem.className = "list-group-item list-group-item-action";
                newListItem.dataset.projectName = projectName;
                newListItem.dataset.about = projectAbout;
                newListItem.dataset.fileName = projectFileName;
                newListItem.dataset.fileData = projectFileData;
                newListItem.dataset.reportName = projectReportName;
                newListItem.dataset.reportData = projectReportData;
                newListItem.onclick = (e) => {
                    setActiveItem(e.currentTarget);
                };

                newListItem.innerHTML = `
                ${projectName}
                <button class="trash-container deleteList" data-project-name="${projectName}" onclick="deleteProject(this)">
                    <svg xmlns="http://www.w3.org/2000/svg" class="trash-icon" viewBox="0 0 16 16">
                        <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0z"/>
                        <path d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4zM2.5 3h11V2h-11z"/>
                    </svg>
                </button>
            `;

                const listGroup = document.querySelector(".list-group.d-none.d-lg-block");
                listGroup.insertBefore(newListItem, listGroup.firstChild);

                const select = document.getElementById("projectSelect");
                const newOption = document.createElement("option");
                newOption.value = projectName;
                newOption.textContent = projectName;
                newOption.dataset.about = projectAbout;
                newOption.dataset.fileName = projectFileName;
                newOption.dataset.fileData = projectFileData;
                newOption.dataset.reportName = projectReportName;
                newOption.dataset.reportData = projectReportData;

                if (projectFileName && projectFileData) {
                    newOption.setAttribute("data-file-name", projectFileName);
                    newOption.setAttribute("data-file-data", projectFileData);
                } else {
                    newOption.removeAttribute("data-file-name");
                    newOption.removeAttribute("data-file-data");
                }

                if (projectReportName && projectReportData) {
                    newOption.setAttribute("data-report-name", projectReportName);
                    newOption.setAttribute("data-report-data", projectReportData);
                    newOption.setAttribute("data-report-reasoning", project.report_reasoning || "");
                } else {
                    newOption.removeAttribute("data-report-name");
                    newOption.removeAttribute("data-report-data");
                    newOption.removeAttribute("data-report-reasoning");
                }

                select.insertBefore(newOption, select.firstChild)
            });

            const listItems = document.querySelectorAll(".list-group-item");
            const storedProjectName = localStorage.getItem("activeProject");
            let activated = false;

            if (storedProjectName) {
                listItems.forEach(item => {
                    if (item.dataset.projectName === storedProjectName) {
                        setActiveItem(item);
                        activated = true;
                    }
                });
            }

            if (!activated && listItems.length > 0) {
                setActiveItem(listItems[0]);
            }
        } else {
            showAlertBanner("Error al cargar los proyectos");
            console.error("Error al cargar proyectos:", data);
        }
    } catch (error) {
        showAlertBanner("Error de conexión al intentar cargar los proyectos");
        console.error("Error en la solicitud");
    }
}

document.addEventListener("DOMContentLoaded", async function () {
    await loadAllProjects();
    checkAndSchedule(true);
});
// <-------------------- LOAD ALL PROJECTS --------------------->
// <-------------------- CHECK AND SCHEDULE --------------------->
async function checkGenerationStatus() {
    try {
        console.log("Consultando estado de generación de reportes...");
        const response = await fetch(API_ROUTE + "/check-generation-status", {
            method: "GET",
            credentials: "include",
        });

        if (!response.ok) {
            console.error("Error en el fetch:", response.status);
            return null;
        }

        const result = await response.json();
        console.log("Estado de generación recibido:", result);
        return result.projects || [];
    } catch (error) {
        console.error("Error al consultar el estado de generación:", error);
        return null;
    }
}

async function checkAndSchedule(isFirstRun = false) {
    const projects = await checkGenerationStatus();
    console.log("Proyectos en proceso de generación:", projects);

    if (projects && projects.length > 0) {
        localStorage.setItem("CurrentReportGenerate", JSON.stringify(projects));
        for (const project of projects) {
            if (!toUpdateReports.includes(project)) {
                toUpdateReports.push(project);
            }
        }
        console.log("LocalStorage: ", localStorage.getItem("CurrentReportGenerate"));

        if (isFirstRun) {
            showAlertBanner("Ya hay un reporte en proceso de generación. Por favor, espera a que se complete antes de generar otro.", "success");
            setFiles();
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
// <-------------------- CHECK AND SCHEDULE --------------------->





