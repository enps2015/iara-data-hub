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
        console.log('📊 Dados carregados:', globalData.length, 'registros');
        
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
// KPIs - Médias Ponderadas 2023
// ============================================
function initKPIs(data) {
    const data2023 = DataUtils.filterByYear(data, 2023);
    
    if (data2023.length === 0) {
        console.warn('⚠️ Sem dados de 2023 para KPIs');
        return;
    }
    
    // Calcular médias ponderadas por população
    const totalPop = data2023.reduce((s, d) => s + (d.populacao || 0), 0);
    
    // Cobertura de água (ponderada)
    const aguaData = data2023.filter(d => d.cobertura_agua > 0);
    const aguaPop = aguaData.reduce((s, d) => s + (d.populacao || 0), 0);
    const aguaWeighted = aguaData.reduce((s, d) => s + (d.cobertura_agua * (d.populacao || 0)), 0);
    const aguaAvg = aguaPop > 0 ? (aguaWeighted / aguaPop) : 0;
    
    // Coleta de esgoto (ponderada)
    const esgotoData = data2023.filter(d => d.coleta_esgoto > 0);
    const esgotoPop = esgotoData.reduce((s, d) => s + (d.populacao || 0), 0);
    const esgotoWeighted = esgotoData.reduce((s, d) => s + (d.coleta_esgoto * (d.populacao || 0)), 0);
    const esgotoAvg = esgotoPop > 0 ? (esgotoWeighted / esgotoPop) : 0;
    
    // Taxa de internações (agregada)
    const totalCases = data2023.reduce((s, d) => s + (d.internacoes_hidricas_total || 0), 0);
    const taxaAvg = totalPop > 0 ? (totalCases / totalPop) * 10000 : 0;
    
    // Risco climático (média simples)
    const riscoData = data2023.filter(d => d.risco_climatico > 0);
    const riscoAvg = riscoData.length > 0 
        ? riscoData.reduce((s, d) => s + d.risco_climatico, 0) / riscoData.length 
        : 0;
    
    // Animate KPIs
    animateValue('kpi-water', 0, aguaAvg, 1500, '%');
    animateValue('kpi-sewage', 0, esgotoAvg, 1500, '%');
    animateValue('kpi-disease', 0, taxaAvg, 1500, '');
    animateValue('kpi-risk', 0, riscoAvg, 1500, '');
}

