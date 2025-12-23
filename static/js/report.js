/**
 * Report Module - ES6
 * Fetches analytics data and renders report charts/cards
 */

class Report {
    constructor() {
        this.section = document.getElementById('report-section');
        if (!this.section) return;

        this.charts = {};
        this.reportData = null;
        this.isLoading = false;
        this.printClass = 'print-report';

        this.cacheElements();
        this.bindEvents();

        if (!this.section.classList.contains('hidden')) {
            this.loadReportData();
        }
    }

    cacheElements() {
        this.elements = {
            refreshButton: document.getElementById('refreshReportButton'),
            generateButton: document.getElementById('generateReportButton'),
            saveButton: document.getElementById('saveReportButton'),
            reportLogger: document.getElementById('reportLogger'),
            reportDateTime: document.getElementById('reportDateTime'),
            totalLogs: document.getElementById('totalLogsCount'),
            parsedLogs: document.getElementById('parsedLogsCount'),
            unparsedLogs: document.getElementById('unparsedLogsCount'),
            parsedPercentage: document.getElementById('parsedPercentage'),
            unparsedPercentage: document.getElementById('unparsedPercentage'),
            successRate: document.getElementById('successRate'),
            parsedTableBody: document.getElementById('logParsedBody'),
            logtypeTableBody: document.getElementById('logStatsBody'),
            parsedChart: document.getElementById('parsedChart'),
            volumeChart: document.getElementById('volumeChart'),
            distributionChart: document.getElementById('distributionChart')
        };
    }

    bindEvents() {
        window.addEventListener('sectionChanged', (e) => {
            if (e.detail?.section === 'report') {
                this.loadReportData();
            }
        });

        window.addEventListener('darkModeChanged', () => this.updateChartsTheme());

        this.elements.refreshButton?.addEventListener('click', () => this.loadReportData(true));
        this.elements.generateButton?.addEventListener('click', () => this.handleGenerateReport());
        this.elements.saveButton?.addEventListener('click', () => this.handleSaveReport());
    }

    async loadReportData(showToastOnSuccess = false) {
        if (this.isLoading) return this.reportData;

        this.setLoadingState(true);

        try {
            const response = await fetch('/api/report/smartlp');
            const payload = await response.json();

            if (!response.ok || !payload.data) {
                throw new Error(payload.logger || 'Failed to load report data');
            }

            this.reportData = payload.data;
            this.populateMetrics(payload.data);
            this.updateTables(payload.data);
            this.renderCharts(payload.data);
            this.updateLogger(payload.logger || 'Report updated successfully.');

            if (showToastOnSuccess && typeof window.showToast === 'function') {
                window.showToast('Report refreshed', 'success');
            }

            return this.reportData;
        } catch (error) {
            console.error('Error loading report data:', error);
            this.updateLogger(error.message || 'Unable to load report data', true);
            if (typeof window.showToast === 'function') {
                window.showToast('Failed to load report data', 'error');
            }
            return null;
        } finally {
            this.setLoadingState(false);
        }
    }

    populateMetrics(data) {
        const parsed = data.parsed || 0;
        const unparsed = data.unparsed || 0;
        const total = data.total || parsed + unparsed;

        const parsedPct = this.getPercentage(parsed, total);
        const unparsedPct = this.getPercentage(unparsed, total);

        this.elements.totalLogs.textContent = this.formatNumber(total);
        this.elements.parsedLogs.textContent = this.formatNumber(parsed);
        this.elements.unparsedLogs.textContent = this.formatNumber(unparsed);
        this.elements.parsedPercentage.textContent = `${parsedPct}%`;
        this.elements.unparsedPercentage.textContent = `${unparsedPct}%`;
        this.elements.successRate.textContent = `${parsedPct}%`;

        if (this.elements.reportDateTime) {
            const timestamp = data.generated_at ? new Date(data.generated_at) : new Date();
            this.elements.reportDateTime.textContent = timestamp.toLocaleString();
        }
    }

    updateTables(data) {
        this.renderParsedTable(data.parsed || 0, data.unparsed || 0);
        this.renderLogtypeTable(data.logtypes || []);
    }

