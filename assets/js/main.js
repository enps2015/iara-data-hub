/* ============================================
   IARA Data Hub - Main Application
   Initializes all components and manages state
   ============================================ */

// Global variables for modal
let globalData = [];
let modalChart = null;
let currentMunIndex = 0;
let municipalitiesList = [];

// ============================================
// INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', async function() {
    console.log('🌊 IARA Data Hub - Iniciando...');
    
    try {
        // Load data
        globalData = await DataUtils.loadData();
        const qualityReport = DataUtils.getLastParseReport();
        renderDataQualityNotice(qualityReport, DataUtils.getLastLoadError());
        console.log('📊 Dados carregados:', globalData.length, 'registros');

        if (globalData.length === 0) {
            console.error('IARA Data Hub interrompido: não há registros válidos para renderizar.');
            return;
        }

        // Initialize all components
        initKPIs(globalData);
        Charts.renderInjustica(globalData);
        Charts.renderTimeline(globalData);
        Charts.renderMatrix(globalData);
        renderMunicipalityCards(globalData);
        initAnimations();
        initSmoothScroll();
        initModalEvents();
        
        console.log('✅ IARA Data Hub carregado com sucesso!');
        
    } catch (error) {
        console.error('❌ Erro ao carregar IARA:', error);
    }
});

// ============================================
// DATA QUALITY NOTICE
// ============================================
function renderDataQualityNotice(report, loadError) {
    const notice = document.createElement('aside');
    notice.id = 'data-quality-notice';
    notice.setAttribute('role', loadError ? 'alert' : 'status');
    notice.style.cssText = [
        'max-width: 1200px',
        'margin: 1rem auto',
        'padding: 0.9rem 1.1rem',
        'border: 1px solid rgba(103, 232, 249, 0.35)',
        'border-radius: 12px',
        'background: rgba(8, 24, 38, 0.94)',
        'color: #d7e5ee',
        'font-size: 0.9rem',
        'line-height: 1.55'
    ].join(';');

    if (loadError || !report) {
        notice.style.borderColor = 'rgba(248, 113, 113, 0.65)';
        notice.textContent = `Não foi possível carregar os dados do observatório. ${loadError || 'Verifique o CSV e tente novamente.'}`;
    } else if (report.invalidCells > 0 || report.missingCells > 0) {
        const year2023 = globalData.filter(record => record.ano === 2023);
        const completeComparisons2023 = year2023.filter(record =>
            DataUtils.isAvailableNumber(record.coleta_esgoto) &&
            DataUtils.isAvailableNumber(record.taxa_internacoes_hidricas_10k)
        ).length;
        const comparisonNote = year2023.length > 0
            ? ` <strong>${completeComparisons2023} de ${year2023.length}</strong> registros de 2023 têm coleta de esgoto e taxa de internações simultaneamente disponíveis; o gráfico de dispersão usa apenas essas observações.`
            : '';
        if (report.invalidCells > 0) {
            notice.innerHTML = `<strong style="color:#fbbf24">Qualidade dos dados:</strong> ${report.rowCount} registros carregados. ${report.missingCells} células vazias e ${report.invalidCells} valores inválidos estão preservados como <code>N/D</code>, sem serem convertidos em zero.${comparisonNote}`;
        } else {
            notice.innerHTML = `<strong style="color:#67e8f9">Transparência dos dados:</strong> ${report.rowCount} registros carregados. ${report.missingCells} células sem informação são exibidas como <code>N/D</code>; valores ausentes não são tratados como zero.${comparisonNote}`;
        }
    }

    if (!loadError && report && report.missingCells === 0 && report.invalidCells === 0) return;
    const header = document.querySelector('.header');
    if (header && header.parentNode) {
        header.insertAdjacentElement('afterend', notice);
    } else {
        document.body.prepend(notice);
    }
}

