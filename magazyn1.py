import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import time

# --- 1. KONFIGURACJA I STYLE CSS ---
st.set_page_config(page_title="Cloud Logistics Pro", page_icon="📦", layout="wide")

# Wstrzykujemy trochę CSS, żeby było ładniej (ukrywamy menu i stopkę, stylujemy kafelki)
st.markdown("""
    <style>
    /* Ukrycie domyślnego menu hamburgera i stopki Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Stylizacja metryk (dużych liczb) */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #0066cc;
    }
    
    /* Delikatne tło dla całej aplikacji */
    .stApp {
        background-color: #f9f9f9;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. POŁĄCZENIE Z BAZĄ ---
try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)
except Exception as e:
    st.error("⚠️ Błąd połączenia! Sprawdź plik .streamlit/secrets.toml")
    st.stop()

# --- 3. FUNKCJE ---

def pobierz_magazyn():
    """Pobiera dane z tabeli produkty"""
    response = supabase.table('produkty').select("*").execute()
    return pd.DataFrame(response.data)

def dodaj_log(produkt, akcja, ilosc):
    """Dodaje wpis do tabeli historia"""
    teraz = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dane = {
        "data": teraz,
        "produkt": produkt,
        "akcja": akcja,
        "ilosc": ilosc
    }
    try:
        supabase.table('historia').insert(dane).execute()
    except:
        pass 

# --- 4. GŁÓWNA APLIKACJA ---

def main():
    # --- NAGŁÓWEK ---
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/2821/2821852.png", width=80)
    with col2:
        st.title("Cloud Logistics Hub")
        st.caption("System zarządzania magazynem oparty na Supabase & AI")

    st.divider()

    # --- PANEL BOCZNY (SIDEBAR) ---
    with st.sidebar:
        st.header("🛠️ Panel Operacyjny")
        st.write("Dodaj nowy asortyment do bazy")
        
        with st.form("dodawanie_form", clear_on_submit=True):
            nazwa_input = st.text_input("📦 Nazwa produktu")
            
            c1, c2 = st.columns(2)
            with c1:
                liczba_input = st.number_input("Ilość", min_value=1, value=10, step=1)
            with c2:
                cena_input = st.number_input("Cena (PLN)", min_value=0.01, value=10.00, step=0.01)

            submitted = st.form_submit_button("💾 Zatwierdź przyjęcie")
            
            if submitted:
                if nazwa_input:
                    nowy_towar = {
                        "nazwa": nazwa_input,   
                        "liczba": liczba_input, 
                        "cena": cena_input
                    }
                    try:
                        with st.spinner("Wysyłanie do chmury..."):
                            supabase.table('produkty').insert(nowy_towar).execute()
                            dodaj_log(nazwa_input, "PRZYJĘCIE", liczba_input)
                            time.sleep(0.5) # Krótka pauza dla efektu
                        st.success("✅ Pomyślnie dodano towar!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Błąd: {e}")
                else:
                    st.warning("⚠️ Nazwa produktu jest wymagana!")

        st.info("💡 Wskazówka: Użyj formularza powyżej, aby zaktualizować stan magazynowy.")

    # --- DASHBOARD (METRYKI) ---
    # To jest sekcja, która robi wrażenie "Managera"
    
    try:
        df = pobierz_magazyn()
        
        if not df.empty:
            # Normalizacja kolumn (małe litery)
            df.columns = [c.lower() for c in df.columns]
            
            # Obliczenia
            total_items = df['id'].count()
            total_stock = df['liczba'].sum()
            total_value = (df['liczba'] * df['cena']).sum() if 'cena' in df.columns else 0

            # Wyświetlanie kafelków (KPI)
            m1, m2, m3 = st.columns(3)
            m1.metric("📦 Liczba produktów (SKU)", f"{total_items}", delta="Stan bieżący")
            m2.metric("📊 Łączna ilość sztuk", f"{total_stock}", delta="Sztuki")
            m3.metric("💰 Wartość Magazynu", f"{total_value:,.2f} PLN", delta="Szacunkowa")
            
            st.divider()

            # --- ZAKŁADKI ---
            tab1, tab2 = st.tabs(["📋 Tabela Magazynowa", "📜 Dziennik Zdarzeń (Logi)"])

            with tab1:
                st.subheader("Szczegółowy stan magazynowy")
                
                # Konfiguracja wyglądu tabeli (formatowanie waluty i paska postępu)
                st.dataframe(
                    df[['id', 'nazwa', 'liczba', 'cena']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "id": st.column_config.TextColumn("ID", width="small"),
                        "nazwa": st.column_config.TextColumn("Nazwa Produktu", width="medium"),
                        "liczba": st.column_config.ProgressColumn(
                            "Stan (szt.)",
                            help="Pasek wizualizujący ilość towaru",
                            format="%d",
                            min_value=0,
                            max_value=max(df['liczba']) * 1.2 if not df.empty else 100,
                        ),
                        "cena": st.column_config.NumberColumn(
                            "Cena jedn.",
                            help="Cena w Polskich Złotych",
                            format="%.2f zł"
                        )
                    }
                )

                # Sekcja usuwania (Expander, żeby nie zajmował miejsca)
                with st.expander("🗑️ Zarządzanie usunięciami"):
                    st.warning("Ta strefa służy do trwałego usuwania pozycji.")
                    if 'id' in df.columns:
                        col_del1, col_del2 = st.columns([3, 1])
                        with col_del1:
                            opcje = df.apply(lambda x: f"{x['id']}: {x['nazwa']}", axis=1)
                            do_usuniecia = st.selectbox("Wybierz towar", opcje, label_visibility="collapsed")
                        with col_del2:
                            if st.button("Usuń trwale", type="primary"):
                                id_usun = int(do_usuniecia.split(":")[0])
                                nazwa_usun = do_usuniecia.split(":")[1].strip()
                                supabase.table('produkty').delete().eq('id', id_usun).execute()
                                dodaj_log(nazwa_usun, "USUNIĘCIE", 0)
                                st.rerun()

            with tab2:
                st.subheader("Historia operacji")
                res = supabase.table('historia').select("*").order("id", desc=True).limit(50).execute()
                df_hist = pd.DataFrame(res.data)
                
                if not df_hist.empty:
                    st.dataframe(
                        df_hist, 
                        use_container_width=True,
                        column_config={
                            "data": st.column_config.DatetimeColumn("Data operacji", format="D MMM YYYY, HH:mm"),
                            "akcja": st.column_config.TextColumn("Rodzaj operacji"),
                            "ilosc": st.column_config.NumberColumn("Ruch (szt.)")
                        }
                    )
                else:
                    st.info("Brak wpisów w historii.")

        else:
            st.info("Magazyn jest pusty. Użyj panelu po lewej, aby dodać pierwszy towar.")

    except Exception as e:
        st.error(f"Wystąpił błąd aplikacji: {e}")

if __name__ == "__main__":
    main()
