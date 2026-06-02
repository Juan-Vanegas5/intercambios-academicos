// =====================================================
//  CONFIGURACIÓN Y UTILIDADES - Intercambios Académicos
// =====================================================

const BASE_URL = "https://api.intercambiosupc.lat";

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
        const msg = Array.isArray(err.detail)
            ? err.detail.map(e => e.msg || JSON.stringify(e)).join(", ")
            : (err.detail || "Error en la petición");
        throw new Error(msg);
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
        "rechazada":          { clase: "badge-rojo",     texto: "Rechazada" },
        "revisando_documentos":{ clase: "badge-azul",    texto: "Revisando docs" },
        "necesita_correcciones":{ clase: "badge-amarillo",texto: "Necesita corrección" },
        "docs_pendientes":     { clase: "badge-amarillo", texto: "Docs pendientes" },
        "docs_viaje_enviados": { clase: "badge-azul",    texto: "Docs viaje enviados" },
        "completada":          { clase: "badge-verde",   texto: "Completada ✓" }
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

// ---- Notificaciones (campanita) ----
async function cargarNotificaciones() {
    if (!getToken()) return;
    try {
        const data = await apiFetch("/api/notificaciones/no-leidas", { headers: authHeaders() });
        const badge = document.getElementById("notif-badge");
        if (badge && data.no_leidas > 0) {
            badge.textContent = data.no_leidas;
            badge.style.display = "inline-block";
        } else if (badge) {
            badge.style.display = "none";
        }
    } catch (e) { /* silenciar */ }
}

async function toggleNotificaciones() {
    const panel = document.getElementById("notif-panel");
    if (!panel) return;
    if (panel.style.display === "block") { panel.style.display = "none"; return; }

    panel.innerHTML = '<p style="padding:1rem;color:#6b7280;font-size:0.85rem;">Cargando...</p>';
    panel.style.display = "block";

    try {
        const notifs = await apiFetch("/api/notificaciones", { headers: authHeaders() });
        if (notifs.length === 0) {
            panel.innerHTML = '<p style="padding:1rem;color:#6b7280;font-size:0.85rem;">No tienes notificaciones.</p>';
            return;
        }
        panel.innerHTML = `
            <div style="display:flex;justify-content:space-between;align-items:center;padding:0.6rem 0.9rem;border-bottom:1px solid #e5e7eb;">
                <strong style="font-size:0.85rem;color:#1a3a6b;">Notificaciones</strong>
                <a href="#" onclick="marcarTodasLeidas();return false;" style="font-size:0.75rem;color:#2563eb;">Marcar todas leídas</a>
            </div>
            ${notifs.map(n => `
                <div onclick="marcarLeida(${n.id},this)" style="padding:0.6rem 0.9rem;border-bottom:1px solid #f3f4f6;cursor:pointer;background:${n.leida ? 'white' : '#eff6ff'};font-size:0.83rem;transition:background 0.15s;">
                    <div style="color:#374151;">${n.mensaje}</div>
                    <div style="color:#9ca3af;font-size:0.75rem;margin-top:0.2rem;">${formatFecha(n.fecha)}</div>
                </div>
            `).join("")}
        `;
    } catch (e) {
        panel.innerHTML = '<p style="padding:1rem;color:#dc2626;font-size:0.85rem;">Error al cargar notificaciones.</p>';
    }
}

async function marcarLeida(id, el) {
    try {
        await apiFetch(`/api/notificaciones/${id}/leer`, { method: "PUT", headers: authHeaders() });
        if (el) el.style.background = "white";
        cargarNotificaciones();
    } catch (e) { /* silenciar */ }
}

async function marcarTodasLeidas() {
    try {
        await apiFetch("/api/notificaciones/leer-todas", { method: "PUT", headers: authHeaders() });
        cargarNotificaciones();
        toggleNotificaciones();
    } catch (e) { /* silenciar */ }
}

function inyectarCampanita() {
    const u = getUsuario();
    if (!u) return;
    const nav = document.querySelector(".nav-links");
    if (!nav || document.getElementById("notif-bell")) return;

    const li = document.createElement("li");
    li.style.position = "relative";
    li.innerHTML = `
        <a href="#" id="notif-bell" onclick="toggleNotificaciones();return false;" style="position:relative;font-size:1.2rem;padding:0.3rem 0.5rem;">
            🔔<span id="notif-badge" style="display:none;position:absolute;top:-4px;right:-4px;background:#dc2626;color:white;font-size:0.65rem;font-weight:700;padding:1px 5px;border-radius:999px;"></span>
        </a>
        <div id="notif-panel" style="display:none;position:absolute;right:0;top:100%;width:320px;max-height:400px;overflow-y:auto;background:white;border-radius:10px;box-shadow:0 4px 20px rgba(0,0,0,0.15);z-index:200;margin-top:0.5rem;"></div>
    `;
    // Insertar antes del último elemento (Cerrar Sesión)
    const items = nav.querySelectorAll("li");
    if (items.length > 0) {
        nav.insertBefore(li, items[items.length - 1]);
    } else {
        nav.appendChild(li);
    }
}

// Cerrar panel al hacer clic fuera
document.addEventListener("click", (e) => {
    const panel = document.getElementById("notif-panel");
    const bell = document.getElementById("notif-bell");
    if (panel && panel.style.display === "block" && !panel.contains(e.target) && e.target !== bell) {
        panel.style.display = "none";
    }
});

document.addEventListener("DOMContentLoaded", () => {
    marcarNavActivo();
    actualizarNav();
    inyectarCampanita();
    cargarNotificaciones();
});
