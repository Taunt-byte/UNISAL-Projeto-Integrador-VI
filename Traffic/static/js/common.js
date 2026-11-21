// Funções compartilhadas por todas as páginas do NetMonitor
const COLORS = ['#4f8cff', '#2ecc8f', '#f5b041', '#ff5d6c', '#9b6dff', '#3ec7e0', '#ff8fd0', '#c4d35b'];

if (window.Chart) {
  Chart.defaults.color = '#8b95a9';
  Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';
  Chart.defaults.font.family = '"Inter", "Segoe UI", system-ui, sans-serif';
  Chart.defaults.plugins.legend.labels.boxWidth = 12;
  Chart.defaults.animation.duration = 400;
}

function formatBytes(b) {
  if (b == null) return '—';
  const u = ['B', 'KB', 'MB', 'GB', 'TB'];
  let i = 0;
  while (b >= 1024 && i < u.length - 1) { b /= 1024; i++; }
  return b.toFixed(i === 0 ? 0 : 1) + ' ' + u[i];
}

function formatRate(bytesPerSec) {
  // velocidade de rede costuma ser mostrada em bits por segundo
  if (bytesPerSec == null) return '—';
  let v = bytesPerSec * 8;
  const u = ['bps', 'Kbps', 'Mbps', 'Gbps'];
  let i = 0;
  while (v >= 1000 && i < u.length - 1) { v /= 1000; i++; }
  return v.toFixed(i === 0 ? 0 : 1) + ' ' + u[i];
}

function formatDuration(s) {
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60;
  return (h ? h + 'h ' : '') + (h || m ? m + 'min ' : '') + sec + 's';
}

function escapeHtml(v) {
  return String(v == null ? '' : v).replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

async function getJSON(url, options) {
  const r = await fetch(url, options);
  if (!r.ok) throw new Error(url + ' → ' + r.status);
  return r.status === 204 || r.status === 202 ? null : r.json();
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

// Executa fn agora e depois a cada ms milissegundos
function every(ms, fn) {
  const run = () => Promise.resolve(fn()).catch(e => console.error(e));
  run();
  return setInterval(run, ms);
}

function lineChart(canvasId, datasets, opts = {}) {
  return new Chart(document.getElementById(canvasId), {
    type: 'line',
    data: {
      labels: [],
      datasets: datasets.map((d, i) => ({
        label: d.label, data: [], borderColor: d.color || COLORS[i], backgroundColor: (d.color || COLORS[i]) + '22',
        fill: d.fill !== false, tension: 0.35, pointRadius: 0, borderWidth: 2,
      })),
    },
    options: {
      maintainAspectRatio: false, interaction: { mode: 'index', intersect: false },
      scales: {
        x: { ticks: { maxTicksLimit: 8 } },
        y: { beginAtZero: true, max: opts.max, ticks: { callback: opts.tick || (v => v) } },
      },
      plugins: {
        tooltip: { callbacks: { label: c => c.dataset.label + ': ' + (opts.tick ? opts.tick(c.parsed.y) : c.parsed.y) } },
      },
    },
  });
}

function setLineData(chart, labels, series) {
  chart.data.labels = labels;
  series.forEach((s, i) => { chart.data.datasets[i].data = s; });
  chart.update('none');
}

function doughnutChart(canvasId) {
  return new Chart(document.getElementById(canvasId), {
    type: 'doughnut',
    data: { labels: [], datasets: [{ data: [], backgroundColor: COLORS, borderColor: '#171e2e', borderWidth: 3 }] },
    options: { maintainAspectRatio: false, cutout: '62%', plugins: { legend: { position: 'right' } } },
  });
}

function barChart(canvasId, horizontal) {
  return new Chart(document.getElementById(canvasId), {
    type: 'bar',
    data: { labels: [], datasets: [{ data: [], backgroundColor: COLORS[0] + 'cc', borderRadius: 6 }] },
    options: {
      maintainAspectRatio: false, indexAxis: horizontal ? 'y' : 'x',
      plugins: { legend: { display: false } },
      scales: { x: { beginAtZero: true }, y: { beginAtZero: true, ticks: { precision: 0 } } },
    },
  });
}

function setDictData(chart, dict) {
  chart.data.labels = Object.keys(dict);
  chart.data.datasets[0].data = Object.values(dict);
  chart.update();
}

every(1000, () => setText('clock', new Date().toLocaleString('pt-BR')));
