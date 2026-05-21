import requests
import pandas as pd
from datetime import date
import os

TENORES = {
    '1m':  'M.U2.EUR.RT.MM.EURIBOR1MD_.HSTA',
    '3m':  'M.U2.EUR.RT.MM.EURIBOR3MD_.HSTA',
    '6m':  'M.U2.EUR.RT.MM.EURIBOR6MD_.HSTA',
    '12m': 'M.U2.EUR.RT.MM.EURIBOR1YD_.HSTA',
}
BASE_URL = "https://data-api.ecb.europa.eu/service/data/FM/"
CSV_PATH = "euribor_diario.csv"
START    = "2005-01-01"

def descargar_tenor(serie, start):
    url = BASE_URL + serie
    params = {
        'startPeriod': start,
        'detail': 'dataonly',
        'format': 'csvdata'
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    df = pd.read_csv(pd.io.common.StringIO(r.text))
    return df[['TIME_PERIOD', 'OBS_VALUE']].dropna()

def main():
    if os.path.exists(CSV_PATH):
        existing = pd.read_csv(CSV_PATH, parse_dates=['date'])
        last_date = existing['date'].max().strftime('%Y-%m')
        start = last_date
        print(f"CSV existente. Actualizando desde {start}...")
    else:
        existing = None
        start = START
        print(f"Primer run. Descargando historico desde {start}...")

    dfs = {}
    for tenor, serie in TENORES.items():
        print(f"  Descargando {tenor}...")
        df = descargar_tenor(serie, start)
        df.columns = ['date', tenor]
        dfs[tenor] = df

    merged = dfs['1m']
    for t in ['3m', '6m', '12m']:
        merged = merged.merge(dfs[t], on='date', how='outer')

    merged = merged.sort_values('date').reset_index(drop=True)

    if existing is not None:
        combined = pd.concat([existing, merged])
        combined = combined.drop_duplicates(subset='date', keep='last')
        combined = combined.sort_values('date').reset_index(drop=True)
    else:
        combined = merged

    combined.to_csv(CSV_PATH, index=False, float_format='%.4f')
    print(f"Guardado: {len(combined)} filas | Ultimo dato: {combined['date'].max()}")

if __name__ == "__main__":
    main()
