import pandas as pd
import numpy as np

# Load Data
df = pd.read_csv('data/iara/iara_municipios_rmb.csv')

# Hardcoded Population Data (IBGE 2022/2023 Estimates)
pop_map = {
    'Belém (PA)': 1303389,
    'Ananindeua (PA)': 478112,
    'Marituba (PA)': 111073,
    'Castanhal (PA)': 192262,
    'Benevides (PA)': 63567,
    'Santa Izabel do Pará (PA)': 71247,
    'Santa Bárbara do Pará (PA)': 21071
}

# Update Population for 2023 (and fill others if 0)
for mun, pop in pop_map.items():
    # Update 2023 specifically
    mask_2023 = (df['municipio'] == mun) & (df['ano'] == 2023)
    df.loc[mask_2023, 'populacao'] = pop
    
    # If 0 in other years, fill with this value (better than 0)
    mask_zero = (df['municipio'] == mun) & (df['populacao'] == 0)
    df.loc[mask_zero, 'populacao'] = pop

# Recalculate Rates
# taxa = (internacoes / populacao) * 10000
df['taxa_internacoes_hidricas_10k'] = (df['internacoes_hidricas_total'] / df['populacao']) * 10000

# Handle Inf/NaN
df['taxa_internacoes_hidricas_10k'] = df['taxa_internacoes_hidricas_10k'].replace([np.inf, -np.inf], 0).fillna(0)

# Save
df.to_csv('data/iara/iara_municipios_rmb.csv', index=False)
print("Data patched successfully.")
print(df[df['ano'] == 2023][['municipio', 'populacao', 'taxa_internacoes_hidricas_10k']])
