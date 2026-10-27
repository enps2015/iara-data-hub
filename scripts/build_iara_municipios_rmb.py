import pandas as pd
import numpy as np
import glob
import os
import unicodedata

# -------------------------------------------------------------------------
# CONSTANTS & CONFIG
# -------------------------------------------------------------------------

# Target Municipalities (RMB)
# Normalized names for matching
RMB_CITIES = [
    'BELEM',
    'ANANINDEUA',
    'MARITUBA',
    'BENEVIDES',
    'SANTA BARBARA DO PARA',
    'SANTA IZABEL DO PARA',
    'CASTANHAL' # Often included in broader metro analysis, checking if data exists
]

# Path Config
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
BRONZE_DIR = os.path.join(DATA_DIR, 'bronze')
OUTPUT_DIR = os.path.join(DATA_DIR, 'iara')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'iara_municipios_rmb.csv')

# -------------------------------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------------------------------

def normalize_text(text):
    """
    Normalizes text: uppercase, removes accents, strips whitespace.
    Example: 'Belém ' -> 'BELEM'
    """
    if not isinstance(text, str):
        return str(text)
    
    text = text.upper().strip()
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    return text

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# -------------------------------------------------------------------------
# DATA LOADING FUNCTIONS
# -------------------------------------------------------------------------

def load_snis():
    """
    Loads and consolidates SNIS data from Excel files.
    Looks for 'Planilha_LEP_Indicadores.xls' in 'snis' subfolders.
    """
    print("--- Loading SNIS Data ---")
    snis_files = glob.glob(os.path.join(BRONZE_DIR, 'snis', '**', 'Planilha_LEP_Indicadores.xls'), recursive=True)
    
    dfs = []
    
    for f in snis_files:
        try:
            # Extract year from path if possible, or try to find in file
            # Assuming path structure like .../Planilhas_AE2022_Completa/...
            year = None
            path_parts = f.split(os.sep)
            for part in path_parts:
                if 'AE20' in part: # Matches AE2018, AE2022 etc
                    year = int(part.replace('Planilhas_AE', '').split('_')[0])
                    break
            
            if not year:
                print(f"Could not determine year for {f}, skipping.")
                continue

            print(f"Processing SNIS {year}...")
            
            # Read Excel - skip header rows to find the actual header
            # Usually SNIS headers start around line 10-15, looking for "Código do Município"
            # We'll try to read with header=None first to find the row
            temp_df = pd.read_excel(f, header=None, nrows=20)
            header_row_idx = -1
            for i, row in temp_df.iterrows():
                row_str = row.astype(str).str.cat(sep=' ').lower()
                if 'código do município' in row_str:
                    header_row_idx = i
                    break
            
            if header_row_idx == -1:
                print(f"Header not found in {f}, skipping.")
                continue
                
            df = pd.read_excel(f, header=header_row_idx)
            
            # Map columns by name
            col_map = {}
            for col in df.columns:
                c_str = str(col).strip().lower() # Lowercase for easier matching
                
                if c_str == 'código do município': col_map[col] = 'cod_ibge'
                elif c_str == 'município': col_map[col] = 'municipio_raw'
                elif c_str == 'uf': col_map[col] = 'uf'
                
                # Indicators
                elif 'índice de atendimento total de água' in c_str: col_map[col] = 'cobertura_agua'
                elif 'índice de atendimento total de esgoto' in c_str: col_map[col] = 'coleta_esgoto'
                elif 'índice de esgoto tratado referido à água consumida' in c_str: col_map[col] = 'esgoto_tratado_ref_agua'
                elif 'tarifa média de água' in c_str: col_map[col] = 'tarifa_media_agua'
                elif 'tarifa média de esgoto' in c_str: col_map[col] = 'tarifa_media_esgoto'
            
            df = df.rename(columns=col_map)
            
            # Remove duplicate columns if any (keep first)
            df = df.loc[:, ~df.columns.duplicated()]
            
            # Keep only mapped columns
            keep_cols = ['cod_ibge', 'municipio_raw', 'uf', 'cobertura_agua', 'coleta_esgoto', 
                         'esgoto_tratado_ref_agua', 'tarifa_media_agua', 'tarifa_media_esgoto']
            
            # Filter for columns that actually exist
            existing_cols = [c for c in keep_cols if c in df.columns]
            df = df[existing_cols]
            
            df['ano'] = year
            dfs.append(df)
            
        except Exception as e:
            print(f"Error reading {f}: {e}")

    if not dfs:
        return pd.DataFrame()

    full_df = pd.concat(dfs, ignore_index=True)
    
    # Normalize Municipality Names for Filtering
    full_df['municipio_norm'] = full_df['municipio_raw'].apply(normalize_text)
    
    # Filter RMB
    full_df = full_df[full_df['municipio_norm'].isin(RMB_CITIES)].copy()
    
    print(f"DEBUG: SNIS Rows after filtering: {len(full_df)}")
    
    # Clean numeric columns (handle strings like '-')
    num_cols = ['cobertura_agua', 'coleta_esgoto', 'esgoto_tratado_ref_agua', 'tarifa_media_agua', 'tarifa_media_esgoto']
    for col in num_cols:
        if col in full_df.columns:
            full_df[col] = pd.to_numeric(full_df[col], errors='coerce')
    
    return full_df

