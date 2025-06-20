document.addEventListener('DOMContentLoaded', () => {
    const statsEl        = document.getElementById('stats');
    const mainContent    = document.getElementById('mainContent');
    const dashboardLink  = document.getElementById('dashboard-link');
    const profesoresLink = document.getElementById('profesores-link');
    const registroLink   = document.getElementById('registro-profesor-link');
    document.getElementById('totalMaterias').textContent = '9';



    // Renombrar el modal de detalles a modalProfesorTareas
    const modalProfesorTareas = new bootstrap.Modal(document.getElementById('modalProfesorTareas'));
    const filtroCursoTareas = document.getElementById('filtroCursoTareas');
    const tareasTableBody = document.getElementById('tareasTableBody');
    let currentProfessorId = null; // Para almacenar el ID del profesor actual en el modal

    // 1) Cargar estadísticas
    async function cargarEstadisticas() {
      try {
        const resE = await fetch('/api/estudiantes/count', { credentials:'same-origin' });
        if (resE.ok) document.getElementById('totalEstudiantes').textContent = (await resE.json()).count;
      } catch {
        document.getElementById('totalEstudiantes').textContent = '0';
      }
      try {
        const resP = await fetch('/api/profesores/count', { credentials:'same-origin' });
        document.getElementById('totalProfesores').textContent = resP.ok ? (await resP.json()).count : '0';
      } catch {
        document.getElementById('totalProfesores').textContent = '0';
      }
     
    }

    // 2) Renderizar tabla de profesores (Mantiene la tabla de administración)
    function renderizarTabla(headers, rows, keys) {
      let html = '<div class="table-responsive"><table class="table table-striped table-sm"><thead><tr>';
      headers.forEach(h => html += `<th>${h}</th>`);
      html += '<th>Acciones</th></tr></thead><tbody>';
      rows.forEach(r => {
        html += `<tr data-id="${r.id}">`;
        keys.forEach(k => html += `<td>${r[k] !== undefined && r[k] !== null ? r[k] : ''}</td>`); // Handle undefined/null values
        html += `
          <td>
            <button class="btn btn-sm btn-primary btn-edit me-2">Editar</button>
            <button class="btn btn-sm btn-danger btn-disable">Inactivar</button>
          </td>
        </tr>`;
      });
      html += '</tbody></table></div>';
      mainContent.innerHTML = html;
      document.querySelectorAll('.btn-edit').forEach(b => b.onclick = onEdit);
      document.querySelectorAll('.btn-disable').forEach(b => b.onclick = onDisable);
    }

    // 3) Navegación principal
    dashboardLink.addEventListener('click', e => {
      e.preventDefault();
      statsEl.style.display = 'flex';
      mainContent.innerHTML = '';
      cargarEstadisticas();
    });

    profesoresLink.addEventListener('click', async e => {
      e.preventDefault();
      statsEl.style.display = 'none';
      try {
        const res = await fetch('/api/profesores', { credentials:'same-origin' });
        if (!res.ok) throw new Error('Error al cargar profesores');
        const profesores = await res.json();
        renderizarTabla(

          [
            'Nombre','Apellido','Usuario','Contraseña','Documento','Líder',
            'Experiencia','Materia','Correo','Teléfono','Dirección','Estado','Fecha de Registro'
          ],
          profesores,
          [
            'nombre','apellido','nombre_usuario','contrasena','documento','lider',
            'experiencia','materia','correo','telefono','direccion','estado','fecha_de_registro'
          ]
        );
      } catch (error) {
        alert('❌ ' + error.message);
      }
    });

    registroLink.addEventListener('click', e => {
      e.preventDefault();
      statsEl.style.display = 'none';
      mostrarFormulario();
    });

    // 4) Formulario crear/editar profesor
    function mostrarFormulario(prof = {}) {
      const isEdit = !!prof.id;
      const title  = isEdit ? 'Editar Profesor' : 'Crear Profesor';
      mainContent.innerHTML = `
        <h4>${title}</h4>
        <form id="formProfesor" class="row g-3">
          <div class="col-md-6"><label>Nombre</label><input name="nombre" value="${prof.nombre||''}" class="form-control" required></div>
          <div class="col-md-6"><label>Apellido</label><input name="apellido" value="${prof.apellido||''}" class="form-control" required></div>
          <div class="col-md-6"><label>Usuario</label><input name="nombre_usuario" value="${prof.nombre_usuario||''}" class="form-control" required></div>
          <div class="col-md-6"><label>Contraseña</label><input name="contrasena" value="${prof.contrasena||''}" class="form-control" required></div>
          <div class="col-md-6"><label>Documento</label><input name="documento" value="${prof.documento||''}" class="form-control" required></div>
          <div class="col-md-6"><label>Correo</label><input type="email" name="correo" value="${prof.correo||''}" class="form-control" required></div>
          <div class="col-md-6"><label>Experiencia</label><input name="experiencia" value="${prof.experiencia||''}" class="form-control" required></div>
          <div class="col-md-6"><label>Materia</label>
            <select name="materia" class="form-select" required>
              ${['Matemática','Sociales','Inglés','Biología','Español','Educación física','Etica & Valores','Química','Física']
                .map(m => `<option${prof.materia===m?' selected':''}>${m}</option>`).join('')}
            </select>
          </div>
          <div class="col-md-6"><label>Líder de Curso</label><input name="lider" value="${prof.lider||''}" class="form-control"></div>
          <div class="col-md-6"><label>Teléfono</label><input name="telefono" value="${prof.telefono||''}" class="form-control" required></div>
          <div class="col-12"><label>Dirección</label><input name="direccion" value="${prof.direccion||''}" class="form-control" required></div>
          <div class="col-12"><button type="submit" class="btn btn-success">${title}</button></div>
        </form>`;
      document.getElementById('formProfesor').addEventListener('submit', async ev => {
        ev.preventDefault();
        const data   = Object.fromEntries(new FormData(ev.target).entries());
        const url    = isEdit ? `/api/profesores/${prof.id}` : '/api/profesores';
        const method = isEdit ? 'PUT' : 'POST';
        try {
          const res    = await fetch(url, {
            method, credentials:'same-origin',
            headers:{ 'Content-Type':'application/json' },
            body: JSON.stringify(data)
          });
          const result = await res.json();
          if (!res.ok) {
            alert('❌ ' + (result.error||'Error desconocido'));
            return;
          }
          alert(`✅ Profesor ${isEdit?'actualizado':'creado'} correctamente`);
          cargarEstadisticas();
          profesoresLink.click(); // Reload the professors list
        } catch {
          alert('❌ No se pudo conectar');
        }
      });
    }

    // 5) Funciones de acciones para la TABLA de administración de profesores
    function onViewDetailsFromTable(e) {
        const tr = e.target.closest('tr');
        const professorId = tr.dataset.id;
        // Obtenemos los datos completos del profesor para el modal
        fetch(`/api/profesores/${professorId}`, { credentials:'same-origin' })
            .then(response => response.json())
            .then(professor => {
                showProfessorModal(professor);
            })
            .catch(error => {
                console.error('Error fetching professor details:', error);
                alert('No se pudo cargar los detalles del profesor.');
            });
    }

    function onEdit(e) {
      const tr = e.target.closest('tr');
      const rowData = Array.from(tr.querySelectorAll('td')).map(td => td.textContent);
      // Asume que los datos están en el mismo orden que las keys en renderizarTabla
      fetch(`/api/profesores/${tr.dataset.id}`, { credentials:'same-origin' })
        .then(response => response.json())
        .then(prof => {
            mostrarFormulario(prof); // Pasamos el objeto completo para prellenar el formulario
        })
        .catch(error => {
            console.error('Error fetching professor for edit:', error);
            alert('No se pudo cargar los datos del profesor para editar.');
        });
    }

    async function onDisable(e) {
      if (!confirm('¿Inactivar este profesor?')) return;
      const tr = e.target.closest('tr'), id = tr.dataset.id;
      try {
        const res = await fetch(`/api/profesores/${id}`, {
          method:'PUT', credentials:'same-origin',
          headers:{ 'Content-Type':'application/json' },
          body: JSON.stringify({ estado:'Inactivo' })
        });
        if (!res.ok) throw new Error('Error al inactivar');
        tr.remove();
        document.getElementById('totalProfesores').textContent =
          (+document.getElementById('totalProfesores').textContent - 1).toString();
      } catch (error) {
        alert('❌ ' + error.message);
      }
    }

    // --- Funciones para el Modal de Tareas del Profesor ---

    // Función para mostrar el modal de detalles y tareas
    async function showProfessorModal(professor) {
        currentProfessorId = professor.id; // Guarda el ID del profesor actual
        document.getElementById('profesorModalNombre').textContent = `${professor.nombre} ${professor.apellido}`;
        document.getElementById('profesorModalNombreCompleto').textContent = `${professor.nombre} ${professor.apellido}`;
        // Set image source. Check if professor.imagen exists, otherwise use default
        document.getElementById('profesorModalImage').src = professor.imagen ? professor.imagen : '/static/avatars/default.png';
        document.getElementById('profesorModalCorreo').textContent = professor.correo || 'N/A';
        document.getElementById('profesorModalTelefono').textContent = professor.telefono || 'N/A';
        document.getElementById('profesorModalDireccion').textContent = professor.direccion || 'N/A';

        // Restablecer el filtro de curso a "Todos" cada vez que se abre el modal
        filtroCursoTareas.value = 'Todos';

        // Cargar las tareas iniciales (todas)
        await loadProfessorTasks(currentProfessorId, 'Todos');
        modalProfesorTareas.show();
    }

    // Función para cargar y renderizar las tareas del profesor
    async function loadProfessorTasks(profesorId, curso = 'Todos') {
        tareasTableBody.innerHTML = '<tr><td colspan="4">Cargando tareas...</td></tr>';
        try {
            // Modified to use the new API endpoint for tasks
            const url = `/api/profesores/${profesorId}/tareas` + (curso !== 'Todos' ? `?curso=${encodeURIComponent(curso)}` : '');
            // Simulate API response for demonstration purposes
            // In a real application, you would fetch from your backend here.
            const response = await fetch(url, { credentials: 'same-origin' });
            if (!response.ok) {
                if (response.status === 404) {
                    tareasTableBody.innerHTML = '<tr><td colspan="4">No hay tareas para este profesor.</td></tr>';
                    return;
                }
                throw new Error(`Error al cargar las tareas: ${response.statusText}`);
            }
            const tareas = await response.json();

            // Mock data for demonstration (remove in production when connected to real API)
            // const mockTareas = [
            //     { curso: '6A', titulo: 'Ejercicios de improbabilidad', promedio: 4.6, pendiente: 'Juan Mendez' },
            //     { curso: '9B', titulo: 'Áreas y perímetros', promedio: 4.2, pendiente: 'Carlos Ramirez' },
            //     { curso: '8A', titulo: 'Funciones lineales', promedio: 5.0, pendiente: null },
            //     { curso: '7C', titulo: 'Polinomios', promedio: 4.1, pendiente: 'Luisa Herrera' },
            // ];
            // const tareasToDisplay = curso === 'Todos' ? mockTareas : mockTareas.filter(t => t.curso === curso);


            if (tareas.length === 0) {
                tareasTableBody.innerHTML = '<tr><td colspan="4">No hay tareas para este curso.</td></tr>';
            } else {
                tareasTableBody.innerHTML = tareas.map(tarea => `
                    <tr>
                        <td>${tarea.curso || ''}</td>
                        <td>${tarea.titulo || ''}</td>
                        <td>${tarea.promedio !== undefined && tarea.promedio !== null ? tarea.promedio : 'N/A'}</td>
                        <td class="${tarea.pendiente ? 'text-danger' : ''}">${tarea.pendiente || 'N/A'}</td>
                    </tr>
                `).join('');
            }
        } catch (error) {
            console.error('Error al cargar las tareas:', error);
            tareasTableBody.innerHTML = `<tr><td colspan="4" class="text-danger">Error: ${error.message}</td></tr>`;
        }
    }

    // Event listener para el filtro de curso en el modal
    filtroCursoTareas.addEventListener('change', () => {
        if (currentProfessorId) {
            loadProfessorTasks(currentProfessorId, filtroCursoTareas.value);
        }
    });


    // 6) Handler para Materias (Modificado para abrir el modal al clickear la tarjeta)
    const materiaLinks = document.querySelectorAll('.materia-link');
    materiaLinks.forEach(link => {
      link.addEventListener('click', async e => {
        e.preventDefault();
        const materia = link.dataset.materia;
        statsEl.style.display = 'none';
        mainContent.innerHTML = `
          <h4 class="mb-3">Profesores de ${materia}</h4>
          <div id="profesoresContainer" class="d-flex flex-column">
            <div class="col-12"><p>Cargando profesores…</p></div>
          </div>
        `;
        const profesoresContainer = document.getElementById('profesoresContainer');
        try {
          const url = `/api/materia/${encodeURIComponent(materia)}/profesores`;
          const res = await fetch(url, { credentials: 'same-origin' });
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          const profes = await res.json();
          if (!profes.length) {
            profesoresContainer.innerHTML = `<div class="col-12"><p>No hay profesores asignados.</p></div>`;
          } else {
            // Note: Assuming 'imagen' property exists in the professor object from the backend
            // If not, you might need to construct the image path differently or use a default.
            profesoresContainer.innerHTML = profes.map(p => `
              <div class="profesor-card" data-profesor-id="${p.id}">
                <div class="card-header">
                  <img src="${p.imagen ? p.imagen : '/static/avatars/default.png'}"
                       onerror="this.onerror=null;this.src='/static/avatars/default.png';"
                       class="rounded-circle"
                       style="width:50px; height:50px; object-fit:cover;"
                       alt="Imagen de ${p.nombre}">
                  <span>${p.nombre} ${p.apellido}</span>
                </div>
              </div>
            `).join('');

            // Añadir event listeners a las nuevas tarjetas
            document.querySelectorAll('.profesor-card').forEach(card => {
                card.addEventListener('click', async (event) => {
                    const profesorId = event.currentTarget.dataset.profesorId;
                    try {
                        // Fetch the full professor details, as the card itself might not contain all info
                        const res = await fetch(`/api/profesores/${profesorId}`, { credentials:'same-origin' });
                        if (!res.ok) throw new Error('Error al cargar los detalles del profesor.');
                        const professor = await res.json();
                        showProfessorModal(professor);
                    } catch (error) {
                        console.error('Error al abrir modal:', error);
                        alert('No se pudo cargar la información del profesor.');
                    }
                });
            });
          }
        } catch (err) {
          profesoresContainer.innerHTML = `<div class="col-12"><p class="text-danger">Error: ${err.message}</p></div>`;
        }
      });
    });

    // Inicial
    statsEl.style.display = 'flex';
    cargarEstadisticas();
  });

