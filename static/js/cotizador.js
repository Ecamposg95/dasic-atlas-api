// --- ESTADO GLOBAL ---
let inventarioCache = [];
let clientesCache = [];
let carrito = [];
let clienteSeleccionado = null;

// --- INICIALIZACIÓN ---
document.addEventListener('DOMContentLoaded', () => {
    inicializar();
});

async function inicializar() {
    console.log("Iniciando Cotizador...");
    await Promise.all([cargarInventario(), cargarClientes()]);
    actualizarTotalesUI(0, "USD");
}

// --- 1. CARGA DE DATOS ---
async function cargarInventario() {
    try {
        const res = await fetch('/api/inventario/', {
            headers: { 'Authorization': `Bearer ${sessionStorage.getItem('token')}` }
        });
        if (!res.ok) throw new Error("Error API Inventario");
        inventarioCache = await res.json();
        console.log("Inventario cargado:", inventarioCache.length, "items");
        renderGrid(inventarioCache);
    } catch (e) {
        console.error("Error:", e);
        document.getElementById('gridProductos').innerHTML = '<p class="text-center text-red-500 mt-10">Error de conexión</p>';
    }
}

async function cargarClientes() {
    try {
        const res = await fetch('/api/clientes/', {
            headers: { 'Authorization': `Bearer ${sessionStorage.getItem('token')}` }
        });
        if (res.ok) clientesCache = await res.json();
    } catch (e) { console.error("Error clientes:", e); }
}

// --- 2. RENDERIZADO DEL CATÁLOGO ---
function renderGrid(lista) {
    const contenedor = document.getElementById('gridProductos');
    contenedor.innerHTML = '';

    if (lista.length === 0) {
        contenedor.innerHTML = '<p class="col-span-full text-center text-gray-400 mt-10">Sin resultados</p>';
        return;
    }

    lista.forEach(prod => {
        // Fallback imagen
        const imgUrl = (prod.imagen_url && prod.imagen_url.startsWith('http')) ? prod.imagen_url : 'https://placehold.co/400x300/e2e8f0/94a3b8?text=No+Image';
        
        // Stock Badge
        let badgeColor = prod.stock_actual > 0 ? 'bg-green-500' : 'bg-red-500';
        let badgeText = prod.stock_actual > 0 ? `${prod.stock_actual} ud.` : 'Agotado';

        const card = document.createElement('div');
        card.className = "bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-200 dark:border-slate-700 overflow-hidden hover:shadow-xl hover:border-blue-400 dark:hover:border-blue-500 transition-all cursor-pointer group flex flex-col h-[260px]";
        
        // Evento Click -> Agregar
        card.onclick = () => agregarAlCarrito(prod);

        card.innerHTML = `
            <div class="h-32 overflow-hidden relative bg-gray-100 dark:bg-slate-700">
                <img src="${imgUrl}" class="w-full h-full object-cover group-hover:scale-110 transition duration-500">
                <span class="absolute top-2 right-2 ${badgeColor} text-white text-[10px] font-bold px-2 py-0.5 rounded shadow">${badgeText}</span>
            </div>
            <div class="p-3 flex flex-col flex-1 justify-between">
                <div>
                    <h4 class="font-bold text-gray-800 dark:text-white text-sm leading-tight mb-1 truncate" title="${prod.numero_catalogo}">${prod.numero_catalogo}</h4>
                    <p class="text-xs text-gray-500 dark:text-gray-400 line-clamp-2" title="${prod.descripcion}">${prod.descripcion}</p>
                </div>
                <div class="mt-2 text-right">
                    <span class="font-bold text-blue-600 dark:text-blue-400 font-mono">$${prod.costo_proveedor.toFixed(2)} ${prod.moneda_compra}</span>
                </div>
            </div>
        `;
        contenedor.appendChild(card);
    });
}

function filtrarProductos(filtroMarca = '') {
    const texto = document.getElementById('buscadorProductos').value.toLowerCase();
    const filtrados = inventarioCache.filter(p => {
        const coincideTexto = p.numero_catalogo.toLowerCase().includes(texto) || p.descripcion.toLowerCase().includes(texto);
        const coincideMarca = filtroMarca === '' || (p.marca && p.marca.includes(filtroMarca));
        return coincideTexto && coincideMarca;
    });
    renderGrid(filtrados);
}

// --- 3. LÓGICA DEL CARRITO ---
function agregarAlCarrito(prod) {
    // Buscar si ya existe
    const index = carrito.findIndex(item => item.id === prod.id);
    
    if (index >= 0) {
        carrito[index].cantidad++;
    } else {
        // Nuevo Item
        carrito.push({
            id: prod.id,
            numero_catalogo: prod.numero_catalogo,
            descripcion: prod.descripcion,
            marca: prod.marca,
            costo_proveedor: prod.costo_proveedor,
            moneda_compra: prod.moneda_compra,
            tiempo_entrega: prod.tiempo_entrega,
            imagen_url: prod.imagen_url,
            // Defaults Venta
            cantidad: 1,
            margen_ganancia: 0.30, 
            descuento_cliente: 0.00
        });
    }
    renderCarrito();
}

