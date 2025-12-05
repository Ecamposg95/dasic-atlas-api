document.addEventListener("DOMContentLoaded", () => {
    // 1. OBTENER ELEMENTOS PRINCIPALES
    const sidebarContainer = document.getElementById("sidebar-container");
    const mainContent = document.querySelector('main');

    // 2. OBTENER USUARIO DEL TOKEN
    let user = 'Usuario';
    const token = localStorage.getItem('token');
    if (token) {
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            user = payload.sub.split('@')[0]; // Nombre antes del @
        } catch (e) {
            console.error("Error leyendo token");
        }
    }

    // 3. DEFINICIÓN DE MÓDULOS (Rutas actualizadas)
    const menuItems = [
        { header: "Principal" },
        { name: "Dashboard", link: "/dashboard", icon: "fas fa-chart-line" },
        
        { header: "Comercial" },
        { name: "Cotizador", link: "/ventas/cotizador", icon: "fas fa-cash-register" },
        { name: "Seguimiento", link: "/seguimiento", icon: "fas fa-route" },
        
        { header: "Gestión" },
        { name: "Inventario", link: "/inventario", icon: "fas fa-boxes" },
        { name: "Clientes", link: "/clientes", icon: "fas fa-users" },
        { name: "Compras", link: "/compras", icon: "fas fa-truck-loading" },
        
        { header: "Administración" },
        { name: "Gastos", link: "/gastos", icon: "fas fa-file-invoice-dollar" },
        { name: "Reportes", link: "/reportes", icon: "fas fa-chart-pie" },
        { name: "Equipo", link: "/usuarios", icon: "fas fa-user-shield" },
    ];

    const path = window.location.pathname;
    let linksHtml = "";

    // Colores de Marca (Para uso en estilos inline si Tailwind no los tiene)
    const dasicNavy = 'background-color: #001e62;'; 

    menuItems.forEach(item => {
        // Si es un encabezado de sección
        if (item.header) {
            linksHtml += `<div class="px-4 mt-4 mb-2 text-[10px] font-bold text-gray-400 uppercase tracking-wider">${item.header}</div>`;
            return;
        }

        // Lógica de estado activo
        const isActive = path === item.link || path.startsWith(item.link);
        
        // Estilos Dinámicos
        const activeClass = "bg-white/10 text-cyan-400 border-l-4 border-cyan-400 shadow-lg"; 
        const inactiveClass = "text-gray-300 hover:bg-white/5 hover:text-white border-l-4 border-transparent transition-colors";

        linksHtml += `
            <a href="${item.link}" class="flex items-center gap-3 p-3 text-sm font-medium transition-all duration-200 ${isActive ? activeClass : inactiveClass}">
                <i class="${item.icon} w-6 text-center text-lg"></i>
                <span>${item.name}</span>
            </a>
        `;
    });

    // 4. HTML DEL SIDEBAR (Estilo Navy)
    const sidebarHtml = `
        <aside class="w-64 text-white flex flex-col h-screen fixed left-0 top-0 shadow-2xl z-50 font-sans transition-all duration-300" style="${dasicNavy}">
            <div class="h-16 flex items-center px-6 bg-black/20 border-b border-white/10">
                <i class="fas fa-layer-group text-cyan-400 text-2xl mr-3 filter drop-shadow-md"></i>
                <div>
                    <h1 class="font-bold text-xl tracking-wide text-white">DASIC</h1>
                    <p class="text-[9px] text-cyan-200 uppercase tracking-[0.2em] font-semibold">DATAX ERP System</p>
                </div>
            </div>

            <nav class="flex-1 overflow-y-auto py-4 space-y-1 custom-scrollbar">
                ${linksHtml}
            </nav>

            <div class="p-4 bg-black/20 border-t border-white/10">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-white font-bold text-lg shadow-inner border border-white/20">
                        ${user.charAt(0).toUpperCase()}
                    </div>
                    <div class="overflow-hidden">
                        <p class="text-sm font-bold text-white truncate w-32">${user}</p>
                        <div class="flex items-center gap-1.5">
                            <span class="relative flex h-2 w-2">
                              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                              <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                            </span>
                            <span class="text-[10px] text-gray-300">En línea</span>
                        </div>
                    </div>
                </div>
            </div>
        </aside>
    `;

    // 5. HTML DEL HEADER
    const currentPage = menuItems.find(i => !i.header && path.includes(i.link))?.name || 'Panel Principal';
    
    const headerHtml = `
        <header class="h-16 bg-white/90 backdrop-blur-md shadow-sm fixed top-0 right-0 left-64 z-40 flex justify-between items-center px-8 transition-all duration-300 dark:bg-slate-900/90 dark:border-b dark:border-slate-800">
            <h2 class="text-xl font-bold text-slate-800 dark:text-white tracking-tight">
                ${currentPage}
            </h2>

            <div class="flex items-center gap-2">
                <button onclick="toggleTheme()" class="w-10 h-10 rounded-full flex items-center justify-center text-slate-500 hover:bg-slate-100 hover:text-blue-600 dark:text-slate-400 dark:hover:bg-slate-800 transition-all duration-300 focus:outline-none" title="Cambiar Tema">
                    <i class="fas fa-moon text-lg transition-transform duration-500 rotate-0" id="theme-icon"></i>
                </button>
                
                <div class="h-6 w-px bg-slate-200 dark:bg-slate-700 mx-2"></div>

                <button onclick="logout()" class="flex items-center gap-2 text-slate-500 hover:text-red-600 font-medium text-sm px-4 py-2 rounded-full hover:bg-red-50 transition-all duration-200 group dark:hover:bg-red-900/20 dark:hover:text-red-400">
                    <span>Salir</span>
                    <i class="fas fa-sign-out-alt group-hover:translate-x-1 transition-transform"></i>
                </button>
            </div>
        </header>
    `;

    // 6. HTML DEL FOOTER
    const footerHtml = `
        <footer class="fixed bottom-0 right-0 left-64 bg-white border-t border-slate-200 px-6 py-1.5 flex justify-between items-center text-[10px] text-slate-400 z-30 dark:bg-slate-900 dark:border-slate-800">
            <div class="flex items-center gap-1.5 group cursor-default">
                <span>Powered by</span>
                <span class="font-bold text-slate-600 dark:text-slate-300 flex items-center gap-1 group-hover:text-blue-600 transition-colors">
                    <i class="fas fa-bolt text-yellow-500"></i> Smart Site Company SAS de CV
                </span>
            </div>
            <div class="font-mono font-bold tracking-widest text-slate-500" id="live-clock">--:--:--</div>
        </footer>
    `;

    // 7. INYECCIÓN EN EL DOM
    if (sidebarContainer) {
        sidebarContainer.innerHTML = sidebarHtml;
        
        // Inyectar Header al inicio
        const headerDiv = document.createElement('div');
        headerDiv.innerHTML = headerHtml;
        document.body.insertBefore(headerDiv.firstElementChild, document.body.firstChild);

        // Inyectar Footer al final
        const footerDiv = document.createElement('div');
        footerDiv.innerHTML = footerHtml;
        document.body.appendChild(footerDiv.firstElementChild);

        // Ajustar Main para respetar los espacios fijos
        if (mainContent) {
            mainContent.classList.add('ml-64', 'pt-20', 'pb-12', 'px-8', 'min-h-screen', 'transition-all', 'duration-300');
            // Nota: pt-20 = header height + gap, pb-12 = footer height + gap
        }
    }

    // 8. INICIAR FUNCIONES
    startClock();
    initTheme();
});

