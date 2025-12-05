document.addEventListener("DOMContentLoaded", () => {
    // 1. OBTENER ELEMENTOS PRINCIPALES
    const sidebarContainer = document.getElementById("sidebar-container");
    const mainContent = document.querySelector('main');

    // 2. OBTENER USUARIO DEL TOKEN (Lógica FastAPI)
    let user = 'Admin';
    const token = localStorage.getItem('token');
    if (token) {
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            user = payload.sub.split('@')[0]; // Toma el nombre antes del @
        } catch (e) {
            console.error("Error leyendo usuario del token");
        }
    }

    // 3. DEFINICIÓN DE MÓDULOS (Rutas FastAPI)
    const menuItems = [
        { name: "Dashboard", link: "/dashboard", icon: "fas fa-chart-line" },
        { name: "Cotizador", link: "/ventas/cotizador", icon: "fas fa-cash-register" }, // Ajustaremos estas rutas luego
        { name: "Clientes", link: "/clientes", icon: "fas fa-users" },
        { name: "Inventario", link: "/inventario", icon: "fas fa-boxes" },
        { name: "Compras", link: "/compras", icon: "fas fa-truck" },
    ];

    const path = window.location.pathname;
    let linksHtml = "";

    menuItems.forEach(item => {
        // Lógica para marcar activo (si la URL contiene el link)
        const isActive = path === item.link || path.startsWith(item.link); 
        const activeClass = "bg-blue-600 text-white shadow-md transform translate-x-1";
        const inactiveClass = "text-gray-400 hover:bg-gray-800 hover:text-white";

        linksHtml += `
            <a href="${item.link}" class="flex items-center gap-4 p-3 mb-2 rounded-lg transition-all duration-200 ${isActive ? activeClass : inactiveClass}">
                <i class="${item.icon} w-6 text-center"></i>
                <span class="font-medium">${item.name}</span>
            </a>
        `;
    });

    // 4. HTML DEL SIDEBAR (Tu diseño original restaurado)
    const sidebarHtml = `
        <aside class="w-64 bg-slate-900 text-white flex flex-col h-screen fixed left-0 top-0 shadow-2xl z-50 font-sans transition-all duration-300 border-r border-slate-800">
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
                    <div class="overflow-hidden">
                        <p class="text-sm font-bold text-white truncate w-32" title="${user}">${user}</p>
                        <p class="text-xs text-green-400 flex items-center gap-1">
                            <span class="w-2 h-2 bg-green-500 rounded-full"></span> En línea
                        </p>
                    </div>
                </div>
            </div>
        </aside>
    `;

    // 5. HTML DEL HEADER (Con Tema y Botón de Salir)
    const currentPageName = menuItems.find(i => path.includes(i.link))?.name || 'Panel Principal';
    
    const headerHtml = `
        <header class="h-16 bg-white shadow-sm fixed top-0 right-0 left-64 z-40 flex justify-between items-center px-6 transition-all duration-300 dark:bg-slate-800 dark:border-b dark:border-slate-700">
            <h2 class="text-xl font-bold text-gray-700 dark:text-gray-200 capitalize">
                ${currentPageName}
            </h2>

            <div class="flex items-center gap-4">
                <button onclick="toggleTheme()" class="p-2 rounded-full text-gray-500 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-slate-700 transition" title="Cambiar Tema">
                    <i class="fas fa-moon" id="theme-icon"></i>
                </button>
                
                <div class="h-6 w-px bg-gray-300 dark:bg-slate-600"></div>

                <button onclick="logout()" class="flex items-center gap-2 text-red-500 hover:text-red-700 font-medium text-sm px-3 py-1 rounded hover:bg-red-50 transition dark:hover:bg-slate-700">
                    <i class="fas fa-sign-out-alt"></i> Salir
                </button>
            </div>
        </header>
    `;

    // 6. HTML DEL FOOTER (Restaurado Smart Site + Reloj)
    const footerHtml = `
        <footer class="fixed bottom-0 right-0 left-64 bg-white border-t border-gray-200 p-2 px-6 flex justify-between items-center text-xs text-gray-500 z-40 dark:bg-slate-800 dark:border-slate-700 dark:text-gray-400 transition-all duration-300">
            <div class="flex items-center gap-1">
                <span>Powered by</span>
                <span class="font-bold text-slate-700 dark:text-white flex items-center gap-1">
                    <i class="fas fa-bolt text-yellow-500"></i> Smart Site Company SAS de CV 
                </span>
            </div>
            <div class="font-mono font-bold" id="live-clock">--:--:--</div>
        </footer>
    `;

    // 7. INYECCIÓN EN EL DOM
    if (sidebarContainer) {
        sidebarContainer.innerHTML = sidebarHtml;
        
        // Inyectar Header
        const headerDiv = document.createElement('div');
        headerDiv.innerHTML = headerHtml;
        document.body.insertBefore(headerDiv.firstElementChild, document.body.firstChild);

        // Inyectar Footer
        const footerDiv = document.createElement('div');
        footerDiv.innerHTML = footerHtml;
        document.body.appendChild(footerDiv.firstElementChild);

        // Ajustar Main para que no quede debajo
        if (mainContent) {
            mainContent.classList.add('ml-64', 'mt-16', 'mb-10', 'p-6', 'transition-all', 'duration-300', 'dark:bg-slate-900'); 
            mainContent.style.minHeight = "calc(100vh - 4rem)";
        }
    }

    // 8. INICIAR RELOJ Y TEMA
    startClock();
    
    // Cargar tema previo
    if(localStorage.getItem('theme') === 'dark') {
        document.documentElement.classList.add('dark');
        const icon = document.getElementById('theme-icon');
        if(icon) { icon.classList.remove('fa-moon'); icon.classList.add('fa-sun'); }
    }
});

// --- FUNCIONES GLOBALES ---

function logout() {
    if(confirm("¿Cerrar sesión en DASIC ERP?")) {
        localStorage.removeItem('token');
        window.location.href = '/'; 
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
            // Formato amigable: 05/12/2025 10:30:45 AM
            el.innerText = now.toLocaleDateString() + ' ' + now.toLocaleTimeString();
        }
    }
    setInterval(update, 1000);
    update();
}