    renderParsedTable(parsed, unparsed) {
        const tbody = this.elements.parsedTableBody;
        if (!tbody) return;

        tbody.innerHTML = '';

        const rows = [
            { label: 'Parsed Logs', count: parsed },
            { label: 'Unparsed Logs', count: unparsed }
        ];

        rows.forEach((row) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="px-4 py-2 text-sm text-gray-700 dark:text-gray-200">${row.label}</td>
                <td class="px-4 py-2 text-sm text-right text-gray-900 dark:text-gray-100">${this.formatNumber(row.count)}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    renderLogtypeTable(logtypes) {
        const tbody = this.elements.logtypeTableBody;
        if (!tbody) return;

        tbody.innerHTML = '';

        if (!logtypes.length) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="2" class="px-4 py-4 text-center text-sm text-gray-500 dark:text-gray-400">
                        No unparsed log data available.
                    </td>
                </tr>
            `;
            return;
        }

        logtypes.forEach(([label, count]) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="px-4 py-2 text-sm text-gray-700 dark:text-gray-200">${label}</td>
                <td class="px-4 py-2 text-sm text-right text-gray-900 dark:text-gray-100">${this.formatNumber(count)}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    renderCharts(data) {
        this.renderParsedChart(data);
        this.renderVolumeChart(data);
        this.renderDistributionChart(data.logtypes || []);
    }

    renderParsedChart(data) {
        const canvas = this.elements.parsedChart;
        if (!canvas) return;

        this.destroyChart('parsed');

        const colors = this.getThemeColors();
        const parsed = data.parsed || 0;
        const unparsed = data.unparsed || 0;

        this.charts.parsed = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: ['Parsed', 'Unparsed'],
                datasets: [
                    {
                        data: [parsed, unparsed],
                        backgroundColor: [colors.parsed, colors.unparsed],
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                cutout: '65%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: colors.text }
                    }
                }
            }
        });
    }

    renderVolumeChart(data) {
        const canvas = this.elements.volumeChart;
        if (!canvas) return;

        this.destroyChart('volume');

        const colors = this.getThemeColors();
        const timeline = Array.isArray(data.volume_over_time) && data.volume_over_time.length
            ? data.volume_over_time
            : [
                { label: 'Parsed', total: data.parsed || 0 },
                { label: 'Unparsed', total: data.unparsed || 0 }
            ];

        const labels = timeline.map((item) => item.label || item.date || 'N/A');
        const totals = timeline.map((item) => item.total ?? (item.parsed || 0) + (item.unparsed || 0));

        this.charts.volume = new Chart(canvas, {
            type: 'line',
            data: {
                labels,
                datasets: [
                    {
                        label: 'Total Logs',
                        data: totals,
                        borderColor: colors.accent[0],
                        backgroundColor: colors.accent[0],
                        tension: 0.3,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        ticks: { color: colors.text },
                        grid: { color: colors.grid }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: { color: colors.text },
                        grid: { color: colors.grid }
                    }
                },
                plugins: {
                    legend: {
                        labels: { color: colors.text }
                    }
                }
            }
        });
    }

    renderDistributionChart(logtypes) {
        const canvas = this.elements.distributionChart;
        if (!canvas) return;

        this.destroyChart('distribution');

        const colors = this.getThemeColors();
        const labels = logtypes.length ? logtypes.map(([label]) => label) : ['No Data'];
        const counts = logtypes.length ? logtypes.map(([, count]) => count) : [0];

        this.charts.distribution = new Chart(canvas, {
            type: 'bar',
            data: {
                labels,
                datasets: [
                    {
                        label: 'Unparsed Logs',
                        data: counts,
                        backgroundColor: labels.map((_, idx) => colors.accent[idx % colors.accent.length])
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        ticks: { color: colors.text },
                        grid: { color: colors.grid }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: { color: colors.text },
                        grid: { color: colors.grid }
                    }
                },
                plugins: {
                    legend: {
                        labels: { color: colors.text }
                    }
                }
            }
        });
    }

    updateChartsTheme() {
        if (this.reportData) {
            this.renderCharts(this.reportData);
        }
    }

    async handleGenerateReport() {
        const data = await this.loadReportData();
        if (!data) {
            return;
        }

        this.togglePrintMode(true);

        let cleanupCalled = false;
        const cleanup = () => {
            if (cleanupCalled) return;
            cleanupCalled = true;
            this.togglePrintMode(false);
            window.removeEventListener('afterprint', cleanup);
        };

        window.addEventListener('afterprint', cleanup);

        setTimeout(() => {
            window.print();
            if (!('onafterprint' in window)) {
                setTimeout(cleanup, 500);
            }
        }, 100);
    }

    async handleSaveReport() {
        if (!this.reportData) {
            await this.loadReportData();
            if (!this.reportData) return;
        }

        const blob = new Blob([JSON.stringify(this.reportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `smartlp-report-${Date.now()}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        if (typeof window.showToast === 'function') {
            window.showToast('Report saved locally', 'success');
        }
    }

    destroyChart(key) {
        if (this.charts[key]) {
            this.charts[key].destroy();
            delete this.charts[key];
        }
    }

    togglePrintMode(enable) {
        const body = document.body;
        if (!body) return;
        body.classList.toggle(this.printClass, Boolean(enable));
    }

    setLoadingState(isLoading) {
        this.isLoading = isLoading;
        const refreshBtn = this.elements.refreshButton;
        if (!refreshBtn) return;

        refreshBtn.disabled = isLoading;
        refreshBtn.innerHTML = isLoading
            ? '<i class="fas fa-spinner fa-spin mr-2"></i>Loading'
            : '<i class="fas fa-sync-alt mr-2"></i>Refresh';
    }

    updateLogger(message, isError = false) {
        if (!this.elements.reportLogger) return;
        this.elements.reportLogger.textContent = message;
        this.elements.reportLogger.classList.toggle('text-red-500', isError);
        this.elements.reportLogger.classList.toggle('text-gray-600', !isError);
        this.elements.reportLogger.classList.toggle('dark:text-gray-400', !isError);
    }

    formatNumber(value) {
        const num = Number(value) || 0;
        return num.toLocaleString();
    }

    getPercentage(part, total) {
        if (!total) return '0.0';
        return ((part / total) * 100).toFixed(1);
    }

    getThemeColors() {
        const dark = document.documentElement.classList.contains('dark');
        return {
            text: dark ? '#f3f4f6' : '#1f2937',
            grid: dark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.08)',
            parsed: '#22c55e',
            unparsed: '#ef4444',
            accent: ['#6366f1', '#f97316', '#0ea5e9', '#a855f7', '#14b8a6']
        };
    }
}

const report = new Report();
window.report = report;
export default report;
