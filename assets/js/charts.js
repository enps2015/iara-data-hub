/* ============================================
   IARA Data Hub - Charts Module
   Nova paleta: Ciano/Magenta/Laranja/Lima
   ============================================ */

const Charts = {
    
    // ============================================
    // MAPA DA INJUSTIÇA HÍDRICA 2023
    // Scatter com quadrantes e labels
    // ============================================
    renderInjustica(data) {
        const ctx = document.getElementById('chartInjustica');
        if (!ctx) return;
        
        const data2023 = DataUtils.filterByYear(data, 2023);
        
        // Usar apenas observações com os dois indicadores disponíveis.
        // Ausência de dado não equivale a cobertura ou internação igual a zero.
        const completeCases = data2023.filter(d =>
            DataUtils.isAvailableNumber(d.coleta_esgoto) &&
            DataUtils.isAvailableNumber(d.taxa_internacoes_hidricas_10k)
        );
        const esgotoValues = completeCases.map(d => d.coleta_esgoto);
        const internValues = completeCases.map(d => d.taxa_internacoes_hidricas_10k);
        
        const medianEsgoto = esgotoValues.length > 0 
            ? esgotoValues.sort((a,b) => a-b)[Math.floor(esgotoValues.length/2)] 
            : 15;
        const medianIntern = internValues.length > 0 
            ? internValues.sort((a,b) => a-b)[Math.floor(internValues.length/2)] 
            : 5;
        
        const scatterData = completeCases.map(d => ({
            x: d.coleta_esgoto,
            y: d.taxa_internacoes_hidricas_10k,
            r: DataUtils.isAvailableNumber(d.populacao) && d.populacao > 0
                ? Math.max(Math.sqrt(d.populacao) / 25, 8)
                : 8,
            municipio: d.municipio.split('(')[0].trim(),
            populacao: d.populacao
        }));

        new Chart(ctx, {
            type: 'bubble',
            data: {
                datasets: [{
                    label: 'Municípios',
                    data: scatterData,
                    backgroundColor: scatterData.map(d => {
                        // Alto risco: canto superior esquerdo
                        if (d.y > medianIntern && d.x < medianEsgoto) {
                            return 'rgba(236, 72, 153, 0.7)'; // Magenta
                        }
                        return 'rgba(34, 211, 238, 0.7)'; // Ciano
                    }),
                    borderColor: scatterData.map(d => {
                        if (d.y > medianIntern && d.x < medianEsgoto) {
                            return '#ec4899';
                        }
                        return '#22d3ee';
                    }),
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#0f172a',
                        titleColor: '#fff',
                        bodyColor: '#94a3b8',
                        borderColor: '#22d3ee',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                const p = context.raw;
                                return [
                                    `${p.municipio}`,
                                    `Esgoto: ${p.x.toFixed(1)}%`,
                                    `CID A00–A09: ${p.y.toFixed(1)}/10k`,
                                    `População: ${DataUtils.isAvailableNumber(p.populacao) ? (p.populacao / 1000).toFixed(0) + 'k' : 'N/D'}`
                                ];
                            }
                        }
                    },
                    annotation: {
                        annotations: {
                            // Linha mediana vertical (esgoto)
                            lineEsgoto: {
                                type: 'line',
                                xMin: medianEsgoto,
                                xMax: medianEsgoto,
                                borderColor: 'rgba(255, 255, 255, 0.3)',
                                borderWidth: 2,
                                borderDash: [6, 4],
                                label: {
                                    display: true,
                                    content: 'Mediana Esgoto',
                                    position: 'start',
                                    backgroundColor: 'rgba(15, 23, 42, 0.8)',
                                    color: '#94a3b8',
                                    font: { size: 10 }
                                }
                            },
                            // Linha mediana horizontal (internações)
                            lineIntern: {
                                type: 'line',
                                yMin: medianIntern,
                                yMax: medianIntern,
                                borderColor: 'rgba(255, 255, 255, 0.3)',
                                borderWidth: 2,
                                borderDash: [6, 4],
                                label: {
                                    display: true,
                                    content: 'Mediana taxa CID A00–A09',
                                    position: 'end',
                                    backgroundColor: 'rgba(15, 23, 42, 0.8)',
                                    color: '#94a3b8',
                                    font: { size: 10 }
                                }
                            },
                            // Zona crítica (canto superior esquerdo)
                            zonaCritica: {
                                type: 'box',
                                xMin: 0,
                                xMax: medianEsgoto,
                                yMin: medianIntern,
                                yMax: 15,
                                backgroundColor: 'rgba(236, 72, 153, 0.1)',
                                borderWidth: 0
                            },
                            // Quadrant labels
                            labelCritico: {
                                type: 'label',
                                xValue: 5,
                                yValue: 12,
                                content: ['⚠️ ALERTA RELATIVO', 'Coleta abaixo da mediana', 'Taxa CID A00–A09 acima da mediana'],
                                backgroundColor: 'rgba(236, 72, 153, 0.2)',
                                color: '#ec4899',
                                font: { size: 10, weight: 'bold' },
                                padding: 6,
                                borderRadius: 4
                            },
                            labelIdeal: {
                                type: 'label',
                                xValue: 40,
                                yValue: 2,
                                content: ['✓ QUADRANTE FAVORÁVEL', 'Coleta acima da mediana', 'Taxa CID A00–A09 abaixo da mediana'],
                                backgroundColor: 'rgba(34, 211, 238, 0.2)',
                                color: '#22d3ee',
                                font: { size: 10, weight: 'bold' },
                                padding: 6,
                                borderRadius: 4
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: { 
                            display: true, 
                            text: 'Coleta de Esgoto (%)', 
                            color: '#94a3b8',
                            font: { size: 13, weight: 'bold' }
                        },
                        grid: { color: 'rgba(148, 163, 184, 0.1)' },
                        ticks: { color: '#94a3b8' },
                        min: 0,
                        max: 50
                    },
                    y: {
                        title: { 
                            display: true, 
                            text: 'Taxa CID A00–A09 (por 10 mil hab)', 
                            color: '#94a3b8',
                            font: { size: 13, weight: 'bold' }
                        },
                        grid: { color: 'rgba(148, 163, 184, 0.1)' },
                        ticks: { color: '#94a3b8' },
                        min: 0
                    }
                }
            }
        });
    },

    // ============================================
    // LINHA DO TEMPO 2017-2025
    // Com marcação COP30 e faixa de aceleração
    // ============================================
    renderTimeline(data) {
        const ctx = document.getElementById('chartTimeline');
        if (!ctx) return;
        
        const years = DataUtils.getYears(data);
        
        // Agregados da RMB por ano
        const internTrend = years.map(year => {
            const yearData = DataUtils.filterByYear(data, year);
            const healthData = yearData.filter(d =>
                DataUtils.isAvailableNumber(d.populacao) &&
                d.populacao > 0 &&
                DataUtils.isAvailableNumber(d.internacoes_hidricas_total)
            );
            const totalPop = healthData.reduce((sum, d) => sum + d.populacao, 0);
            const totalCases = healthData.reduce((sum, d) => sum + d.internacoes_hidricas_total, 0);
            const completeCoverage = yearData.length > 0 && healthData.length === yearData.length;
            return completeCoverage && totalPop > 0 ? (totalCases / totalPop) * 10000 : null;
        });
        
        const esgotoTrend = years.map(year => {
            const yearData = DataUtils.filterByYear(data, year).filter(d =>
                DataUtils.isAvailableNumber(d.coleta_esgoto) &&
                DataUtils.isAvailableNumber(d.populacao) &&
                d.populacao > 0
            );
            if (yearData.length === 0) return null;
            const totalPop = yearData.reduce((s, d) => s + d.populacao, 0);
            const weighted = yearData.reduce((s, d) => s + (d.coleta_esgoto * d.populacao), 0);
            return totalPop > 0 ? weighted / totalPop : null;
        });

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: years,
                datasets: [
                    {
                        label: 'CID A00–A09 (por 10k)',
                        data: internTrend,
                        borderColor: '#ec4899',
                        backgroundColor: 'rgba(236, 72, 153, 0.1)',
                        yAxisID: 'y',
                        tension: 0.3,
                        pointBackgroundColor: '#ec4899',
                        pointRadius: 5,
                        pointHoverRadius: 8,
                        fill: true,
                        borderWidth: 3
                    },
                    {
                        label: 'Esgoto (%)',
                        data: esgotoTrend,
                        borderColor: '#22d3ee',
                        backgroundColor: 'rgba(34, 211, 238, 0.1)',
                        yAxisID: 'y1',
                        tension: 0.3,
                        pointBackgroundColor: '#22d3ee',
                        pointRadius: 5,
                        pointHoverRadius: 8,
                        fill: true,
                        borderWidth: 3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        display: false // Usando legenda customizada no HTML
                    },
                    tooltip: {
                        backgroundColor: '#0f172a',
                        titleColor: '#fff',
                        bodyColor: '#94a3b8',
                        borderColor: '#22d3ee',
                        borderWidth: 1
                    },
                    annotation: {
                        annotations: {
                            // Faixa de aceleração 2019-2023
                            faixaAceleracao: {
                                type: 'box',
                                xMin: '2019',
                                xMax: '2023',
                                backgroundColor: 'rgba(255, 255, 255, 0.05)',
                                borderWidth: 0
                            },
                            // Linha COP30
                            cop30: {
                                type: 'line',
                                xMin: '2025',
                                xMax: '2025',
                                borderColor: '#fbbf24',
                                borderWidth: 3,
                                borderDash: [8, 4],
                                label: {
                                    display: true,
                                    content: 'COP30',
                                    position: 'start',
                                    backgroundColor: '#fbbf24',
                                    color: '#0f172a',
                                    font: { size: 12, weight: 'bold' },
                                    padding: 6
                                }
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: { 
                            display: true, 
                            text: 'CID A00–A09/10k', 
                            color: '#ec4899',
                            font: { weight: 'bold' }
                        },
                        grid: { color: 'rgba(148, 163, 184, 0.1)' },
                        ticks: { color: '#94a3b8' }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: { 
                            display: true, 
                            text: 'Esgoto (%)', 
                            color: '#22d3ee',
                            font: { weight: 'bold' }
                        },
                        grid: { drawOnChartArea: false },
                        ticks: { color: '#94a3b8' },
                        max: 50
                    },
                    x: {
                        grid: { color: 'rgba(148, 163, 184, 0.1)' },
                        ticks: { 
                            color: '#94a3b8',
                            font: { weight: 'bold' }
                        }
                    }
                }
            }
        });
    },

    // ============================================
    // MATRIZ DE DADOS (APAGÃO)
    // ============================================
    renderMatrix(data) {
        const container = document.getElementById('matrixContainer');
        if (!container) return;
        
        const municipalities = DataUtils.getMunicipalities(data);
        const years = DataUtils.getYears(data);
        
        // Count cells
        let totalCells = 0;
        let cellsWithData = 0;
        let cellsWithoutData = 0;
        
        let html = '<table class="w-full text-left border-collapse min-w-[600px]">';
        
        // Header
        html += '<thead><tr><th class="p-3">Município</th>';
        years.forEach(y => {
            const isCop = y === 2025;
            html += `<th class="p-2 text-center ${isCop ? 'bg-amber-500/20 rounded' : ''}">${y}</th>`;
        });
        html += '</tr></thead><tbody>';
        
        // Rows
        municipalities.forEach(mun => {
            const cityName = mun.split('(')[0].trim();
            html += `<tr class="border-b border-slate-700/50"><td class="p-3 font-medium text-white">${cityName}</td>`;
            
            years.forEach(y => {
                totalCells++;
                const record = data.find(d => d.municipio === mun && d.ano === y);
                const hasData = record && (
                    DataUtils.isAvailableNumber(record.cobertura_agua) ||
                    DataUtils.isAvailableNumber(record.coleta_esgoto)
                );
                
                if (hasData) {
                    cellsWithData++;
                } else {
                    cellsWithoutData++;
                }
                
                const cellClass = hasData ? 'has-data' : 'no-data';
                const title = hasData
                    ? `${cityName} ${y}: Água ${DataUtils.formatNumber(record.cobertura_agua, 0, '%')}, Esgoto ${DataUtils.formatNumber(record.coleta_esgoto, 0, '%')}`
                    : `${cityName} ${y}: SEM DADOS - Gestão no escuro`;
                
                html += `<td class="p-2"><div class="matrix-cell ${cellClass}" title="${title}"></div></td>`;
            });
            
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        container.innerHTML = html;
        
        // Update cell counter
        const counterEl = document.getElementById('matrixCellCount');
        if (counterEl) {
            const pctWithoutData = ((cellsWithoutData / totalCells) * 100).toFixed(0);
            counterEl.innerHTML = `
                <i class="fas fa-calculator mr-2" style="color: var(--accent-magenta)"></i>
                <strong>${totalCells}</strong> células município×ano | 
                <strong style="color: var(--accent-cyan)">${cellsWithData}</strong> com dados | 
                <strong style="color: var(--accent-magenta)">${cellsWithoutData}</strong> em apagão 
                (<strong style="color: var(--accent-magenta)">${pctWithoutData}%</strong> de lacunas)
            `;
        }
    },

    // ============================================
    // SPARKLINES para Cards Municipais
    // ============================================
    renderSparkline(canvasId, dataPoints) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: dataPoints.map((_, i) => i),
                datasets: [{
                    data: dataPoints.map(value => DataUtils.isAvailableNumber(value) ? value : null),
                    borderColor: '#ec4899',
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: true,
                    backgroundColor: 'rgba(236, 72, 153, 0.15)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { 
                    legend: { display: false }, 
                    tooltip: { enabled: false } 
                },
                scales: {
                    x: { display: false },
                    y: { display: false, min: 0 }
                },
                layout: { padding: 0 },
                elements: {
                    line: { tension: 0.4 }
                }
            }
        });
    }
};
