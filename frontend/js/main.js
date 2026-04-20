// =====================================================
//  FUNCIONES COMPARTIDAS - Intercambios Académicos
// =====================================================

// Datos de convocatorias de ejemplo (simulando la base de datos)
const convocatorias = [
  {
    id: 1,
    titulo: "Intercambio Universidad de Barcelona",
    universidad: "Universidad de Barcelona",
    pais: "España",
    descripcion: "Programa semestral para estudiantes de tecnología e ingeniería con enfoque en innovación digital.",
    requisitos: "Promedio mínimo 3.5, inglés B2, paz y salvo académico.",
    fecha_inicio: "2026-07-01",
    fecha_cierre: "2026-05-15",
    cupos: 5,
    estado: "activa"
  },
  {
    id: 2,
    titulo: "Pasantía Universidad Nacional de México (UNAM)",
    universidad: "Universidad Nacional Autónoma de México",
    pais: "México",
    descripcion: "Intercambio académico enfocado en desarrollo de software y ciencias de la computación.",
    requisitos: "Promedio mínimo 3.8, haber cursado al menos 5 semestres.",
    fecha_inicio: "2026-08-01",
    fecha_cierre: "2026-06-01",
    cupos: 3,
    estado: "activa"
  },
  {
    id: 3,
    titulo: "Convenio Universidad de São Paulo",
    universidad: "Universidade de São Paulo",
    pais: "Brasil",
    descripcion: "Programa de un año completo con enfoque en investigación y desarrollo tecnológico.",
    requisitos: "Promedio mínimo 4.0, inglés o portugués B1.",
    fecha_inicio: "2027-01-01",
    fecha_cierre: "2026-09-30",
    cupos: 2,
    estado: "proximamente"
  },
  {
    id: 4,
    titulo: "Intercambio Instituto Tecnológico de Monterrey",
    universidad: "Instituto Tecnológico de Monterrey",
    pais: "México",
    descripcion: "Semestre académico en uno de los campus del Tecnológico de Monterrey.",
    requisitos: "Promedio mínimo 3.6, sin materias reprobadas.",
    fecha_inicio: "2026-02-01",
    fecha_cierre: "2025-12-01",
    cupos: 4,
    estado: "cerrada"
  }
];

// Postulaciones de ejemplo (simulando datos del usuario logueado)
const miPostulacion = [
  {
    convocatoria: "Intercambio Universidad de Barcelona",
    universidad: "Universidad de Barcelona",
    pais: "España",
    fecha_postulacion: "2026-04-10",
    estado: "en_revision",
    comentario: ""
  }
];

// Mapeo de estados a badges
function getBadge(estado) {
  const mapa = {
    "activa":      { clase: "badge-verde",    texto: "Activa" },
    "cerrada":     { clase: "badge-rojo",     texto: "Cerrada" },
    "proximamente":{ clase: "badge-amarillo", texto: "Próximamente" },
    "en_revision": { clase: "badge-amarillo", texto: "En revisión" },
    "aprobada":    { clase: "badge-verde",    texto: "Aprobada" },
    "rechazada":   { clase: "badge-rojo",     texto: "Rechazada" }
  };
  const info = mapa[estado] || { clase: "badge-azul", texto: estado };
  return `<span class="badge ${info.clase}">${info.texto}</span>`;
}

// Formatear fechas a formato legible en español
function formatFecha(fecha) {
  const opciones = { year: 'numeric', month: 'long', day: 'numeric' };
  return new Date(fecha + 'T00:00:00').toLocaleDateString('es-CO', opciones);
}

// Simular envío de formulario con alerta de éxito
function simularEnvio(mensajeExito, redirigir) {
  const btn = document.querySelector('.btn-submit');
  if (btn) {
    btn.disabled = true;
    btn.textContent = 'Enviando...';
  }
  setTimeout(() => {
    alert(mensajeExito);
    if (redirigir) window.location.href = redirigir;
  }, 800);
}

// Marcar link activo en la navegación
function marcarNavActivo() {
  const actual = window.location.pathname.split('/').pop();
  document.querySelectorAll('.nav-links a').forEach(link => {
    if (link.getAttribute('href') === actual) {
      link.classList.add('activo');
    }
  });
}

document.addEventListener('DOMContentLoaded', marcarNavActivo);
