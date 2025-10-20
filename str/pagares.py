import pandas as pd
import numpy as np

from pyxirr import xirr

from str.constantes import com_gst_bco, d_mercado, arancel


def pagares(tamar: float, tna: float, plazo:int, capital: float = 10**6, fecha: pd.Period = pd.Period.now('D'), periodos: int = 12) -> pd.DataFrame:
    
    df = []
    precio = 1 / (1 + (tna/365 * plazo))
    der_mer = d_mercado * min(plazo,90) / 90 * 1.21
    gst_arancel = arancel * min(plazo,365) / 365 * 1.21
    
    for i in range(periodos):
        vto = fecha + plazo
        descontado = capital * precio
        gastos = descontado * (der_mer + gst_arancel)
        neto = descontado - gastos
        interes = neto * tamar * plazo / 365
        total = capital + interes
        df.append({
            'Emisión'   : fecha,
            'Vto.'      : vto,
            'Capital'   : capital,
            'Descontado': descontado,
            'Gastos'    : gastos,
            'Neto'      : neto,
            'Interés'   : interes,
            'Total'     : total})
        
        capital = np.ceil(total * (1 + com_gst_bco) / 10**5) * 10**5
        fecha = vto
    
    df = pd.DataFrame(df)
    
    return df


def flujo(tamar: float, tna: float, plazo: int, capital: float = 10**6, fecha: pd.Period = pd.Period.now('D'), periodo: int =12) -> tuple[pd.DataFrame, float, float]:
   
    periodos = min(periodo, int(365 / plazo), 12)
    df_pagares = pagares(tamar, tna, plazo, capital, fecha, periodos)
    
    fechas = list(df_pagares['Emisión']) + list(df_pagares['Vto.'])
    fechas = {'Fecha': fechas}
    df = pd.DataFrame(fechas)
    df = df.drop_duplicates().sort_values(by='Fecha').reset_index(drop=True)
    df.set_index('Fecha', inplace=True)
    df['Flujo'] = 0.0
    
    df.loc[fecha, 'Flujo'] -= df_pagares.at[0, 'Neto'] * (1 - com_gst_bco) # type: ignore
    for i in range(periodos-1):
        vto = df_pagares.at[i, 'Vto.']
        neto = df_pagares.at[i + 1, 'Neto']
        total = df_pagares.at[i, 'Total']
        df.at[vto, 'Flujo'] += total * (1+com_gst_bco) - neto * (1 - com_gst_bco) # type: ignore
    
    ult_vto = max(df_pagares['Vto.'])
    df.loc[ult_vto, 'Flujo'] += df_pagares.at[periodos-1, 'Total'] * (1 + com_gst_bco) # type: ignore
    
    df.index = df.index.to_timestamp() # type: ignore
    
    tea = float(xirr(dates=df.index, amounts=df['Flujo'])) # type: ignore
    tem = (1+tea)**(30/365) - 1
    
    print('Costo de fondearse con pagares:')
    print(f'    TEM: {tem:.2%}')
    print(f'    TEA: {tea:.2%}')
    
    return df, tea, tem