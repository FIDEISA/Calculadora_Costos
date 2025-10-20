import pandas as pd
from pyxirr import xirr

from str.constantes import gast_dep_chq, com_gst_bco

def deuda_bcbb(tna: float, comision: float, plazo: int, capital: float = 10**6, fecha: pd.Period = pd.Period.now('D'), periodos: int = 12) -> pd.DataFrame:
     
    cap = capital
    
    df = []
    
    for p in range(periodos):
        vto = fecha + plazo
        f_com = pd.Period(fecha, freq='M') + 1
        f_com = pd.Period(year=f_com.year, month=f_com.month, day=10, freq='D')
        com = capital * comision/365 * plazo
        interes = capital * tna/365 * plazo
        total = capital + interes
        df.append({
            'Emisión': fecha,
            'Vto.' : vto,
            'Capital': capital,
            'Interés': interes,
            'Total'  : capital + interes,
            'Pago Comisión': f_com,
            'Comisión': com
        })
        fecha = vto
        capital = total
    
    df = pd.DataFrame(df)
    df.index.name = 'Periodo'
    
    return df

def flujo(tna: float, comision: float, plazo: int, capital: float = 10**6, fecha: pd.Period = pd.Period.now('D'), periodo: int =12) -> tuple[pd.DataFrame, float, float]:
    
    periodos = min(periodo, int(365 / plazo), 12)
    df_bcbb = deuda_bcbb(tna, comision, plazo, capital, fecha, periodos)
    
    fechas = list(df_bcbb['Emisión']) + list(df_bcbb['Vto.']) + list(df_bcbb['Pago Comisión'])
    fechas = {'Fecha': fechas}
    df = pd.DataFrame(fechas)
    df = df.drop_duplicates().sort_values(by='Fecha').reset_index(drop=True)
    df.set_index('Fecha', inplace=True)
    df['Flujo'] = 0.0
    
    df.loc[fecha, 'Flujo'] -= capital * (1 - gast_dep_chq) * (1 - com_gst_bco)**2 # type: ignore
    for i in df_bcbb.index:
        f_pago = df_bcbb.at[i, 'Pago Comisión']
        comision = df_bcbb.at[i, 'Comisión'] # type: ignore
        df.loc[f_pago, 'Flujo'] += comision * (1 + com_gst_bco) # type: ignore
        
    ult_vto = max(df_bcbb['Vto.'])
    df.loc[ult_vto, 'Flujo'] += df_bcbb.loc[periodos-1, 'Total'] * (1 + com_gst_bco)**2 # type: ignore
    df.index = df.index.to_timestamp() # type: ignore
    
    tea = float(xirr(dates=df.index, amounts=df['Flujo'])) # type: ignore
    tem = (1+tea)**(30/365) - 1 # type: ignore
    
    print('Costo de fondearse con inversores de la BCBB:')
    print(f'    TEM: {tem:.2%}')
    print(f'    TEA: {tea:.2%}')
    
    return df, tea, tem