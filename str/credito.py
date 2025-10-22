import pandas as pd
import numpy_financial as npf

from pyxirr import xirr
from IPython.display import display

from str.constantes import com_gst_bco

def nuevo(tna: float, plazo:int, gracia: int = 2, cap: float = 10**6, fecha: pd.Period = pd.Period.now('D'))-> pd.DataFrame:
    
    r = tna * 30 / 365

    val_cta = round(float(npf.pmt(r, plazo, -cap)), 2)

    df = []
    for i in range(plazo):
        vto = pd.Period(fecha, freq='M') + i + gracia
        capital = round(float(npf.ppmt(r, i+1, plazo, -cap)), 2)
        interes = round(float(npf.ipmt(r, i+1, plazo, -cap)/1.21), 2)
        iva     = val_cta - capital - interes
        df.append({
            'Nro_Cuota':i+1,
            'Vto.': pd.Period(year=vto.year, month=vto.month, day=28, freq='D'),
            'Capital': capital,
            'Interés': interes,
            'IVA': iva,
            'Total': val_cta,
        })

    df = pd.DataFrame(df)
    df.set_index(['Nro_Cuota', 'Vto.'], inplace=True)

    return df


def flujo(tna: float, plazo:int, colocacion: float, cobranza: float, iibb: float, comision: float = 0.0, gracia: int = 2, cap: float = 10**6, fecha: pd.Period = pd.Period.now('D'))-> tuple[pd.DataFrame, float, float]:
    
    pago_col = pd.Period(fecha, freq='M') + 1
    pago_col = pd.Period(year=pago_col.year, month=pago_col.month, day=10, freq='D')

    df = pd.DataFrame()
    df.loc[fecha.to_timestamp(), 'Flujo'] = -cap * (1+com_gst_bco)
    df.loc[pago_col.to_timestamp(), 'Flujo'] = -cap * colocacion * (1+com_gst_bco)

    df_ctas = nuevo(tna, plazo, gracia, cap, fecha)
    # display(df_ctas.map('$ {:,.2f}'.format))
    df_ctas = df_ctas.reset_index(level='Nro_Cuota')
    for vto in df_ctas.index.get_level_values('Vto.'):

        df.loc[vto.to_timestamp(), 'Flujo'] = df_ctas.at[vto, 'Total'] * (1-cobranza) * (1-com_gst_bco) # type: ignore
        df.loc[vto.to_timestamp(), 'Flujo'] -= df_ctas.at[vto, 'IVA'] * (1+com_gst_bco)# type: ignore
        df.loc[vto.to_timestamp(), 'Flujo'] -= df_ctas.at[vto, 'Interés'] * iibb * (1+com_gst_bco)# type: ignore

    tea = float(xirr(dates=df.index, amounts=df['Flujo'])) # type: ignore
    tem = (1+tea)**(30/365) - 1 # type: ignore

    print('Rendimiento de vender créditos:')
    print(f'    TEM: {tem:.2%}')
    print(f'    TEA: {tea:.2%}')

    return df, tea, tem