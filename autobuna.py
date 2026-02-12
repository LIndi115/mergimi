import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

# --- 1. KONFIGURIMI I FIREBASE ---
# Ky bllok kodi lidh aplikacionin me "çelësin" që vendose te Streamlit Secrets
if not firebase_admin._apps:
    try:
        fb_dict = dict(st.secrets["firebase"])
        cred = credentials.Certificate(fb_dict)
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://herolind-6ca5f-default-rtdb.europe-west1.firebasedatabase.app/'
        })
    except Exception as e:
        st.error(f"Gabim në lidhjen me Firebase: {e}")

# --- 2. FUNKSIONET PËR CLOUD ---
def load_data(path):
    """Merr të dhënat nga Firebase"""
    try:
        ref = db.reference(path)
        data = ref.get()
        return data if data is not None else []
    except:
        return []

def save_data(path, data):
    """Ruan të dhënat në Firebase"""
    try:
        ref = db.reference(path)
        ref.set(data)
    except Exception as e:
        st.error(f"Gabim gjatë ruajtjes: {e}")

# --- 3. NGARKIMI I TË DHËNAVA LIVE ---
stoku = load_data('stoku')
historiku = load_data('historiku')

# --- 4. DIZAJNI DHE MENUJA ---
st.set_page_config(page_title="AUTO BUNA PRO", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button { width: 100%; background-color: #2563eb; color: white; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.title("🚗 AUTO BUNA")
    menu = st.radio("NAVIGIMI:", ["📊 Dashboard", "📦 Gjendja e Stokut", "📥 Pranim Malli", "💸 Shitje e Re"])

# --- 5. LOGJIKA E PROGRAMIT ---

if menu == "📊 Dashboard":
    st.title("📊 Pasqyra e Biznesit")
    # Llogaritja e shpejtë e vlerave
    total_stoku = sum(item['sasia'] for item in stoku) if stoku else 0
    total_shitje = len(historiku) if historiku else 0
    
    col1, col2 = st.columns(2)
    col1.metric("Pjesë në Stok", total_stoku)
    col2.metric("Shitje të Kryera", total_shitje)

elif menu == "📦 Gjendja e Stokut":
    st.title("📦 Malli në Depo")
    if stoku:
        df = pd.DataFrame(stoku)
        st.dataframe(df, use_container_width=True)
        
        # Butoni për fshirje (opsionale)
        fshij_idx = st.number_input("Rreshti për fshirje", min_value=0, max_value=len(stoku)-1, step=1)
        if st.button("🗑️ Fshij Pjesën"):
            stoku.pop(fshij_idx)
            save_data('stoku', stoku)
            st.success("U fshi nga Cloud!")
            st.rerun()
    else:
        st.info("Nuk ka mall në stok.")

elif menu == "📥 Pranim Malli":
    st.title("📥 Regjistro Mall të Ri")
    with st.form("forma_pranim"):
        col1, col2 = st.columns(2)
        marka = col1.text_input("Marka").upper()
        modeli = col2.text_input("Modeli/Pjesa").upper()
        sasia = col1.number_input("Sasia", min_value=1, step=1)
        blerja = col2.number_input("Preçi i Blerjes (€)", min_value=0.0)
        
        if st.form_submit_button("RUAJ NË FIREBASE"):
            i_ri = {
                "marka": marka, "modeli": modeli, 
                "sasia": sasia, "blerja": blerja,
                "data": datetime.now().strftime("%d-%m-%Y %H:%M")
            }
            stoku.append(i_ri)
            save_data('stoku', stoku) # Ruhet direkt në Cloud
            st.success("U regjistrua me sukses!")
            st.rerun()

elif menu == "💸 Shitje e Re":
    st.title("💸 Realizo Shitje")
    if stoku:
        opsionet = [f"{i}: {item['marka']} {item['modeli']} (Gjendja: {item['sasia']})" for i, item in enumerate(stoku)]
        zgjedhja = st.selectbox("Zgjidh mallin:", opsionet)
        idx = int(zgjedhja.split(":")[0])
        
        sasia_shitjes = st.number_input("Sasia për shitje", min_value=1, max_value=stoku[idx]['sasia'])
        preci_shitjes = st.number_input("Preçi i shitjes (€)", min_value=0.0)
        
        if st.button("KRYEJ SHITJEN"):
            # 1. Zbrit sasinë nga stoku
            stoku[idx]['sasia'] -= sasia_shitjes
            # 2. Shto te historiku
            shitja_re = {
                "malli": f"{stoku[idx]['marka']} {stoku[idx]['modeli']}",
                "sasia": sasia_shitjes,
                "preci": preci_shitjes,
                "data": datetime.now().strftime("%d-%m-%Y %H:%M")
            }
            historiku.append(shitja_re)
            
            # 3. Ruaj të dyja në Firebase
            save_data('stoku', stoku)
            save_data('historiku', historiku)
            st.success("Shitja u krye dhe stoku u përditësua!")
            st.rerun()
    else:
        st.warning("Nuk mund të shesësh, stoku është i zbrazët!")