function animateValue(elementId, start, end, duration, suffix) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
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
        const aguaVal = record2023?.cobertura_agua || 0;
        const esgotoVal = record2023?.coleta_esgoto || 0;
        const internVal = record2023?.taxa_internacoes_hidricas_10k || 0;
        
        // Sparkline data
        const sparkData = munData.map(d => d.taxa_internacoes_hidricas_10k || 0);
        const canvasId = `spark-${index}`;
        
        // Generate insight phrase
        let insight = '';
        if (aguaVal > 80 && internVal > 5) {
            insight = `Mesmo com ${aguaVal.toFixed(0)}% de água, as internações seguem em ${internVal.toFixed(1)}/10k hab.`;
        } else if (esgotoVal < 5) {
            insight = `Apenas ${esgotoVal.toFixed(1)}% de coleta de esgoto. Prioridade crítica.`;
        } else if (internVal > 6) {
            insight = `Taxa de internação de ${internVal.toFixed(1)}/10k hab indica pressão no sistema de saúde.`;
        } else {
            insight = `Dados de 2023. Monitoramento contínuo necessário.`;
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
                            <div class="metric-value cyan">${aguaVal.toFixed(1)}%</div>
                            <div class="metric-label">Água</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value magenta">${esgotoVal.toFixed(1)}%</div>
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
    document.getElementById('modalAgua').textContent = record2023?.cobertura_agua ? 
        `${record2023.cobertura_agua.toFixed(1)}%` : 'N/D';
    document.getElementById('modalEsgoto').textContent = record2023?.coleta_esgoto ? 
        `${record2023.coleta_esgoto.toFixed(1)}%` : 'N/D';
    document.getElementById('modalIntern').textContent = record2023?.taxa_internacoes_hidricas_10k ? 
        record2023.taxa_internacoes_hidricas_10k.toFixed(1) : 'N/D';
    document.getElementById('modalRisco').textContent = record2023?.risco_climatico ? 
        record2023.risco_climatico.toFixed(2) : 'N/D';
    
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
    const peakRecord = munData.filter(d => d.taxa_internacoes_hidricas_10k > 0)
        .sort((a, b) => (b.taxa_internacoes_hidricas_10k || 0) - (a.taxa_internacoes_hidricas_10k || 0))[0];
    
    // Find water trend
    const agua2019 = munData.find(d => d.ano === 2019)?.cobertura_agua || 0;
    const agua2023 = record2023?.cobertura_agua || 0;
    
    // Calculate RMB average for comparison
    const data2023 = DataUtils.filterByYear(globalData, 2023);
    const rmbEsgotoPop = data2023.filter(d => d.coleta_esgoto > 0);
    const totalPop = rmbEsgotoPop.reduce((s, d) => s + (d.populacao || 0), 0);
    const rmbEsgoto = totalPop > 0 ? rmbEsgotoPop.reduce((s, d) => s + (d.coleta_esgoto * (d.populacao || 0)), 0) / totalPop : 0;
    
    const esgoto2023 = record2023?.coleta_esgoto || 0;
    const comparison = esgoto2023 >= rmbEsgoto ? 'acima' : 'abaixo';
    const compColor = esgoto2023 >= rmbEsgoto ? 'var(--accent-lime)' : 'var(--accent-magenta)';
    
    let html = '<ul style="margin: 0; padding-left: 1rem">';
    
    if (peakRecord) {
        html += `<li><strong>Pico de internações em ${peakRecord.ano}:</strong> ${peakRecord.taxa_internacoes_hidricas_10k.toFixed(1)} por 10 mil hab.</li>`;
    }
    
    if (agua2019 > 0 && agua2023 > 0) {
        const trend = agua2023 > agua2019 ? 'sobe' : 'cai';
        html += `<li><strong>Cobertura de água ${trend}</strong> de ${agua2019.toFixed(0)}% para ${agua2023.toFixed(0)}% entre 2019 e 2023.</li>`;
    }
    
    if (esgoto2023 > 0) {
        html += `<li>Coleta de esgoto ${esgoto2023 < 50 ? '<strong style="color: var(--accent-magenta)">permanece abaixo de 50%</strong>' : `está em ${esgoto2023.toFixed(0)}%`} em 2023.</li>`;
    }
    
    html += `<li style="margin-top: 0.5rem; color: ${compColor}"><strong>Este município está ${comparison} da média da RMB</strong> em coleta de esgoto.</li>`;
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
    const internData = munData.map(d => d.taxa_internacoes_hidricas_10k || null);
    const aguaData = munData.map(d => d.cobertura_agua || null);
    const esgotoData = munData.map(d => d.coleta_esgoto || null);
    
    modalChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: years,
            datasets: [
                {
                    label: 'Internações/10k',
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
                        text: 'Internações/10k', 
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
    const totalPop = data2023.reduce((s, d) => s + (d.populacao || 0), 0);
    
    // RMB Água
    const aguaData = data2023.filter(d => d.cobertura_agua > 0);
    const aguaPop = aguaData.reduce((s, d) => s + (d.populacao || 0), 0);
    const rmbAgua = aguaPop > 0 ? aguaData.reduce((s, d) => s + (d.cobertura_agua * (d.populacao || 0)), 0) / aguaPop : 0;
    
    // RMB Esgoto
    const esgotoData = data2023.filter(d => d.coleta_esgoto > 0);
    const esgotoPop = esgotoData.reduce((s, d) => s + (d.populacao || 0), 0);
    const rmbEsgoto = esgotoPop > 0 ? esgotoData.reduce((s, d) => s + (d.coleta_esgoto * (d.populacao || 0)), 0) / esgotoPop : 0;
    
    // RMB Internações
    const totalCases = data2023.reduce((s, d) => s + (d.internacoes_hidricas_total || 0), 0);
    const rmbIntern = totalPop > 0 ? (totalCases / totalPop) * 10000 : 0;
    
    // Municipality values
    const munAgua = record2023?.cobertura_agua || 0;
    const munEsgoto = record2023?.coleta_esgoto || 0;
    const munIntern = record2023?.taxa_internacoes_hidricas_10k || 0;
    
    const bars = [
        { label: 'Água', value: munAgua, max: 100, rmb: rmbAgua, color: 'cyan' },
        { label: 'Esgoto', value: munEsgoto, max: 100, rmb: rmbEsgoto, color: 'cyan' },
        { label: 'Internações', value: munIntern, max: 40, rmb: rmbIntern, color: 'magenta' }
    ];
    
    container.innerHTML = bars.map(bar => {
        const munWidth = Math.min((bar.value / bar.max) * 100, 100);
        const rmbWidth = Math.min((bar.rmb / bar.max) * 100, 100);
        const comparison = bar.value > bar.rmb ? '↑' : bar.value < bar.rmb ? '↓' : '=';
        const compColor = bar.label === 'Internações' ? 
            (bar.value > bar.rmb ? '#ec4899' : '#a3e635') : 
            (bar.value > bar.rmb ? '#a3e635' : '#ec4899');
        
        return `
            <div class="comparison-bar-item">
                <span class="comparison-bar-label">${bar.label}</span>
                <div class="comparison-bar-track">
                    <div class="comparison-bar-fill ${bar.color}" style="width: ${munWidth}%"></div>
                    <div style="position: absolute; left: ${rmbWidth}%; top: 0; bottom: 0; width: 2px; background: #fbbf24; opacity: 0.8;"></div>
                </div>
                <span class="comparison-bar-value" style="color: ${compColor}">
                    ${bar.value.toFixed(1)}${bar.label !== 'Internações' ? '%' : ''} ${comparison}
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
