# Sidebar Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Arreglar el bug donde clicar "Cotizador" rebota siempre a `/dashboard` y reestructurar el sidebar a single-column estilo Linear/Notion con grupos colapsables.

**Architecture:** Dos fases secuenciales sobre la rama `main`. Fase 1 migra `cotizador.html` para que extienda `base.html` (esto solo arregla el bug). Fase 2 reemplaza el sidebar dual-column actual (rail+panel) por una única columna de 256px con grupos colapsables y un agrupado más semántico (Resumen / CRM / Operación / Reportes / Sistema).

**Tech Stack:** Jinja2 SSR · Tailwind CSS CDN · Alpine.js 3 (+ `@alpinejs/collapse` plugin) · Cookie-based JWT auth.

**Spec:** `docs/superpowers/specs/2026-04-28-sidebar-redesign.md`

---

## File map

**Modify:**
- `app/templates/cotizador.html` — migrar a `extends "base.html"`, dropear localStorage check, dropear sidebar-container y navbar.js, stripear headers `Authorization: Bearer ${token}` de los fetch (cookie carries auth)
- `app/templates/base.html` — activar `darkMode: 'class'`, reemplazar sidebar dual-column por single-column con grupos colapsables, swap CSS tokens, swap Alpine `x-data`

**Delete:**
- `app/static/js/navbar.js` — sidebar legacy basado en JS-injection, sin consumidores tras Fase 1

**Out of touch:**
- Las otras 8 plantillas (dashboard, clientes, compras, gastos, inventario, login, reportes, seguimiento, usuarios) — ya extienden `base.html`. Heredan el nuevo sidebar automáticamente.
- Routers, modelos, migraciones — sin cambios.

---

## Sequencing

```
Fase 1 (cotizador):  Task 1 → Task 2 → Task 3
                                          ↓
Fase 2 (sidebar):    Task 4 → Task 5 → Task 6
                                          ↓
                                       Task 7 (smoke)
```

Cada task = un commit. Fase 1 deja la app funcional con el sidebar viejo (bug arreglado). Fase 2 reemplaza el sidebar. Si quieres parar después de Fase 1, queda mergeable.

---

## Task 1: Migrate `cotizador.html` to extend `base.html`

**Files:**
- Modify: `app/templates/cotizador.html`

- [ ] **Step 1: Replace the entire file content**

Reescribe `app/templates/cotizador.html` completo con esta estructura. Conserva el contenido del `<main>` actual y el JS original — solo cambian los wrappers.

