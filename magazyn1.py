import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import time

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Cloud Logistics Pro", page_icon="📦", layout="wide")

# --- 2. CSS - WYMUSZENIE JASNEGO MOTYWU I KOLORÓW ---
# To jest ta część, która zastępuje plik config.toml. 
# Wymuszamy ciemny tekst na jasnym tle.
st.markdown("""
    <style>
    /* 1. Tło całej aplikacji - jasnoszare */
    .stApp {
        background-color: #f0f2f6;
    }

    /* 2. Wymuszenie czarnego koloru czcionki dla wszystkich tekstów */
    h1, h2, h3, h4, h5, h6, p, div, span, label {
        color: #31333F !important;
    }
    
    /* 3. Wyjątek: Tekst wewnątrz przycisków i inputów */
    button p {
        color: inherit !important;
    }
    
    /* 4. Stylizacja głównego kontenera (Karta) */
    .main .block-container {
        background-color: #ffffff;
        padding: 2rem 3rem;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-top: 1rem;
    }

    /* 5. Ukrycie stopki i menu Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 6. Powiększenie liczb w metrykach */
    [data-testid="stMetricValue"] {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0066cc !important; /* Niebieski kolor dla liczb */
    }
    
    /* 7. Poprawa widoczności inputów (pól do wpisywania) */
    .stTextInput input, .stNumberInput input {
        color: #31333F !important;
        background-color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. POŁĄCZENIE Z BAZĄ ---
try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)
except Exception as e:
    st.error("⚠️ Błąd połączenia! Sprawdź czy masz wpisane hasła w .streamlit/secrets.toml")
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
        st.title("Cloud Logistics Hub")
        st.markdown("**Profesjonalny system zarządzania stanem magazynowym**")

    st.divider()

    # --- SIDEBAR (PANEL BOCZNY) ---
    with st.sidebar:
        st.header("🛠️ Panel Operacyjny")
        st.write("Wypełnij formularz, aby przyjąć towar:")
        
        with st.form("dodawanie_form", clear_on_submit=True):
            nazwa_input = st.text_input("Nazwa produktu", placeholder="np. Opony Zimowe")
            
            c1, c2 = st.columns(2)
            with c1:
                liczba_input = st.number_input("Ilość szt.", min_value=1, value=10, step=1)
            with c2:
                cena_input = st.number_input("Cena jedn. (PLN)", min_value=0.01, value=0.00, step=0.01)

            # Przycisk typu 'primary' (wyróżniony)
            submitted = st.form_submit_button("💾 Zatwierdź przyjęcie", type="primary")
            
            if submitted:
                if nazwa_input:
                    nowy_towar = {"nazwa": nazwa_input, "liczba": liczba_input, "cena": cena_input}
                    try:
                        with st.spinner("Przetwarzanie danych w chmurze..."):
                            supabase.table('produkty').insert(nowy_towar).execute()
                            dodaj_log(nazwa_input, "PRZYJĘCIE", liczba_input)
                            time.sleep(0.5)
                        st.success("✅ Sukces! Towar dodany.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Błąd: {e}")
                else:
                    st.warning("⚠️ Musisz podać nazwę produktu.")

        st.markdown("---")
        st.info("System połączony z bazą Supabase (PostgreSQL).")

    # --- DASHBOARD (GŁÓWNY EKRAN) ---
    try:
        df = pobierz_magazyn()
        
        if not df.empty:
            # Zamiana nazw kolumn na małe litery (dla pewności)
            df.columns = [c.lower() for c in df.columns]
            
            # KPI (Kluczowe Wskaźniki)
            total_items = df['id'].count()
            total_stock = df['liczba'].sum()
            total_value = (df['liczba'] * df['cena']).sum() if 'cena' in df.columns else 0

            # Wyświetlanie metryk
            m1, m2, m3 = st.columns(3)
            m1.metric("📦 Asortyment (SKU)", f"{total_items}", delta="Pozycji")
            m2.metric("📊 Łączny stan", f"{total_stock:,}".replace(",", " "), delta="Sztuk łącznie")
            m3.metric("💰 Wartość magazynu", f"{total_value:,.2f} PLN".replace(",", " "), delta="Szacunkowa")
            
            st.write("") # Pusty odstęp

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

                # Sekcja usuwania
                with st.expander("🗑️ Strefa usuwania (Wydanie zewnętrzne)"):
                    st.warning("Tutaj możesz trwale usunąć towar z ewidencji.")
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
                # Pobieramy historię
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
        st.error("Wystąpił problem z połączeniem.")
        with st.expander("Szczegóły błędu"):
            st.write(e)

if __name__ == "__main__":
    main()
