import pandas as pd
import numpy_financial as npf

from pyxirr import xirr
from IPython.display import display

import str.credito as credito
from str.constantes import com_gst_bco


def flujo(fecha_vta: pd.Period, tna_desc: float, tna: float, plazo:int, colocacion: float, cobranza: float, iibb: float, fondeo: bool = True, comision: float = 0.0, gracia: int = 2, cap: float = 10**6, fecha: pd.Period = pd.Period.now('D'))-> tuple[pd.DataFrame, float, float]:
    
    df = pd.DataFrame()
    if not fondeo:
        pago_col = pd.Period(fecha, freq='M') + 1
        pago_col = pd.Period(year=pago_col.year, month=pago_col.month, day=10, freq='D')

        df.loc[fecha.to_timestamp(), 'Flujo'] = -cap * (1+com_gst_bco)
        df.loc[pago_col.to_timestamp(), 'Flujo'] = -cap * colocacion * (1+com_gst_bco)

    df_ctas = credito.nuevo(tna, plazo, gracia, cap, fecha)
    df_ctas = df_ctas.reset_index(level='Nro_Cuota')
    df_ctas['Cap. + Int.'] = df_ctas[['Capital', 'Interés']].sum(axis=1)
    df_ctas['Val. Act.'] = df_ctas.apply(lambda row: row['Cap. + Int.']/(1+tna_desc/365)**(row.name - fecha_vta).n, axis=1) 

    if fecha_vta in df.index:
        df.loc[fecha_vta.to_timestamp(), 'Flujo'] += df_ctas['Val. Act.'].sum() * (1-com_gst_bco)
    else:
        df.loc[fecha_vta.to_timestamp(), 'Flujo'] = df_ctas['Val. Act.'].sum() * (1-com_gst_bco)

    for vto in df_ctas.index.get_level_values('Vto.'):
        vto = vto.to_timestamp()
        if fondeo:
            df.loc[vto, 'Flujo'] = -df_ctas.at[vto, 'Cap. + Int.'] * (1+com_gst_bco) # type: ignore
            df.loc[vto, 'Flujo'] -= df_ctas.at[vto, 'Total'] * cobranza # type: ignore
            df.loc[vto, 'Flujo'] -= df_ctas.at[vto, 'Total'] * (1-cobranza) * com_gst_bco # type: ignore
            df.loc[vto, 'Flujo'] -= df_ctas.at[vto, 'Interés'] * iibb * (1+com_gst_bco) # type: ignore
            df.loc[vto, 'Flujo'] -= df_ctas.at[vto, 'IVA'] * com_gst_bco # type: ignore
        else:
            df.loc[vto, 'Flujo'] = df_ctas.at[vto, 'Total'] * (1-cobranza) * (1-com_gst_bco) # type: ignore
            df.loc[vto, 'Flujo'] -= df_ctas.at[vto, 'IVA'] * (1+com_gst_bco)# type: ignore
            df.loc[vto, 'Flujo'] -= df_ctas.at[vto, 'Interés'] * iibb * (1+com_gst_bco)# type: ignore
            df.loc[vto, 'Flujo'] -= df_ctas.at[vto, 'Cap. + Int.'] * (1+com_gst_bco) # type: ignore

    tea = xirr(dates=df.index, amounts=df['Flujo'])
    if tea is None:
        display(df.map('$ {:,.2f}'.format))
        # tu implementación devolvió None (no convergió); avisamos claro
        raise RuntimeError(f"XIRR no convergió con los flujos dados.")
    else:
        tea = float(tea)

    tem = (1+tea)**(30/365) - 1 # type: ignore

    if fondeo:
        print('Costo fondearse vendiendo cartera:')
    else:
        print('Rendimiento de vender cartera:')
        
    print(f'    TEM: {tem:.2%}')
    print(f'    TEA: {tea:.2%}')
    
    return df, tea, tem
