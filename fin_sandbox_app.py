import datetime as dt
import pandas as pd
import numpy as np
import streamlit as st # type: ignore

# Import user's domain modules. If these aren't on PYTHONPATH yet, show a helpful message.
modules_ok = True
cheques = pagares = credito = venta = None

try:
    import str.cheques as cheques
    import str.pagares as pagares
    import str.credito as credito
    import str.venta   as venta
except Exception as e:
    modules_ok = False
    import traceback
    tb = traceback.format_exc()

# ---------- Page config ----------
st.set_page_config(
    page_title="Calculadora de tasas y flujos 💸",
    page_icon="💸",
    layout="wide",
)
st.title("Calculadora de tasas y flujos 💸")
# st.caption("Tweak inputs. See flows. Poke reality with a slider.")

if not modules_ok:
    with st.expander("Troubleshooting: couldn't import your modules", expanded=True):
        st.write(
            "I tried to import `str.cheques`, `str.pagares`, `str.credito`, and `str.venta` "
            "but hit an error. Make sure your project root (where the `str/` package lives) "
            "is on `PYTHONPATH` or run Streamlit from that root.\n\n"
            "**Import error trace:**"
        )
        st.code(tb, language="text")

# ---------- Sidebar controls ----------
st.sidebar.header("Parameters")
product = st.sidebar.selectbox(
    "Instrument",
    options=[
        "Inversores BCBB",
        "Pagarés",
        "Créditos",
        "Venta de crédito"        
    ],
    index=0,
)

# Common UI helpers
def pct_slider(label, value, minv=0.0, maxv=3.0, step=0.01, help_text=None):
    return st.sidebar.slider(label, min_value=minv, max_value=maxv, value=float(value), step=step, help=help_text)

def int_slider(label, value, minv=1, maxv=360, step=1, help_text=None):
    return st.sidebar.slider(label, min_value=int(minv), max_value=int(maxv), value=int(value), step=step, help=help_text)

def period_from_date(d):
    # Streamlit date -> pandas Period (day frequency), as expected by user's API
    return pd.Period(pd.Timestamp(d).date(), freq="D")

def number_input_float(label, value, minv, maxv, step, **kw):
    return st.sidebar.number_input(label,
        value=float(value), min_value=float(minv),
        max_value=float(maxv), step=float(step), **kw)

def number_input_int(label, value, minv, maxv, step=1, **kw):
    return st.sidebar.number_input(label,
        value=int(value), min_value=int(minv),
        max_value=int(maxv), step=int(step), **kw)

df = None
tea = None
tem = None

# Controls & calls per instrument
if product == "Inversores BCBB":
    fecha    = st.sidebar.date_input("Fecha de colocación", value=dt.date.today())
    capital  = st.sidebar.number_input("Capital inicial", min_value=0.0, value=100000.0, step=1000.0)
    tna_desc = number_input_float("TNA descuento (e.g., 0.51 = 51%)", 0.51, 0.0, 2.0, 0.01)
    coloc    = number_input_float("Comisión BCBB", 0.05, 0.0, 2.0, 0.01)
    plazo_d  = int_slider("Plazo (días)", 30, minv=15, maxv=365, step=15)
    

    st.sidebar.caption("Calls: `cheques.flujo(tna_desc, colocacion, plazo, capital, fecha)`")
    if modules_ok and cheques is not None:
        df, tea, tem = cheques.flujo(tna_desc, coloc, plazo_d, capital, pd.Period(fecha, freq="D"))

elif product == "Pagarés":
    fecha    = st.sidebar.date_input("Fecha de colocación", value=dt.date.today())
    capital  = st.sidebar.number_input("Capital inicial", min_value=0.0, value=100000.0, step=1000.0)
    tna_desc = number_input_float("TAMAR (e.g., 0.51 = 51%)", 0.60, 0.0, 2.0, 0.01)
    coloc    = number_input_float("TNA Descuento", 0.05, 0.0, 2.0, 0.01)
    plazo_d  = int_slider("Plazo (días)", 30, minv=15, maxv=365, step=15)

    st.sidebar.caption("Calls: `pagares.flujo(tna_desc, colocacion, plazo, capita, fecha)`")
    if modules_ok and pagares is not None:
        df, tea, tem = pagares.flujo(tna_desc, coloc, plazo_d, capital, pd.Period(fecha, freq="D"))

