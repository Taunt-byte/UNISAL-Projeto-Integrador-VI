// Página "Dispositivos": tabela de sessões + gráficos, atualizados a cada 5 s
$(function () {
  const PT_BR = {
    search: 'Buscar:', lengthMenu: 'Mostrar _MENU_', info: '_START_–_END_ de _TOTAL_ sessões',
    infoEmpty: 'Nenhuma sessão', infoFiltered: '(filtrado de _MAX_)', zeroRecords: 'Nada encontrado',
    emptyTable: 'Nenhuma sessão registrada ainda', paginate: { previous: '‹', next: '›' },
  };
  const tabela = $('#dataTable').DataTable({ order: [[0, 'desc']], pageLength: 10, language: PT_BR });

  const osChart = doughnutChart('osChart');
  const browserChart = doughnutChart('browserChart');
  const countryChart = barChart('countryChart', true);
  const pagesChart = barChart('pagesChart', true);
  pagesChart.data.datasets[0].backgroundColor = '#2ecc8fcc';
  const hourChart = barChart('hourChart');
  hourChart.data.datasets[0].backgroundColor = '#9b6dffcc';

  let lastSignature = '';

  async function update() {
    const [sessions, stats, charts] = await Promise.all([
      getJSON('/api/sessions'), getJSON('/api/stats'), getJSON('/api/charts'),
    ]);

    setText('total-sessions', stats.total_sessions);
    setText('total-visitors', stats.total_visitors);
    setText('total-pageviews', stats.total_pageviews);
    setText('unique-pageviews', stats.unique_pageviews);
    setText('demoInfo', stats.demo_sessions ? stats.demo_sessions + ' sessões de demonstração' : '');

    // só redesenha tabela e gráficos se algo mudou (não perde a página/busca da tabela)
    const signature = stats.total_sessions + '-' + stats.total_pageviews;
    if (signature !== lastSignature) {
      lastSignature = signature;
      tabela.clear();
      sessions.forEach(s => tabela.row.add([
        escapeHtml(s.time),
        escapeHtml(s.ip) + (s.demo ? ' <span class="badge text-bg-secondary">demo</span>' : ''),
        escapeHtml(s.continent), escapeHtml(s.country), escapeHtml(s.city),
        escapeHtml(s.os), escapeHtml(s.browser),
        `<a class="btn btn-sm btn-outline-secondary" href="/dashboard/${encodeURIComponent(s.session)}">páginas</a>`,
      ]));
      tabela.draw(false);

      setDictData(osChart, charts.os);
      setDictData(browserChart, charts.browser);
      setDictData(countryChart, charts.country);
      setDictData(pagesChart, charts.pages);
      const hours = {};
      for (let h = 0; h < 24; h++) hours[String(h).padStart(2, '0') + 'h'] = charts.by_hour[String(h).padStart(2, '0')] || 0;
      setDictData(hourChart, hours);
    }
    setText('session-update-time', new Date().toLocaleTimeString('pt-BR'));
  }

  $('#btnDemo').on('click', async () => {
    await fetch('/api/demo', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{"n": 30}' });
    update();
  });
  $('#btnClear').on('click', async () => {
    await fetch('/api/demo', { method: 'DELETE' });
    update();
  });

  every(5000, update);
});
