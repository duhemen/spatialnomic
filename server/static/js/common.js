/* ================================================================
   SpatiaNomics — Common Utilities
   ================================================================ */

const API_BASE = window.location.origin;

const CATEGORY_COLORS = {
  "AMAN":    "#4ADE80",
  "WASPADA": "#FACC15",
  "SIAGA":   "#FF6E40",
  "BAHAYA":  "#EF4444",
  "UNKNOWN": "#8A94A6"
};

/**
 * Fetch wrapper dengan error handling.
 */
async function api(path, options = {}) {
  const url = `${API_BASE}${path}`;
  try {
    const r = await fetch(url, options);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return await r.json();
  } catch (e) {
    console.error(`API error ${path}:`, e);
    throw e;
  }
}

/**
 * Format angka dengan pemisah ribuan.
 */
function formatNumber(n) {
  if (n === null || n === undefined) return '—';
  return Number(n).toLocaleString('id-ID');
}

/**
 * Format waktu lokal.
 */
function formatTime(iso) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString('id-ID', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  } catch { return iso; }
}

/**
 * Klasifikasi UERI → kategori.
 */
function classifyUERI(u) {
  if (u < 0.3) return "AMAN";
  if (u < 0.6) return "WASPADA";
  if (u < 0.8) return "SIAGA";
  return "BAHAYA";
}

/**
 * Return badge HTML untuk kategori.
 */
function categoryBadge(cat) {
  const cls = `badge-${(cat || 'unknown').toLowerCase()}`;
  return `<span class="badge ${cls}">${cat || '—'}</span>`;
}

/**
 * Update status server indicator.
 */
async function checkServerStatus() {
  const el = document.getElementById('server-status');
  if (!el) return;
  try {
    await api('/api/health');
    el.textContent = '🟢 online';
    el.style.color = 'var(--green)';
  } catch {
    el.textContent = '🔴 offline';
    el.style.color = 'var(--red)';
  }
}

// Update status tiap 30 detik
setInterval(checkServerStatus, 30000);
document.addEventListener('DOMContentLoaded', checkServerStatus);

/* ================================================================
   DASHBOARD functions
   ================================================================ */

async function loadDashboardKPI() {
  try {
    const gj = await api('/api/wilayah/geojson?level=provinsi&limit=100');
    const features = gj.features || [];
    const values = features.map(f => f.properties.ueri).filter(v => v != null);
    const avg = values.length ? values.reduce((a, b) => a + b, 0) / values.length : 0;

    const ueriEl = document.getElementById('kpi-ueri');
    const catEl = document.getElementById('kpi-cat');
    const catSubEl = document.getElementById('kpi-cat-sub');
    const regEl = document.getElementById('kpi-regions');

    const cat = classifyUERI(avg);
    if (ueriEl) {
      ueriEl.textContent = avg.toFixed(3);
      ueriEl.style.color = CATEGORY_COLORS[cat];
    }
    if (catEl) {
      catEl.textContent = cat;
      catEl.style.color = CATEGORY_COLORS[cat];
    }
    if (catSubEl) catSubEl.textContent = `dari ${values.length} provinsi`;
    if (regEl) regEl.textContent = features.length;

    // Laporan
    try {
      const reports = await api('/api/field-observation/list?verified_only=true');
      const repEl = document.getElementById('kpi-reports');
      if (repEl) repEl.textContent = reports.length;
    } catch { /* ignore */ }
  } catch (e) {
    console.error('loadDashboardKPI:', e);
  }
}

/* ================================================================
   LAPORAN functions
   ================================================================ */

async function loadReports() {
  const tbody = document.getElementById('tbody-reports');
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="7" class="loading">Memuat data...</td></tr>';
  try {
    const rows = await api('/api/field-observation/list?verified_only=false');
    if (!rows.length) {
      tbody.innerHTML = '<tr><td colspan="7" class="loading">Tidak ada laporan.</td></tr>';
      return;
    }
    tbody.innerHTML = rows.map(r => {
      const status = r.verified
        ? '<span class="badge badge-aman">✅ Verified</span>'
        : r.rejected
          ? '<span class="badge badge-bahaya">❌ Ditolak</span>'
          : '<span class="badge badge-waspada">⏳ Pending</span>';
      return `<tr>
        <td>${r.id}</td>
        <td>${r.wilayah_kode}</td>
        <td>${r.variable_kode}</td>
        <td>${Number(r.nilai).toFixed(2)}</td>
        <td>${r.observer || '—'}</td>
        <td>${formatTime(r.timestamp)}</td>
        <td>${status}</td>
      </tr>`;
    }).join('');
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7" class="loading" style="color:var(--red)">Error: ${e.message}</td></tr>`;
  }
}

window.CATEGORY_COLORS = CATEGORY_COLORS;