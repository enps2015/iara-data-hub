const Storytelling = {
    init(data) {
        // Legacy init if needed
    },

    renderRealityCheck(data) {
        // Calculate Total Hospitalizations (All Years)
        const totalHosp = data.reduce((sum, d) => sum + (d.internacoes_hidricas_total || 0), 0);
        
        // Calculate Average Sewage Treatment (2023 only for "current state")
        const data2023 = data.filter(d => d.ano === 2023);
        const avgSewage = data2023.reduce((sum, d) => sum + (d.tratamento_esgoto || 0), 0) / data2023.length;

        // Animate Numbers
        this.animateValue("stat-hospitalizations", 0, totalHosp, 2000);
        this.animateValue("stat-sewage", 0, avgSewage, 2000, 1);
    },

    renderMunicipalityCards(data) {
        const container = document.getElementById('municipality-grid');
        const munis = [...new Set(data.map(d => d.municipio))].sort();
        
        // Image mapping (based on available files)
        const imgMap = {
            'Ananindeua (PA)': 'img/ananindeua_vista_aerea.jpg',
            'Belém (PA)': 'img/belem_vista_do_rio01.png',
            'Benevides (PA)': 'img/benevides_vista_aerea.jpg',
            'Castanhal (PA)': 'img/castanhal.jpg',
            'Marituba (PA)': 'img/marituba_vista_aerea.png',
            'Santa Bárbara do Pará (PA)': 'img/sanatabarbara.png',
            'Santa Izabel do Pará (PA)': 'img/santaizabeldopara.jpg'
        };

        munis.forEach(mun => {
            const munData = data.filter(d => d.municipio === mun);
            const lastRecord = munData.find(d => d.ano === 2023) || munData[munData.length - 1];
            
            // Calculate Risk Score (Simple avg of available risks)
            const risks = munData.map(d => d.risco_climatico).filter(r => r !== null);
            const avgRisk = risks.length ? (risks.reduce((a,b)=>a+b,0)/risks.length).toFixed(2) : 'N/A';
            
            const img = imgMap[mun] || 'img/mapa_rmb.png';

            const card = `
                <div class="glass-card overflow-hidden group">
                    <div class="h-48 overflow-hidden relative">
                        <img src="${img}" alt="${mun}" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700">
                        <div class="absolute inset-0 bg-gradient-to-t from-slate-900/90 to-transparent"></div>
                        <div class="absolute bottom-4 left-4">
                            <h3 class="text-xl font-bold font-outfit text-white">${mun.split('(')[0]}</h3>
                        </div>
                    </div>
                    <div class="p-6">
                        <div class="grid grid-cols-2 gap-4 mb-4">
                            <div>
                                <p class="text-xs text-slate-400 uppercase font-bold">Internações (2023)</p>
                                <p class="text-xl font-bold text-rose-500">${lastRecord.internacoes_hidricas_total || 0}</p>
                            </div>
                            <div>
                                <p class="text-xs text-slate-400 uppercase font-bold">Esgoto (2023)</p>
                                <p class="text-xl font-bold text-teal-500">${(lastRecord.coleta_esgoto || 0).toFixed(1)}%</p>
                            </div>
                        </div>
                        <div class="border-t border-white/5 pt-4 mt-2">
                            <div class="flex justify-between items-center">
                                <span class="text-xs text-slate-400">Risco Climático</span>
                                <span class="text-sm font-bold ${avgRisk > 0.5 ? 'text-rose-400' : 'text-slate-300'}">${avgRisk}</span>
                            </div>
                            <div class="w-full bg-slate-700 h-1 mt-2 rounded-full overflow-hidden">
                                <div class="bg-gradient-to-r from-teal-500 to-rose-500 h-full" style="width: ${avgRisk * 100}%"></div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            container.innerHTML += card;
        });
    },

    animateValue(id, start, end, duration, decimals = 0) {
        const obj = document.getElementById(id);
        if (!obj) return;
        
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const value = progress * (end - start) + start;
            obj.innerHTML = value.toFixed(decimals) + (decimals > 0 ? '%' : '');
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }
};
