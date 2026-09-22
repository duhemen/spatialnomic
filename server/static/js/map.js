/* ================================================================
   SpatiaNomics — Map & Drill-Down dengan Dropdown Hierarchy
   ================================================================ */

let mainMap = null;
let geoLayer = null;
let currentLevel = 'region';
let currentParent = null;
let breadcrumbPath = [];

const TILE_URL = 'https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}';
const TILE_ATTR = 'Esri, HERE, Garmin, © OpenStreetMap contributors';

/* ================= Init Map ================= */
function initDrillDownMap(containerId) {
  if (typeof L === 'undefined') { console.error('Leaflet tidak ada!'); return; }

  mainMap = L.map(containerId, {
    center: [-2.5, 118], zoom: 5,
    zoomControl: true, attributionControl: false, preferCanvas: true,
  });
  L.tileLayer(TILE_URL, { maxZoom: 16, attribution: TILE_ATTR }).addTo(mainMap);

  // Legend
  const legend = L.control({ position: 'bottomright' });
  legend.onAdd = function () {
    const div = L.DomUtil.create('div', 'legend');
    div.style.cssText = 'background:rgba(10,14,23,0.9);padding:10px 14px;border-radius:8px;border:1px solid #1E2A44;color:#E0E0E0;font-size:11px;';
    div.innerHTML = '<div style="font-weight:700;color:#00E5FF;margin-bottom:6px;">UERI</div>' +
      ['AMAN', 'WASPADA', 'SIAGA', 'BAHAYA'].map(k =>
        `<div style="display:flex;align-items:center;margin:3px 0;"><div style="width:14px;height:14px;background:${CATEGORY_COLORS[k]};margin-right:8px;border-radius:3px;"></div>${k}</div>`
      ).join('');
    return div;
  };
  legend.addTo(mainMap);

  initDropdowns();
  loadRegions();
}

/* ================= Dropdowns ================= */
async function initDropdowns() {
  const selRegion = document.getElementById('select-region');
  if (!selRegion) return;

  try {
    const regions = await api('/api/wilayah/regions');
    regions.forEach(r => {
      const opt = document.createElement('option');
      opt.value = r.key;
      opt.textContent = `${r.icon} ${r.nama}`;
      opt.dataset.center = JSON.stringify(r.center);
      opt.dataset.zoom = r.zoom;
      selRegion.appendChild(opt);
    });
  } catch (e) { console.error('loadRegions dropdown:', e); }

  selRegion.addEventListener('change', onRegionChange);
  document.getElementById('select-provinsi')?.addEventListener('change', onProvinsiChange);
  document.getElementById('select-kabupaten')?.addEventListener('change', onKabupatenChange);
  document.getElementById('select-kecamatan')?.addEventListener('change', onKecamatanChange);
}

async function onRegionChange(e) {
  const regionKey = e.target.value;
  const opt = e.target.selectedOptions[0];
  // Reset dropdown anak
  resetDropdown('select-provinsi', '— Pilih Provinsi —');
  resetDropdown('select-kabupaten', '— Pilih Kabupaten —');
  resetDropdown('select-kecamatan', '— Pilih Kecamatan —');

  if (!regionKey) {
    if (geoLayer) mainMap.removeLayer(geoLayer);
    mainMap.setView([-2.5, 118], 5);
    breadcrumbPath = [];
    updateBreadcrumb();
    loadRegions();
    return;
  }

  try {
    const gj = await api(`/api/wilayah/region-geojson/${regionKey}`);
    renderGeoJSON(gj);

    const center = JSON.parse(opt.dataset.center);
    const zoom = parseInt(opt.dataset.zoom) || 5;
    mainMap.flyTo(center, zoom, { duration: 1.2 });

    breadcrumbPath = [{ level: 'region', kode: regionKey, nama: gj.region.nama, icon: gj.region.icon }];
    currentLevel = 'provinsi';
    currentParent = null;
    updateBreadcrumb();
    populateSidebar(gj, 'provinsi');

    // Isi dropdown provinsi
    const selProv = document.getElementById('select-provinsi');
    selProv.disabled = false;
    gj.features.forEach(f => {
      const p = f.properties;
      const opt = document.createElement('option');
      opt.value = p.kode;
      opt.textContent = `${p.nama} (${Number(p.ueri).toFixed(2)})`;
      opt.dataset.nama = p.nama;
      selProv.appendChild(opt);
    });
  } catch (e) {
    console.error('onRegionChange:', e);
    alert('Gagal memuat region: ' + e.message);
  }
}