document.addEventListener("DOMContentLoaded", function () {
  // Toggle sidebar
  const toggleButton = document.getElementById("btn-toggle-sidebar");
  const sidebar = document.getElementById("sidebar");
  const mainContent = document.querySelector(".flex-grow-1");

  if (toggleButton && sidebar && mainContent) {
    toggleButton.addEventListener("click", () => {
      sidebar.classList.toggle("collapsed");
      mainContent.classList.toggle("expanded");
    });
  }

  // Ocultar todas las secciones (ajusta los IDs según tus secciones)
  function ocultarTodasLasSecciones() {
    [
      "seccion-inicio",
      "seccion-profesores",
      "seccion-proyectos",
      "seccion-tareas",
      "contenido-calendario",
      "contenido-planificacion"
    ].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.style.display = "none";
    });
  }

  // Activar botón del sidebar
  function activarBoton(boton) {
    document.querySelectorAll("#sidebar .nav-link").forEach(link => link.classList.remove("active"));
    boton.classList.add("active");
  }

  // Listeners para cada botón (ajusta los IDs según tus botones)
  document.getElementById("btn-inicio")?.addEventListener("click", function (e) {
    e.preventDefault();
    ocultarTodasLasSecciones();
    document.getElementById("seccion-inicio").style.display = "block";
    activarBoton(this);
  });
  document.getElementById("btn-profesores")?.addEventListener("click", function (e) {
    e.preventDefault();
    ocultarTodasLasSecciones();
    document.getElementById("seccion-profesores").style.display = "block";
    activarBoton(this);
  });
  document.getElementById("btn-proyectos")?.addEventListener("click", function (e) {
    e.preventDefault();
    ocultarTodasLasSecciones();
    document.getElementById("seccion-proyectos").style.display = "block";
    activarBoton(this);
  });
  document.getElementById("btn-tareas")?.addEventListener("click", function (e) {
    e.preventDefault();
    ocultarTodasLasSecciones();
    document.getElementById("seccion-tareas").style.display = "block";
    activarBoton(this);
  });
  document.getElementById("btn-calendario")?.addEventListener("click", function (e) {
    e.preventDefault();
    ocultarTodasLasSecciones();
    document.getElementById("contenido-calendario").style.display = "block";
    activarBoton(this);
  });
  document.getElementById("btn-planificacion")?.addEventListener("click", function (e) {
    e.preventDefault();
    ocultarTodasLasSecciones();
    document.getElementById("contenido-planificacion").style.display = "block";
    activarBoton(this);
  });

  // Agrega el handler para el botón de Ajustes
  const btnAjustes = document.getElementById("btn-ajustes");
  if (btnAjustes) {
    btnAjustes.addEventListener("click", function (e) {
      e.preventDefault();
      const modal = new bootstrap.Modal(document.getElementById('ajustesModal'));
      modal.show();
    });
  }

  // Agrega el handler para el botón de Perfil
  const btnPerfil = document.getElementById("btn-perfil");
  if (btnPerfil) {
    btnPerfil.addEventListener("click", function (e) {
      e.preventDefault();
      const modal = new bootstrap.Modal(document.getElementById('perfilModal'));
      modal.show();
    });
  }
});

  // Sidebar colapsable: solo iconos al salir el mouse
  document.addEventListener('DOMContentLoaded', function () {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.add('sidebar-collapsed'); // <-- Esto la colapsa al cargar
    sidebar.addEventListener('mouseenter', function () {
      sidebar.classList.remove('sidebar-collapsed');
    });
    sidebar.addEventListener('mouseleave', function () {
      sidebar.classList.add('sidebar-collapsed');
      // No cierres los submenús aquí
    });
  });
  
document.addEventListener('DOMContentLoaded', function () {
  const sidebar = document.getElementById('sidebar');
  // Colapsar por defecto al cargar
  sidebar.classList.add('sidebar-collapsed');
  // Expandir al pasar el mouse
  sidebar.addEventListener('mouseenter', function () {
    sidebar.classList.remove('sidebar-collapsed');
  });
  // Colapsar al salir el mouse y cerrar submenús
  sidebar.addEventListener('mouseleave', function () {
    sidebar.classList.add('sidebar-collapsed');
  });
  // Colapsar/expandir con la tecla "S"
  document.addEventListener('keydown', function(e) {
    if (e.key === 's' || e.key === 'S') {
      sidebar.classList.toggle('sidebar-collapsed');
    }
  });
  // Activar visualmente el enlace seleccionado
  document.querySelectorAll('.sidebar .nav-link').forEach(link => {
    link.addEventListener('click', function () {
      document.querySelectorAll('.sidebar .nav-link').forEach(l => l.classList.remove('active'));
      this.classList.add('active');
    });
  });
 
});