def load_snis_consolidated():
    """
    Loads the new consolidated SNIS file (UTF-16-LE).
    """
    print("--- Loading Consolidated SNIS Data ---")
    f = os.path.join(BRONZE_DIR, 'snis', 'ConsolidadoMunicipio-20251206192115.csv')
    
    if not os.path.exists(f):
        print(f"Consolidated file not found: {f}")
        return pd.DataFrame()
        
    try:
        df = pd.read_csv(f, sep=';', encoding='utf-16-le', on_bad_lines='warn', engine='python', index_col=False)
        
        print(f"DEBUG: SNIS Raw Columns: {list(df.columns[:10])}")
        print(f"DEBUG: SNIS Raw Head: {df.head(1).iloc[:, :10].to_dict()}")
        
        # Map columns
        col_map = {
            'Código do IBGE': 'cod_ibge',
            'Município': 'municipio_raw',
            'Ano de Referência': 'ano',
            'IN055_AE - Índice de atendimento total de água': 'cobertura_agua',
            'IN056_AE - Índice de atendimento total de esgoto referido aos municípios atendidos com água': 'coleta_esgoto',
            'IN046_AE - Índice de esgoto tratado referido à água consumida': 'esgoto_tratado_ref_agua',
            'IN016_AE - Índice de tratamento de esgoto': 'tratamento_esgoto',
            'IN005_AE - Tarifa média de água': 'tarifa_media_agua',
            'IN006_AE - Tarifa média de esgoto': 'tarifa_media_esgoto'
        }
        
        # Select and Rename
        available_cols = [c for c in col_map.keys() if c in df.columns]
        df = df[available_cols].rename(columns=col_map)
        
        # Convert keys to numeric
        df['cod_ibge'] = pd.to_numeric(df['cod_ibge'], errors='coerce').astype('Int64')
        df['ano'] = pd.to_numeric(df['ano'], errors='coerce').astype('Int64')
        
        # Clean numeric
        num_cols = ['cobertura_agua', 'coleta_esgoto', 'esgoto_tratado_ref_agua', 'tratamento_esgoto', 'tarifa_media_agua', 'tarifa_media_esgoto']
        for col in num_cols:
            if col in df.columns:
                # Replace ',' with '.' and handle non-numeric
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
        
        # Filter RMB
        if 'municipio_raw' in df.columns:
            df['municipio_norm'] = df['municipio_raw'].apply(normalize_text)
            print(f"DEBUG: SNIS Consolidated unique municipalities: {df['municipio_norm'].unique()}")
            df = df[df['municipio_norm'].isin(RMB_CITIES)].copy()
            df = df.drop(columns=['municipio_norm'])
            
        print(f"DEBUG: SNIS Consolidated rows after filtering: {len(df)}")
        if not df.empty:
            print(f"DEBUG: SNIS Consolidated sample: {df.head(1).to_dict()}")
            print(f"DEBUG: SNIS Consolidated dtypes: {df.dtypes}")
            
        return df
        
    except Exception as e:
        print(f"Error reading consolidated SNIS: {e}")
        return pd.DataFrame()