async function onProvinsiChange(e) {
  const kode = e.target.value;
  const nama = e.target.selectedOptions[0].dataset.nama;
  resetDropdown('select-kabupaten', '— Pilih Kabupaten —');
  resetDropdown('select-kecamatan', '— Pilih Kecamatan —');

  if (!kode) return;
  await drillToWilayah(kode, nama, 'provinsi');

  // Isi dropdown kabupaten
  try {
    const gj = await api(`/api/wilayah/geojson?parent=${kode}&level=kabupaten&limit=100`);
    const selKab = document.getElementById('select-kabupaten');
    selKab.disabled = false;
    gj.features.forEach(f => {
      const p = f.properties;
      const opt = document.createElement('option');
      opt.value = p.kode;
      opt.textContent = `${p.nama} (${Number(p.ueri).toFixed(2)})`;
      opt.dataset.nama = p.nama;
      selKab.appendChild(opt);
    });
  } catch (err) { console.error(err); }
}

async function onKabupatenChange(e) {
  const kode = e.target.value;
  const nama = e.target.selectedOptions[0].dataset.nama;
  resetDropdown('select-kecamatan', '— Pilih Kecamatan —');

  if (!kode) return;
  await drillToWilayah(kode, nama, 'kabupaten');

  // Isi dropdown kecamatan
  try {
    const gj = await api(`/api/wilayah/geojson?parent=${kode}&level=kecamatan&limit=200`);
    const selKec = document.getElementById('select-kecamatan');
    selKec.disabled = false;
    gj.features.forEach(f => {
      const p = f.properties;
      const opt = document.createElement('option');
      opt.value = p.kode;
      opt.textContent = `${p.nama} (${Number(p.ueri).toFixed(2)})`;
      opt.dataset.nama = p.nama;
      selKec.appendChild(opt);
    });
  } catch (err) { console.error(err); }
}

async function onKecamatanChange(e) {
  const kode = e.target.value;
  const nama = e.target.selectedOptions[0].dataset.nama;
  if (!kode) return;
  await drillToWilayah(kode, nama, 'kecamatan');
}

function resetDropdown(id, placeholder) {
  const el = document.getElementById(id);
  if (!el) return;
  el.innerHTML = `<option value="">${placeholder}</option>`;
  el.disabled = true;
}

/* ================= Load Regions (Sidebar) ================= */
async function loadRegions() {
  try {
    const regions = await api('/api/wilayah/regions');
    const listEl = document.getElementById('region-list');
    if (listEl) {
      listEl.innerHTML = regions.map(r =>
        `<li data-region="${r.key}" data-lat="${r.center[0]}" data-lng="${r.center[1]}" data-zoom="${r.zoom}">
          <span class="icon">${r.icon}</span>${r.nama}
        </li>`
      ).join('');
      listEl.querySelectorAll('li').forEach(li => {
        li.addEventListener('click', () => {
          // Trigger dropdown
          const selRegion = document.getElementById('select-region');
          selRegion.value = li.dataset.region;
          selRegion.dispatchEvent(new Event('change'));
        });
      });
    }
    const titleEl = document.getElementById('sidebar-title');
    if (titleEl) titleEl.textContent = '🌏 Region Indonesia';
    breadcrumbPath = [];
    updateBreadcrumb();
  } catch (e) {
    console.error('loadRegions:', e);
    const listEl = document.getElementById('region-list');
    if (listEl) listEl.innerHTML = `<li style="color:var(--red);padding:10px;">❌ Gagal load region: ${e.message}</li>`;
  }
}