// ============================================
// KPIs - Médias Ponderadas 2023
// ============================================
function initKPIs(data) {
    const data2023 = DataUtils.filterByYear(data, 2023);
    
    if (data2023.length === 0) {
        console.warn('⚠️ Sem dados de 2023 para KPIs');
        return;
    }
    
    // Calcular médias ponderadas por população
    // Cada indicador é agregado somente sobre registros com valor conhecido.
    const aguaData = data2023.filter(d =>
        DataUtils.isAvailableNumber(d.cobertura_agua) &&
        DataUtils.isAvailableNumber(d.populacao) &&
        d.populacao > 0
    );
    const aguaPop = aguaData.reduce((s, d) => s + d.populacao, 0);
    const aguaWeighted = aguaData.reduce((s, d) => s + (d.cobertura_agua * d.populacao), 0);
    const aguaAvg = aguaPop > 0 ? aguaWeighted / aguaPop : null;

    const esgotoData = data2023.filter(d =>
        DataUtils.isAvailableNumber(d.coleta_esgoto) &&
        DataUtils.isAvailableNumber(d.populacao) &&
        d.populacao > 0
    );
    const esgotoPop = esgotoData.reduce((s, d) => s + d.populacao, 0);
    const esgotoWeighted = esgotoData.reduce((s, d) => s + (d.coleta_esgoto * d.populacao), 0);
    const esgotoAvg = esgotoPop > 0 ? esgotoWeighted / esgotoPop : null;

    const healthData = data2023.filter(d =>
        DataUtils.isAvailableNumber(d.internacoes_hidricas_total) &&
        DataUtils.isAvailableNumber(d.populacao) &&
        d.populacao > 0
    );
    const healthPop = healthData.reduce((s, d) => s + d.populacao, 0);
    const totalCases = healthData.reduce((s, d) => s + d.internacoes_hidricas_total, 0);
    const healthCoverageComplete = data2023.length > 0 && healthData.length === data2023.length;
    const taxaAvg = healthPop > 0 && healthCoverageComplete ? (totalCases / healthPop) * 10000 : null;

    const riscoData = data2023.filter(d => DataUtils.isAvailableNumber(d.risco_climatico));
    const riscoAvg = riscoData.length > 0
        ? riscoData.reduce((s, d) => s + d.risco_climatico, 0) / riscoData.length
        : null;
    
    // Animate KPIs
    animateValue('kpi-water', 0, aguaAvg, 1500, '%');
    animateValue('kpi-sewage', 0, esgotoAvg, 1500, '%');
    animateValue('kpi-disease', 0, taxaAvg, 1500, '');
    animateValue('kpi-risk', 0, riscoAvg, 1500, '');
}

