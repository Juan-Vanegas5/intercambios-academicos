// =====================================================
//  CONFIGURACIÓN Y UTILIDADES - Intercambios Académicos
// =====================================================

const BASE_URL = "http://18.191.193.192:8001";

// ---- Manejo de sesión ----
function getToken()   { return localStorage.getItem("token"); }
function getUsuario() { return JSON.parse(localStorage.getItem("usuario") || "null"); }

function setSession(token, usuario) {
    localStorage.setItem("token", token);
    localStorage.setItem("usuario", JSON.stringify(usuario));
}

function cerrarSesion() {
    localStorage.removeItem("token");
    localStorage.removeItem("usuario");
    const esAdmin = window.location.pathname.includes("/admin/");
    window.location.href = esAdmin ? "../login.html" : "login.html";
}

function requireAuth() {
    if (!getToken()) {
        window.location.href = "login.html";
    }
}

function requireAdmin() {
    const u = getUsuario();
    if (!u || u.rol !== "administrador") {
        window.location.href = "../login.html";
    }
}

// ---- Peticiones a la API ----
function authHeaders() {
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getToken()}`
    };
}

async function apiFetch(url, options = {}) {
    const res = await fetch(BASE_URL + url, options);
    if (res.status === 401) { cerrarSesion(); return null; }
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "Error en la petición");
    }
    return res.json();
}

// ---- Helpers visuales ----
function getBadge(estado) {
    const mapa = {
        "activa":        { clase: "badge-verde",    texto: "Activa" },
        "cerrada":       { clase: "badge-rojo",     texto: "Cerrada" },
        "proximamente":  { clase: "badge-amarillo", texto: "Próximamente" },
        "en_revision":   { clase: "badge-amarillo", texto: "En revisión" },
        "aprobada":      { clase: "badge-verde",    texto: "Aprobada" },
        "rechazada":     { clase: "badge-rojo",     texto: "Rechazada" }
    };
    const info = mapa[estado] || { clase: "badge-azul", texto: estado };
    return `<span class="badge ${info.clase}">${info.texto}</span>`;
}

function formatFecha(fecha) {
    if (!fecha) return "—";
    return new Date(fecha).toLocaleDateString("es-CO", {
        year: "numeric", month: "long", day: "numeric"
    });
}

function mostrarError(contenedor, msg) {
    contenedor.className = "alerta alerta-error";
    contenedor.textContent = msg;
}

function marcarNavActivo() {
    const actual = window.location.pathname.split("/").pop();
    document.querySelectorAll(".nav-links a").forEach(link => {
        if (link.getAttribute("href") === actual) link.classList.add("activo");
    });
}

function actualizarNav() {
    const u = getUsuario();
    const links = document.querySelector(".nav-links");
    if (!links) return;

    if (u) {
        // Reemplazar "Iniciar Sesión" si existe
        const loginLink = [...links.querySelectorAll("a")]
            .find(a => a.textContent.trim() === "Iniciar Sesión");
        if (loginLink) {
            const li = loginLink.parentElement;
            li.innerHTML = `<span style="color:#1a3a6b;font-weight:600;">${u.nombre}</span>&nbsp;&nbsp;<a href="#" onclick="cerrarSesion()">Cerrar Sesión</a>`;
        }

        // Agregar nombre antes de "Cerrar Sesión" si ya existe y no tiene nombre
        const logoutLink = [...links.querySelectorAll("a")]
            .find(a => a.textContent.trim() === "Cerrar Sesión");
        if (logoutLink && !logoutLink.parentElement.querySelector("span")) {
            const span = document.createElement("span");
            span.style.cssText = "color:#1a3a6b;font-weight:600;margin-right:0.75rem;";
            span.textContent = u.nombre;
            logoutLink.parentElement.insertBefore(span, logoutLink);
        }
    }
}

document.addEventListener("DOMContentLoaded", () => {
    marcarNavActivo();
    actualizarNav();
});

// =====================================================
//  SISTEMA DE NOTIFICACIONES — campanita navbar
// =====================================================

const NOTIF_POLL_MS = 30000; // refresca cada 30 s
let _notifTimer = null;

/**
 * Determina la URL de destino según el campo `url` de la notificación
 * y la ubicación actual del archivo HTML.
 */
function _resolverUrlNotif(notif) {
  if (!notif.url) return null;
  const esAdmin = window.location.pathname.includes("/admin/");
  // El backend guarda rutas relativas desde la carpeta pages/
  // Ej.: "seguimiento.html"  →  desde admin/ hay que ir con "../"
  if (esAdmin) {
    // Si la url ya arranca con "../" la usamos tal cual, si no, la prefijamos
    return notif.url.startsWith("..") ? notif.url : "../" + notif.url;
  }
  // Desde pages/ la url es directa
  return notif.url;
}

function _tiempoRelativo(isoFecha) {
  if (!isoFecha) return "";
  const diff = Date.now() - new Date(isoFecha).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1)  return "ahora mismo";
  if (m < 60) return `hace ${m} min`;
  const h = Math.floor(m / 60);
  if (h < 24) return `hace ${h} h`;
  return `hace ${Math.floor(h / 24)} día${Math.floor(h/24)>1?"s":""}`;
}

function _renderNotificaciones(lista) {
  const lista_el   = document.getElementById("notif-lista");
  const badge_el   = document.getElementById("notif-badge");
  if (!lista_el) return;

  const noLeidas = lista.filter(n => !n.leida).length;

  // badge
  if (noLeidas > 0) {
    badge_el.textContent = noLeidas > 9 ? "9+" : noLeidas;
    badge_el.style.display = "flex";
  } else {
    badge_el.style.display = "none";
  }

  if (lista.length === 0) {
    lista_el.innerHTML = `<div class="notif-vacia">🔔 No tienes notificaciones</div>`;
    return;
  }

  lista_el.innerHTML = lista.map(n => {
    const url = _resolverUrlNotif(n);
    const claseLeida = n.leida ? "leida" : "no-leida";
    return `
      <div class="notif-item ${claseLeida}" data-id="${n.id}" data-url="${url || ""}">
        <div class="notif-punto"></div>
        <div style="flex:1;">
          <div class="notif-texto">${n.mensaje}</div>
          <span class="notif-fecha">${_tiempoRelativo(n.fecha)}</span>
        </div>
      </div>
    `;
  }).join("");

  // click en cada notificación
  lista_el.querySelectorAll(".notif-item").forEach(el => {
    el.addEventListener("click", async (e) => {
      e.stopPropagation();
      const id  = el.dataset.id;
      const url = el.dataset.url;

      // marcar como leída en el servidor
      try {
        await fetch(BASE_URL + `/api/notificaciones/${id}/leer`, {
          method: "PUT",
          headers: authHeaders()
        });
      } catch (_) {}

      // cerrar dropdown
      _cerrarNotifDropdown();

      // navegar si hay url
      if (url && url.trim() !== "") {
        window.location.href = url;
      } else {
        await _cargarNotificaciones();
      }
    });
  });
}

async function _cargarNotificaciones() {
  if (!getToken()) return;
  try {
    const lista = await apiFetch("/api/notificaciones", { headers: authHeaders() });
    if (lista) _renderNotificaciones(lista);
  } catch (_) {}
}

function _abrirNotifDropdown() {
  const dd = document.getElementById("notif-dropdown");
  if (!dd) return;
  dd.classList.toggle("abierto");
}

function _cerrarNotifDropdown() {
  const dd = document.getElementById("notif-dropdown");
  if (dd) dd.classList.remove("abierto");
}

async function _marcarTodasLeidas() {
  try {
    await apiFetch("/api/notificaciones/leer-todas", {
      method: "PUT",
      headers: authHeaders()
    });
    await _cargarNotificaciones();
  } catch (_) {}
}

/**
 * Inyecta la campanita en el <nav> y arranca el polling.
 * Se llama desde actualizarNav() cuando hay sesión activa.
 */
function _inyectarCampanita() {
  if (document.getElementById("notif-btn")) return; // ya existe

  const nav = document.querySelector("nav");
  if (!nav) return;

  const wrapper = document.createElement("div");
  wrapper.className = "notif-wrapper";
  wrapper.innerHTML = `
    <button class="notif-btn" id="notif-btn" title="Notificaciones">
      🔔
      <span class="notif-badge" id="notif-badge" style="display:none;">0</span>
    </button>
    <div class="notif-dropdown" id="notif-dropdown">
      <div class="notif-header">
        <strong>Notificaciones</strong>
        <button class="notif-leer-todas" onclick="_marcarTodasLeidas()">Marcar todas como leídas</button>
      </div>
      <div class="notif-lista" id="notif-lista">
        <div class="notif-vacia">Cargando...</div>
      </div>
    </div>
  `;

  // Insertar antes del primer <li> del nav (junto a los links)
  const navLinks = nav.querySelector(".nav-links");
  if (navLinks) {
    nav.insertBefore(wrapper, navLinks);
  } else {
    nav.appendChild(wrapper);
  }

  // Abrir/cerrar al hacer click en la campanita
  document.getElementById("notif-btn").addEventListener("click", (e) => {
    e.stopPropagation();
    _abrirNotifDropdown();
  });

  // Cerrar al hacer click en CUALQUIER otro lugar de la página
  document.addEventListener("click", () => {
    _cerrarNotifDropdown();
  });

  // Cargar inmediatamente y luego cada 30 s
  _cargarNotificaciones();
  _notifTimer = setInterval(_cargarNotificaciones, NOTIF_POLL_MS);
}

// Sobreescribir actualizarNav para que inyecte la campanita cuando hay sesión
const _actualizarNavOriginal = actualizarNav;
actualizarNav = function() {
  _actualizarNavOriginal();
  if (getToken()) {
    // Pequeño delay para que el DOM del nav ya esté listo
    setTimeout(_inyectarCampanita, 0);
  }
};

// Exponer función al scope global para que funcione el onclick del HTML
window._marcarTodasLeidas = _marcarTodasLeidas;