// --- FUNCIONES GLOBALES ---

function logout() {
    Swal.fire({
        title: '¿Cerrar sesión?',
        text: "Tendrás que ingresar nuevamente.",
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Sí, salir',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            localStorage.removeItem('token');
            window.location.href = '/'; 
        }
    });
}

function initTheme() {
    const icon = document.getElementById('theme-icon');
    if(localStorage.getItem('theme') === 'dark') {
        document.documentElement.classList.add('dark');
        if(icon) {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun', 'text-yellow-400');
        }
    }
}

function toggleTheme() {
    const html = document.documentElement;
    const icon = document.getElementById('theme-icon');
    
    if (html.classList.contains('dark')) {
        html.classList.remove('dark');
        localStorage.setItem('theme', 'light');
        // Cambiar a Luna
        if(icon) { 
            icon.classList.remove('fa-sun', 'text-yellow-400', 'rotate-180'); 
            icon.classList.add('fa-moon', 'rotate-0'); 
        }
    } else {
        html.classList.add('dark');
        localStorage.setItem('theme', 'dark');
        // Cambiar a Sol
        if(icon) { 
            icon.classList.remove('fa-moon', 'rotate-0'); 
            icon.classList.add('fa-sun', 'text-yellow-400', 'rotate-180'); 
        }
    }
}

function startClock() {
    function update() {
        const el = document.getElementById('live-clock');
        if (el) {
            const now = new Date();
            // Formato 24h limpio
            el.innerText = now.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        }
    }
    setInterval(update, 1000);
    update();
}