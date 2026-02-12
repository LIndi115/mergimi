import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

# --- 1. LIDHJA DIREKT ME FIREBASE ---
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

# --- 2. FUNKSIONET PËR KOMUNIKIM ME DATABAZËN ---
def load_from_cloud(path):
    """Merr të dhënat direkt nga Firebase Realtime Database"""
    ref = db.reference(path)
    data = ref.get()
    return data if data is not None else []

def save_to_cloud(path, data):
    """Ruan të dhënat direkt në Firebase Realtime Database"""
    ref = db.reference(path)
    ref.set(data)

# --- 3. NGARKIMI I TË DHËNAVE ---
stoku = load_from_cloud('stoku')
historiku = load_from_cloud('historiku')

# --- 4. INTERFACE I PROGRAMIT ---
st.set_page_config(page_title="AUTO BUNA CLOUD", layout="wide")

with st.sidebar:
    st.title("🚗 AUTO BUNA")
    menu = st.radio("MENUJA:", ["📊 Dashboard", "📦 Stoku", "📥 Pranim Malli", "💸 Shitje"])

# --- 5. LOGJIKA E PROGRAMIT ---

if menu == "📊 Dashboard":
    st.title("📊 Pasqyra Live")
    total_stoku = sum(item['sasia'] for item in stoku) if stoku else 0
    st.metric("Pjesë në Stok (Cloud)", total_stoku)

elif menu == "📦 Stoku":
    st.title("📦 Malli në Depo (Firebase)")
    if stoku:
        st.dataframe(pd.DataFrame(stoku), use_container_width=True)
    else:
        st.info("Nuk ka të dhëna në Cloud.")

elif menu == "📥 Pranim Malli":
    st.title("📥 Furnizim i Ri")
    with st.form("forma_cloud"):
        marka = st.text_input("Marka").upper()
        modeli = st.text_input("Pjesa").upper()
        sasia = st.number_input("Sasia", min_value=1)
        if st.form_submit_button("RUAJ DIREKT NË FIREBASE"):
            i_ri = {
                "marka": marka, "modeli": modeli, "sasia": sasia,
                "data": datetime.now().strftime("%d-%m-%Y %H:%M")
            }
            stoku.append(i_ri)
            save_to_cloud('stoku', stoku) # Këtu dërgohet direkt te Firebase
            st.success("Të dhënat u siguruan në Cloud!")
            st.rerun()

elif menu == "💸 Shitje":
    st.title("💸 Shitje e Re")
    if stoku:
        opsionet = [f"{i}: {item['marka']} {item['modeli']}" for i, item in enumerate(stoku)]
        zgjedhja = st.selectbox("Zgjidh mallin:", opsionet)
        idx = int(zgjedhja.split(":")[0])
        sasia_shitjes = st.number_input("Sasia", min_value=1, max_value=stoku[idx]['sasia'])
        
        if st.button("KRYEJ SHITJEN"):
            stoku[idx]['sasia'] -= sasia_shitjes
            historiku.append({
                "malli": f"{stoku[idx]['marka']} {stoku[idx]['modeli']}",
                "sasia": sasia_shitjes,
                "data": datetime.now().strftime("%d-%m-%Y %H:%M")
            })
            save_to_cloud('stoku', stoku)
            save_to_cloud('historiku', historiku)
            st.success("Stoku u përditësua në Firebase!")
            st.rerun()