def load_snis_indicators_folder(folder_path, type_):
    """
    Loads SNIS indicators from individual Excel files in a folder.
    type_: 'AGUA' or 'ESGOTO'
    """
    print(f"--- Loading SNIS Indicators from {type_} ---")
    files = glob.glob(os.path.join(folder_path, '*.xlsx'))
    dfs = []
    
    for f in files:
        try:
            # Read header info (Row 1 for Year, Row 2 for City)
            header_df = pd.read_excel(f, header=None, nrows=5)
            
            # Extract Year
            year_str = str(header_df.iloc[1, 1]) # "Ano atual: 2024 / Ano de referência: 2023"
            if 'Ano de referência:' in year_str:
                year = int(year_str.split('Ano de referência:')[1].strip())
            else:
                year = 2023 # Default fallback if format changes
                
            # Extract Municipality
            city = str(header_df.iloc[2, 1]).strip()
            
            # Read Data Table (Header at Row 5, so skiprows=5)
            df = pd.read_excel(f, header=5)
            
            # Filter for relevant codes
            # Map codes to our columns
            code_map = {
                'IAG0001': 'cobertura_agua',
                'IES0001': 'coleta_esgoto',
                'IES2003': 'esgoto_tratado_ref_agua',
                'IES2004': 'tratamento_esgoto',
                'IFA1001': 'tarifa_media_agua',
                'IFE1001': 'tarifa_media_esgoto'
            }
            
            # The file has 'Código', 'Descrição', 'Valor', 'Unidade'
            # We want to pivot this: One row per city/year, columns are indicators
            
            # Filter rows where 'Código' is in our map
            df_filtered = df[df['Código'].isin(code_map.keys())].copy()
            
            # Create a dictionary for this city/year
            row_data = {
                'municipio_raw': city,
                'ano': year
            }
            
            for _, row in df_filtered.iterrows():
                code = row['Código']
                val_str = str(row['Valor']).replace(',', '.')
                try:
                    val = float(val_str)
                except:
                    val = None
                
                if code in code_map:
                    row_data[code_map[code]] = val
            
            dfs.append(pd.DataFrame([row_data]))
            
        except Exception as e:
            print(f"Error reading {f}: {e}")
            
    if not dfs:
        return pd.DataFrame()
        
    return pd.concat(dfs, ignore_index=True)

