import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import base64

# --- 1. LIDHJA ME FIREBASE ---
if not firebase_admin._apps:
    try:
        fb_dict = dict(st.secrets["firebase"])
        cred = credentials.Certificate(fb_dict)
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://herolind-6ca5f-default-rtdb.europe-west1.firebasedatabase.app/'
        })
    except Exception as e:
        st.error(f"Gabim në lidhje: {e}")

def load_cloud(path):
    res = db.reference(path).get()
    return res if res is not None else []

def save_cloud(path, data):
    db.reference(path).set(data)

# --- 2. KONFIGURIMI DHE STILI ---
st.set_page_config(page_title="AUTO BUNA PRO 2026", layout="wide", page_icon="🚗")

MUAJT_SHQIP = {
    "01": "Janar", "02": "Shkurt", "03": "Mars", "04": "Prill",
    "05": "Maj", "06": "Qershor", "07": "Korrik", "08": "Gusht",
    "09": "Shtator", "10": "Tetor", "11": "Nëntor", "12": "Dhjetor"
}

st.markdown("""
    <style>
    .fatura-container { 
        padding: 40px; border: 1px solid #000; background-color: #fff; color: #000; 
        font-family: 'Courier New', monospace; line-height: 1.5;
    }
    .signature-section { margin-top: 50px; display: flex; justify-content: space-between; }
    .signature-line { border-top: 1px solid #000; width: 200px; text-align: center; padding-top: 5px; }
    .stButton>button { background-color: #e60073; color: white; border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

def create_pdf_download_link(html_content, filename="fatura.html"):
    b64 = base64.b64encode(html_content.encode()).decode()
    return f'<a href="data:text/html;base64,{b64}" download="{filename}" style="text-decoration:none;"><button style="background-color:#28a745; color:white; padding:10px; border:none; border-radius:5px; width:100%; cursor:pointer;">💾 SHKARKO FATURËN (PDF)</button></a>'

stoku = load_cloud('stoku')
historiku = load_cloud('historiku')
investimet = load_cloud('investimet')

# --- 3. NAVIGIMI ---
with st.sidebar:
    st.title("🚗 AUTO BUNA")
    menu = st.radio("MENUJA:", ["📊 Dashboard", "📦 Gjendja e Stokut", "📥 Pranim Malli", "💸 Shitje & Faturë"])
    st.write("---")
    st.write("📍 **DRENAS**")

# --- 4. DASHBOARD (ME BILANCIN) ---
if menu == "📊 Dashboard":
    st.title("📈 Raporti Mujor i Biznesit")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        viti_zgjedhur = st.selectbox("Viti:", [str(y) for y in range(2024, 2051)], index=2) # 2026
    with col_f2:
        muaji_emri = st.selectbox("Muaji:", list(MUAJT_SHQIP.values()), index=datetime.now().month-1)
    
    muaji_kod = [k for k, v in MUAJT_SHQIP.items() if v == muaji_emri][0]
    kerko_daten = f"{muaji_kod}-{viti_zgjedhur}"

    hyrje = sum(float(i.get('shuma_blerjes', 0)) for i in investimet if kerko_daten in str(i.get('data', '')))
    dalje = sum(float(h.get('total', 0)) for h in historiku if kerko_daten in str(h.get('data_shitjes', '')))
    bilanci = dalje - hyrje

    st.write("##")
    c1, c2, c3 = st.columns(3)
    c1.metric("Totali i Investuar", f"{hyrje:,.2f} €")
    c2.metric("Totali i Shitur", f"{dalje:,.2f} €")
    c3.metric("BILANCI (FITIMI)", f"{bilanci:,.2f} €", delta=f"{bilanci:,.2f} €")

# --- 5. GJENDJA E STOKUT ---
elif menu == "📦 Gjendja e Stokut":
    st.title("📦 Malli në Depo (Drenas)")
    search = st.text_input("🔍 Kërko...").upper()
    if stoku:
        for idx, r in enumerate(stoku):
            if search in r.get('marka', '') or search in r.get('modeli', ''):
                with st.expander(f"📌 {r.get('marka')} {r.get('modeli')} - {r.get('ana', 'N/A')}"):
                    st.write(f"Sasia: {r.get('sasia')} | Blerja: {r.get('blerja')}€")
                    if st.button("🗑️ FSHIJ", key=f"d_{idx}"):
                        stoku.pop(idx)
                        save_cloud('stoku', stoku)
                        st.rerun()

# --- 6. PRANIM MALLI ---
elif menu == "📥 Pranim Malli":
    st.title("📥 Pranim i Ri")
    with st.form("forma"):
        m = st.text_input("Marka:").upper()
        mod = st.text_input("Modeli:").upper()
        ana = st.selectbox("Ana:", ["MAJTAS (L)", "DJATHTAS (R)", "SET (L+R)"])
        sas = st.number_input("Sasia:", min_value=1)
        ble = st.number_input("Blerja (€):", min_value=0.0)
        if st.form_submit_button("RUAJ"):
            dt = datetime.now().strftime("%d-%m-%Y")
            stoku.append({"marka": m, "modeli": mod, "ana": ana, "sasia": sas, "blerja": ble, "data": dt})
            investimet.append({"data": dt, "shuma_blerjes": sas * ble})
            save_cloud('stoku', stoku)
            save_cloud('investimet', investimet)
            st.success("U ruajt!")

# --- 7. SHITJE & FATURË (ME KONTAKTE TË REJA) ---
elif menu == "💸 Shitje & Faturë":
    st.title("💸 Shitje e Re")
    klienti = st.text_input("Klienti:")
    if stoku:
        ops = [f"{i.get('marka')} {i.get('modeli')} ({i.get('sasia')})" for i in stoku]
        zgj = st.selectbox("Produkti:", ops)
        idx = ops.index(zgj)
        s_sh = st.number_input("Sasia:", min_value=1, max_value=int(stoku[idx].get('sasia')))
        c_sh = st.number_input("Çmimi (€):", min_value=0.0)

        if st.button("KRYEJ SHITJEN"):
            stoku[idx]['sasia'] -= s_sh
            total = s_sh * c_sh
            dt_f = datetime.now().strftime("%d-%m-%Y")
            historiku.append({"data_shitjes": dt_f, "klienti": klienti, "total": total})
            if stoku[idx]['sasia'] <= 0: stoku.pop(idx)
            save_cloud('stoku', stoku)
            save_cloud('historiku', historiku)

            fatura_html = f"""
            <div class='fatura-container'>
                <h1 style='text-align:center;'>AUTO BUNA</h1>
                <p style='text-align:center;'>📍 DRENAS | 📞 049 160 886 | 📞 044 532 990</p>
                <hr>
                <p><b>DATA:</b> {dt_f} | <b>KLIENTI:</b> {klienti}</p>
                <p><b>PRODUKTI:</b> {zgj}</p>
                <p><b>SASIA:</b> {s_sh} | <b>PËR NJËSI:</b> {c_sh:.2f} €</p>
                <hr>
                <h2 style='text-align:right;'>TOTALI: {total:.2f} €</h2>
                <div class='signature-section'>
                    <div class='signature-line'>Nënshkrimi i Shitësit</div>
                    <div class='signature-line'>Nënshkrimi i Blerësit</div>
                </div>
            </div>
            """
            st.markdown(fatura_html, unsafe_allow_html=True)
            st.markdown(create_pdf_download_link(fatura_html, f"Fatura_{klienti}.html"), unsafe_allow_html=True)