function renderCarrito() {
    const contenedor = document.getElementById('listaCarrito');
    const monedaSalida = document.getElementById('monedaSalida').value;
    const tc = parseFloat(document.getElementById('tcDia').value) || 1;
    
    contenedor.innerHTML = '';
    let granTotal = 0;

    if (carrito.length === 0) {
        contenedor.innerHTML = `
            <div class="h-full flex flex-col items-center justify-center text-gray-400 opacity-60">
                <i class="fas fa-basket-shopping text-6xl mb-4"></i>
                <p>Carrito vacío</p>
            </div>`;
        actualizarTotalesUI(0, monedaSalida);
        return;
    }

    carrito.forEach((item, index) => {
        // Cálculo Precio Venta
        let costoNorm = item.costo_proveedor;
        if (item.moneda_compra === 'USD' && monedaSalida === 'MXN') costoNorm *= tc;
        if (item.moneda_compra === 'MXN' && monedaSalida === 'USD') costoNorm /= tc;

        let precioLista = costoNorm / (1 - item.margen_ganancia);
        let precioFinal = precioLista * (1 - item.descuento_cliente);
        let subtotal = precioFinal * item.cantidad;
        granTotal += subtotal;

        // Render Fila Ticket
        const div = document.createElement('div');
        div.className = "bg-white dark:bg-slate-800 p-3 rounded-lg shadow-sm border border-gray-200 dark:border-slate-700 flex justify-between items-center group relative overflow-hidden mb-2";
        
        div.innerHTML = `
            <div class="w-1 bg-blue-500 absolute left-0 top-0 bottom-0"></div>
            <div class="flex-1 pl-3 overflow-hidden">
                <div class="flex justify-between">
                    <span class="font-bold text-sm text-gray-800 dark:text-gray-200 truncate w-32">${item.numero_catalogo}</span>
                    <span class="text-xs font-bold bg-gray-100 dark:bg-slate-700 px-2 py-0.5 rounded">x${item.cantidad}</span>
                </div>
                <div class="text-[10px] text-gray-500 dark:text-gray-400 truncate w-40">${item.descripcion}</div>
            </div>
            <div class="text-right pl-2">
                <div class="font-bold text-blue-600 dark:text-blue-400 text-sm">$${subtotal.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
                <button onclick="borrarDelCarrito(${index})" class="text-gray-300 hover:text-red-500 text-xs"><i class="fas fa-trash"></i></button>
            </div>
        `;
        contenedor.appendChild(div);
    });

    actualizarTotalesUI(granTotal, monedaSalida);
}

function actualizarTotalesUI(total, moneda) {
    const lblTotal = document.getElementById('lblTotal');
    if (lblTotal) {
        lblTotal.innerText = `$${total.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})} ${moneda}`;
    }
}

function borrarDelCarrito(index) {
    carrito.splice(index, 1);
    renderCarrito();
}

// --- 4. CRM (Clientes) ---
function filtrarClientes() {
    const texto = document.getElementById('busquedaCliente').value.toLowerCase();
    const lista = document.getElementById('listaResultadosClientes');
    lista.innerHTML = '';
    
    if(texto.length < 2) {
        lista.classList.add('hidden');
        return;
    }

    const filtrados = clientesCache.filter(c => 
        (c.compania && c.compania.toLowerCase().includes(texto)) || 
        (c.nombre && c.nombre.toLowerCase().includes(texto))
    );
    
    lista.classList.remove('hidden');
    
    if(filtrados.length === 0) {
        lista.innerHTML = '<div class="p-3 text-xs text-gray-500">No encontrado</div>';
        return;
    }

    filtrados.forEach(c => {
        const div = document.createElement('div');
        div.className = "p-2 hover:bg-blue-50 dark:hover:bg-slate-600 cursor-pointer text-xs border-b border-gray-100 dark:border-slate-600";
        div.innerText = c.compania;
        div.onclick = () => seleccionarCliente(c);
        lista.appendChild(div);
    });
}

function seleccionarCliente(c) {
    clienteSeleccionado = c;
    document.getElementById('busquedaCliente').value = '';
    document.getElementById('listaResultadosClientes').classList.add('hidden');
    
    // Mostrar UI de seleccionado
    document.getElementById('clienteSeleccionadoInfo').classList.remove('hidden');
    // Forzar display flex si tailwind lo ocultó
    document.getElementById('clienteSeleccionadoInfo').style.display = 'flex';
    document.getElementById('lblClienteNombre').innerText = c.compania;
    
    // Animación simple
    document.getElementById('clienteSeleccionadoInfo').classList.remove('animate-pulse');
}

function deseleccionarCliente() {
    clienteSeleccionado = null;
    document.getElementById('clienteSeleccionadoInfo').classList.add('hidden');
    document.getElementById('clienteSeleccionadoInfo').style.display = 'none';
}

// --- 5. GUARDAR / FINALIZAR ---
async function guardarCotizacion(accion) {
    if (!clienteSeleccionado) return alert("⚠️ Selecciona un cliente primero");
    if (carrito.length === 0) return alert("⚠️ El carrito está vacío");

    const payload = {
        cliente_id: clienteSeleccionado.id,
        moneda_salida: document.getElementById('monedaSalida').value,
        tipo_cambio: parseFloat(document.getElementById('tcDia').value),
        items: carrito
    };

    try {
        const res = await fetch('/api/ventas/cotizar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${sessionStorage.getItem('token')}`
            },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            const data = await res.json();
            if (accion === 'Finalizar') {
                const url = data.url_pdf || data.pdf_url;
                if(url) window.open(url, '_blank');
                alert("✅ Cotización generada con éxito");
                carrito = [];
                renderCarrito();
                deseleccionarCliente();
            } else {
                alert("💾 Borrador guardado");
            }
        } else {
            const err = await res.json();
            alert("❌ Error: " + (err.detail || "Desconocido"));
        }
    } catch (e) {
        console.error(e);
        alert("❌ Error de conexión");
    }
}