/* ================= Drill ================= */
async function drillToWilayah(kode, nama, level) {
  const childLevel = { 'provinsi': 'kabupaten', 'kabupaten': 'kecamatan', 'kecamatan': 'desa' }[level];
  if (!childLevel) { alert(`Sudah level terdalam: ${nama}`); return; }

  try {
    const gj = await api(`/api/wilayah/geojson?parent=${kode}&level=${childLevel}&limit=2000`);
    if (!gj.features.length) { alert(`Tidak ada data ${childLevel} di ${nama}`); return; }
    renderGeoJSON(gj);

    setTimeout(() => {
      if (geoLayer) {
        const b = geoLayer.getBounds();
        if (b.isValid()) mainMap.fitBounds(b, { padding: [20, 20] });
      }
    }, 100);

    breadcrumbPath.push({ level: childLevel, kode, nama });
    currentLevel = childLevel;
    currentParent = kode;
    updateBreadcrumb();
    populateSidebar(gj, childLevel);
  } catch (e) {
    console.error('drillToWilayah:', e);
    alert('Gagal: ' + e.message);
  }
}

/* ================= Render ================= */
function renderGeoJSON(gj) {
  if (geoLayer) mainMap.removeLayer(geoLayer);
  geoLayer = L.geoJSON(gj, {
    filter: f => f.geometry && f.geometry.coordinates,
    style: f => {
      const cat = (f.properties.category || 'UNKNOWN').toUpperCase();
      return {
        color: '#1E2A44', weight: 0.8, opacity: 0.9,
        fillColor: CATEGORY_COLORS[cat] || CATEGORY_COLORS.UNKNOWN,
        fillOpacity: 0.65,
      };
    },
    onEachFeature: (f, l) => {
      const p = f.properties;
      const cat = (p.category || 'UNKNOWN').toUpperCase();
      const color = CATEGORY_COLORS[cat] || CATEGORY_COLORS.UNKNOWN;
      const html = `
        <div style="min-width:200px;">
          <div style="color:#00E5FF;font-weight:700;font-size:14px;margin-bottom:6px;">${p.nama}</div>
          <div style="display:flex;justify-content:space-between;padding:2px 0;"><span style="color:#8A94A6;">Kode</span><span>${p.kode}</span></div>
          <hr style="border:none;border-top:1px solid #1E2A44;margin:8px 0;">
          <div style="display:flex;justify-content:space-between;padding:2px 0;"><span style="color:#8A94A6;">UERI</span><span style="color:${color};font-weight:700;">${Number(p.ueri).toFixed(3)}</span></div>
          <div style="display:flex;justify-content:space-between;padding:2px 0;"><span style="color:#8A94A6;">Kategori</span><span style="background:${color};color:#0A0E17;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700;">${cat}</span></div>
        </div>`;
      l.bindPopup(html);
      l.on('mouseover', () => l.setStyle({ weight: 2, color: '#00E5FF', fillOpacity: 0.85 }));
      l.on('mouseout', () => l.setStyle({ weight: 0.8, color: '#1E2A44', fillOpacity: 0.65 }));
      l.on('click', () => drillToWilayah(p.kode, p.nama, p.level));
    }
  }).addTo(mainMap);
}