def load_ibge():
    """
    Loads IBGE Population data.
    """
    print("--- Loading IBGE Data ---")
    ibge_files = glob.glob(os.path.join(BRONZE_DIR, 'ibge', 'sidra6579_pop_*.csv'))
    
    dfs = []
    for f in ibge_files:
        try:
            # Filename format: sidra6579_pop_2022.csv
            year = int(os.path.basename(f).split('_')[-1].replace('.csv', ''))
            
            # Assuming standard SIDRA CSV format (skiprows might be needed depending on download format)
            # Usually: "Município (Código)","Município","Ano","População"
            df = pd.read_csv(f, sep=None, engine='python') # Auto-detect separator
            
            # Normalize columns
            df.columns = [normalize_text(c) for c in df.columns]
            
            # Identify columns
            # Looking for 'MUNICIPIO (CODIGO)', 'MUNICIPIO', 'VALOR' or 'POPULACAO'
            rename_map = {}
            for c in df.columns:
                if 'CODIGO' in c and 'MUNICIPIO' in c: rename_map[c] = 'cod_ibge'
                elif 'MUNICIPIO' in c and 'CODIGO' not in c: rename_map[c] = 'municipio_raw'
                elif 'VALOR' in c or 'POPULACAO' in c: rename_map[c] = 'populacao'
            
            df = df.rename(columns=rename_map)
            
            if 'cod_ibge' not in df.columns or 'populacao' not in df.columns:
                print(f"Columns missing in {f}, skipping.")
                continue
                
            df['ano'] = year
            dfs.append(df)
            
        except Exception as e:
            print(f"Error reading {f}: {e}")
            
    if not dfs:
        return pd.DataFrame()
        
    full_df = pd.concat(dfs, ignore_index=True)
    
    # Clean cod_ibge (sometimes comes as "1501402 Belém", sometimes just code)
    # If it's numeric, fine. If string, extract first part.
    # Actually SIDRA often gives "Município (Código)" as just the code if selected right, 
    # or "1100015"
    
    full_df['cod_ibge'] = pd.to_numeric(full_df['cod_ibge'], errors='coerce')
    full_df['populacao'] = pd.to_numeric(full_df['populacao'], errors='coerce')
    
    # We might need to filter by RMB here too, but we can do it at merge time via cod_ibge
    # But let's filter by name to be safe if cod_ibge is missing
    # Keep missing populations as missing. A previous version forward-filled
    # values across years without recording the source/reference year.
    full_df = full_df.sort_values(['cod_ibge', 'ano'])
    
    if 'municipio_raw' in full_df.columns:
        # Handle "Belém (PA)" -> "BELEM"
        full_df['municipio_norm'] = full_df['municipio_raw'].astype(str).apply(lambda x: normalize_text(x.split('(')[0]))
        # Filter RMB
        full_df = full_df[full_df['municipio_norm'].isin(RMB_CITIES)].copy()
        
    return full_df[['cod_ibge', 'municipio_raw', 'populacao', 'ano']]

def select_sih_admissions(frame, source_name, seen_aihs=None):
    """Return validated admissions with principal ICD-10 diagnosis A00–A09.

    A00–A09 means intestinal infectious diseases; this range is not proof that
    each admission was transmitted through water. Invalid target rows fail
    visibly instead of being silently dropped.
    """
    if seen_aihs is None:
        seen_aihs = set()

    data = frame.copy()
    data.columns = [str(column).strip().upper() for column in data.columns]
    required = {'MUNIC_RES', 'DT_INTER', 'DIAG_PRINC'}
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(
            f"{source_name}: colunas obrigatórias ausentes: {', '.join(missing)}"
        )

    diagnosis = data['DIAG_PRINC'].astype(str).str.strip().str.upper()
    selected = data.loc[diagnosis.str.match(r'^A0[0-9]')].copy()
    if selected.empty:
        return selected

    residence = pd.to_numeric(selected['MUNIC_RES'], errors='coerce')
    invalid_residence = residence.isna() | ~np.isfinite(residence)
    if invalid_residence.any():
        raise ValueError(
            f"{source_name}: {int(invalid_residence.sum())} internações A00–A09 "
            "têm MUNIC_RES ausente ou inválido."
        )
    if not np.equal(residence, np.floor(residence)).all():
        raise ValueError(f"{source_name}: MUNIC_RES contém código não inteiro.")
    residence_codes = residence.astype(int).astype(str)
    if not residence_codes.str.fullmatch(r'[0-9]{6}').all():
        raise ValueError(f"{source_name}: MUNIC_RES deve usar código municipal DATASUS de 6 dígitos.")
    selected['MUNIC_RES'] = residence.astype(int)

    date_text = selected['DT_INTER'].astype(str).str.strip()
    valid_formats = date_text.str.fullmatch(r'(?:[0-9]{6}|[0-9]{8})')
    if not valid_formats.all():
        raise ValueError(
            f"{source_name}: {int((~valid_formats).sum())} internações A00–A09 "
            "têm DT_INTER fora do formato YYYYMM ou YYYYMMDD."
        )

    # Validate the calendar date/month as well as the string format.
    parsed_dates = pd.Series(pd.NaT, index=date_text.index, dtype='datetime64[ns]')
    day_precision = date_text.str.len() == 8
    parsed_dates.loc[day_precision] = pd.to_datetime(
        date_text.loc[day_precision], format='%Y%m%d', errors='coerce'
    )
    month_precision = ~day_precision
    parsed_dates.loc[month_precision] = pd.to_datetime(
        date_text.loc[month_precision], format='%Y%m', errors='coerce'
    )
    if parsed_dates.isna().any():
        raise ValueError(
            f"{source_name}: {int(parsed_dates.isna().sum())} internações A00–A09 "
            "têm DT_INTER inválida (data de atendimento)."
        )
    years = parsed_dates.dt.year
    if not years.between(1990, 2100).all():
        raise ValueError(f"{source_name}: ano inválido derivado de DT_INTER.")
    selected['ano'] = years

    # N_AIH is commonly present in reduced SIH files. If available, use it to
    # detect duplicate target admissions across overlapping source files.
    if 'N_AIH' in selected.columns:
        ids = selected['N_AIH'].astype(str).str.strip()
        missing_ids = ids.str.lower().isin(['', 'nan', 'none', 'na', '<na>'])
        usable_ids = ids.loc[~missing_ids]
        duplicate_ids = usable_ids[usable_ids.duplicated() | usable_ids.isin(seen_aihs)]
        if not duplicate_ids.empty:
            sample = ', '.join(duplicate_ids.drop_duplicates().head(5).tolist())
            raise ValueError(
                f"{source_name}: possíveis AIHs duplicadas entre arquivos "
                f"de origem (exemplos: {sample}). Verifique sobreposição."
            )
        seen_aihs.update(usable_ids.tolist())

    return selected


