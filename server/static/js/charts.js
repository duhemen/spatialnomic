/* ================================================================
   SpatiaNomics — Charts (Chart.js wrapper)
   ================================================================ */

Chart.defaults.color = '#8A94A6';
Chart.defaults.borderColor = '#1E2A44';
Chart.defaults.font.family = "'Segoe UI', 'Inter', sans-serif";

/* ================= Sample Series (variabel global di sini saja) ================= */
window.sampleSeries = window.sampleSeries || [];

/* ================= Distribution Pie ================= */
async function loadDistributionChart() {
  const el = document.getElementById('chart-distribution');
  if (!el) return;
  try {
    const gj = await api('/api/wilayah/geojson?level=provinsi&limit=100');
    const counts = { AMAN: 0, WASPADA: 0, SIAGA: 0, BAHAYA: 0 };
    gj.features.forEach(f => {
      const c = (f.properties.category || 'WASPADA').toUpperCase();
      if (counts[c] !== undefined) counts[c]++;
    });
    new Chart(el, {
      type: 'doughnut',
      data: {
        labels: Object.keys(counts),
        datasets: [{
          data: Object.values(counts),
          backgroundColor: ['#4ADE80', '#FACC15', '#FF6E40', '#EF4444'],
          borderColor: '#0A0E17',
          borderWidth: 3,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { position: 'right', labels: { color: '#E0E0E0', padding: 14, font: { size: 12 } } },
        },
      },
    });
  } catch (e) { console.error('distribution:', e); }
}

/* ================= Top Risk List ================= */
async function loadTopRisk() {
  const el = document.getElementById('top-risk-list');
  if (!el) return;
  try {
    const gj = await api('/api/wilayah/geojson?level=provinsi&limit=100');
    const sorted = gj.features
      .map(f => ({ nama: f.properties.nama, ueri: f.properties.ueri, cat: f.properties.category }))
      .sort((a, b) => b.ueri - a.ueri)
      .slice(0, 10);

    el.innerHTML = sorted.map((r, i) => `
      <div class="list-item">
        <span class="name">${i + 1}. ${r.nama}</span>
        <span class="value badge-${r.cat.toLowerCase()}" style="background:${CATEGORY_COLORS[r.cat]};color:#0A0E17;">
          ${r.ueri.toFixed(3)} · ${r.cat}
        </span>
      </div>
    `).join('');
  } catch (e) {
    el.innerHTML = `<div class="loading" style="color:var(--red)">Error: ${e.message}</div>`;
  }
}

/* ================= Forecast ================= */
let forecastChart = null;

/**
 * Generate sample time-series dan gambar chart.
 */
function generateSample() {
  const n = 60;
  const series = [];
  for (let i = 0; i < n; i++) {
    const base = 0.5 + 0.15 * Math.sin(2 * Math.PI * i / 25);
    const noise = (Math.random() - 0.5) * 0.08;
    series.push(Math.max(0.05, Math.min(0.95, base + noise)));
  }
  window.sampleSeries = series;
  drawForecastChart(series, null);
  const el = document.getElementById('forecast-info');
  if (el) el.textContent = `✅ Sample series: ${n} titik. Klik "🔮 Jalankan Prediksi" untuk forecast.`;
}

/**
 * Jalankan forecast.
 * @param {HTMLElement} btn - tombol yang dipanggil (opsional)
 */
async function runForecast(btn) {
  const regionEl = document.getElementById('pred-region');
  const wilayahEl = document.getElementById('pred-wilayah');
  const horizonEl = document.getElementById('input-horizon');

  const region = regionEl ? regionEl.value : 'DEMO-001';
  const wilayah = wilayahEl ? wilayahEl.value : '';
  const kode = wilayah || region || 'DEMO-001';
  const horizon = parseInt(horizonEl ? horizonEl.value : 14) || 14;

  if (!window.sampleSeries || !window.sampleSeries.length) {
    alert('Klik "🎲 Sample Series" dulu untuk membuat data.');
    return;
  }

  const btnEl = btn || document.getElementById('btn-run');
  const origText = btnEl ? btnEl.textContent : '🔮 Jalankan Prediksi';
  if (btnEl) { btnEl.disabled = true; btnEl.textContent = '⏳ Memproses...'; }

  const infoEl = document.getElementById('forecast-info');
  if (infoEl) infoEl.textContent = '⏳ Memanggil server...';

  try {
    console.log('📤 POST /api/forecast/run', { kode, horizon, n: window.sampleSeries.length });
    const res = await api('/api/forecast/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        wilayah_kode: kode,
        series: window.sampleSeries,
        horizon: horizon,
      }),
    });
    console.log('📥 Response:', res);
    drawForecastChart(window.sampleSeries, res);
    if (infoEl) {
      const wilayahEl = document.getElementById('pred-wilayah');
      const wilayahNama = wilayahEl?.selectedOptions[0]?.textContent?.split(' — ')[0] || res.wilayah_kode;

      infoEl.textContent = `✅ Prediksi ${res.horizon} langkah via ${res.method} | Mean akhir: ${res.mean.at(-1).toFixed(3)} | Wilayah: ${wilayahNama}`;
    }
  } catch (e) {
    console.error('Forecast error:', e);
    if (infoEl) infoEl.textContent = `❌ Gagal: ${e.message}`;
    alert('Gagal prediksi: ' + e.message);
  } finally {
    if (btnEl) { btnEl.disabled = false; btnEl.textContent = origText; }
  }
}

