(function() {
    'use strict';

    const CHART_CONFIG = {
        datasets: [
            { label: 'Total', field: 'total', color: '#417690' },
            { label: 'Sucesso', field: 'sucesso', color: '#155724' },
            { label: 'Falha', field: 'falha', color: '#721c24' },
            { label: 'Processando', field: 'processando', color: '#856404' },
        ],
    };

    function buildDataset(label, field, color) {
        const series = window.dashboardChartData || [];
        return {
            label,
            data: series.map(point => point[field]),
            borderColor: color,
            backgroundColor: color,
            tension: 0.25,
            pointRadius: 2,
            fill: false,
        };
    }

    function initChart() {
        const canvas = document.getElementById('solicitacoes-series-chart');
        if (!canvas) {
            console.warn('Canvas element #solicitacoes-series-chart not found');
            return;
        }

        const series = window.dashboardChartData || [];
        
        if (!series || series.length === 0) {
            console.warn('No data available for dashboard chart');
            canvas.parentElement.style.display = 'none';
            return;
        }

        const labels = series.map(point => point.date);
        
        const datasets = CHART_CONFIG.datasets.map(cfg =>
            buildDataset(cfg.label, cfg.field, cfg.color)
        );

        try {
            new Chart(canvas, {
                type: 'line',
                data: { labels, datasets },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
                    plugins: {
                        legend: { display: true },
                        tooltip: {
                            callbacks: {
                                label: ctx => `${ctx.dataset.label}: ${ctx.formattedValue}`,
                            },
                        },
                    },
                    scales: {
                        x: {
                            title: { display: true, text: 'Data' },
                        },
                        y: {
                            beginAtZero: true,
                            title: { display: true, text: 'Solicitações' },
                        },
                    },
                },
            });
        } catch (error) {
            console.error('Error initializing chart:', error);
        }
    }

    // Inicializa quando o DOM está pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initChart);
    } else {
        initChart();
    }
})();
