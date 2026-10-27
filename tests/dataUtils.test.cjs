const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const DataUtils = require('../assets/js/dataUtils.js');

test('preserva zero real e mantém campos vazios como null', () => {
    const csv = [
        'municipio,cod_ibge,ano,populacao,cobertura_agua,coleta_esgoto,risco_climatico',
        'Belém (PA),1501402,2024,1000,0,,0',
        'Ananindeua (PA),1500800,2024,2000,88.5,21.25,'
    ].join('\r\n');

    const records = DataUtils.parseCSV(csv);
    assert.equal(records[0].cobertura_agua, 0);
    assert.equal(records[0].coleta_esgoto, null);
    assert.equal(records[0].risco_climatico, 0);
    assert.equal(records[1].cobertura_agua, 88.5);
    assert.equal(records[1].coleta_esgoto, 21.25);
    assert.equal(records[1].risco_climatico, null);

    const report = DataUtils.getLastParseReport();
    assert.equal(report.rowCount, 2);
    assert.equal(report.missingCells, 2);
    assert.equal(report.invalidCells, 0);
});

test('lê BOM, CRLF, vírgulas e aspas escapadas em campos', () => {
    const csv = '\uFEFFmunicipio,ano,populacao\r\n"São, João (PA)",2024,100\r\n"Santa ""Rita"" (PA)",2025,200\r\n';
    const records = DataUtils.parseCSV(csv);

    assert.equal(records.length, 2);
    assert.equal(records[0].municipio, 'São, João (PA)');
    assert.equal(records[1].municipio, 'Santa "Rita" (PA)');
    assert.deepEqual(DataUtils.getYears(records), [2024, 2025]);
});

test('preserva vírgulas e quebras de linha dentro de campos entre aspas', () => {
    const csv = 'municipio,ano\n"Localidade, setor A\nsegunda linha",2024';
    const records = DataUtils.parseCSV(csv);
    assert.equal(records[0].municipio, 'Localidade, setor A\nsegunda linha');
});

test('valor numérico inválido não vira zero e fica registrado no relatório', () => {
    const records = DataUtils.parseCSV(
        'municipio,ano,cobertura_agua\nBelém,2024,desconhecido'
    );

    assert.equal(records[0].cobertura_agua, null);
    const report = DataUtils.getLastParseReport();
    assert.equal(report.invalidCells, 1);
    assert.equal(report.missingCells, 0);
    assert.deepEqual(report.invalidValues, [
        { row: 2, column: 'cobertura_agua', value: 'desconhecido' }
    ]);
});

test('rejeita linhas com quantidade de colunas inconsistente', () => {
    assert.throws(
        () => DataUtils.parseCSV('municipio,ano\nBelém,2024,extra'),
        /esperado 2 colunas, recebidas 3/
    );
});

test('rejeita aspas abertas e cabeçalho inválido', () => {
    assert.throws(
        () => DataUtils.parseCSV('municipio,ano\n"Belém,2024'),
        /campo entre aspas não foi fechado/
    );
    assert.throws(
        () => DataUtils.parseCSV('municipio,municipio\nBelém,Belém'),
        /cabeçalhos duplicados/
    );
});

test('formata zero como zero e ausência como N/D', () => {
    assert.equal(DataUtils.formatNumber(0, 1, '%'), '0.0%');
    assert.equal(DataUtils.formatNumber(null, 1, '%'), 'N/D');
    assert.equal(DataUtils.formatNumber(Number.NaN, 2), 'N/D');
});

test('CSV publicado preserva os indicadores ausentes de 2017 como N/D', () => {
    const csvPath = path.join(__dirname, '..', 'data', 'iara', 'iara_municipios_rmb.csv');
    const csv = fs.readFileSync(csvPath, 'utf8');
    const records = DataUtils.parseCSV(csv);
    const ananindeua2017 = records.find(row => row.municipio === 'Ananindeua (PA)' && row.ano === 2017);

    assert.ok(ananindeua2017, 'registro de Ananindeua para 2017 deveria existir');
    assert.equal(ananindeua2017.cobertura_agua, null);
    assert.equal(ananindeua2017.coleta_esgoto, null);
    assert.equal(ananindeua2017.internacoes_hidricas_total, 194);
    assert.ok(DataUtils.getLastParseReport().missingCells > 0);
});

test('loadData informa erro de rede e retorna conjunto vazio', async () => {
    const originalFetch = global.fetch;
    const originalConsoleError = console.error;
    global.fetch = async () => ({ ok: false, status: 503 });
    console.error = () => {};

    try {
        const records = await DataUtils.loadData();
        assert.deepEqual(records, []);
        assert.match(DataUtils.getLastLoadError(), /HTTP 503/);
    } finally {
        global.fetch = originalFetch;
        console.error = originalConsoleError;
    }
});
