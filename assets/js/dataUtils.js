const DataUtils = {
    async loadData() {
        try {
            console.log("Loading CSV data...");
            const response = await fetch('data/iara/iara_municipios_rmb.csv');
            if (!response.ok) throw new Error('Network response was not ok');
            const csvText = await response.text();
            return this.parseCSV(csvText);
        } catch (error) {
            console.error("Error loading CSV:", error);
            return [];
        }
    },

    parseCSV(csvText) {
        const lines = csvText.trim().split('\n');
        const headers = lines[0].split(',').map(h => h.trim());
        
        return lines.slice(1).map(line => {
            const values = line.split(',');
            const entry = {};
            
            headers.forEach((header, index) => {
                let value = values[index] ? values[index].trim() : '';
                
                // Type Conversion
                if (header === 'ano' || header === 'cod_ibge' || header === 'populacao' || header === 'internacoes_hidricas_total') {
                    entry[header] = parseInt(value) || 0;
                } else if (header === 'municipio') {
                    entry[header] = value;
                } else {
                    // Floats (handle potential commas if any, though file uses dots)
                    entry[header] = parseFloat(value) || 0;
                }
            });
            return entry;
        });
    },

    filterByYear(data, year) {
        return data.filter(d => d.ano === year);
    },

    getMunicipalities(data) {
        return [...new Set(data.map(d => d.municipio))].sort();
    },

    getYears(data) {
        return [...new Set(data.map(d => d.ano))].sort((a, b) => a - b);
    }
};
