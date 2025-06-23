// Event listener for the banner close button
document.addEventListener('DOMContentLoaded', function () {
    const alertBanner = document.getElementById('alert-banner');
    const closeButton = document.getElementById('alert-banner-close');

    closeButton.addEventListener('click', function () {
        alertBanner.classList.add('d-none');
    });
});

const API_ROUTE = 'http://localhost:3000/api';
const notificacionesContainer = document.getElementById('notificaciones-container');
const projectList = document.getElementById('project-list');

let datos = {};

function agruparPorProyecto(notificaciones) {
    const agrupadas = {};
    notificaciones.forEach((n) => {
        const proyecto = n.project_name || "Sin Proyecto";
        if (!agrupadas[proyecto]) agrupadas[proyecto] = [];
        agrupadas[proyecto].push({
            titulo: n.notification_title,
            mensaje: n.message,
            fecha: new Date(n.timestamp).toLocaleDateString(),
            leida: n.is_read,
        });
    });
    return agrupadas;
}

function renderListaProyectos() {
    projectList.innerHTML = `
      <div class="list-group-item bg-primary text-white">Proyectos</div>
    `;
    Object.keys(datos).forEach((proyecto) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'list-group-item list-group-item-action';
        btn.dataset.proyecto = proyecto;
        btn.textContent = proyecto;
        projectList.appendChild(btn);
    });
}

function renderNotificaciones(nombreProyecto) {
    const notificaciones = datos[nombreProyecto] || [];

    const listGroup = document.createElement('div');
    listGroup.className = 'list-group';

    const encabezado = document.createElement('div');
    encabezado.className = 'list-group-item bg-primary text-white';
    encabezado.textContent = 'Notificaciones';
    listGroup.appendChild(encabezado);

    if (notificaciones.length === 0) {
        const emptyItem = document.createElement('div');
        emptyItem.className = 'list-group-item text-muted';
        emptyItem.textContent = 'No hay notificaciones para este proyecto.';
        listGroup.appendChild(emptyItem);
    } else {
        notificaciones.forEach((noti) => {
            const item = document.createElement('button');
            item.type = 'button';
            item.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
            item.innerHTML = `
          <div>${noti.titulo}</div>
          <span class="badge ${noti.leida ? 'bg-secondary' : 'bg-success'} rounded-pill">
            ${noti.leida ? 'Leída' : 'Nueva'}
          </span>
        `;
            item.addEventListener('click', () => {
                document.getElementById('modalNotificacionLabel').textContent = noti.titulo;
                document.getElementById('modalMensaje').textContent = noti.mensaje;
                document.getElementById('modalFecha').textContent = 'Fecha: ' + noti.fecha;
                const modal = new bootstrap.Modal(document.getElementById('modalNotificacion'));
                modal.show();
            });
            listGroup.appendChild(item);
        });
    }

    notificacionesContainer.innerHTML = '';
    notificacionesContainer.appendChild(listGroup);
}

function renderDefaultMessage() {
    const listGroup = document.createElement('div');
    listGroup.className = 'list-group';

    const encabezado = document.createElement('div');
    encabezado.className = 'list-group-item bg-primary text-white';
    encabezado.textContent = 'Notificaciones';
    listGroup.appendChild(encabezado);

    const defaultItem = document.createElement('div');
    defaultItem.className = 'list-group-item text-muted';
    defaultItem.textContent = 'Selecciona un proyecto para ver sus notificaciones.';
    listGroup.appendChild(defaultItem);

    notificacionesContainer.innerHTML = '';
    notificacionesContainer.appendChild(listGroup);
}

projectList.addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-proyecto]');
    if (!btn) return;
    const nombreProyecto = btn.dataset.proyecto;
    renderNotificaciones(nombreProyecto);
});

async function cargarNotificaciones() {
    try {
        const url = currentUserRole === "admin"
            ? `${API_ROUTE}/notification/admin`
            : `${API_ROUTE}/notification`;

        const response = await fetch(url, {
            credentials: 'include'
        });

        const data = await response.json();
        if (data.notifications) {
            datos = agruparPorProyecto(data.notifications);
            renderListaProyectos();
        } else {
            datos = {};
        }
        renderDefaultMessage();
    } catch (error) {
        console.error("Error al cargar notificaciones:", error);
    }
}


cargarNotificaciones();