```jinja
{% extends "base.html" %}

{% block title %}Cotizador{% endblock %}
{% block page_title %}Cotizador{% endblock %}

{% block extra_head %}
  <link rel="stylesheet" href="{{ url_for('static', path='css/cotizador.css') }}">
  <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
{% endblock %}

{% block content %}
<div class="flex-1 flex flex-col gap-4 overflow-hidden h-full">

  <div class="mb-4 border-b border-slate-300 dark:border-slate-700 flex-none">
    <ul class="flex flex-wrap -mb-px text-sm font-medium text-center">
      <li class="mr-2">
        <button onclick="cambiarTab('nuevo')" id="tab-btn-nuevo" class="inline-block p-3 border-b-2 border-blue-600 text-blue-600 rounded-t-lg active dark:text-blue-400 dark:border-blue-400 transition-colors">
          <i class="fas fa-cash-register mr-2"></i> Cotizador
        </button>
      </li>
      <li class="mr-2">
        <button onclick="cambiarTab('historial')" id="tab-btn-historial" class="inline-block p-3 border-b-2 border-transparent hover:text-slate-600 hover:border-slate-300 rounded-t-lg dark:hover:text-slate-300 transition-colors">
          <i class="fas fa-history mr-2"></i> Historial
        </button>
      </li>
    </ul>
  </div>

  <div id="view-nuevo" class="flex-1 flex flex-col gap-4 overflow-hidden">

    <div class="bg-white dark:bg-slate-800 p-4 rounded-lg shadow-sm border-l-4 border-cyan-500 flex-none">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
        <div class="md:col-span-2">
          <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">Cliente</label>
          <select id="select-cliente" class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded p-2 text-sm focus:ring-2 focus:ring-cyan-500 outline-none"></select>
        </div>
        <div>
          <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">Moneda</label>
          <select id="select-moneda" onchange="cambiarMoneda()" class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded p-2 text-sm font-bold">
            <option value="MXN" selected>🇲🇽 MXN</option>
            <option value="USD">🇺🇸 USD</option>
          </select>
        </div>
        <div id="div-tc" class="opacity-50 pointer-events-none">
          <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">T.C.</label>
          <input type="number" id="input-tc" value="20.00" onchange="recalculer()" class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded p-2 text-sm text-right">
        </div>
      </div>
      <input type="text" id="observaciones" class="w-full mt-2 border-b border-slate-300 dark:border-slate-600 bg-transparent text-sm py-1 focus:outline-none focus:border-cyan-500 placeholder-slate-400" placeholder="+ Agregar notas u observaciones...">
    </div>

    <div class="flex flex-col lg:flex-row gap-4 flex-1 overflow-hidden">
      <div class="w-full lg:w-1/3 bg-white dark:bg-slate-800 p-4 rounded-lg shadow-sm flex flex-col">
        <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase mb-2">Catálogo</label>
        <div class="relative">
          <input type="text" id="buscador" class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded p-2 pl-8 mb-2 text-sm focus:ring-2 focus:ring-cyan-500 outline-none" placeholder="Buscar SKU...">
          <i class="fas fa-search absolute left-2.5 top-2.5 text-slate-400 text-xs"></i>
        </div>

        <div id="lista-resultados" class="flex-1 overflow-y-auto border-t border-slate-200 dark:border-slate-700 hidden custom-scroll"></div>
        <div id="empty-search" class="flex-1 flex items-center justify-center text-slate-300 dark:text-slate-600">
          <i class="fas fa-barcode text-4xl"></i>
        </div>

        <button type="button" onclick="abrirModalFantasma()"
            class="mt-2 w-full bg-amber-50 hover:bg-amber-100 dark:bg-amber-900/20 dark:hover:bg-amber-900/40 border border-dashed border-amber-300 dark:border-amber-700 text-amber-700 dark:text-amber-300 text-xs font-bold rounded-lg py-2 transition flex items-center justify-center gap-2">
          <i class="fas fa-ghost"></i> Agregar producto fantasma
        </button>
      </div>

      <div id="modal-fantasma" class="hidden fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-md border border-amber-300 dark:border-amber-700 overflow-hidden">
          <div class="px-6 py-4 bg-amber-50 dark:bg-amber-900/30 border-b border-amber-200 dark:border-amber-800 flex justify-between items-center">
            <div>
              <h3 class="text-base font-black text-amber-700 dark:text-amber-300 uppercase">Producto Fantasma</h3>
              <p class="text-xs text-amber-600 dark:text-amber-400">Cotizar sin afectar inventario</p>
            </div>
            <button onclick="cerrarModalFantasma()" class="text-slate-400 hover:text-slate-700 dark:hover:text-white p-1"><i class="fas fa-times"></i></button>
          </div>
          <div class="p-5 space-y-3">
            <div>
              <label class="block text-[10px] font-black uppercase text-slate-500 mb-1 tracking-wider">SKU / Catálogo (opcional)</label>
              <input id="fantasma-sku" type="text" placeholder="P/N FAB-XYZ" class="w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded p-2 text-sm">
            </div>
            <div>
              <label class="block text-[10px] font-black uppercase text-slate-500 mb-1 tracking-wider">Descripción *</label>
              <input id="fantasma-desc" type="text" placeholder="Ej. Válvula especial bajo pedido" class="w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded p-2 text-sm">
            </div>
            <div class="grid grid-cols-3 gap-2">
              <div>
                <label class="block text-[10px] font-black uppercase text-slate-500 mb-1 tracking-wider">Costo *</label>
                <input id="fantasma-cost" type="number" min="0" step="0.01" value="0" class="w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded p-2 text-sm text-right">
              </div>
              <div>
                <label class="block text-[10px] font-black uppercase text-slate-500 mb-1 tracking-wider">Mon.</label>
                <select id="fantasma-mon" class="w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded p-2 text-sm font-bold">
                  <option value="MXN">MXN</option>
                  <option value="USD">USD</option>
                </select>
              </div>
              <div>
                <label class="block text-[10px] font-black uppercase text-slate-500 mb-1 tracking-wider">Cant.</label>
                <input id="fantasma-qty" type="number" min="1" value="1" class="w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded p-2 text-sm text-right">
              </div>
            </div>
            <div>
              <label class="block text-[10px] font-black uppercase text-slate-500 mb-1 tracking-wider">Utilidad %</label>
              <input id="fantasma-util" type="number" min="0" max="99" value="30" class="w-full bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-300 dark:border-emerald-700 rounded p-2 text-sm text-right text-emerald-700 dark:text-emerald-300 font-bold">
            </div>
          </div>
          <div class="px-5 py-3 border-t border-slate-200 dark:border-slate-700 flex justify-end gap-2">
            <button onclick="cerrarModalFantasma()" class="px-3 py-1.5 text-xs font-bold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg">Cancelar</button>
            <button onclick="agregarFantasma()" class="px-4 py-1.5 bg-amber-500 hover:bg-amber-400 text-white text-xs font-black uppercase tracking-wider rounded-lg shadow-md">
              <i class="fas fa-plus mr-1"></i> Agregar
            </button>
          </div>
        </div>
      </div>

      <div class="w-full lg:w-2/3 bg-white dark:bg-slate-800 rounded-lg shadow-sm flex flex-col overflow-hidden">
        <div class="p-3 bg-slate-50 dark:bg-slate-700 border-b border-slate-200 dark:border-slate-600 flex justify-between items-center flex-none">
          <span class="font-bold text-sm text-blue-900 dark:text-cyan-400">Detalle de Partidas</span>
          <span class="text-xs bg-blue-100 dark:bg-slate-600 text-blue-800 dark:text-blue-200 px-2 py-1 rounded-full font-bold" id="items-count">0 Ítems</span>
        </div>

        <div class="flex-1 overflow-y-auto custom-scroll">
          <table class="w-full text-left text-sm">
            <thead class="bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-400 text-xs uppercase sticky top-0 z-10 shadow-sm">
              <tr>
                <th class="p-3 bg-white dark:bg-slate-800">Producto</th>
                <th class="p-3 bg-white dark:bg-slate-800 text-center w-16">Cant.</th>
                <th class="p-3 bg-white dark:bg-slate-800 text-center w-20">Mon. Origen</th>
                <th class="p-3 bg-white dark:bg-slate-800 text-right">Costo</th>
                <th class="p-3 bg-white dark:bg-slate-800 text-center w-16">Util%</th>
                <th class="p-3 bg-white dark:bg-slate-800 text-right">Venta</th>
                <th class="p-3 bg-white dark:bg-slate-800 text-right font-bold">Total</th>
                <th class="p-3 bg-white dark:bg-slate-800 w-8"></th>
              </tr>
            </thead>
            <tbody id="tabla-carrito" class="divide-y divide-slate-100 dark:divide-slate-700">
              <tr><td colspan="8" class="p-10 text-center text-slate-400 italic">Carrito vacío</td></tr>
            </tbody>
          </table>
        </div>

        <div class="p-4 bg-slate-50 dark:bg-slate-900 border-t border-slate-200 dark:border-slate-700 flex-none">
          <div class="flex flex-col md:flex-row justify-between items-end gap-4">
            <div class="flex gap-2">
              <button onclick="guardar('cotizacion')" class="bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-600 px-4 py-2 rounded-lg font-bold text-xs shadow-sm transition flex items-center">
                <i class="fas fa-save mr-2 text-yellow-500"></i> Guardar
              </button>
              <button onclick="guardar('pendiente')" class="bg-cyan-600 hover:bg-cyan-700 text-white px-4 py-2 rounded-lg font-bold text-xs shadow-md transition flex items-center">
                <i class="fas fa-check-circle mr-2"></i> Vender
              </button>
            </div>

            <div class="text-right text-xs text-slate-600 dark:text-slate-400 space-y-1 min-w-[200px]">
              <div class="flex justify-between"><span>Subtotal:</span> <span id="lbl-sub" class="font-bold">$0.00</span></div>
              <div class="flex justify-between"><span>IVA (16%):</span> <span id="lbl-iva" class="font-bold">$0.00</span></div>
              <div class="flex justify-between border-t border-slate-300 dark:border-slate-600 pt-1 mt-1 text-base text-blue-900 dark:text-cyan-400 font-bold">
                <span>Total:</span> <span id="lbl-total">$0.00</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div id="view-historial" class="hidden flex-1 overflow-hidden bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
    <div class="h-full overflow-y-auto custom-scroll">
      <table class="min-w-full text-sm text-left">
        <thead class="bg-slate-100 dark:bg-slate-900 text-slate-600 dark:text-slate-300 text-xs uppercase sticky top-0 shadow-sm">
          <tr>
            <th class="px-6 py-3">Folio</th>
            <th class="px-6 py-3">Fecha</th>
            <th class="px-6 py-3">Cliente</th>
            <th class="px-6 py-3 text-right">Total</th>
            <th class="px-6 py-3 text-center">Estatus</th>
            <th class="px-6 py-3 text-center">Acciones</th>
          </tr>
        </thead>
        <tbody id="tabla-historial" class="divide-y divide-slate-100 dark:divide-slate-700 text-slate-700 dark:text-slate-300"></tbody>
      </table>
    </div>
  </div>

</div>
{% endblock %}

{% block extra_scripts %}
<script>
  let state = { prods: [], cart: [], moneda: 'MXN', tc: 20.00 };

  document.addEventListener('DOMContentLoaded', () => {
      loadData();
      const input = document.getElementById('buscador');
      input.addEventListener('input', (e) => filterProds(e.target.value));
      input.addEventListener('focus', () => { if(input.value) filterProds(input.value); });
      document.addEventListener('click', (e) => {
          const list = document.getElementById('lista-resultados');
          const empty = document.getElementById('empty-search');
          if (!list.contains(e.target) && e.target !== input) {
              list.classList.add('hidden');
              if(input.value === '') empty.classList.remove('hidden');
          }
      });
  });

  function cambiarTab(tab) {
      document.getElementById('view-nuevo').classList.add('hidden');
      document.getElementById('view-historial').classList.add('hidden');

      const baseBtn = "inline-block p-3 border-b-2 border-transparent hover:text-slate-600 dark:hover:text-slate-300 rounded-t-lg transition-colors";
      const activeBtn = "inline-block p-3 border-b-2 border-cyan-500 text-cyan-600 dark:text-cyan-400 rounded-t-lg active transition-colors font-bold";

      document.getElementById('tab-btn-nuevo').className = baseBtn;
      document.getElementById('tab-btn-historial').className = baseBtn;

      document.getElementById(`view-${tab}`).classList.remove('hidden');
      document.getElementById(`tab-btn-${tab}`).className = activeBtn;

      if(tab === 'historial') loadHistorial();
  }

  async function loadData() {
      try {
          const [cRes, pRes] = await Promise.all([
              fetch('/api/clientes/?limit=200'),
              fetch('/api/productos/?limit=2000')
          ]);
          if(cRes.ok) {
              const clientes = await cRes.json();
              const sel = document.getElementById('select-cliente');
              sel.innerHTML = '<option value="">-- Seleccionar --</option>';
              clientes.forEach(c => sel.innerHTML += `<option value="${c.id}">${c.nombre_empresa}</option>`);
          }
          if(pRes.ok) state.prods = await pRes.json();
      } catch(e) { console.error(e); }
  }

  function cambiarMoneda() {
      state.moneda = document.getElementById('select-moneda').value;
      const divTC = document.getElementById('div-tc');
      if(state.moneda === 'USD') {
          divTC.classList.remove('opacity-50', 'pointer-events-none');
          state.tc = parseFloat(document.getElementById('input-tc').value) || 20;
      } else {
          divTC.classList.add('opacity-50', 'pointer-events-none');
          state.tc = 1;
      }
      renderCart();
      filterProds(document.getElementById('buscador').value);
  }
  function recalculer() { state.tc = parseFloat(document.getElementById('input-tc').value); renderCart(); }
  function fmtMoney(amount) {
      return moneyForQuote(amount);
  }

  function moneyForQuote(amount) {
      const sym = state.moneda === 'USD' ? 'US$' : '$';
      return sym + Number(amount || 0).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
  }

  function quoteCost(producto) {
      const cost = parseFloat(producto.costo_compra ?? producto.precio_publico ?? 0);
      const sourceCurrency = (producto.moneda_compra || 'MXN').toUpperCase();
      if(sourceCurrency === state.moneda) return cost;
      if(sourceCurrency === 'USD' && state.moneda === 'MXN') return cost * state.tc;
      if(sourceCurrency === 'MXN' && state.moneda === 'USD') return cost / state.tc;
      return cost;
  }

  function filterProds(txt) {
      const list = document.getElementById('lista-resultados');
      const empty = document.getElementById('empty-search');
      list.innerHTML = '';

      const clean = txt.toLowerCase();
      if(clean.length < 1) {
          list.classList.add('hidden');
          empty.classList.remove('hidden');
          return;
      }

      const matches = state.prods.filter(p =>
          p.nombre.toLowerCase().includes(clean) ||
          p.sku.toLowerCase().includes(clean) ||
          ((p.sku_comercial || '').toLowerCase().includes(clean))
      );

      empty.classList.add('hidden');
      list.classList.remove('hidden');

      if(matches.length === 0) { list.innerHTML = '<div class="p-4 text-center text-xs text-slate-400">Sin resultados</div>'; return; }

      matches.slice(0, 10).forEach(p => {
          const el = document.createElement('div');
          el.className = "p-3 border-b border-slate-100 dark:border-slate-700 hover:bg-cyan-50 dark:hover:bg-slate-700 cursor-pointer flex justify-between items-center transition group";
          el.onmousedown = (e) => { e.preventDefault(); addCart(p); };
          el.innerHTML = `
              <div>
                  <div class="font-bold text-xs text-slate-700 dark:text-slate-300">${p.sku_comercial || '—'}</div>
                  <div class="text-xs text-slate-500 truncate w-40 group-hover:text-cyan-600">${p.nombre}</div>
              </div>
              <div class="text-right">
                  <div class="font-bold text-cyan-600 dark:text-cyan-400">${moneyForQuote(quoteCost(p))}</div>
                  <div class="text-[10px] text-slate-400">${(p.moneda_compra || 'MXN').toUpperCase()} compra | Stock: ${p.stock_actual}</div>
              </div>`;
          list.appendChild(el);
      });
  }

  function abrirModalFantasma() {
      document.getElementById('modal-fantasma').classList.remove('hidden');
      document.getElementById('modal-fantasma').classList.add('flex');
      document.getElementById('fantasma-desc').focus();
  }
  function cerrarModalFantasma() {
      const m = document.getElementById('modal-fantasma');
      m.classList.add('hidden'); m.classList.remove('flex');
  }
  function agregarFantasma() {
      const desc = document.getElementById('fantasma-desc').value.trim();
      const cost = parseFloat(document.getElementById('fantasma-cost').value);
      const qty = parseInt(document.getElementById('fantasma-qty').value) || 1;
      if (!desc || !cost || cost <= 0) {
          Swal.fire({toast:true, position:'top-end', icon:'warning', title:'Falta descripción y costo', showConfirmButton:false, timer:1500});
          return;
      }
      state.cart.push({
          id: null,
          ghost: true,
          sku: document.getElementById('fantasma-sku').value.trim() || '— FANTASMA',
          nom: desc,
          cost: cost,
          productCurrency: document.getElementById('fantasma-mon').value,
          qty: qty,
          max: 9999,
          utilidad: parseInt(document.getElementById('fantasma-util').value) || 30,
      });
      cerrarModalFantasma();
      ['fantasma-sku','fantasma-desc'].forEach(id => document.getElementById(id).value = '');
      document.getElementById('fantasma-cost').value = '0';
      document.getElementById('fantasma-qty').value = '1';
      document.getElementById('fantasma-util').value = '30';
      renderCart();
  }

  function addCart(p) {
      if(p.stock_actual <= 0) Swal.fire({toast:true, position:'top-end', icon:'warning', title:'Sin Stock', showConfirmButton:false, timer:1500});
      const ex = state.cart.find(x => x.id === p.id);
      if(ex) {
          ex.qty++;
      } else {
          state.cart.push({
              id: p.id,
              sku: p.sku_comercial || '—',
              nom: p.nombre,
              cost: parseFloat(p.costo_compra || 0),
              productCurrency: (p.moneda_compra || 'MXN').toUpperCase(),
              qty: 1,
              max: p.stock_actual,
              utilidad: 30
          });
      }

      const input = document.getElementById('buscador');
      input.value = ''; input.focus();
      document.getElementById('lista-resultados').classList.add('hidden');
      document.getElementById('empty-search').classList.remove('hidden');
      renderCart();
  }

  function renderCart() {
      const tb = document.getElementById('tabla-carrito');
      tb.innerHTML = '';
      let subtotal = 0;

      if(state.cart.length === 0) {
          tb.innerHTML = '<tr><td colspan="8" class="p-10 text-center text-slate-400 italic">Agrega productos</td></tr>';
          updTotal(0); return;
      }

      state.cart.forEach((i, idx) => {
          let costo = i.cost;
          if(i.productCurrency === 'USD' && state.moneda === 'MXN') costo *= state.tc;
          if(i.productCurrency === 'MXN' && state.moneda === 'USD') costo /= state.tc;
          const precioFinal = costo * (1 + (i.utilidad / 100));
          const importe = i.qty * precioFinal;
          subtotal += importe;

          const monedaBadge = i.productCurrency === 'USD'
              ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300 border-emerald-300 dark:border-emerald-700'
              : 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 border-blue-300 dark:border-blue-700';

          const ghostBadge = i.ghost ? '<span class="text-[9px] font-bold bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 px-1.5 py-0.5 rounded ml-1 uppercase">Fantasma</span>' : '';
          tb.innerHTML += `
              <tr class="border-b border-slate-50 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 transition">
                  <td class="p-3">
                      <div class="font-bold text-slate-700 dark:text-slate-200 text-xs">${i.sku}${ghostBadge}</div>
                      <div class="text-xs text-slate-500 truncate w-48">${i.nom}</div>
                  </td>
                  <td class="p-3 text-center">
                      <input type="number" min="1" value="${i.qty}" onchange="updItem(${idx}, 'qty', this.value)"
                          class="w-12 bg-transparent border border-slate-300 dark:border-slate-600 text-center text-xs rounded focus:border-cyan-500 outline-none dark:text-white">
                  </td>
                  <td class="p-3 text-center">
                      <select onchange="updItem(${idx}, 'productCurrency', this.value)"
                          class="text-[11px] font-bold rounded px-1 py-0.5 border ${monedaBadge} outline-none cursor-pointer">
                          <option value="MXN" ${i.productCurrency==='MXN'?'selected':''}>MXN</option>
                          <option value="USD" ${i.productCurrency==='USD'?'selected':''}>USD</option>
                      </select>
                  </td>
                  <td class="p-3 text-right text-xs text-slate-600 dark:text-slate-300">${moneyForQuote(costo)}</td>
                  <td class="p-3 text-center">
                      <input type="number" min="0" max="99" value="${i.utilidad}" onchange="updItem(${idx}, 'utilidad', this.value)"
                          class="w-12 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 text-center text-xs rounded text-emerald-700 dark:text-emerald-300 font-bold outline-none">
                  </td>
                  <td class="p-3 text-right text-xs font-bold text-cyan-700 dark:text-cyan-300">${moneyForQuote(precioFinal)}</td>
                  <td class="p-3 text-right text-xs font-bold text-slate-800 dark:text-slate-200">${fmtMoney(importe)}</td>
                  <td class="p-3 text-center cursor-pointer text-slate-300 hover:text-red-500 transition" onclick="delItem(${idx})"><i class="fas fa-times"></i></td>
              </tr>`;
      });
      updTotal(subtotal);
      document.getElementById('items-count').innerText = state.cart.length + " Ítems";
  }

  function updItem(idx, t, v) {
      if(t=='productCurrency') {
          state.cart[idx].productCurrency = (v === 'USD') ? 'USD' : 'MXN';
          renderCart();
          return;
      }
      let val = parseFloat(v)||0;
      if(t=='qty') state.cart[idx].qty = val < 1 ? 1 : val;
      if(t=='utilidad') state.cart[idx].utilidad = val < 0 ? 0 : (val > 99 ? 99 : val);
      renderCart();
  }
  function delItem(i) { state.cart.splice(i, 1); renderCart(); }
  function updTotal(sub) {
      const iva = sub * 0.16;
      document.getElementById('lbl-sub').innerText = fmtMoney(sub);
      document.getElementById('lbl-iva').innerText = fmtMoney(iva);
      document.getElementById('lbl-total').innerText = fmtMoney(sub + iva);
  }

  async function guardar(tipo) {
      const cli = document.getElementById('select-cliente').value;
      if(!cli || state.cart.length === 0) return Swal.fire('Error', 'Faltan datos', 'warning');

      const payload = {
          cliente_id: parseInt(cli),
          moneda: state.moneda,
          tipo_cambio: state.moneda === 'USD' ? state.tc : 1,
          detalles: state.cart.map(i => ({
              producto_id: i.id || null,
              cantidad: i.qty,
              utilidad: i.utilidad,
              descuento: 0,
              moneda_origen: i.productCurrency,
              sku_libre: i.ghost ? (i.sku === '— FANTASMA' ? null : i.sku) : null,
              descripcion_libre: i.ghost ? i.nom : null,
              costo_unitario: i.ghost ? i.cost : null
          })),
          observaciones: document.getElementById('observaciones').value
      };

      Swal.fire({title:'Guardando...', didOpen:()=>Swal.showLoading()});
      try {
          const res = await fetch(`/api/ventas/?tipo_orden=${tipo}`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
          if(res.ok) {
              const d = await res.json();
              Swal.fire({icon:'success', title: tipo==='cotizacion'?'Cotización':'Venta', text:`Folio: ${d.folio}`, showDenyButton:true, confirmButtonText:'Nueva', denyButtonText:'PDF'}).then(r => {
                  if(r.isDenied) window.open(`/api/ventas/${d.id}/pdf`, '_blank');
                  state.cart = []; renderCart(); document.getElementById('observaciones').value = '';
              });
          } else { const err = await res.json(); Swal.fire('Error', err.detail, 'error'); }
      } catch(e) { console.error(e); }
  }

  async function loadHistorial() {
      const res = await fetch('/api/ventas/historial');
      const data = await res.json();
      const tb = document.getElementById('tabla-historial');
      tb.innerHTML = '';
      data.forEach(o => {
          const color = o.estatus === 'cotizacion' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800';
          const verBtn = o.estatus === 'cotizacion'
              ? `<button onclick="convertir(${o.id})" class="text-cyan-600 hover:text-cyan-500 font-bold text-xs mr-2">VENDER</button>
                 <button onclick="recotizar(${o.id})" class="text-amber-600 hover:text-amber-500 font-bold text-xs mr-2" title="Crear nueva versión"><i class="fas fa-code-branch"></i></button>
                 <button onclick="generarOC(${o.id})" class="text-violet-600 hover:text-violet-500 font-bold text-xs mr-2" title="Generar OC borrador"><i class="fas fa-truck"></i></button>`
              : '';
          const versionTag = o.version > 1 ? `<span class="text-[9px] font-bold text-amber-600 ml-1">v${o.version}</span>` : '';
          tb.innerHTML += `
              <tr class="hover:bg-slate-50 dark:hover:bg-slate-800 border-b border-slate-100 dark:border-slate-700 transition">
                  <td class="px-6 py-4 font-bold text-blue-900 dark:text-blue-300">${o.folio}${versionTag}</td>
                  <td class="px-6 py-4 text-slate-500 dark:text-slate-400">${new Date(o.fecha).toLocaleDateString()}</td>
                  <td class="px-6 py-4 font-medium text-slate-700 dark:text-slate-300">${o.cliente}</td>
                  <td class="px-6 py-4 text-right font-mono font-bold text-slate-800 dark:text-white">${o.moneda === 'USD' ? 'US$' : '$'}${parseFloat(o.total).toLocaleString('en-US', {minimumFractionDigits:2})}</td>
                  <td class="px-6 py-4 text-center"><span class="px-2 py-1 rounded text-[10px] font-bold uppercase ${color}">${o.estatus}</span></td>
                  <td class="px-6 py-4 text-center flex justify-center items-center">
                      ${verBtn}
                      <a href="/api/ventas/${o.id}/pdf" target="_blank" class="text-slate-400 hover:text-red-500 transition"><i class="fas fa-file-pdf text-lg"></i></a>
                  </td>
              </tr>`;
      });
  }
  async function convertir(id) {
      if(!confirm('¿Aprobar venta?')) return;
      await fetch(`/api/ventas/${id}/convertir`, { method: 'POST' });
      loadHistorial();
  }
  async function recotizar(id) {
      const r = await Swal.fire({title:'Crear nueva versión?', text:'Se duplica la cotización con un nuevo folio y queda lista para editar.', showCancelButton:true, confirmButtonText:'Recotizar'});
      if (!r.isConfirmed) return;
      const res = await fetch(`/api/ventas/${id}/recotizar`, { method: 'POST' });
      if (res.ok) {
          const nueva = await res.json();
          Swal.fire({icon:'success', title:'Versión creada', text:`Folio: ${nueva.folio}`});
          loadHistorial();
      } else {
          const err = await res.json();
          Swal.fire('Error', err.detail || 'No se pudo recotizar', 'error');
      }
  }
  async function generarOC(quoteId) {
      const r = await Swal.fire({
          title:'Generar OC',
          input:'select',
          inputOptions:{borrador:'Borrador (no persiste)', persistir:'OC real (persiste, sin afectar stock)'},
          inputValue:'borrador',
          showCancelButton:true
      });
      if (!r.isConfirmed) return;
      if (r.value === 'borrador') {
          window.open(`/api/compras/cotizacion/${quoteId}/borrador`, '_blank');
          return;
      }
      const proveedor = await Swal.fire({title:'Proveedor ID', input:'number', inputLabel:'ID del proveedor para vincular la OC'});
      if (!proveedor.value) return;
      const res = await fetch(`/api/compras/cotizacion/${quoteId}/orden`, {
          method:'POST',
          headers:{'Content-Type':'application/json'},
          body: JSON.stringify({proveedor_id: parseInt(proveedor.value)})
      });
      if (res.ok) {
          const oc = await res.json();
          Swal.fire({icon:'success', title:'OC creada', text:`Folio: ${oc.folio || ('OC#'+oc.id)}`});
      } else {
          const err = await res.json();
          Swal.fire('Error', err.detail || 'No se pudo crear OC', 'error');
      }
  }
</script>
{% endblock %}
```

