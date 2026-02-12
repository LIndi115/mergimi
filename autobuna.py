import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import base64

# --- SHTESA: SISTEMI I LOG-IN (VETËM KJO PJESË U SHTUA) ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("🔐 AUTO BUNA - HYRJA")
        user = st.text_input("Përdoruesi (Username):")
        password = st.text_input("Fjalëkalimi (Password):", type="password")
        
        if st.button("Hyr në Sistem"):
            if user == "admin" and password == "buna2026":
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Përdoruesi ose fjalëkalimi është i gabuar!")
        return False
    return True

# Nëse Log-In është i saktë, ekzekutohet i gjithë kodi yt poshtë:
if check_password():
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

    # --- 2. KONFIGURIMI YT ORIGJINAL ---
    st.set_page_config(page_title="AUTO BUNA PRO 2026", layout="wide", page_icon="🚗")

    MUAJT_SHQIP = {
        "01": "Janar", "02": "Shkurt", "03": "Mars", "04": "Prill",
        "05": "Maj", "06": "Qershor", "07": "Korrik", "08": "Gusht",
        "09": "Shtator", "10": "Tetor", "11": "Nëntor", "12": "Dhjetor"
    }

    # Stili yt origjinal
    st.markdown("""
        <style>
        .fatura-container { 
            padding: 40px; 
            border: 1px solid #000; 
            background-color: #fff; 
            color: #000; 
            font-family: 'Courier New', Courier, monospace;
            line-height: 1.5;
        }
        .signature-section {
            margin-top: 50px;
            display: flex;
            justify-content: space-between;
        }
        .signature-line {
            border-top: 1px solid #000;
            width: 200px;
            text-align: center;
            padding-top: 5px;
        }
        .stButton>button { background-color: #e60073; color: white; border-radius: 8px; font-weight: bold; }
        .delete-btn { color: #ff4b4b; cursor: pointer; border: 1px solid #ff4b4b; padding: 2px 5px; border-radius: 4px; }
        </style>
        """, unsafe_allow_html=True)

    def create_pdf_download_link(html_content, filename="fatura.html"):
        b64 = base64.b64encode(html_content.encode()).decode()
        return f'<a href="data:text/html;base64,{b64}" download="{filename}" style="text-decoration:none;"><button style="background-color:#28a745; color:white; padding:10px; border:none; border-radius:5px; width:100%; cursor:pointer;">💾 SHKARKO FATURËN (HTML/PDF)</button></a>'

    # Ngarkimi nga Cloud
    stoku = load_cloud('stoku')
    historiku = load_cloud('historiku')
    investimet = load_cloud('investimet')

    # --- 3. NAVIGIMI ---
    with st.sidebar:
        st.title("🚗 AUTO BUNA")
        # Opsioni për Log Out
        if st.button("🔐 Log Out (Dil)"):
            st.session_state["authenticated"] = False
            st.rerun()
            
        menu = st.radio("MENUJA:", ["📊 Dashboard", "📦 Gjendja e Stokut", "📥 Pranim Malli", "💸 Shitje & Faturë"])
        st.write("---")
        st.write("📍 **DRENAS**")

    # --- 4. DASHBOARD ---
    if menu == "📊 Dashboard":
        st.title("📈 Raporti Mujor i Biznesit")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            vitet = [str(year) for year in range(2024, 2051)]
            viti_zgjedhur = st.selectbox("Zgjidh Vitin:", vitet, index=vitet.index("2026"))
        with col_f2:
            muaji_emri = st.selectbox("Zgjidh Muajin:", list(MUAJT_SHQIP.values()), index=datetime.now().month-1)
        
        muaji_kod = [k for k, v in MUAJT_SHQIP.items() if v == muaji_emri][0]
        kerko_daten = f"{muaji_kod}-{viti_zgjedhur}"

        hyrje_totale = sum(float(i.get('shuma_blerjes', 0)) for i in investimet if kerko_daten in str(i.get('data', '')))
        dalje_totale = sum(float(h.get('total', 0)) for h in historiku if kerko_daten in str(h.get('data_shitjes', '')))
        
        # SHTESA: BILANCI
        bilanci = dalje_totale - hyrje_totale

        st.write("##")
        c1, c2, c3 = st.columns(3)
        c1.metric("Totali i Investuar", f"{hyrje_totale:,.2f} €")
        c2.metric("Totali i Shitur", f"{dalje_totale:,.2f} €")
        c3.metric("BILANCI (FITIMI)", f"{bilanci:,.2f} €", delta=f"{bilanci:,.2f} €")

    # --- 5. GJENDJA E STOKUT ---
    elif menu == "📦 Gjendja e Stokut":
        st.title("📦 Malli aktual në Depo")
        search_query = st.text_input("🔍 Kërko mallin...", "").strip().upper()
        
        if stoku:
            df = pd.DataFrame(stoku)
            if search_query:
                mask = df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)
                df = df[mask]

            for index, row in df.iterrows():
                m = row.get('marka', 'N/A')
                mod = row.get('modeli', 'N/A')
                ana = row.get('ana', 'N/A')
                sas = row.get('sasia', 0)
                
                with st.expander(f"📌 {m} {mod} - {ana} ({sas} copë)"):
                    col_info, col_del = st.columns([4, 1])
                    col_info.write(f"**Data:** {row.get('data')} | **Viti:** {row.get('viti')} | **Blerja:** {row.get('blerja')}€ | **Përshkrimi:** {row.get('pershkrimi')}")
                    if col_del.button("🗑️ FSHIJ", key=f"del_{index}"):
                        stoku.pop(index)
                        save_cloud('stoku', stoku)
                        st.rerun()
        else:
            st.info("Depoja është e zbrazët.")

    # --- 6. PRANIM MALLI ---
    elif menu == "📥 Pranim Malli":
        st.title("📥 Regjistrim i Mallit të Ri")
        with st.form("forma_pranim", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1: d_r = st.date_input("Data e Pranimit:", datetime.now())
            with c2: marka = st.text_input("Marka:")
            with c3: modeli = st.text_input("Modeli:")
            c4, c5, c6 = st.columns(3)
            with c4: viti = st.text_input("Viti i Prodhimit:")
            with c5: ana = st.selectbox("Ana:", ["MAJTAS (L)", "DJATHTAS (R)", "SET (L+R)"])
            with c6: pershkrimi = st.text_input("Përshkrimi:")
            c7, c8 = st.columns(2)
            with c7: sasia = st.number_input("Sasia:", min_value=1)
            with c8: blerja = st.number_input("Çmimi Blerjes (€):", min_value=0.0)
            
            if st.form_submit_button("KONFIRMO DHE RUAJ"):
                data_str = d_r.strftime("%d-%m-%Y")
                stoku.append({"data": data_str, "marka": marka.upper(), "modeli": modeli.upper(), "viti": viti, "ana": ana, "pershkrimi": pershkrimi, "sasia": sasia, "blerja": blerja})
                investimet.append({"data": data_str, "shuma_blerjes": sasia * blerja})
                save_cloud('stoku', stoku)
                save_cloud('investimet', investimet)
                st.success("U regjistrua në Cloud!")

    # --- 7. SHITJE & FATURË ---
    elif menu == "💸 Shitje & Faturë":
        st.title("💸 Shitje dhe Faturim")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            klienti = st.text_input("Emri i Klientit:")
            data_sh = st.date_input("Data e Shitjes:", datetime.now())
        with col_s2:
            tipi = st.radio("Zgjidh:", ["Nga Stoku", "Shkrim i Lirë"])

        if tipi == "Nga Stoku" and stoku:
            opsionet = [f"{i.get('marka')} {i.get('modeli')} - {i.get('ana')} | {i.get('sasia')} në stok" for i in stoku]
            zgjedh = st.selectbox("Zgjidh produktin:", opsionet)
            idx_s = opsionet.index(zgjedh)
            p_fatura = zgjedh.split(" | ")[0]
            s_max = int(stoku[idx_s].get('sasia', 100))
        else:
            p_fatura = st.text_input("Shkruaj mallin:")
            s_max = 1000
            idx_s = None

        c_p1, c_p2 = st.columns(2)
        with c_p1: s_sh = st.number_input("Sasia:", min_value=1, max_value=s_max)
        with c_p2: c_sh = st.number_input("Çmimi (€):", min_value=0.0)

        if st.button("KRYEJ SHITJEN"):
            total_f = s_sh * c_sh
            if tipi == "Nga Stoku" and idx_s is not None:
                stoku[idx_s]['sasia'] -= s_sh
                if stoku[idx_s]['sasia'] <= 0: stoku.pop(idx_s)
                save_cloud('stoku', stoku)
            
            data_f = data_sh.strftime("%d-%m-%Y")
            historiku.append({"data_shitjes": data_f, "klienti": klienti, "produkti": p_fatura, "sasia": s_sh, "total": total_f})
            save_cloud('historiku', historiku)
            
            fatura_html = f"""
            <div class='fatura-container'>
                <h1 style='text-align:center;'>AUTO BUNA</h1>
                <p style='text-align:center;'>📍 DRENAS | 📞 049 160 886 | 📞 044 532 990</p>
                <hr>
                <p><b>DATA:</b> {data_f}</p>
                <p><b>KLIENTI:</b> {klienti}</p>
                <p><b>PRODUKTI:</b> {p_fatura}</p>
                <p><b>SASIA:</b> {s_sh} copë</p>
                <p><b>ÇMIMI PËR NJËSI:</b> {c_sh:.2f} €</p>
                <hr>
                <h2 style='text-align:right;'>TOTALI: {total_f:.2f} €</h2>
                <div class='signature-section'>
                    <div class='signature-line'>Nënshkrimi i Shitësit</div>
                    <div class='signature-line'>Nënshkrimi i Blerësit</div>
                </div>
            </div>
            """
            st.markdown(fatura_html, unsafe_allow_html=True)
            st.markdown(create_pdf_download_link(fatura_html, f"Fatura_{klienti}.html"), unsafe_allow_html=True)
