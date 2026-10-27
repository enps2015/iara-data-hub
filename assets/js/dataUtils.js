/* ============================================
   IARA Data Hub - Data Utilities
   CSV parsing with missing-data preservation
   ============================================ */

const DataUtils = {
    integerFields: new Set(['cod_ibge', 'ano', 'populacao', 'internacoes_hidricas_total']),
    numericFields: new Set([
        'cod_ibge',
        'ano',
        'populacao',
        'cobertura_agua',
        'coleta_esgoto',
        'tratamento_esgoto',
        'esgoto_tratado_ref_agua',
        'tarifa_media_agua',
        'tarifa_media_esgoto',
        'internacoes_hidricas_total',
        'taxa_internacoes_hidricas_10k',
        'risco_climatico'
    ]),
    lastParseReport: null,
    lastLoadError: null,

    async loadData() {
        this.lastLoadError = null;
        try {
            const response = await fetch('data/iara/iara_municipios_rmb.csv');
            if (!response.ok) {
                throw new Error(`Falha ao carregar o CSV: HTTP ${response.status}`);
            }

            const csvText = await response.text();
            const rows = this.parseCSV(csvText);
            const report = this.getLastParseReport();

            console.info(
                `IARA Data Hub: ${report.rowCount} registros, ${report.missingCells} células ausentes e ${report.invalidCells} valores inválidos preservados como N/D.`
            );
            if (report.invalidValues.length > 0) {
                console.warn('Valores numéricos inválidos convertidos em N/D:', report.invalidValues);
            }
            return rows;
        } catch (error) {
            this.lastLoadError = error instanceof Error ? error.message : String(error);
            console.error('Erro ao carregar os dados do IARA Data Hub:', this.lastLoadError);
            return [];
        }
    },

    /**
     * RFC-4180-style CSV parser supporting quoted commas, escaped quotes,
     * CRLF/LF line endings and newlines inside quoted fields.
     */
    parseRows(csvText) {
        if (typeof csvText !== 'string' || csvText.trim() === '') {
            throw new Error('O arquivo CSV está vazio.');
        }

        const rows = [];
        let row = [];
        let field = '';
        let inQuotes = false;

        for (let i = 0; i < csvText.length; i += 1) {
            const char = csvText[i];

            if (inQuotes) {
                if (char === '"') {
                    if (csvText[i + 1] === '"') {
                        field += '"';
                        i += 1;
                    } else {
                        inQuotes = false;
                    }
                } else {
                    field += char;
                }
                continue;
            }

            if (char === '"') {
                if (field.trim() !== '') {
                    throw new Error(`Aspas fora de posição perto do caractere ${i + 1}.`);
                }
                field = '';
                inQuotes = true;
            } else if (char === ',') {
                row.push(field);
                field = '';
            } else if (char === '\n' || char === '\r') {
                if (char === '\r' && csvText[i + 1] === '\n') i += 1;
                row.push(field);
                if (row.some(value => value.trim() !== '')) rows.push(row);
                row = [];
                field = '';
            } else {
                field += char;
            }
        }

        if (inQuotes) {
            throw new Error('CSV inválido: campo entre aspas não foi fechado.');
        }

        if (field !== '' || row.length > 0) {
            row.push(field);
            if (row.some(value => value.trim() !== '')) rows.push(row);
        }

        if (rows.length < 2) {
            throw new Error('O CSV precisa conter um cabeçalho e ao menos um registro.');
        }

        return rows;
    },

    parseCSV(csvText) {
        const rows = this.parseRows(csvText);
        const headers = rows[0].map((header, index) =>
            (index === 0 ? header.replace(/^\uFEFF/, '') : header).trim()
        );

        if (headers.some(header => header === '')) {
            throw new Error('CSV inválido: há uma coluna sem nome no cabeçalho.');
        }
        const duplicateHeaders = headers.filter((header, index) => headers.indexOf(header) !== index);
        if (duplicateHeaders.length > 0) {
            throw new Error(`CSV inválido: cabeçalhos duplicados (${[...new Set(duplicateHeaders)].join(', ')}).`);
        }
        if (!headers.includes('municipio') || !headers.includes('ano')) {
            throw new Error('CSV inválido: o cabeçalho precisa conter ao menos as colunas municipio e ano.');
        }

        const missingByColumn = Object.fromEntries(headers.map(header => [header, 0]));
        const invalidValues = [];
        let missingCells = 0;
        let invalidCells = 0;
        let rowsWithMissing = 0;

        const records = rows.slice(1).map((values, index) => {
            const rowNumber = index + 2;
            if (values.length !== headers.length) {
                throw new Error(
                    `CSV inválido na linha de dados ${rowNumber}: esperado ${headers.length} colunas, recebidas ${values.length}.`
                );
            }

            const entry = {};
            let rowHasMissing = false;

            headers.forEach((header, columnIndex) => {
                const raw = values[columnIndex].trim();
                const isMissing = raw === '' || /^(?:na|n\/a|n\/d|null)$/i.test(raw);

                if (isMissing) {
                    entry[header] = null;
                    missingByColumn[header] += 1;
                    missingCells += 1;
                    rowHasMissing = true;
                    return;
                }

                if (this.numericFields.has(header)) {
                    const value = Number(raw);
                    const validInteger = !this.integerFields.has(header) || Number.isInteger(value);
                    if (!Number.isFinite(value) || !validInteger) {
                        entry[header] = null;
                        invalidValues.push({ row: rowNumber, column: header, value: raw });
                        missingByColumn[header] += 1;
                        invalidCells += 1;
                        rowHasMissing = true;
                    } else {
                        entry[header] = value;
                    }
                } else {
                    entry[header] = raw;
                }
            });

            if (rowHasMissing) rowsWithMissing += 1;
            return entry;
        });

        this.lastParseReport = {
            rowCount: records.length,
            columnCount: headers.length,
            headers,
            missingCells,
            invalidCells,
            rowsWithMissing,
            missingByColumn,
            invalidValues
        };

        return records;
    },

    getLastParseReport() {
        if (!this.lastParseReport) return null;
        return {
            ...this.lastParseReport,
            headers: [...this.lastParseReport.headers],
            missingByColumn: { ...this.lastParseReport.missingByColumn },
            invalidValues: this.lastParseReport.invalidValues.map(item => ({ ...item }))
        };
    },

    getLastLoadError() {
        return this.lastLoadError;
    },

    isAvailableNumber(value) {
        return typeof value === 'number' && Number.isFinite(value);
    },

    formatNumber(value, decimals = 1, suffix = '') {
        return this.isAvailableNumber(value) ? `${value.toFixed(decimals)}${suffix}` : 'N/D';
    },

    filterByYear(data, year) {
        return data.filter(record => record.ano === year);
    },

    getMunicipalities(data) {
        return [...new Set(data
            .map(record => record.municipio)
            .filter(value => typeof value === 'string' && value.trim() !== '')
        )].sort((a, b) => a.localeCompare(b, 'pt-BR'));
    },

    getYears(data) {
        return [...new Set(data
            .map(record => record.ano)
            .filter(value => this.isAvailableNumber(value))
        )].sort((a, b) => a - b);
    }
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = DataUtils;
} else if (typeof window !== 'undefined') {
    window.DataUtils = DataUtils;
}
