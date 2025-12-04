document.addEventListener("DOMContentLoaded", () => {
    // 1. OBTENER ELEMENTOS PRINCIPALES
    const sidebarContainer = document.getElementById("sidebar-container");
    const mainContent = document.querySelector('main');
    const body = document.body;

    // Usuario actual
    const user = sessionStorage.getItem('user') || 'Admin';

    // 2. DEFINICIÓN DE MÓDULOS (Links)
    const menuItems = [
        { name: "Dashboard", link: "/static/index.html", icon: "fas fa-chart-line" },
        { name: "Cotizador", link: "/static/cotizador.html", icon: "fas fa-cash-register" },
        { name: "CRM & Clientes", link: "/static/clientes.html", icon: "fas fa-users" },
        { name: "Inventario", link: "/static/inventario.html", icon: "fas fa-boxes" },
    ];

    const path = window.location.pathname;
    let linksHtml = "";

    menuItems.forEach(item => {
        const isActive = path.includes(item.link);
        const activeClass = "bg-blue-600 text-white shadow-md transform translate-x-1";
        const inactiveClass = "text-gray-400 hover:bg-gray-800 hover:text-white";

        linksHtml += `
            <a href="${item.link}" class="flex items-center gap-4 p-3 mb-2 rounded-lg transition-all duration-200 ${isActive ? activeClass : inactiveClass}">
                <i class="${item.icon} w-6 text-center"></i>
                <span class="font-medium">${item.name}</span>
            </a>
        `;
    });

    // 3. HTML DEL SIDEBAR (Usuario Abajo)
    const sidebarHtml = `
        <aside class="w-64 bg-slate-900 text-white flex flex-col h-screen fixed left-0 top-0 shadow-2xl z-50 font-sans">
            <div class="h-16 flex items-center px-6 border-b border-gray-700 bg-slate-950">
                <i class="fas fa-layer-group text-blue-500 text-2xl mr-3"></i>
                <div>
                    <h1 class="font-bold text-lg tracking-wide">DASIC</h1>
                    <p class="text-[10px] text-gray-400 uppercase tracking-widest">ERP System</p>
                </div>
            </div>

            <nav class="flex-1 overflow-y-auto p-4 space-y-1">
                ${linksHtml}
            </nav>

            <div class="p-4 border-t border-gray-700 bg-slate-950">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg shadow">
                        ${user.charAt(0).toUpperCase()}
                    </div>
                    <div>
                        <p class="text-sm font-bold text-white">${user}</p>
                        <p class="text-xs text-green-400 flex items-center gap-1">
                            <span class="w-2 h-2 bg-green-500 rounded-full"></span> En línea
                        </p>
                    </div>
                </div>
            </div>
        </aside>
    `;

    // 4. HTML DEL HEADER (Botones Tema y Salir)
    const headerHtml = `
        <header class="h-16 bg-white shadow-sm fixed top-0 right-0 left-64 z-40 flex justify-between items-center px-6 transition-colors duration-300 dark:bg-slate-800 dark:border-b dark:border-slate-700">
            <h2 class="text-xl font-bold text-gray-700 dark:text-gray-200">
                ${menuItems.find(i => path.includes(i.link))?.name || 'Dasic ERP'}
            </h2>

            <div class="flex items-center gap-4">
                <button onclick="toggleTheme()" class="p-2 rounded-full text-gray-500 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-slate-700 transition" title="Cambiar Tema">
                    <i class="fas fa-moon" id="theme-icon"></i>
                </button>
                
                <div class="h-6 w-px bg-gray-300 dark:bg-slate-600"></div>

                <button onclick="logout()" class="flex items-center gap-2 text-red-500 hover:text-red-700 font-medium text-sm px-3 py-1 rounded hover:bg-red-50 transition">
                    <i class="fas fa-sign-out-alt"></i> Salir
                </button>
            </div>
        </header>
    `;

    // 5. HTML DEL FOOTER (Powered By + Reloj)
    const footerHtml = `
        <footer class="fixed bottom-0 right-0 left-64 bg-white border-t border-gray-200 p-2 px-6 flex justify-between items-center text-xs text-gray-500 z-40 dark:bg-slate-800 dark:border-slate-700 dark:text-gray-400">
            <div class="flex items-center gap-1">
                <span>Powered by</span>
                <span class="font-bold text-slate-700 dark:text-white flex items-center gap-1">
                    <i class="fas fa-bolt text-yellow-500"></i> SMART SITE
                </span>
            </div>
            <div class="font-mono font-bold" id="live-clock">--:--:--</div>
        </footer>
    `;

    // 6. INYECTAR Y AJUSTAR LAYOUT
    if (sidebarContainer) {
        sidebarContainer.innerHTML = sidebarHtml;
        
        // Inyectar Header antes del Main
        const headerDiv = document.createElement('div');
        headerDiv.innerHTML = headerHtml;
        document.body.insertBefore(headerDiv.firstElementChild, mainContent);

        // Inyectar Footer al final del Body
        const footerDiv = document.createElement('div');
        footerDiv.innerHTML = footerHtml;
        document.body.appendChild(footerDiv.firstElementChild);

        // Ajustar márgenes del contenido principal para que no quede tapado
        if (mainContent) {
            mainContent.classList.add('ml-64', 'mt-16', 'mb-8', 'dark:bg-slate-900'); // Margen Izq, Top y Bottom
            mainContent.style.minHeight = "calc(100vh - 4rem)"; // Altura completa menos header
        }
    }

    // 7. INICIAR RELOJ
    startClock();
    
    // 8. CARGAR TEMA PREVIO
    if(localStorage.getItem('theme') === 'dark') {
        document.documentElement.classList.add('dark');
        const icon = document.getElementById('theme-icon');
        if(icon) { icon.classList.remove('fa-moon'); icon.classList.add('fa-sun'); }
    }
});

// --- FUNCIONES GLOBALES ---

function logout() {
    if(confirm("¿Cerrar sesión?")) {
        sessionStorage.removeItem('token');
        window.location.href = '/static/login.html';
    }
}

function toggleTheme() {
    const html = document.documentElement;
    const icon = document.getElementById('theme-icon');
    
    if (html.classList.contains('dark')) {
        html.classList.remove('dark');
        localStorage.setItem('theme', 'light');
        if(icon) { icon.classList.remove('fa-sun'); icon.classList.add('fa-moon'); }
    } else {
        html.classList.add('dark');
        localStorage.setItem('theme', 'dark');
        if(icon) { icon.classList.remove('fa-moon'); icon.classList.add('fa-sun'); }
    }
}

function startClock() {
    function update() {
        const el = document.getElementById('live-clock');
        if (el) {
            const now = new Date();
            el.innerText = now.toLocaleDateString() + ' ' + now.toLocaleTimeString();
        }
    }
    setInterval(update, 1000);
    update();
}