def load_sih():
    """
    Loads SIH/SUS hospitalization records and aggregates principal diagnoses
    ICD-10 A00–A09 (intestinal infectious diseases) by residence and year.

    An absent match is kept as missing, not converted to zero. The raw files
    are required to validate time coverage before a zero can be inferred.
    """
    print("--- Loading SIH/SUS Data (CID-10 A00–A09) ---")
    sih_files = sorted(glob.glob(os.path.join(BRONZE_DIR, 'sih', 'csv', 'RDPA*.csv')))
    empty_result = pd.DataFrame(columns=['cod_ibge', 'ano', 'internacoes_hidricas_total'])

    if not sih_files:
        print("WARNING: No SIH RDPA*.csv files found; admission counts will remain missing, not zero.")
        return empty_result

    dfs = []
    seen_aihs = set()

    for source_file in sih_files:
        try:
            df = pd.read_csv(
                source_file,
                sep=None,
                engine='python',
                encoding='iso-8859-1',
                on_bad_lines='error'
            )
            source_rows = len(df)
            selected = select_sih_admissions(df, source_file, seen_aihs)
            print(
                f"SIH source {os.path.basename(source_file)}: "
                f"{source_rows} input rows; {len(selected)} records with primary CID A00–A09."
            )

            if selected.empty:
                continue

            grouped = (
                selected.groupby(['MUNIC_RES', 'ano'])
                .size()
                .reset_index(name='internacoes_hidricas_total')
            )
            dfs.append(grouped)
        except Exception as error:
            raise RuntimeError(
                f"Failed to validate SIH source file {source_file}; "
                f"the file was not silently skipped: {error}"
            ) from error

    if not dfs:
        print("WARNING: No validated A00–A09 admissions were found; counts will remain missing, not zero.")
        return empty_result

    full_df = pd.concat(dfs, ignore_index=True)
    final_df = (
        full_df.groupby(['MUNIC_RES', 'ano'])['internacoes_hidricas_total']
        .sum()
        .reset_index()
        .rename(columns={'MUNIC_RES': 'cod_ibge'})
    )

    print(f"SIH aggregation produced {len(final_df)} municipality/year groups.")
    return final_df