> **Diferencias importantes vs el archivo actual:**
> - Eliminado `<!DOCTYPE html>`, `<html>`, `<head>`, `<body>` propios.
> - Eliminado `<script>if (!localStorage.getItem('token'))...</script>`.
> - Eliminado `<div id="sidebar-container"></div>`.
> - Eliminado `<script src="/static/js/navbar.js"></script>`.
> - Eliminado `<script>tailwind.config = { darkMode: 'class' };</script>` (Task 4 lo agrega a `base.html`).
> - Eliminada la línea `const token = localStorage.getItem('token');`.
> - Cada `fetch(...)` ya no incluye `headers: {'Authorization': 'Bearer ${token}'}`. Las requests se autentican vía cookie HttpOnly enviada automáticamente (same-origin).
> - El `<main>` envolvente desaparece (`base.html` ya provee el `<main>`); el contenido se mete en un `<div>` flex.
> - SweetAlert2 y `cotizador.css` cargan vía `{% block extra_head %}`.

- [ ] **Step 2: Verify**

```bash
cd /home/atlas-tech/Devs/Dasic_Atlas_api
git diff --stat app/templates/cotizador.html
grep -nE "localStorage.getItem\('token'\)|sidebar-container|navbar\.js|Authorization.*Bearer.*token" app/templates/cotizador.html
```