/* ================= Sidebar ================= */
function populateSidebar(gj, level) {
  const listEl = document.getElementById('region-list');
  const titleEl = document.getElementById('sidebar-title');
  if (!listEl) return;

  const titles = {
    'provinsi': '📍 Provinsi (klik untuk detail)',
    'kabupaten': '🏙️ Kabupaten/Kota',
    'kecamatan': '🏘️ Kecamatan',
    'desa': '🏡 Desa/Kelurahan',
  };
  if (titleEl) titleEl.textContent = titles[level] || 'Wilayah';

  listEl.innerHTML = gj.features.map(f => {
    const p = f.properties;
    const cat = (p.category || 'UNKNOWN').toUpperCase();
    const icon = { 'AMAN': '🟢', 'WASPADA': '🟡', 'SIAGA': '🟠', 'BAHAYA': '🔴' }[cat] || '⚪';
    return `<li data-kode="${p.kode}" data-nama="${p.nama}" data-level="${p.level}">
      <span class="icon">${icon}</span>${p.nama}
      <span style="float:right;color:${CATEGORY_COLORS[cat]};font-weight:700;font-size:11px;">${Number(p.ueri).toFixed(2)}</span>
    </li>`;
  }).join('');

  listEl.querySelectorAll('li').forEach(li => {
    li.addEventListener('click', () => drillToWilayah(li.dataset.kode, li.dataset.nama, li.dataset.level));
  });
}

/* ================= Breadcrumb ================= */
function updateBreadcrumb() {
  const el = document.getElementById('breadcrumb');
  if (!el) return;
  let html = '<span class="crumb" data-action="reset">🌏 Indonesia</span>';
  breadcrumbPath.forEach((b, i) => {
    html += '<span class="crumb-separator">›</span>';
    const isLast = i === breadcrumbPath.length - 1;
    html += `<span class="crumb ${isLast ? 'active' : ''}" data-action="reset-before" data-index="${i}">${b.icon || ''} ${b.nama}</span>`;
  });
  el.innerHTML = html;

  el.querySelectorAll('.crumb').forEach(c => {
    c.addEventListener('click', () => {
      const action = c.dataset.action;
      if (action === 'reset') resetDrill();
      else if (action === 'reset-before') {
        const idx = parseInt(c.dataset.index);
        const target = breadcrumbPath[idx];
        // Trigger dropdown change
        if (target.level === 'region') {
          const sel = document.getElementById('select-region');
          sel.value = target.kode;
          sel.dispatchEvent(new Event('change'));
        }
      }
    });
  });
}

function resetDrill() {
  if (geoLayer) mainMap.removeLayer(geoLayer);
  mainMap.setView([-2.5, 118], 5);
  breadcrumbPath = [];
  currentLevel = 'region';
  currentParent = null;
  updateBreadcrumb();
  resetDropdown('select-region', '— Pilih Region —');
  resetDropdown('select-provinsi', '— Pilih Provinsi —');
  resetDropdown('select-kabupaten', '— Pilih Kabupaten —');
  resetDropdown('select-kecamatan', '— Pilih Kecamatan —');
  initDropdowns();
  loadRegions();
}

/* ================= Mini Map ================= */
function initMiniMap(containerId) {
  const mini = L.map(containerId, {
    center: [-2.5, 118], zoom: 4,
    zoomControl: false, attributionControl: false, preferCanvas: true,
  });
  L.tileLayer(TILE_URL, { maxZoom: 16 }).addTo(mini);
  loadMiniMapData(mini);
}

async function loadMiniMapData(map) {
  try {
    const gj = await api('/api/wilayah/geojson?level=provinsi&limit=100');
    L.geoJSON(gj, {
      style: f => {
        const cat = (f.properties.category || 'UNKNOWN').toUpperCase();
        return {
          color: '#1E2A44', weight: 0.6,
          fillColor: CATEGORY_COLORS[cat] || CATEGORY_COLORS.UNKNOWN, fillOpacity: 0.6,
        };
      },
      onEachFeature: (f, l) => {
        const p = f.properties;
        l.bindPopup(`<b style="color:#00E5FF">${p.nama}</b><br>UERI: <b>${Number(p.ueri).toFixed(3)}</b>`);
      }
    }).addTo(map);
  } catch (e) { console.error('miniMap:', e); }
}