def load_inmet():
    """
    Loads INMET Climate data for Belém (A201) and calculates Risk Index.
    """
    print("--- Loading INMET Data ---")
    # Pattern: .../inmet/*/INMET_N_PA_A201_BELEM_*.CSV
    inmet_files = glob.glob(os.path.join(BRONZE_DIR, 'inmet', '**', 'INMET_N_PA_A201_BELEM_*.CSV'), recursive=True)
    
    stats = []
    
    for f in inmet_files:
        try:
            # Extract year
            year = int(os.path.basename(f).split('_')[-1].split('-')[-1].replace('.CSV', ''))
            
            # INMET CSVs have header metadata, actual data starts after "DATA;HORA..."
            # Usually skip 8 rows
            df = pd.read_csv(f, sep=';', encoding='iso-8859-1', skiprows=8)
            
            # Columns (standard INMET names)
            # PRECIPITAÇÃO TOTAL, HORÁRIO (mm)
            # TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)
            
            # Normalize columns
            df.columns = [normalize_text(c) for c in df.columns]
            
            precip_col = next((c for c in df.columns if 'PRECIPITACAO' in c), None)
            temp_col = next((c for c in df.columns if 'TEMPERATURA' in c and 'AR' in c), None)
            
            if not precip_col or not temp_col:
                continue
                
            # Convert to numeric (replace , with .)
            df[precip_col] = pd.to_numeric(df[precip_col].astype(str).str.replace(',', '.'), errors='coerce')
            df[temp_col] = pd.to_numeric(df[temp_col].astype(str).str.replace(',', '.'), errors='coerce')
            
            # Aggregates
            total_precip = df[precip_col].sum()
            avg_temp = df[temp_col].mean()
            
            stats.append({
                'ano': year,
                'precipitacao_anual': total_precip,
                'temperatura_media': avg_temp
            })
            
        except Exception as e:
            print(f"Error reading {f}: {e}")
            
    if not stats:
        return pd.DataFrame()
        
    df_climate = pd.DataFrame(stats)
    
    # Exploratory descriptive index only: min–max normalized precipitation and
    # temperature are combined across available station-years. This is not a
    # validated epidemiological model, and it does not establish a causal link
    # with CID-10 A00–A09 or measure municipality-specific exposure.
    
    # Simple Min-Max Normalization
    if not df_climate.empty:
        p_min, p_max = df_climate['precipitacao_anual'].min(), df_climate['precipitacao_anual'].max()
        t_min, t_max = df_climate['temperatura_media'].min(), df_climate['temperatura_media'].max()
        
        # Avoid division by zero
        if p_max == p_min: p_max += 1
        if t_max == t_min: t_max += 1
        
        df_climate['norm_p'] = (df_climate['precipitacao_anual'] - p_min) / (p_max - p_min)
        df_climate['norm_t'] = (df_climate['temperatura_media'] - t_min) / (t_max - t_min)
        
        # Risk = Average of norms
        df_climate['risco_climatico'] = (df_climate['norm_p'] + df_climate['norm_t']) / 2
        
    return df_climate[['ano', 'risco_climatico']]

# -------------------------------------------------------------------------
# MAIN PIPELINE
# -------------------------------------------------------------------------