Expected:
- `git diff --stat`: ~570 líneas removidas, ~510 líneas agregadas (los wrappers se fueron, el contenido se reorganiza).
- `grep`: zero results.

- [ ] **Step 3: Commit**

```bash
git add app/templates/cotizador.html
git commit -m "fix(cotizador): migrar a base.html — elimina rebote a /dashboard"
```

---

## Task 2: Verify Task 1 didn't miss anything

**Files:**
- Read-only verification

- [ ] **Step 1: Confirmar que no quedaron referencias a token-en-localStorage o navbar.js**

```bash
cd /home/atlas-tech/Devs/Dasic_Atlas_api
grep -rnE "localStorage.getItem\('token'\)|sidebar-container|navbar\.js" app/
```

Expected: zero results. Si aparece algo, ABRE BLOCKER y reporta — no continúes.

- [ ] **Step 2: Confirmar que ningún fetch en cotizador.html usa Bearer header**

```bash
grep -nE "Authorization.*Bearer" app/templates/cotizador.html
```

Expected: zero results.

> No hay commit en esta task — es solo verificación. Si la verificación falla, regresa a Task 1 y arregla.

---

## Task 3: Delete `app/static/js/navbar.js`

**Files:**
- Delete: `app/static/js/navbar.js`

- [ ] **Step 1: Verificar cero consumidores**