function animateValue(elementId, start, end, duration, suffix) {
    const element = document.getElementById(elementId);
    if (!element) return;
    if (!DataUtils.isAvailableNumber(end)) {
        element.textContent = 'N/D';
        return;
    }

    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const current = start + (end - start) * easeOut;
        
        element.textContent = current.toFixed(1) + suffix;
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

// ============================================
// MUNICIPALITY CARDS
// ============================================
function renderMunicipalityCards(data) {
    const grid = document.getElementById('municipality-grid');
    if (!grid) return;
    
    const municipalities = DataUtils.getMunicipalities(data);
    const data2023 = DataUtils.filterByYear(data, 2023);

    const cityImages = {
        'Belém': 'img/belem_vista_aerea.png',
        'Ananindeua': 'img/ananindeua_vista_aerea.jpg',
        'Marituba': 'img/marituba_vista_aerea.png',
        'Benevides': 'img/benevides_vista_aerea.jpg',
        'Santa Bárbara do Pará': 'img/sanatabarbara.png',
        'Santa Izabel do Pará': 'img/santaizabeldopara.jpg',
        'Castanhal': 'img/castanhal.jpg',
        'Barcarena': 'img/barcarena.png'
    };

    grid.innerHTML = municipalities.map((mun, index) => {
        const munData = data.filter(d => d.municipio === mun).sort((a, b) => a.ano - b.ano);
        const record2023 = data2023.find(d => d.municipio === mun);
        const cityName = mun.split('(')[0].trim();
        const bgImage = cityImages[cityName] || 'img/belem_vista_do_rio02.png';
        
        // Values
        const aguaVal = record2023?.cobertura_agua ?? null;
        const esgotoVal = record2023?.coleta_esgoto ?? null;
        const internVal = record2023?.taxa_internacoes_hidricas_10k ?? null;

        // Valores ausentes ficam como null para o gráfico interromper a linha.
        const sparkData = munData.map(d => d.taxa_internacoes_hidricas_10k ?? null);
        const canvasId = `spark-${index}`;
        
        // Generate insight phrase
        let insight = '';
        if (DataUtils.isAvailableNumber(aguaVal) && DataUtils.isAvailableNumber(internVal) && aguaVal > 80 && internVal > 5) {
            insight = `Em 2023, a cobertura de água registrada é ${aguaVal.toFixed(0)}% e a taxa CID A00–A09 é ${internVal.toFixed(1)}/10k hab.; a associação não demonstra causalidade nem via de transmissão.`;
        } else if (DataUtils.isAvailableNumber(esgotoVal) && esgotoVal < 5) {
            insight = `A coleta de esgoto registrada é ${esgotoVal.toFixed(1)}%. Avalie o contexto e a cobertura dos dados.`;
        } else if (DataUtils.isAvailableNumber(internVal) && internVal > 6) {
            insight = `Taxa registrada no grupo CID A00–A09: ${internVal.toFixed(1)}/10k hab.; a classificação não comprova transmissão hídrica.`;
        } else if (!DataUtils.isAvailableNumber(aguaVal) || !DataUtils.isAvailableNumber(esgotoVal) || !DataUtils.isAvailableNumber(internVal)) {
            insight = 'Há indicadores sem informação em 2023. Consulte a matriz de cobertura antes de comparar municípios.';
        } else {
            insight = 'Dados de 2023 disponíveis. Monitoramento contínuo necessário.';
        }

        // Render sparkline after DOM update
        setTimeout(() => Charts.renderSparkline(canvasId, sparkData), 150);

        return `
            <div class="municipality-card fade-in" data-municipality="${mun}" onclick="openModal('${mun}')" style="transition-delay: ${index * 0.05}s">
                <div class="municipality-image" style="background-image: url('${bgImage}')">
                    <span class="municipality-name">${cityName}</span>
                </div>
                
                <div class="municipality-body">
                    <div class="municipality-metrics">
                        <div class="metric">
                            <div class="metric-value cyan">${DataUtils.formatNumber(aguaVal, 1, '%')}</div>
                            <div class="metric-label">Água</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value magenta">${DataUtils.formatNumber(esgotoVal, 1, '%')}</div>
                            <div class="metric-label">Esgoto</div>
                        </div>
                    </div>

                    <div class="sparkline-container">
                        <canvas id="${canvasId}"></canvas>
                    </div>
                    
                    <div class="municipality-insight">
                        💡 ${insight}
                    </div>
                    
                    <div style="margin-top: 0.75rem; text-align: center;">
                        <span style="font-size: 0.75rem; color: var(--accent-cyan); font-weight: 600;">
                            <i class="fas fa-expand"></i> Clique para detalhes
                        </span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// ============================================
// MODAL FUNCTIONALITY
// ============================================
function initModalEvents() {
    const modal = document.getElementById('municipalityModal');
    if (!modal) return;
    
    // Close on overlay click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });
    
    // Close on ESC key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            closeModal();
        }
    });
}

function openModal(municipality) {
    const modal = document.getElementById('municipalityModal');
    if (!modal || !globalData.length) return;
    
    // Initialize municipalities list if not done
    if (municipalitiesList.length === 0) {
        municipalitiesList = DataUtils.getMunicipalities(globalData);
    }
    
    // Find current index
    currentMunIndex = municipalitiesList.indexOf(municipality);
    if (currentMunIndex === -1) currentMunIndex = 0;
    
    const cityName = municipality.split('(')[0].trim();
    const munData = globalData.filter(d => d.municipio === municipality).sort((a, b) => a.ano - b.ano);
    const record2023 = munData.find(d => d.ano === 2023);
    
    // Update title
    document.getElementById('modalTitle').textContent = cityName;
    document.getElementById('modalSubtitle').textContent = `Série histórica completa: ${munData.length} anos de dados`;
    
    // Update KPIs
    document.getElementById('modalAgua').textContent = DataUtils.formatNumber(record2023?.cobertura_agua, 1, '%');
    document.getElementById('modalEsgoto').textContent = DataUtils.formatNumber(record2023?.coleta_esgoto, 1, '%');
    document.getElementById('modalIntern').textContent = DataUtils.formatNumber(record2023?.taxa_internacoes_hidricas_10k, 1);
    document.getElementById('modalRisco').textContent = DataUtils.formatNumber(record2023?.risco_climatico, 2);
    
    // Render chart
    renderModalChart(munData);
    
    // Render comparison bars
    renderComparisonBars(municipality, record2023);
    
    // Render quick reading
    renderQuickReading(cityName, munData, record2023);
    
    // Update counter
    document.getElementById('modalCounter').textContent = `${currentMunIndex + 1} / ${municipalitiesList.length}`;
    
    // Show modal
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    const modal = document.getElementById('municipalityModal');
    if (!modal) return;
    
    modal.classList.remove('active');
    document.body.style.overflow = '';
    
    // Destroy chart
    if (modalChart) {
        modalChart.destroy();
        modalChart = null;
    }
}

function navigateModal(direction) {
    if (municipalitiesList.length === 0) return;
    
    currentMunIndex += direction;
    
    // Wrap around
    if (currentMunIndex < 0) currentMunIndex = municipalitiesList.length - 1;
    if (currentMunIndex >= municipalitiesList.length) currentMunIndex = 0;
    
    openModal(municipalitiesList[currentMunIndex]);
}

function renderQuickReading(cityName, munData, record2023) {
    const container = document.getElementById('quickReadContent');
    if (!container) return;
    
    // Find peak internations
    const peakRecord = munData
        .filter(d => DataUtils.isAvailableNumber(d.taxa_internacoes_hidricas_10k) && d.taxa_internacoes_hidricas_10k > 0)
        .sort((a, b) => b.taxa_internacoes_hidricas_10k - a.taxa_internacoes_hidricas_10k)[0];
    
    // Find water trend
    const agua2019 = munData.find(d => d.ano === 2019)?.cobertura_agua ?? null;
    const agua2023 = record2023?.cobertura_agua ?? null;

    // Comparar apenas municípios com indicador e população informados.
    const data2023 = DataUtils.filterByYear(globalData, 2023);
    const rmbEsgotoPop = data2023.filter(d =>
        DataUtils.isAvailableNumber(d.coleta_esgoto) &&
        DataUtils.isAvailableNumber(d.populacao) &&
        d.populacao > 0
    );
    const totalPop = rmbEsgotoPop.reduce((s, d) => s + d.populacao, 0);
    const rmbEsgoto = totalPop > 0
        ? rmbEsgotoPop.reduce((s, d) => s + (d.coleta_esgoto * d.populacao), 0) / totalPop
        : null;

    const esgoto2023 = record2023?.coleta_esgoto ?? null;
    const canCompareSewage = DataUtils.isAvailableNumber(esgoto2023) && DataUtils.isAvailableNumber(rmbEsgoto);
    const comparison = canCompareSewage ? (esgoto2023 >= rmbEsgoto ? 'igual ou acima' : 'abaixo') : null;
    const compColor = canCompareSewage
        ? (esgoto2023 >= rmbEsgoto ? 'var(--accent-lime)' : 'var(--accent-magenta)')
        : 'var(--text-light-muted)';
    
    let html = '<ul style="margin: 0; padding-left: 1rem">';
    
    if (peakRecord) {
        html += `<li><strong>Pico da taxa registrada CID A00–A09 em ${peakRecord.ano}:</strong> ${peakRecord.taxa_internacoes_hidricas_10k.toFixed(1)} por 10 mil hab.</li>`;
    }
    
    if (DataUtils.isAvailableNumber(agua2019) && DataUtils.isAvailableNumber(agua2023)) {
        const trend = agua2023 > agua2019 ? 'sobe' : 'cai';
        html += `<li><strong>Cobertura de água ${trend}</strong> de ${agua2019.toFixed(0)}% para ${agua2023.toFixed(0)}% entre 2019 e 2023.</li>`;
    }
    
    if (DataUtils.isAvailableNumber(esgoto2023)) {
        html += `<li>Coleta de esgoto ${esgoto2023 < 50 ? '<strong style="color: var(--accent-magenta)">permanece abaixo de 50%</strong>' : `está em ${esgoto2023.toFixed(0)}%`} em 2023.</li>`;
    } else {
        html += '<li>Coleta de esgoto: N/D em 2023; não é possível avaliar esse indicador neste ano.</li>';
    }

    if (canCompareSewage) {
        html += `<li style="margin-top: 0.5rem; color: ${compColor}"><strong>Coleta de esgoto deste município está ${comparison} da média calculada com dados disponíveis da RMB.</strong></li>`;
    } else {
        html += '<li style="margin-top: 0.5rem">Comparação com a média da RMB indisponível por falta de dados completos.</li>';
    }
    html += '</ul>';
    
    container.innerHTML = html;
}

function renderModalChart(munData) {
    const ctx = document.getElementById('modalChart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (modalChart) {
        modalChart.destroy();
    }
    
    const years = munData.map(d => d.ano);
    const internData = munData.map(d => d.taxa_internacoes_hidricas_10k ?? null);
    const aguaData = munData.map(d => d.cobertura_agua ?? null);
    const esgotoData = munData.map(d => d.coleta_esgoto ?? null);
    
    modalChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: years,
            datasets: [
                {
                    label: 'CID A00–A09/10k',
                    data: internData,
                    borderColor: '#ec4899',
                    backgroundColor: 'rgba(236, 72, 153, 0.1)',
                    yAxisID: 'y',
                    tension: 0.4,
                    pointBackgroundColor: '#ec4899',
                    pointRadius: 6,
                    pointHoverRadius: 9,
                    fill: true,
                    borderWidth: 3
                },
                {
                    label: 'Água (%)',
                    data: aguaData,
                    borderColor: '#22d3ee',
                    backgroundColor: 'rgba(34, 211, 238, 0.05)',
                    yAxisID: 'y1',
                    tension: 0.4,
                    pointBackgroundColor: '#22d3ee',
                    pointRadius: 5,
                    pointHoverRadius: 8,
                    fill: true,
                    borderWidth: 2
                },
                {
                    label: 'Esgoto (%)',
                    data: esgotoData,
                    borderColor: '#a3e635',
                    backgroundColor: 'rgba(163, 230, 53, 0.05)',
                    yAxisID: 'y1',
                    tension: 0.4,
                    pointBackgroundColor: '#a3e635',
                    pointRadius: 5,
                    pointHoverRadius: 8,
                    fill: true,
                    borderWidth: 2,
                    borderDash: [5, 5]
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
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#0f172a',
                    titleColor: '#fff',
                    bodyColor: '#94a3b8',
                    borderColor: '#22d3ee',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true
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
                        text: 'Cobertura (%)', 
                        color: '#22d3ee',
                        font: { weight: 'bold' }
                    },
                    grid: { drawOnChartArea: false },
                    ticks: { color: '#94a3b8' },
                    max: 100,
                    min: 0
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
}

function renderComparisonBars(municipality, record2023) {
    const container = document.getElementById('comparisonBars');
    if (!container) return;
    
    // Calculate RMB averages
    const data2023 = DataUtils.filterByYear(globalData, 2023);
    const aguaData = data2023.filter(d =>
        DataUtils.isAvailableNumber(d.cobertura_agua) &&
        DataUtils.isAvailableNumber(d.populacao) && d.populacao > 0
    );
    const aguaPop = aguaData.reduce((s, d) => s + d.populacao, 0);
    const rmbAgua = aguaPop > 0
        ? aguaData.reduce((s, d) => s + (d.cobertura_agua * d.populacao), 0) / aguaPop
        : null;

    const esgotoData = data2023.filter(d =>
        DataUtils.isAvailableNumber(d.coleta_esgoto) &&
        DataUtils.isAvailableNumber(d.populacao) && d.populacao > 0
    );
    const esgotoPop = esgotoData.reduce((s, d) => s + d.populacao, 0);
    const rmbEsgoto = esgotoPop > 0
        ? esgotoData.reduce((s, d) => s + (d.coleta_esgoto * d.populacao), 0) / esgotoPop
        : null;

    const healthData = data2023.filter(d =>
        DataUtils.isAvailableNumber(d.internacoes_hidricas_total) &&
        DataUtils.isAvailableNumber(d.populacao) && d.populacao > 0
    );
    const healthPop = healthData.reduce((s, d) => s + d.populacao, 0);
    const totalCases = healthData.reduce((s, d) => s + d.internacoes_hidricas_total, 0);
    const rmbIntern = healthPop > 0 ? (totalCases / healthPop) * 10000 : null;

    const munAgua = record2023?.cobertura_agua ?? null;
    const munEsgoto = record2023?.coleta_esgoto ?? null;
    const munIntern = record2023?.taxa_internacoes_hidricas_10k ?? null;
    
    const bars = [
        { label: 'Água', value: munAgua, max: 100, rmb: rmbAgua, color: 'cyan' },
        { label: 'Esgoto', value: munEsgoto, max: 100, rmb: rmbEsgoto, color: 'cyan' },
        { label: 'Internações', value: munIntern, max: 40, rmb: rmbIntern, color: 'magenta' }
    ];
    
    container.innerHTML = bars.map(bar => {
        const hasValue = DataUtils.isAvailableNumber(bar.value);
        const hasReference = DataUtils.isAvailableNumber(bar.rmb);
        const munWidth = hasValue ? Math.min((bar.value / bar.max) * 100, 100) : 0;
        const rmbWidth = hasReference ? Math.min((bar.rmb / bar.max) * 100, 100) : 0;
        const comparison = hasValue && hasReference
            ? (bar.value > bar.rmb ? '↑' : bar.value < bar.rmb ? '↓' : '=')
            : '';
        const compColor = !hasValue || !hasReference
            ? 'var(--text-light-muted)'
            : (bar.label === 'Internações'
                ? (bar.value > bar.rmb ? '#ec4899' : '#a3e635')
                : (bar.value > bar.rmb ? '#a3e635' : '#ec4899'));

        return `
            <div class="comparison-bar-item">
                <span class="comparison-bar-label">${bar.label}</span>
                <div class="comparison-bar-track">
                    <div class="comparison-bar-fill ${bar.color}" style="width: ${munWidth}%"></div>
                    ${hasReference ? `<div title="Referência RMB: ${bar.rmb.toFixed(1)}" style="position: absolute; left: ${rmbWidth}%; top: 0; bottom: 0; width: 2px; background: #fbbf24; opacity: 0.8;"></div>` : ''}
                </div>
                <span class="comparison-bar-value" style="color: ${compColor}">
                    ${hasValue ? `${bar.value.toFixed(1)}${bar.label !== 'Internações' ? '%' : ''}` : 'N/D'} ${comparison}
                </span>
            </div>
        `;
    }).join('');
}

// ============================================
// ANIMATIONS (Intersection Observer)
// ============================================
function initAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });

    // Observe all animated elements
    document.querySelectorAll('.fade-in, .fade-in-left, .fade-in-right').forEach(el => {
        observer.observe(el);
    });
}

// ============================================
// SMOOTH SCROLL
// ============================================
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                const headerHeight = 64; // Header height
                const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - headerHeight;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
}
