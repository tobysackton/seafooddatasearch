                },
                options: getChartOptions()
            });
        }
        
        // Get chart options
        function getChartOptions() {
            const options = {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                if (context.dataset.label.includes('Volume')) {
                                    return context.dataset.label + ': ' + formatNumber(context.parsed.y);
                                } else if (context.dataset.label.includes('Price')) {
                                    return context.dataset.label + ': $' + context.parsed.y.toFixed(2);
                                }
                                return context.dataset.label + ': ' + context.parsed.y;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        position: 'left',
                        title: {
                            display: true,
                            text: state.currentMetric === 'price' ? 'Price ($)' : 'Volume'
                        },
                        ticks: state.currentMetric === 'price' ? {
                            callback: value => '$' + value.toFixed(2)
                        } : {}
                    }
                }
            };
            
            if (state.currentMetric === 'both') {
                options.scales.y.title.text = 'Volume';
                options.scales.y1 = {
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Price ($)'
                    },
                    grid: {
                        drawOnChartArea: false
                    },
                    ticks: {
                        callback: value => '$' + value.toFixed(2)
                    }
                };
            }
            
            return options;
        }
        
        // Export functions
        function exportChart() {
            if (!state.currentChart) {
                showStatus('error', 'No chart to export');
                return;
            }
            
            const canvas = document.getElementById('mainChart');
            const link = document.createElement('a');
            link.download = `circana_${state.chartType}_${Date.now()}.png`;
            link.href = canvas.toDataURL('image/png');
            link.click();
            
            showStatus('success', 'Chart exported');
        }
        
        function exportData() {
            if (state.primaryData.length === 0) {
                showStatus('error', 'No data to export');
                return;
            }
            
            let csv = 'Period,Segment,Year,Month,Month Display,Total Volume,Average Price\n';
            
            // Export primary data
            state.primaryData.forEach(row => {
                csv += `Primary,${row.segment},${row.year},${row.month + 1},${row.displayMonth},${row.totalVolume},${row.avgPrice.toFixed(2)}\n`;
            });
            
            // Export comparison data
            state.comparisonData.forEach(row => {
                csv += `Comparison,${row.segment},${row.year},${row.month + 1},${row.displayMonth},${row.totalVolume},${row.avgPrice.toFixed(2)}\n`;
            });
            
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `circana_data_${Date.now()}.csv`;
            link.click();
            
            setTimeout(() => URL.revokeObjectURL(url), 100);
            
            showStatus('success', 'Data exported');
        }
        
        // Utility functions
        function parseDate(dateStr) {
            if (!dateStr) return null;
            let date = new Date(dateStr);
            if (isNaN(date)) {
                const parts = dateStr.split('/');
                if (parts.length === 3) {
                    const month = parseInt(parts[0]) - 1;
                    const day = parseInt(parts[1]);
                    let year = parseInt(parts[2]);
                    if (year < 100) year += 2000;
                    date = new Date(year, month, day);
                }
            }
            return isNaN(date) ? null : date;
        }
        
        function parseNumber(value) {
            if (typeof value === 'number') return value;
            if (!value) return 0;
            const cleaned = String(value).replace(/[,$]/g, '');
            return parseFloat(cleaned) || 0;
        }
        
        function getMonthName(month) {
            const names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            return names[month];
        }
        
        function getMonthYearDisplay(monthKey) {
            const [year, month] = monthKey.split('-');
            return getMonthName(parseInt(month) - 1) + '-' + year.substr(-2);
        }
        
        function getMonthCount(startKey, endKey) {
            const [startYear, startMonth] = startKey.split('-').map(Number);
            const [endYear, endMonth] = endKey.split('-').map(Number);
            return (endYear - startYear) * 12 + (endMonth - startMonth) + 1;
        }
        
        function calculatePriorYearMonth(monthKey) {
            const [year, month] = monthKey.split('-').map(Number);
            return `${year - 1}-${String(month).padStart(2, '0')}`;
        }
        
        function formatNumber(num) {
            if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
            if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
            return num.toFixed(0);
        }
        
        function showStatus(type, message) {
            const statusEl = document.getElementById('fileStatus');
            statusEl.className = 'status-message status-' + type;
            statusEl.textContent = message;
            statusEl.classList.remove('hidden');
            
            if (type === 'success' || type === 'info') {
                setTimeout(() => {
                    statusEl.classList.add('hidden');
                }, 3000);
            }
        }
        
        // Initialize - add event listeners
        document.getElementById('primaryStart').addEventListener('change', updateDateDisplays);
        document.getElementById('primaryEnd').addEventListener('change', updateDateDisplays);
        document.getElementById('comparisonStart').addEventListener('change', updateDateDisplays);
        document.getElementById('comparisonEnd').addEventListener('change', updateDateDisplays);
        
        debug('Application initialized - v3 with enhanced chart configurations');
    </script>
</body>
</html>