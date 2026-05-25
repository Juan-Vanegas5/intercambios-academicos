// =====================================================
//  CONFIGURACIÓN Y UTILIDADES - Intercambios Académicos
// =====================================================

const BASE_URL = "http://18.217.178.92:8001";

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
        "activa":                 { clase: "badge-verde",    texto: "Activa" },
        "cerrada":                { clase: "badge-rojo",     texto: "Cerrada" },
        "proximamente":           { clase: "badge-amarillo", texto: "Próximamente" },
        "en_revision":            { clase: "badge-amarillo", texto: "En revisión" },
        "revisando_documentos":   { clase: "badge-azul",     texto: "Revisando docs" },
        "necesita_correcciones":  { clase: "badge-amarillo", texto: "Necesita correcciones" },
        "aprobada":               { clase: "badge-verde",    texto: "Aprobada" },
        "rechazada":              { clase: "badge-rojo",     texto: "Rechazada" }
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
        // Ocultar pestañas de estudiante cuando el usuario es admin
        if (u.rol === "administrador") {
            ["Postularme", "Mis Postulaciones"].forEach(texto => {
                const a = [...links.querySelectorAll("a")].find(el => el.textContent.trim() === texto);
                if (a) a.parentElement.remove();
            });
        }

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
    iniciarNotificaciones();
});

// =====================================================
//  SISTEMA DE NOTIFICACIONES
// =====================================================

// Cache para admin (notificaciones vienen del backend)
let _notifCache = null;

function _esAdmin() {
    const u = getUsuario();
    return u && u.rol === "administrador";
}

function _claveNotif() {
    const u = getUsuario();
    return u ? `notificaciones_${u.email}` : null;
}

function guardarNotificacion(tipo, mensaje, destinatarioEmail) {
    const clave = `notificaciones_${destinatarioEmail}`;
    const lista = JSON.parse(localStorage.getItem(clave) || "[]");
    lista.unshift({ id: Date.now(), tipo, mensaje, leida: false, fecha: new Date().toISOString() });
    if (lista.length > 30) lista.pop();
    localStorage.setItem(clave, JSON.stringify(lista));
}

function obtenerNotificaciones() {
    if (_esAdmin()) return _notifCache || [];
    const clave = _claveNotif();
    if (!clave) return [];
    return JSON.parse(localStorage.getItem(clave) || "[]");
}

async function _cargarNotificacionesAdmin() {
    try {
        const data = await apiFetch("/api/admin/notificaciones", { headers: authHeaders() });
        _notifCache = data || [];
        actualizarContadorNotif();
    } catch (_) { /* silencioso si la sesión expira */ }
}

async function marcarTodasLeidas() {
    if (_esAdmin()) {
        try {
            await apiFetch("/api/admin/notificaciones/leidas", { method: "PUT", headers: authHeaders() });
            if (_notifCache) _notifCache = _notifCache.map(n => ({ ...n, leida: true }));
        } catch (_) {}
    } else {
        const clave = _claveNotif();
        if (!clave) return;
        const lista = obtenerNotificaciones().map(n => ({ ...n, leida: true }));
        localStorage.setItem(clave, JSON.stringify(lista));
    }
    actualizarContadorNotif();
}

function limpiarNotificaciones() {
    if (!_esAdmin()) {
        const clave = _claveNotif();
        if (!clave) return;
        localStorage.removeItem(clave);
        _notifCache = null;
    }
    actualizarContadorNotif();
    const lista = document.getElementById("notif-lista");
    if (lista) lista.innerHTML = `<p style="color:#9ca3af;font-size:0.9rem;text-align:center;padding:1rem;">No tienes notificaciones.</p>`;
}

function actualizarContadorNotif() {
    const badge = document.getElementById("notif-badge");
    if (!badge) return;
    const noLeidas = obtenerNotificaciones().filter(n => !n.leida).length;
    if (noLeidas > 0) {
        badge.textContent = noLeidas > 9 ? "9+" : noLeidas;
        badge.style.display = "flex";
    } else {
        badge.style.display = "none";
    }
}

function togglePanelNotif(e) {
    e.stopPropagation();
    const panel = document.getElementById("notif-panel");
    const abierto = panel.style.display === "block";
    if (abierto) {
        panel.style.display = "none";
    } else {
        renderNotificaciones();
        panel.style.display = "block";
        marcarTodasLeidas();
    }
}

function renderNotificaciones() {
    const lista = obtenerNotificaciones();
    const contenedor = document.getElementById("notif-lista");
    if (!contenedor) return;

    if (lista.length === 0) {
        contenedor.innerHTML = `<p style="color:#9ca3af;font-size:0.9rem;text-align:center;padding:1rem;">No tienes notificaciones.</p>`;
        return;
    }

    const iconos = { postulacion: "📋", documento: "📎", comentario: "💬", estado: "🔔" };

    contenedor.innerHTML = lista.map(n => `
        <div style="display:flex;gap:0.6rem;padding:0.75rem 0;border-bottom:1px solid #f3f4f6;${!n.leida ? 'background:#eff6ff;margin:0 -1rem;padding:0.75rem 1rem;' : ''}">
            <span style="font-size:1.2rem;">${iconos[n.tipo] || "🔔"}</span>
            <div style="flex:1;">
                <p style="margin:0;font-size:0.88rem;color:#374151;">${n.mensaje}</p>
                <span style="font-size:0.75rem;color:#9ca3af;">${formatFecha(n.fecha)}</span>
            </div>
        </div>
    `).join("");
}

function iniciarNotificaciones() {
    const u = getUsuario();
    if (!u) return;

    const nav = document.querySelector(".nav-links");
    if (!nav) return;

    const li = document.createElement("li");
    li.style.cssText = "position:relative;";
    li.innerHTML = `
        <button id="notif-btn" onclick="togglePanelNotif(event)"
            style="background:none;border:none;cursor:pointer;font-size:1.3rem;position:relative;padding:0.2rem 0.4rem;line-height:1;">
            🔔
            <span id="notif-badge" style="display:none;position:absolute;top:-4px;right:-4px;background:#dc2626;color:white;border-radius:50%;width:18px;height:18px;font-size:0.65rem;font-weight:700;align-items:center;justify-content:center;">0</span>
        </button>
        <div id="notif-panel" style="display:none;position:absolute;right:0;top:calc(100% + 8px);width:320px;background:white;border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,0.15);z-index:999;border:1px solid #e5e7eb;">
            <div style="display:flex;justify-content:space-between;align-items:center;padding:0.85rem 1rem;border-bottom:1px solid #e5e7eb;">
                <strong style="color:#1a3a6b;font-size:0.95rem;">Notificaciones</strong>
                <button onclick="limpiarNotificaciones()" style="background:none;border:none;font-size:0.75rem;color:#9ca3af;cursor:pointer;">Limpiar</button>
            </div>
            <div id="notif-lista" style="max-height:340px;overflow-y:auto;padding:0 1rem;"></div>
        </div>
    `;
    nav.appendChild(li);

    document.addEventListener("click", () => {
        const panel = document.getElementById("notif-panel");
        if (panel) panel.style.display = "none";
    });

    if (_esAdmin()) {
        _cargarNotificacionesAdmin();
        setInterval(_cargarNotificacionesAdmin, 30000);
    } else {
        actualizarContadorNotif();
    }
}