elif product == "Créditos":
    fecha    = st.sidebar.date_input("Fecha de colocación", value=dt.date.today())
    capital  = st.sidebar.number_input("Capital inicial", min_value=0.0, value=100000.0, step=1000.0)
    tna      = number_input_float("TNA c/IVA", 1.71, 0.0, 2.0, 0.01)
    plazo    = st.sidebar.selectbox("Plazo (días)", options=(9, 12, 15, 18, 24, 48, 30, 36))
    coloc  = number_input_float("Comisión Colocación", 0.05, 0.0, 1.0, 0.01)
    cob    = number_input_float("Comisión Cobranza", 0.04, 0.0, 1.0, 0.01)
    iibb   = number_input_float("IIBB", 0.07, 0.0, 1.0, 0.01)
    st.sidebar.caption("Calls: `credito.flujo(tna=..., plazo=..., colocacion=..., cobranza=..., iibb=...)`")
    if modules_ok and credito is not None:
        df, tea, tem = credito.flujo(tna=tna, plazo=plazo, colocacion=coloc, cobranza=cob, iibb=iibb, cap=capital, fecha=pd.Period(fecha, freq="D"))

else:  # Venta de crédito
    # Default fecha_vta = today + 30d
    fondeo    = st.sidebar.checkbox("Para fondeo", value=True)
    fecha    = st.sidebar.date_input("Fecha de colocación", value=dt.date.today())
    capital  = st.sidebar.number_input("Capital inicial", min_value=0.0, value=100000.0, step=1000.0)
    default_date = (pd.Timestamp(fecha) + pd.Timedelta(days=30)).date()  # ✅
    fecha_vta = st.sidebar.date_input("Fecha de venta", value=default_date)
    tna_desc  = number_input_float("TNA Descuento", 0.6, 0.0, 2.0, 0.01)
    tna       = number_input_float("TNA c/IVA", 1.71, 0.0, 2.0, 0.01)
    plazo     = st.sidebar.selectbox("Plazo (meses)", options=(9, 12, 15, 18, 24, 48, 30, 36))
    coloc     = number_input_float("Comisión Colocación", 0.05, 0.0, 1.0, 0.01)
    cob       = number_input_float("Comisión Cobranza", 0.04, 0.0, 1.0, 0.01)
    iibb      = number_input_float("IIBB", 0.07, 0.0, 1.0, 0.01)
    

    st.sidebar.caption("Calls: `venta.flujo(fecha_vta=Period, tna_desc=..., tna=..., plazo=..., colocacion=..., cobranza=..., iibb=..., fondeo=...)`")
    if modules_ok and venta is not None:
        df, tea, tem = venta.flujo(
            fecha_vta=period_from_date(fecha_vta),
            tna_desc=tna_desc, tna=tna, plazo=plazo,
            colocacion=coloc, cobranza=cob, iibb=iibb,
            fondeo=fondeo, cap=capital, fecha=period_from_date(fecha))
        
# ---------- Output ----------
colA, colB, colC = st.columns(3)
with colA:
    st.metric("TEA", f"{tea:.2%}" if tea is not None else "—")
with colB:
    st.metric("TEM (aprox.)", f"{tem:.2%}" if tem is not None else "—")
with colC:
    if df is not None and len(df):
        try:
            # If the DF has a 'Flujo' column, show simple IRR over a guess schedule (best-effort)
            if "Flujo" in df.columns:
                # Attempt XIRR only if index looks like dates/periods
                idx = df.index
                try:
                    dates = pd.to_datetime(idx.astype(str))
                    vals = df["Flujo"].astype(float).values
                    # A very light-weight "xirr" like computation isn't trivial;
                    # we just display total for now and keep the metric slot.
                    st.metric("Total flujo", f"{np.nansum(vals):,.2f}") # type: ignore
                except Exception:
                    st.metric("Total flujo", "—")
            else:
                st.metric("Total filas", f"{len(df):,}")
        except Exception:
            st.metric("Total filas", f"{len(df):,}" if df is not None else "—")

st.divider()

if df is not None:
    # Try to ensure friendly display: convert PeriodIndex to datetime for grid/plot
    if isinstance(df.index, pd.PeriodIndex):
        df_display = df.map('$ {:,.2f}'.format).copy()
        df_display.index = df_display.index.to_timestamp(how='end', format='%Y-%m-%d') # type: ignore
    else:
        df_display = df.map('$ {:,.2f}'.format).copy()
        
    st.subheader("Cash Flow Table")
    st.dataframe(df_display, use_container_width=True)

    # Download
    csv = df.to_csv(index=True).encode("utf-8")
    st.download_button("Download CSV", data=csv, file_name="cashflow.csv", mime="text/csv")

else:
    st.info("Pick parameters on the left to generate results.")
