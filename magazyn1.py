import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import time

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Magazyn", page_icon="📦", layout="wide")

# --- 2. CSS - MAKSYMALNY KONTRAST (PITCH BLACK) ---
st.markdown("""
    <style>
    /* 1. Tło głównej części aplikacji (Jasne) */
    .stApp {
        background-color: #f0f2f6;
    }

    /* 2. Tło Paska Bocznego (Sidebar) - IDEALNA CZERŃ */
    [data-testid="stSidebar"] {
        background-color: #000000 !important; /* Pitch Black */
        border-right: 1px solid #333;
    }

    /* --- KOLORY TEKSTÓW --- */
    
    /* Tekst główny na jasnym tle (Czarny) */
    .main h1, .main h2, .main h3, .main p, .main div, .main span, .main label, .main li {
        color: #31333F !important;
    }

    /* Teksty w Sidebrze (Panel boczny) - BIAŁE */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] .stMarkdown {
        color: #ffffff !important;
    }

    /* Ukrycie stopki i menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Karta dla głównej treści */
    .main .block-container {
        background-color: #ffffff;
        padding: 2rem 3rem;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-top: 1rem;
    }

    /* Stylizacja inputów (pola do wpisywania) */
    /* Inputy muszą mieć czarny tekst na białym tle, nawet w ciemnym sidebarze */
    .stTextInput input, .stNumberInput input {
        color: #000000 !important;
        background-color: #ffffff !important;
        border: 1px solid #ccc;
    }
    
    /* Naprawienie widoczności etykiet wewnątrz inputów number */
    [data-testid="stSidebar"] button {
        border-color: #444 !important;
        color: #fff !important;
    }

    /* Powiększenie liczb w metrykach */
    [data-testid="stMetricValue"] {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0066cc !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. POŁĄCZENIE Z BAZĄ ---
try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)
except Exception as e:
    st.error("⚠️ Błąd połączenia! Sprawdź plik .streamlit/secrets.toml")
    st.stop()

# --- 4. FUNKCJE ---
def pobierz_magazyn():
    response = supabase.table('produkty').select("*").execute()
    return pd.DataFrame(response.data)

def dodaj_log(produkt, akcja, ilosc):
    teraz = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dane = {"data": teraz, "produkt": produkt, "akcja": akcja, "ilosc": ilosc}
    try:
        supabase.table('historia').insert(dane).execute()
    except:
        pass 

# --- 5. GŁÓWNA APLIKACJA ---
def main():
    # --- NAGŁÓWEK ---
    col_logo, col_title = st.columns([1, 10])
    with col_logo:
        st.markdown("# 📦") 
    with col_title:
        st.title("Magazyn")
        st.markdown("**System zarządzania stanem magazynowym**")

    st.divider()

    # --- PANEL BOCZNY (SIDEBAR) ---
    with st.sidebar:
        st.header("🛠️ Panel Operacyjny")
        st.write("Wypełnij formularz, aby przyjąć towar:")
        
        with st.form("dodawanie_form", clear_on_submit=True):
            # Etykiety będą białe na czarnym tle
            nazwa_input = st.text_input("Nazwa produktu", placeholder="np. Opony Zimowe")
            
            c1, c2 = st.columns(2)
            with c1:
                liczba_input = st.number_input("Ilość szt.", min_value=1, value=10, step=1)
            with c2:
                # step=0.01 daje strzałki
                cena_input = st.number_input("Cena jedn. (PLN)", min_value=0.00, value=0.00, step=0.01)

            submitted = st.form_submit_button("💾 Zatwierdź przyjęcie", type="primary")
            
            if submitted:
                if nazwa_input:
                    nowy_towar = {"nazwa": nazwa_input, "liczba": liczba_input, "cena": cena_input}
                    try:
                        with st.spinner("Przetwarzanie..."):
                            supabase.table('produkty').insert(nowy_towar).execute()
                            dodaj_log(nazwa_input, "PRZYJĘCIE", liczba_input)
                            time.sleep(0.5)
                        st.success("✅ Dodano!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Błąd: {e}")
                else:
                    st.warning("⚠️ Podaj nazwę produktu.")

        st.markdown("---")
        st.info("Baza: Supabase (PostgreSQL)")

    # --- DASHBOARD ---
    try:
        df = pobierz_magazyn()
        
        if not df.empty:
            df.columns = [c.lower() for c in df.columns]
            
            total_items = df['id'].count()
            total_stock = df['liczba'].sum()
            total_value = (df['liczba'] * df['cena']).sum() if 'cena' in df.columns else 0

            # Metryki
            m1, m2, m3 = st.columns(3)
            m1.metric("📦 Asortyment (SKU)", f"{total_items}", delta="Pozycji")
            m2.metric("📊 Łączny stan", f"{total_stock:,}".replace(",", " "), delta="Sztuk łącznie")
            m3.metric("💰 Wartość", f"{total_value:,.2f} PLN".replace(",", " "), delta="Szacunkowa")
            
            st.write("") 

            # Zakładki
            tab1, tab2 = st.tabs(["📋 Tabela Stanów", "📜 Dziennik Operacji"])

            with tab1:
                st.subheader("Szczegółowy wykaz")
                
                st.dataframe(
                    df[['id', 'nazwa', 'liczba', 'cena']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "id": st.column_config.TextColumn("ID", width="small"),
                        "nazwa": st.column_config.TextColumn("Produkt", width="large"),
                        "liczba": st.column_config.ProgressColumn(
                            "Stan magazynowy",
                            format="%d szt.",
                            min_value=0,
                            max_value=max(df['liczba']) * 1.1 if not df.empty else 100,
                        ),
                        "cena": st.column_config.NumberColumn(
                            "Cena jedn.",
                            format="%.2f zł"
                        )
                    }
                )

                with st.expander("🗑️ Strefa usuwania"):
                    st.warning("Trwałe usuwanie towaru z ewidencji.")
                    if 'id' in df.columns:
                        c_del1, c_del2 = st.columns([3,1])
                        with c_del1:
                            opcje = df.apply(lambda x: f"ID {x['id']}: {x['nazwa']}", axis=1)
                            do_usuniecia = st.selectbox("Wybierz pozycję", opcje, label_visibility="collapsed")
                        with c_del2:
                            if st.button("Usuń trwale", type="primary"):
                                id_usun = int(do_usuniecia.split("ID ")[1].split(":")[0])
                                nazwa_usun = do_usuniecia.split(":")[1].strip()
                                supabase.table('produkty').delete().eq('id', id_usun).execute()
                                dodaj_log(nazwa_usun, "USUNIĘCIE", 0)
                                st.rerun()

            with tab2:
                st.subheader("Historia zdarzeń")
                res = supabase.table('historia').select("*").order("id", desc=True).limit(50).execute()
                df_hist = pd.DataFrame(res.data)
                
                if not df_hist.empty:
                    st.dataframe(
                        df_hist, 
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "data": st.column_config.DatetimeColumn("Czas", format="DD.MM.YYYY, HH:mm"),
                            "produkt": st.column_config.TextColumn("Produkt"),
                            "akcja": st.column_config.TextColumn("Typ ruchu"),
                            "ilosc": st.column_config.NumberColumn("Ilość")
                        }
                    )
                else:
                    st.info("Brak wpisów w historii.")

        else:
            st.info("Magazyn jest pusty. Dodaj pierwszy towar w panelu po lewej.")

    except Exception as e:
        st.error("Wystąpił problem.")
        with st.expander("Szczegóły"):
            st.write(e)

if __name__ == "__main__":
    main()