/**
 * Gambar chart forecast dengan confidence interval.
 */
function drawForecastChart(hist, res) {
  const el = document.getElementById('chart-forecast');
  if (!el) return;

  let labels = hist.map((_, i) => `H${i + 1}`);
  let histData = [...hist];
  let meanData = hist.map(() => null);
  let upperData = hist.map(() => null);
  let lowerData = hist.map(() => null);

  if (res) {
    labels = labels.concat(res.mean.map((_, i) => `F${i + 1}`));
    histData = histData.concat(new Array(res.mean.length).fill(null));

    const prefixLen = hist.length - 1;
    meanData = [...new Array(prefixLen).fill(null), hist.at(-1), ...res.mean];
    upperData = [...new Array(prefixLen).fill(null), hist.at(-1), ...res.upper];
    lowerData = [...new Array(prefixLen).fill(null), hist.at(-1), ...res.lower];

    // Pad sampai panjang labels
    while (meanData.length < labels.length) meanData.push(null);
    while (upperData.length < labels.length) upperData.push(null);
    while (lowerData.length < labels.length) lowerData.push(null);
  }

  if (forecastChart) forecastChart.destroy();
  forecastChart = new Chart(el, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Historikal', data: histData,
          borderColor: '#00E5FF', backgroundColor: 'rgba(0,229,255,0.1)',
          borderWidth: 2, pointRadius: 0, tension: 0.3, fill: false,
        },
        ...(res ? [
          {
            label: 'Prediksi (mean)', data: meanData,
            borderColor: '#B388FF', borderWidth: 2,
            borderDash: [5, 4], pointRadius: 0, tension: 0.3,
          },
          {
            label: 'Upper CI', data: upperData,
            borderColor: 'rgba(179,136,255,0.4)', borderWidth: 1,
            pointRadius: 0, tension: 0.3, fill: '+1',
            backgroundColor: 'rgba(179,136,255,0.12)',
          },
          {
            label: 'Lower CI', data: lowerData,
            borderColor: 'rgba(179,136,255,0.4)', borderWidth: 1,
            pointRadius: 0, tension: 0.3, fill: false,
          },
        ] : []),
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#E0E0E0', font: { size: 11 } } } },
      scales: {
        y: { min: 0, max: 1, ticks: { color: '#8A94A6' }, grid: { color: '#1E2A44' } },
        x: { ticks: { color: '#8A94A6', maxTicksLimit: 20 }, grid: { color: '#1E2A44' } },
      },
    },
  });
}

/* ================= Export ke global ================= */
window.loadDistributionChart = loadDistributionChart;
window.loadTopRisk = loadTopRisk;
window.generateSample = generateSample;
window.runForecast = runForecast;
window.drawForecastChart = drawForecastChart;