def main():
    ensure_dir(OUTPUT_DIR)
    
    # 1. Load Data
    df_snis = load_snis()
    df_snis_new = load_snis_consolidated()
    
    # Load new 2023 indicators
    df_agua_new = load_snis_indicators_folder(os.path.join(BRONZE_DIR, 'snis', 'agua_indicadores_RMB'), 'AGUA')
    df_esgoto_new = load_snis_indicators_folder(os.path.join(BRONZE_DIR, 'snis', 'esgoto_indicadores_RMB'), 'ESGOTO')
    
    # Merge water and sewage 2023
    df_snis_2023 = pd.DataFrame()
    if not df_agua_new.empty and not df_esgoto_new.empty:
        df_snis_2023 = pd.merge(df_agua_new, df_esgoto_new, on=['municipio_raw', 'ano'], how='outer')
    elif not df_agua_new.empty:
        df_snis_2023 = df_agua_new
    elif not df_esgoto_new.empty:
        df_snis_2023 = df_esgoto_new
        
    # Combine SNIS data
    if not df_snis_new.empty:
        df_snis = pd.concat([df_snis, df_snis_new], ignore_index=True)
        
    # We need to map municipality names to IBGE codes for the new 2023 data
    # We'll use the existing df_snis (which has cod_ibge and names) or df_ibge to build a map
    df_ibge = load_ibge()
    
    if not df_snis_2023.empty:
        print("--- Processing SNIS 2023 Data ---")
        # Build mapping from IBGE data
        # Normalize names first
        df_ibge_map = df_ibge[['cod_ibge', 'municipio_raw']].drop_duplicates()
        # IBGE has "Belém (PA)", SNIS has "Belém"
        df_ibge_map['municipio_norm'] = df_ibge_map['municipio_raw'].astype(str).apply(lambda x: normalize_text(x.split('(')[0]))
        name_to_code = dict(zip(df_ibge_map['municipio_norm'], df_ibge_map['cod_ibge']))
        
        df_snis_2023['municipio_norm'] = df_snis_2023['municipio_raw'].apply(normalize_text)
        df_snis_2023['cod_ibge'] = df_snis_2023['municipio_norm'].map(name_to_code)
        
        # Drop rows that didn't map (not in RMB)
        df_snis_2023 = df_snis_2023.dropna(subset=['cod_ibge'])
        df_snis_2023['cod_ibge'] = df_snis_2023['cod_ibge'].astype('Int64')
        df_snis_2023['ano'] = df_snis_2023['ano'].astype('Int64')
        
        # Drop helper cols
        df_snis_2023 = df_snis_2023.drop(columns=['municipio_raw', 'municipio_norm'])
        
        # Concat with main SNIS
        df_snis = pd.concat([df_snis, df_snis_2023], ignore_index=True)

    # Drop duplicates if any (by cod_ibge and ano)
    df_snis = df_snis.drop_duplicates(subset=['cod_ibge', 'ano'], keep='last')
        
    # Drop municipio_raw from SNIS to avoid duplication with IBGE
    if 'municipio_raw' in df_snis.columns:
        df_snis = df_snis.drop(columns=['municipio_raw'])
    
    df_sih = load_sih()
    df_inmet = load_inmet()
    
    # 2. Merge Everything
    # Base is IBGE (Population)
    # If IBGE doesn't have 2023, we might lose the SNIS 2023 data if we do left join
    # So we should extend IBGE with 2023 if needed (using 2022 pop as estimate or null)
    
    # Check if we have 2023 in SNIS but not in IBGE
    snis_years = df_snis['ano'].unique()
    ibge_years = df_ibge['ano'].unique()
    missing_years = set(snis_years) - set(ibge_years)
    
    if missing_years:
        print(f"DEBUG: Years in SNIS but not IBGE: {missing_years}. extending base dataframe.")
        # Create rows for missing years for each municipality
        new_rows = []
        municipalities = df_ibge[['cod_ibge', 'municipio_raw']].drop_duplicates()
        
        for year in missing_years:
            for _, row in municipalities.iterrows():
                new_row = row.to_dict()
                new_row['ano'] = year
                new_row['populacao'] = np.nan  # Missing population is not a real zero.
                new_rows.append(new_row)
                
        if new_rows:
            df_ibge = pd.concat([df_ibge, pd.DataFrame(new_rows)], ignore_index=True)

    final_df = df_ibge.copy()
    
    if df_ibge.empty:
        print("CRITICAL: No IBGE data found. Cannot build base dataset.")
        return

    print("--- Merging Data ---")
    
    # 2. Base Merge: IBGE is the anchor
    # IBGE has cod_ibge, populacao, ano
    # We need to ensure we have municipality names. load_ibge returns cod_ibge, populacao, ano.
    # We might need to fetch names from somewhere if load_ibge doesn't return them.
    # Let's check load_ibge. It returns [['cod_ibge', 'populacao', 'ano']].
    # We should modify load_ibge to return municipality name too.
    
    # For now, let's assume we can get names from a map or if we modify load_ibge.
    # Actually, let's modify load_ibge in a separate step or here if possible.
    # But wait, I can't modify load_ibge here easily without replacing the whole function.
    # I'll rely on the fact that I can merge with a mapping or just use what I have.
    # But I need 'municipio' column in the final output.
    
    # Let's assume load_ibge returns what it returns.
    # I'll add a helper to map codes to names for RMB if missing.
    
    final_df = df_ibge.copy()
    
    # Map names if missing (IBGE load might stripped them)
    # Actually, let's just add the names based on RMB_CITIES if we can match codes.
    # But we don't have the codes for RMB_CITIES hardcoded.
    # We should have kept 'municipio_raw' in load_ibge.
    
    # 3. Merge SNIS
    if not df_snis.empty:
        # SNIS has cod_ibge, ano, indicators
        final_df = pd.merge(final_df, df_snis, on=['cod_ibge', 'ano'], how='left')
    else:
        print("WARNING: SNIS data is empty. Indicators will be null.")
        for col in ['cobertura_agua', 'coleta_esgoto', 'tratamento_esgoto', 'esgoto_tratado_ref_agua', 'tarifa_media_agua', 'tarifa_media_esgoto']:
            final_df[col] = np.nan

    # 4. Merge SIH
    # Handle 6-digit vs 7-digit codes
    final_df['cod_ibge_6'] = final_df['cod_ibge'].astype(str).str[:6].astype(int)
    
    if not df_sih.empty:
        final_df = pd.merge(final_df, df_sih, left_on=['cod_ibge_6', 'ano'], right_on=['cod_ibge', 'ano'], how='left', suffixes=('', '_sih'))
        # Drop extra key
        if 'cod_ibge_sih' in final_df.columns:
            final_df = final_df.drop(columns=['cod_ibge_sih'])
            
        print(f"DEBUG: After SIH Merge. Non-null internacoes: {final_df['internacoes_hidricas_total'].count()}")
        print(f"DEBUG: Sample with internacoes:\n{final_df[final_df['internacoes_hidricas_total'].notnull()].head(2)}")
    else:
        # No source rows is not evidence of zero admissions.
        final_df['internacoes_hidricas_total'] = np.nan

    # 5. Merge Climate (Broadcast by Year)
    if not df_inmet.empty:
        final_df = pd.merge(final_df, df_inmet, on='ano', how='left')
    else:
        final_df['risco_climatico'] = np.nan
    
    # 6. Calculations
    # Admission rate per 10,000 is derived only when both the count and a
    # positive population denominator are available.
    final_df['taxa_internacoes_hidricas_10k'] = np.nan
    valid_rate = (
        final_df['internacoes_hidricas_total'].notna()
        & final_df['populacao'].notna()
        & (final_df['populacao'] > 0)
    )
    final_df.loc[valid_rate, 'taxa_internacoes_hidricas_10k'] = (
        final_df.loc[valid_rate, 'internacoes_hidricas_total']
        / final_df.loc[valid_rate, 'populacao']
        * 10000
    )
    
    # 7. Final Cleanup
    cols_order = [
        'municipio_raw', 'cod_ibge', 'ano', 
        'populacao',
        'cobertura_agua', 'coleta_esgoto', 'tratamento_esgoto', 'esgoto_tratado_ref_agua',
        'tarifa_media_agua', 'tarifa_media_esgoto',
        'internacoes_hidricas_total', 'taxa_internacoes_hidricas_10k',
        'risco_climatico'
    ]
    
    # Rename municipio_raw to municipio
    final_df = final_df.rename(columns={'municipio_raw': 'municipio'})
    
    # Select available columns
    available_cols = [c for c in cols_order if c in final_df.columns]
    # Ensure 'municipio' is present (it should be from IBGE)
    if 'municipio' not in available_cols and 'municipio' in final_df.columns:
        available_cols.insert(0, 'municipio')
        
    final_df = final_df[available_cols]
    
    # Sort
    if 'municipio' in final_df.columns:
        final_df = final_df.sort_values(['ano', 'municipio'])
    else:
        final_df = final_df.sort_values(['ano', 'cod_ibge'])

    # Export
    print(f"--- Saving to {OUTPUT_FILE} ---")
    final_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
    print("Done!")
    print(final_df.head())
    print(final_df.info())

if __name__ == "__main__":
    main()