```bash
cd /home/atlas-tech/Devs/Dasic_Atlas_api
grep -rn "navbar.js" app/ 2>/dev/null
```

Expected: zero results (Task 1 lo eliminó del cotizador, no debería estar en otro lado).

- [ ] **Step 2: Eliminar el archivo**

```bash
git rm app/static/js/navbar.js
```

- [ ] **Step 3: Commit**

```bash
git commit -m "chore(static): remove legacy navbar.js sidebar injector"
```

---

## Task 4: Activar `darkMode: 'class'` en `base.html`

**Files:**
- Modify: `app/templates/base.html` (líneas 2 y 11-21)

- [ ] **Step 1: Editar línea 2 — agregar `dark` al `<html>`**

Cambiar:
```html
<html lang="es" class="h-full">
```
A:
```html
<html lang="es" class="h-full dark">
```

- [ ] **Step 2: Editar el `<script>` de tailwind.config (líneas 10-21)**

Cambiar el bloque actual:
```html
<script>
  tailwind.config = {
    theme: {
      extend: {
        fontFamily: { sans: ['Outfit', 'Inter', 'sans-serif'] },
        colors: {
          dasic: { navy:'#001e62', cyan:'#00d4e0' }
        }
      }
    }
  }
</script>
```

Por:
```html
<script>
  tailwind.config = {
    darkMode: 'class',
    theme: {
      extend: {
        fontFamily: { sans: ['Outfit', 'Inter', 'sans-serif'] },
        colors: {
          dasic: { navy:'#001e62', cyan:'#00d4e0' }
        }
      }
    }
  }
</script>
```

- [ ] **Step 3: Verificar**

```bash
grep -n "darkMode\|class=\"h-full" app/templates/base.html | head -5
```

Expected: 2 lines — la `<html ... dark>` y el `darkMode: 'class'`.

- [ ] **Step 4: Commit**

```bash
git add app/templates/base.html
git commit -m "feat(ui): activate Tailwind darkMode:'class' for cotizador parity"
```

---

## Task 5: Add `@alpinejs/collapse` plugin to `base.html`

**Files:**
- Modify: `app/templates/base.html` (línea 31)

- [ ] **Step 1: Agregar plugin antes del Alpine core**

Localiza la línea actual:
```html
<!-- Alpine.js (deferred) -->
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

Reemplaza por:
```html
<!-- Alpine.js + collapse plugin (deferred; plugin must load BEFORE core) -->
<script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/collapse@3.x.x/dist/cdn.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

- [ ] **Step 2: Verificar**

```bash
grep -n "alpinejs" app/templates/base.html
```

Expected: 2 líneas, plugin antes del core.

- [ ] **Step 3: Commit**

```bash
git add app/templates/base.html
git commit -m "feat(ui): load alpinejs/collapse plugin"
```

---

## Task 6: Replace sidebar in `base.html` (single-column with collapsible groups)

**Files:**
- Modify: `app/templates/base.html` (líneas 33-152 CSS, 157-183 Jinja section calc, 168-183 body x-data, 200-403 sidebar markup)

Esta task es grande pero atómica — todo el sidebar nuevo en un solo commit. Tres secciones del archivo cambian.

- [ ] **Step 1: Reemplazar bloque CSS del sidebar (`<style>` interno, líneas ~33-152)**

Localiza el bloque CSS dentro de `<style>` que empieza con el comentario `/* ── Tokens DASIC sidebar ─────...` y termina antes de `/* ── SIDEBAR ─────...` o donde acaba el sidebar CSS — todo el CSS sidebar-related debe reemplazarse.

Sustituye TODO el bloque CSS desde `:root {` hasta el final del bloque del media query del `.main-shell` (incluyendo tokens, `.sidebar-shell`, `.rail-btn`, `.panel-item`, `.panel-section-title`, `.quick-row`, `.quick-icon`, `.quick-badge` y la sección `Layout principal`) por:

```css
:root {
  --sidebar-width: 256px;
  --sidebar-bg: #0d1b3e;
  --sidebar-bg-bottom: #050d22;
  --sidebar-text: #ffffff;
  --sidebar-active-bg: rgba(255,255,255,0.10);
  --sidebar-hover-bg: rgba(255,255,255,0.06);
  --sidebar-accent: #2563eb;
  --sidebar-accent-glow: #00d4e0;
  --header-h:  64px;
  --footer-h:  36px;
}

::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #0f172a; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: #475569; }

.dax-card { @apply bg-slate-800 rounded-xl border border-slate-700/50 shadow-lg; }
.dax-input {
  @apply w-full bg-slate-700/50 border border-slate-600 text-slate-100
         placeholder-slate-400 rounded-lg px-3 py-2 text-sm
         focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/40
         transition duration-200;
}
.dax-btn-primary {
  @apply inline-flex items-center gap-2 bg-cyan-500 hover:bg-cyan-400
         text-slate-900 font-semibold text-sm px-4 py-2 rounded-lg
         transition-all duration-200 shadow-md hover:shadow-cyan-500/30 active:scale-95;
}
.dax-btn-ghost {
  @apply inline-flex items-center gap-2 text-slate-400 hover:text-slate-100
         text-sm px-3 py-2 rounded-lg hover:bg-slate-700/60 transition-all duration-200;
}
.dax-badge-green { @apply text-xs px-2 py-0.5 rounded-full font-semibold bg-emerald-500/15 text-emerald-400; }
.dax-badge-amber { @apply text-xs px-2 py-0.5 rounded-full font-semibold bg-amber-500/15 text-amber-400; }
.dax-badge-red   { @apply text-xs px-2 py-0.5 rounded-full font-semibold bg-red-500/15 text-red-400; }
.dax-badge-slate { @apply text-xs px-2 py-0.5 rounded-full font-semibold bg-slate-600/50 text-slate-300; }

.kpi-card { @apply dax-card p-5 flex items-center justify-between hover:border-slate-600 transition-colors duration-200; }

.dax-table { @apply w-full text-sm text-left; }
.dax-table thead tr { @apply border-b border-slate-700; }
.dax-table thead th { @apply px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider; }
.dax-table tbody tr { @apply border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors; }
.dax-table tbody td { @apply px-4 py-3 text-slate-300; }

@keyframes fadeIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
.fade-in { animation: fadeIn .3s ease both; }

/* ── SIDEBAR ─────────────────────────────────────────── */
.sidebar-shell {
  background: linear-gradient(180deg, var(--sidebar-bg) 0%, var(--sidebar-bg-bottom) 100%);
  transition: transform 0.25s ease;
}

.sidebar-group { @apply mt-1; }
.sidebar-group-header {
  @apply w-full flex items-center justify-between rounded-md px-2.5 py-1.5
         text-[9px] font-bold uppercase tracking-[0.24em] text-white/50
         hover:text-white/80 hover:bg-white/5 transition-colors;
}
.sidebar-group-chevron { @apply text-[9px] transition-transform duration-200; }
.sidebar-group-items { @apply mt-0.5 mb-2 space-y-0.5; }

.sidebar-item {
  @apply relative flex items-center gap-3 rounded-lg px-3 py-2
         text-[13px] font-medium text-slate-300/80 transition-all duration-150 hover:text-white;
}
.sidebar-item:hover { background: var(--sidebar-hover-bg); }
.sidebar-item.is-active { background: var(--sidebar-active-bg); color: #fff; font-weight: 600; }
.sidebar-item.is-active::before {
  content: ""; position: absolute; left: -6px; top: 8px; bottom: 8px;
  width: 3px; border-radius: 9999px;
  background: linear-gradient(180deg, var(--sidebar-accent-glow), #22d3ee);
}
.sidebar-item-icon {
  @apply flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-slate-300/70 transition-colors duration-150;
  background: rgba(0,0,0,0.18);
}
.sidebar-item:hover .sidebar-item-icon { color: #fff; background: rgba(255,255,255,0.08); }
.sidebar-item.is-active .sidebar-item-icon {
  color: var(--sidebar-accent-glow);
  background: rgba(0, 212, 224, 0.12);
  box-shadow: inset 0 0 0 1px rgba(0, 212, 224, 0.25);
}

.quick-row {
  @apply flex items-center gap-3 rounded-lg px-3 py-2 cursor-pointer
         text-[12.5px] text-slate-300/80 transition-colors duration-150
         hover:bg-white/6 hover:text-white;
}
.quick-icon {
  @apply flex h-7 w-7 items-center justify-center rounded-md text-slate-300/70;
  background: rgba(0,0,0,0.18);
}
.quick-badge {
  @apply ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded-full
         bg-cyan-500/15 text-cyan-300 ring-1 ring-cyan-400/20 min-w-[22px] text-center;
}

/* Layout principal */
.main-shell { margin-left: 0; transition: margin-left 0.22s ease; }
@media (min-width: 1024px) {
  body[data-sidebar="expanded"] .main-shell { margin-left: var(--sidebar-width); }
  body[data-sidebar="hidden"]   .main-shell { margin-left: 0; }
}
```

- [ ] **Step 2: Reemplazar el bloque Jinja de cálculo de sección (líneas ~157-166)**

Localiza el bloque que empieza con `{# ── Sección activa según ruta ─────...` y termina con `{% endif %}`.

Reemplaza por:
```jinja
{# ── Sección activa por ruta (auto-expand del grupo correspondiente — opcional, hoy todos abren por defecto) ─────────────────────────────── #}
{% set _path = request.url.path %}
```

(Eliminamos el cálculo de `_section`. El path sigue disponible para el `is-active` por item. El auto-expand de grupos no se hace via Jinja — el default Alpine es "todos abiertos".)

- [ ] **Step 3: Reemplazar el `<body>` x-data + atajos de teclado (líneas ~168-183)**

Localiza la línea `<body class="h-full bg-slate-900 text-slate-200 font-sans antialiased"` y todo el `x-data="..."`, `x-init="..."`, `:data-sidebar`, y los `@keydown.*` hasta el `>` que cierra el body tag.

Reemplaza por:
```html
<body class="h-full bg-slate-900 text-slate-200 font-sans antialiased"
      x-data="{
        searchOpen: false,
        sidebarMobile: false,
        mode: (function(){ const s = localStorage.getItem('dasic_sidebar_mode'); return s === 'collapsed' ? 'expanded' : (s || 'expanded'); })(),
        groups: JSON.parse(localStorage.getItem('dasic_sidebar_groups') || 'null'),
        setMode(m) { this.mode = m; localStorage.setItem('dasic_sidebar_mode', m); document.body.dataset.sidebar = m; },
        hide() { this.setMode('hidden'); },
        show() { this.setMode('expanded'); },
        isGroupOpen(key) { if (this.groups && key in this.groups) return this.groups[key]; return true; },
        toggleGroup(key) { const next = Object.assign({}, this.groups || {}); next[key] = !this.isGroupOpen(key); this.groups = next; localStorage.setItem('dasic_sidebar_groups', JSON.stringify(next)); }
      }"
      x-init="document.body.dataset.sidebar = mode"
      :data-sidebar="mode"
      @keydown.meta.k.window.prevent="searchOpen = true"
      @keydown.ctrl.k.window.prevent="searchOpen = true"
      @keydown.window="if ($event.key === '\\' && ($event.metaKey || $event.ctrlKey)) { $event.preventDefault(); mode === 'hidden' ? show() : hide(); }">
```

- [ ] **Step 4: Reemplazar TODO el `<aside>` (rail + panel) por single-column**

Localiza la línea `<!-- ══════════════════════════════════════════════════════` que precede al `SIDEBAR` y la `</aside>` que lo cierra (~línea 403).

Reemplaza el bloque entero del `<aside>...</aside>` por:

```html
  <!-- ══════════════════════════════════════════════════════
       SIDEBAR (single-column, collapsible groups)
  ═══════════════════════════════════════════════════════ -->
  <aside class="sidebar-shell fixed inset-y-0 left-0 z-50 flex h-full flex-col"
         :class="{
           '-translate-x-full lg:-translate-x-full': mode === 'hidden',
           '-translate-x-full lg:translate-x-0': mode !== 'hidden' && !sidebarMobile,
           'translate-x-0': sidebarMobile
         }"
         style="width: var(--sidebar-width)">

    <!-- Header marca -->
    <div class="flex h-16 shrink-0 items-center justify-between px-4 border-b border-white/10">
      <div class="flex items-center gap-3">
        <div class="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-400/10 ring-1 ring-cyan-400/30">
          <i class="fas fa-layer-group text-cyan-400 text-base"></i>
        </div>
        <div>
          <p class="text-[15px] font-bold tracking-wide text-white leading-none">DASIC</p>
          <p class="text-[9px] text-cyan-300/80 uppercase tracking-[0.18em] font-semibold mt-1">Industrial ERP</p>
        </div>
      </div>
      <button @click="sidebarMobile = false"
              class="lg:hidden h-8 w-8 flex items-center justify-center rounded-lg
                     text-slate-400 hover:text-white hover:bg-white/5 transition"
              title="Cerrar">
        <i class="fas fa-xmark text-sm"></i>
      </button>
    </div>

    <!-- Quick Search + badges -->
    <div class="px-3 pt-3 space-y-1 shrink-0">
      <div class="quick-row" @click="searchOpen = true">
        <span class="quick-icon"><i class="fas fa-magnifying-glass text-[12px]"></i></span>
        <span>Quick search</span>
        <span class="ml-auto text-[10px] font-mono text-slate-400/70 px-1.5 py-0.5 rounded bg-white/5">⌘K</span>
      </div>
      <div class="quick-row">
        <span class="quick-icon"><i class="fas fa-inbox text-[12px]"></i></span>
        <span>Inbox</span>
        <span class="quick-badge">0</span>
      </div>
      <div class="quick-row">
        <span class="quick-icon"><i class="fas fa-bell text-[12px]"></i></span>
        <span>Notifications</span>
        <span class="quick-badge">0</span>
      </div>
    </div>

    <!-- Nav -->
    <nav class="flex-1 min-h-0 overflow-y-auto px-3 mt-2">

      <!-- RESUMEN -->
      <div class="sidebar-group">
        <button class="sidebar-group-header" @click="toggleGroup('resumen')">
          <span>Resumen</span>
          <i class="fas fa-chevron-down sidebar-group-chevron"
             :class="isGroupOpen('resumen') ? 'rotate-0' : '-rotate-90'"></i>
        </button>
        <div x-show="isGroupOpen('resumen')" x-collapse class="sidebar-group-items">
          <a href="/dashboard" class="sidebar-item {% if _path == '/dashboard' %}is-active{% endif %}">
            <span class="sidebar-item-icon"><i class="fas fa-chart-line text-[12px]"></i></span>
            <span>Dashboard</span>
          </a>
        </div>
      </div>

      <!-- CRM -->
      <div class="sidebar-group">
        <button class="sidebar-group-header" @click="toggleGroup('crm')">
          <span>CRM</span>
          <i class="fas fa-chevron-down sidebar-group-chevron"
             :class="isGroupOpen('crm') ? 'rotate-0' : '-rotate-90'"></i>
        </button>
        <div x-show="isGroupOpen('crm')" x-collapse class="sidebar-group-items">
          <a href="/clientes" class="sidebar-item {% if _path == '/clientes' %}is-active{% endif %}">
            <span class="sidebar-item-icon"><i class="fas fa-users text-[12px]"></i></span>
            <span>Clientes</span>
          </a>
          <a href="/ventas/cotizador" class="sidebar-item {% if '/cotizador' in _path %}is-active{% endif %}">
            <span class="sidebar-item-icon"><i class="fas fa-cash-register text-[12px]"></i></span>
            <span>Cotizador</span>
          </a>
          <a href="/seguimiento" class="sidebar-item {% if _path == '/seguimiento' %}is-active{% endif %}">
            <span class="sidebar-item-icon"><i class="fas fa-route text-[12px]"></i></span>
            <span>Seguimiento</span>
          </a>
        </div>
      </div>

      <!-- OPERACIÓN -->
      <div class="sidebar-group">
        <button class="sidebar-group-header" @click="toggleGroup('operacion')">
          <span>Operación</span>
          <i class="fas fa-chevron-down sidebar-group-chevron"
             :class="isGroupOpen('operacion') ? 'rotate-0' : '-rotate-90'"></i>
        </button>
        <div x-show="isGroupOpen('operacion')" x-collapse class="sidebar-group-items">
          <a href="/inventario" class="sidebar-item {% if _path == '/inventario' %}is-active{% endif %}">
            <span class="sidebar-item-icon"><i class="fas fa-boxes-stacked text-[12px]"></i></span>
            <span>Inventario</span>
          </a>
          <a href="/compras" class="sidebar-item {% if _path == '/compras' %}is-active{% endif %}">
            <span class="sidebar-item-icon"><i class="fas fa-truck text-[12px]"></i></span>
            <span>Compras</span>
          </a>
        </div>
      </div>

      <!-- REPORTES -->
      <div class="sidebar-group">
        <button class="sidebar-group-header" @click="toggleGroup('reportes')">
          <span>Reportes</span>
          <i class="fas fa-chevron-down sidebar-group-chevron"
             :class="isGroupOpen('reportes') ? 'rotate-0' : '-rotate-90'"></i>
        </button>
        <div x-show="isGroupOpen('reportes')" x-collapse class="sidebar-group-items">
          <a href="/reportes" class="sidebar-item {% if _path == '/reportes' %}is-active{% endif %}">
            <span class="sidebar-item-icon"><i class="fas fa-chart-pie text-[12px]"></i></span>
            <span>Reportes</span>
          </a>
          <a href="/gastos" class="sidebar-item {% if _path == '/gastos' %}is-active{% endif %}">
            <span class="sidebar-item-icon"><i class="fas fa-file-invoice-dollar text-[12px]"></i></span>
            <span>Gastos</span>
          </a>
        </div>
      </div>

      <!-- SISTEMA -->
      <div class="sidebar-group">
        <button class="sidebar-group-header" @click="toggleGroup('sistema')">
          <span>Sistema</span>
          <i class="fas fa-chevron-down sidebar-group-chevron"
             :class="isGroupOpen('sistema') ? 'rotate-0' : '-rotate-90'"></i>
        </button>
        <div x-show="isGroupOpen('sistema')" x-collapse class="sidebar-group-items">
          <a href="/usuarios" class="sidebar-item {% if _path == '/usuarios' %}is-active{% endif %}">
            <span class="sidebar-item-icon"><i class="fas fa-user-shield text-[12px]"></i></span>
            <span>Usuarios</span>
          </a>
        </div>
      </div>

    </nav>

    <!-- Footer usuario -->
    <div class="shrink-0 border-t border-white/10 px-3 py-3">
      <div class="rounded-xl border border-white/8 bg-white/5 p-2.5 flex items-center gap-2.5">
        <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full
                    bg-gradient-to-br from-cyan-500 to-blue-600 text-white font-bold text-xs
                    ring-2 ring-white/10">
          {{ (current_user.nombre[0] | upper) if current_user else "U" }}
        </div>
        <div class="min-w-0 flex-1">
          <p class="truncate text-[12.5px] font-semibold text-white leading-tight">
            {{ current_user.nombre if current_user else "Usuario" }}
          </p>
          <span class="flex items-center gap-1.5 text-[10px] text-slate-400 mt-0.5">
            <span class="relative flex h-1.5 w-1.5">
              <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
              <span class="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
            </span>
            En línea
          </span>
        </div>
        <button @click="hide()"
                class="hidden lg:flex h-7 w-7 items-center justify-center rounded-md
                       text-slate-400 hover:text-slate-100 hover:bg-white/5 transition"
                title="Ocultar sidebar (Ctrl+\)">
          <i class="fas fa-eye-slash text-xs"></i>
        </button>
        <form action="/api/auth/logout" method="post" class="shrink-0">
          <button type="submit"
                  class="flex h-7 w-7 items-center justify-center rounded-md
                         text-slate-400 hover:text-red-400 hover:bg-red-500/10
                         transition-all duration-200" title="Cerrar sesión">
            <i class="fas fa-arrow-right-from-bracket text-xs"></i>
          </button>
        </form>
      </div>
    </div>

  </aside>
```

