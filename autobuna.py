import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import base64

# --- 1. KONFIGURIMI I CLOUD (FIREBASE) ---
if not firebase_admin._apps:
    try:
        # Merr kredencialet nga Streamlit Secrets
        fb_dict = dict(st.secrets["firebase"])
        cred = credentials.Certificate(fb_dict)
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://herolind-6ca5f-default-rtdb.europe-west1.firebasedatabase.app/'
        })
    except Exception as e:
        st.error(f"Gabim në lidhjen me Cloud: {e}")

# Funksionet për Cloud (Zëvendësojnë load_data/save_data)
def load_cloud(path):
    return db.reference(path).get() or []

def save_cloud(path, data):
    db.reference(path).set(data)

# --- 2. KONFIGURIMI I UI ---
st.set_page_config(page_title="AUTO BUNA PRO 2026", layout="wide", page_icon="🚗")

MUAJT_SHQIP = {
    "01": "Janar", "02": "Shkurt", "03": "Mars", "04": "Prill",
    "05": "Maj", "06": "Qershor", "07": "Korrik", "08": "Gusht",
    "09": "Shtator", "10": "Tetor", "11": "Nëntor", "12": "Dhjetor"
}

st.markdown("""
    <style>
    .fatura-container { padding: 40px; border: 1px solid #000; background-color: #fff; color: #000; font-family: 'Courier New', monospace; line-height: 1.5; }
    .signature-section { margin-top: 50px; display: flex; justify-content: space-between; }
    .signature-line { border-top: 1px solid #000; width: 200px; text-align: center; padding-top: 5px; }
    .stButton>button { background-color: #e60073; color: white; border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# Ngarkimi i të dhënave Live nga Cloud
stoku = load_cloud('stoku')
historiku = load_cloud('historiku')
investimet = load_cloud('investimet')

# --- 3. NAVIGIMI ---
with st.sidebar:
    st.title("🚗 AUTO BUNA")
    menu = st.radio("MENUJA:", ["📊 Dashboard", "📦 Gjendja e Stokut", "📥 Pranim Malli", "💸 Shitje & Faturë"])
    st.write("---")
    st.write("📍 Fushë Kosovë")

# --- 4. LOGJIKA E FAQEVE ---

if menu == "📊 Dashboard":
    st.title("📈 Raporti Mujor i Biznesit (Cloud)")
    vitet = [str(year) for year in range(2024, 2051)]
    viti_zgjedhur = st.selectbox("Viti:", vitet, index=vitet.index("2026"))
    muaji_emri = st.selectbox("Muaji:", list(MUAJT_SHQIP.values()), index=datetime.now().month-1)
    
    muaji_kod = [k for k, v in MUAJT_SHQIP.items() if v == muaji_emri][0]
    kerko_daten = f"{muaji_kod}-{viti_zgjedhur}"

    hyrje_totale = sum(float(i['shuma_blerjes']) for i in investimet if kerko_daten in i['data'])
    dalje_totale = sum(float(h['total']) for h in historiku if kerko_daten in h['data_shitjes'])

    st.write("##")
    c1, c2 = st.columns(2)
    c1.metric("Totali i Investuar", f"{hyrje_totale:,.2f} €")
    c2.metric("Totali i Shitur", f"{dalje_totale:,.2f} €")

elif menu == "📦 Gjendja e Stokut":
    st.title("📦 Malli aktual në Depo (Live)")
    search = st.text_input("🔍 Kërko mallin...", "").upper()
    
    if stoku:
        df = pd.DataFrame(stoku)
        if search:
            mask = df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)
            df = df[mask]

        for index, row in df.iterrows():
            with st.expander(f"📌 {row['marka']} {row['modeli']} - {row['ana']}"):
                st.write(f"**Sasia:** {row['sasia']} | **Blerja:** {row['blerja']}€ | **Data:** {row['data']}")
                if st.button("🗑️ FSHIJ", key=f"del_{index}"):
                    stoku.pop(index)
                    save_cloud('stoku', stoku)
                    st.rerun()
    else:
        st.info("Depoja është e zbrazët.")

elif menu == "📥 Pranim Malli":
    st.title("📥 Regjistrim në Cloud")
    with st.form("forma_pranim", clear_on_submit=True):
        c1, c2 = st.columns(2)
        d_r = c1.date_input("Data:", datetime.now())
        marka = c2.text_input("Marka:").upper()
        modeli = st.text_input("Modeli:").upper()
        c3, c4 = st.columns(2)
        sasia = c3.number_input("Sasia:", min_value=1)
        blerja = c4.number_input("Çmimi Blerjes (€):", min_value=0.0)
        ana = st.selectbox("Ana:", ["MAJTAS (L)", "DJATHTAS (R)", "SET (L+R)"])
        
        if st.form_submit_button("KONFIRMO DHE RUAJ NË CLOUD"):
            data_str = d_r.strftime("%d-%m-%Y")
            stoku.append({"data": data_str, "marka": marka, "modeli": modeli, "ana": ana, "sasia": sasia, "blerja": blerja})
            investimet.append({"data": data_str, "shuma_blerjes": sasia * blerja})
            save_cloud('stoku', stoku)
            save_cloud('investimet', investimet)
            st.success("U ruajt në Firebase!")

elif menu == "💸 Shitje & Faturë":
    st.title("💸 Shitje dhe Faturim")
    klienti = st.text_input("Emri i Klientit:")
    data_sh = st.date_input("Data e Shitjes:", datetime.now())
    
    if stoku:
        opsionet = [f"{i['marka']} {i['modeli']} - {i['ana']} | {i['sasia']} në stok" for i in stoku]
        zgjedh = st.selectbox("Zgjidh produktin:", opsionet)
        idx_s = opsionet.index(zgjedh)
        s_sh = st.number_input("Sasia për shitje:", min_value=1, max_value=int(stoku[idx_s]['sasia']))
        c_sh = st.number_input("Çmimi i Shitjes (€):", min_value=0.0)

        if st.button("KRYEJ SHITJEN & KRIJO FATURËN"):
            total_f = s_sh * c_sh
            stoku[idx_s]['sasia'] -= s_sh
            if stoku[idx_s]['sasia'] <= 0: stoku.pop(idx_s)
            
            data_f = data_sh.strftime("%d-%m-%Y")
            historiku.append({"data_shitjes": data_f, "klienti": klienti, "total": total_f})
            
            save_cloud('stoku', stoku)
            save_cloud('historiku', historiku)
            
            # HTML Fatura
            fatura_html = f"""
            <div class='fatura-container'>
                <h1 style='text-align:center;'>AUTO BUNA</h1>
                <p style='text-align:center;'>Fushë Kosovë</p>
                <hr>
                <p><b>DATA:</b> {data_f} | <b>KLIENTI:</b> {klienti}</p>
                <p><b>PRODUKTI:</b> {zgjedh.split('|')[0]}</p>
                <p><b>SASIA:</b> {s_sh} | <b>TOTALI:</b> {total_f:.2f} €</p>
                <div class='signature-section'>
                    <div class='signature-line'>Shitësi</div>
                    <div class='signature-line'>Blerësi</div>
                </div>
            </div>
            """
            st.markdown(fatura_html, unsafe_allow_html=True)
