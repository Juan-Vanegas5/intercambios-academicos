// =====================================================
//  CONFIGURACIÓN Y UTILIDADES - Intercambios Académicos
// =====================================================

const BASE_URL = "http://3.129.193.160:8001";

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