- [ ] **Step 5: Verificar que el botón flotante "mostrar sidebar" sigue antes del `<aside>`**

Justo antes del `<aside>` debe estar el `<div x-show="sidebarMobile">` (backdrop) y el `<button x-show="mode === 'hidden'">` (botón flotante para reabrir cuando está oculto). NO los toques — siguen funcionando con la nueva Alpine state.

- [ ] **Step 6: Validar HTML/Jinja**

```bash
cd /home/atlas-tech/Devs/Dasic_Atlas_api
DATABASE_URL='postgresql+psycopg://x:x@localhost:5432/dummy' SECRET_KEY='dummy' \
  uv run --with-requirements requirements.txt python -c "
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('app/templates'))
tmpl = env.get_template('base.html')
print('Jinja parse OK')
"
```

Expected: `Jinja parse OK`. Si falla con error de sintaxis Jinja, revisa el bloque editado.

- [ ] **Step 7: Confirmar cleanup de tokens viejos**

```bash
grep -nE "rail-btn|panel-item|panel-section-title|panel-icon|--sidebar-rail-width|--sidebar-panel-width|--sidebar-total-width|mode === 'collapsed'|toggleCollapse" app/templates/base.html
```

Expected: zero results.

- [ ] **Step 8: Commit**

```bash
git add app/templates/base.html
git commit -m "feat(ui): sidebar single-column con grupos colapsables (Resumen/CRM/Operación/Reportes/Sistema)"
```

---

## Task 7: Smoke test end-to-end

**Files:**
- Read-only: arrancar el servidor y validar el comportamiento.

- [ ] **Step 1: Crear DB de smoke (vacía)**

```bash
psql "postgresql://postgres:toor@localhost:5432/postgres" -c "CREATE DATABASE dasic_sidebar_smoke;"
```

- [ ] **Step 2: Arrancar uvicorn en background**

```bash
cd /home/atlas-tech/Devs/Dasic_Atlas_api
DATABASE_URL='postgresql+psycopg://postgres:toor@localhost:5432/dasic_sidebar_smoke' \
  SECRET_KEY='smoke' \
  uv run --with-requirements requirements.txt uvicorn app.main:app --port 8001 \
  > /tmp/uvicorn-sidebar.log 2>&1 &
sleep 5
```

> El startup ejecuta `seed_super_admin` si no hay usuarios. Tendrás `admin@dasic.com / admin123` disponible.

- [ ] **Step 3: Health check**

```bash
curl -s http://127.0.0.1:8001/health
```

Expected: `{"status":"ok","db":"ok"}`. Si no, revisar `/tmp/uvicorn-sidebar.log`.

- [ ] **Step 4: Login y obtener cookie**

```bash
curl -s -c /tmp/cookies-sidebar.txt -X POST http://127.0.0.1:8001/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@dasic.com&password=admin123"
```

Expected: `{"access_token":"...","token_type":"bearer"}`.

- [ ] **Step 5: Verificar que las 9 rutas SSR devuelven 200 con HTML válido**

```bash
for path in /dashboard /clientes /ventas/cotizador /seguimiento /inventario /compras /gastos /reportes /usuarios; do
  code=$(curl -s -o /tmp/last-page.html -w "%{http_code}" -b /tmp/cookies-sidebar.txt "http://127.0.0.1:8001${path}")
  size=$(wc -c < /tmp/last-page.html)
  echo "${path} → ${code} (${size}B)"
done
```

Expected: cada línea con `200` y tamaño > 5000 bytes (HTML real, no redirect/error). Si alguna devuelve 200 pero tamaño < 1000, abrir esa página y verificar.

- [ ] **Step 6: Verificar que el cotizador renderiza con el nuevo sidebar (no rebote)**

```bash
curl -s -b /tmp/cookies-sidebar.txt http://127.0.0.1:8001/ventas/cotizador | grep -c 'sidebar-shell'
```

Expected: `1` (el `<aside class="sidebar-shell">` existe en el HTML renderizado). Si es `0`, cotizador.html no está extendiendo correctamente base.html — abrir BLOCKER.

- [ ] **Step 7: Verificar que NO carga navbar.js viejo**

```bash
curl -s -b /tmp/cookies-sidebar.txt http://127.0.0.1:8001/ventas/cotizador | grep -c 'navbar.js'
```

Expected: `0`.

- [ ] **Step 8: Verificar el plugin de Alpine collapse**

```bash
curl -s -b /tmp/cookies-sidebar.txt http://127.0.0.1:8001/dashboard | grep -c 'alpinejs/collapse'
```

Expected: `1`.

- [ ] **Step 9: Verificar markup de un grupo colapsable**

```bash
curl -s -b /tmp/cookies-sidebar.txt http://127.0.0.1:8001/dashboard | grep -c 'toggleGroup'
```

Expected: `5` (un toggle por grupo).

- [ ] **Step 10: Apagar uvicorn y limpiar smoke DB**

```bash
pkill -f 'uvicorn app.main:app' || true
sleep 1
psql "postgresql://postgres:toor@localhost:5432/postgres" -c "DROP DATABASE IF EXISTS dasic_sidebar_smoke;"
```

- [ ] **Step 11: Manual UX check (opcional pero recomendado)**

Si tienes tiempo: arranca el servidor de nuevo, abre `http://127.0.0.1:8001/` en un navegador, login, y verifica visualmente:
- Click en cada link del sidebar → la URL cambia y la página correspondiente carga.
- Click en el header de un grupo (e.g. "CRM") → el grupo colapsa con animación; recarga → sigue colapsado.
- Click en el botón eye-slash del footer del sidebar → sidebar oculto, aparece botón flotante; click → sidebar reaparece.
- `Ctrl+\` toggle hide/show.
- `Cmd+K` abre el modal de quick search.
- En el cotizador: cargar la lista de clientes y productos funciona, agregar al carrito, guardar como cotización, generar PDF.

> Si todo lo anterior pasa, no hace falta commit final (Task 7 es solo verificación).

---

## Definition of Done

- [ ] `git grep -nE "localStorage.getItem\('token'\)|sidebar-container|navbar\.js" app/` → cero resultados
- [ ] `git grep -nE "rail-btn|panel-item|panel-section-title|--sidebar-rail-width|--sidebar-total-width|toggleCollapse|mode === 'collapsed'" app/templates/base.html` → cero resultados
- [ ] `app/static/js/navbar.js` no existe en el árbol
- [ ] Login → click en CADA link del sidebar (Dashboard, Clientes, Cotizador, Seguimiento, Inventario, Compras, Reportes, Gastos, Usuarios) → llega a la URL correcta, la página renderiza, el sidebar resalta el item activo
- [ ] Toggle de grupo (e.g. CRM) colapsa/expande el grupo; reload conserva el estado
- [ ] Toggle global (`Ctrl+\` o botón eye-slash) oculta/muestra el sidebar; reload conserva el estado
- [ ] Cotizador carga clientes y productos vía cookie auth (sin Bearer header), permite agregar al carrito, guardar y generar PDF
- [ ] Ningún error JS en la consola del navegador
