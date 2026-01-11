import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import time

# --- 1. KONFIGURACJA STRONY I CSS ---
st.set_page_config(page_title="Cloud Logistics Pro", page_icon="📦", layout="wide")

# Uproszczony CSS - kolory załatwia teraz plik config.toml
# Tutaj dodajemy tylko styl "karty" dla głównej zawartości
st.markdown("""
    <style>
    /* Ukrycie menu i stopki */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Stylizacja metryk (dużych liczb) - powiększenie */
    [data-testid="stMetricValue"] {
        font-size: 2.2rem;
        font-weight: 700;
    }
    
    /* Dodanie efektu "karty" do głównego kontenera, żeby odciąć go od tła */
    .main .block-container {
        background-color: #ffffff;
        padding: 2rem 3rem;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-top: 1rem;
    }
    
    /* Delikatne tło dla sidebara */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #eaeaea;
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
    response = supabase.table('produkty').select("*").execute()
    return pd.DataFrame(response.data)

def dodaj_log(produkt, akcja, ilosc):
    teraz = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dane = {"data": teraz, "produkt": produkt, "akcja": akcja, "ilosc": ilosc}
    try:
        supabase.table('historia').insert(dane).execute()
    except:
        pass 

# --- 4. GŁÓWNA APLIKACJA ---
def main():
    # --- NAGŁÓWEK ---
    # Używamy kolumn, żeby ładnie ułożyć logo i tytuł
    col_logo, col_title = st.columns([1, 10])
    with col_logo:
        # Przykładowa ikona logistyczna
        st.markdown("## 📦") 
    with col_title:
        st.title("Cloud Logistics Hub")
        st.caption("Profesjonalny system zarządzania stanem magazynowym")

    st.divider()

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("🛠️ Panel Operacyjny")
        st.markdown("---")
        st.write("**Przyjęcie towaru**")
        
        with st.form("dodawanie_form", clear_on_submit=True):
            nazwa_input = st.text_input("Nazwa produktu", placeholder="np. Paleta EURO")
            
            c1, c2 = st.columns(2)
            with c1:
                liczba_input = st.number_input("Ilość szt.", min_value=1, value=10, step=1)
            with c2:
                cena_input = st.number_input("Cena jedn. (PLN)", min_value=0.01, value=0.00, step=0.01)

            submitted = st.form_submit_button("💾 Zatwierdź przyjęcie", type="primary")
            
            if submitted:
                if nazwa_input:
                    nowy_towar = {"nazwa": nazwa_input, "liczba": liczba_input, "cena": cena_input}
                    try:
                        with st.spinner("Synchronizacja z chmurą..."):
                            supabase.table('produkty').insert(nowy_towar).execute()
                            dodaj_log(nazwa_input, "PRZYJĘCIE", liczba_input)
                            time.sleep(0.5)
                        st.success("✅ Dodano do bazy!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Błąd: {e}")
                else:
                    st.warning("⚠️ Nazwa jest wymagana.")

        st.markdown("---")
        st.info("ℹ️ Użyj formularza, aby zaktualizować stany w czasie rzeczywistym.")

    # --- DASHBOARD ---
    try:
        df = pobierz_magazyn()
        
        if not df.empty:
            df.columns = [c.lower() for c in df.columns]
            
            # Obliczenia KPI
            total_items = df['id'].count()
            total_stock = df['liczba'].sum()
            total_value = (df['liczba'] * df['cena']).sum() if 'cena' in df.columns else 0

            # Kafelki KPI
            m1, m2, m3 = st.columns(3)
            m1.metric("📦 Asortyment (SKU)", f"{total_items}", delta="Pozycji w bazie")
            m2.metric("📊 Łączny stan", f"{total_stock:,}".replace(",", " "), delta="Sztuk łącznie")
            m3.metric("💰 Wartość magazynu", f"{total_value:,.2f} PLN".replace(",", " "), delta="Szacunkowa wycena")
            
            st.markdown("###") # Odstęp

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
                            # Dynamiczny max paska postępu
                            max_value=max(df['liczba']) * 1.1 if not df.empty else 100,
                        ),
                        "cena": st.column_config.NumberColumn(
                            "Cena jedn.",
                            format="%.2f zł"
                        )
                    }
                )

                with st.expander("🗑️ Strefa usuwania (Wydanie zewnętrzne)"):
                    st.warning("Operacja trwałego usunięcia z ewidencji.")
                    if 'id' in df.columns:
                        c_del1, c_del2 = st.columns([3,1])
                        with c_del1:
                            opcje = df.apply(lambda x: f"ID {x['id']}: {x['nazwa']}", axis=1)
                            do_usuniecia = st.selectbox("Wybierz pozycję", opcje, label_visibility="collapsed")
                        with c_del2:
                            if st.button("Potwierdź usunięcie", type="primary"):
                                id_usun = int(do_usuniecia.split("ID ")[1].split(":")[0])
                                nazwa_usun = do_usuniecia.split(":")[1].strip()
                                supabase.table('produkty').delete().eq('id', id_usun).execute()
                                dodaj_log(nazwa_usun, "USUNIĘCIE", 0)
                                st.rerun()

            with tab2:
                st.subheader("Historia zdarzeń")
                res = supabase.table('historia').select("*").order("id", desc=True).limit(100).execute()
                df_hist = pd.DataFrame(res.data)
                
                if not df_hist.empty:
                    st.dataframe(
                        df_hist, 
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "data": st.column_config.DatetimeColumn("Czas operacji", format="DD.MM.YYYY, HH:mm:ss"),
                            "produkt": st.column_config.TextColumn("Produkt"),
                            "akcja": st.column_config.TextColumn("Typ ruchu"),
                            "ilosc": st.column_config.NumberColumn("Ilość")
                        }
                    )
                else:
                    st.info("Brak zarejestrowanych operacji.")

        else:
            st.info("Magazyn jest pusty. Rozpocznij wprowadzanie towaru w panelu bocznym.")

    except Exception as e:
        # Ładniejsze wyświetlanie błędów
        st.error("Wystąpił problem z pobraniem danych.")
        with st.expander("Pokaż szczegóły błędu"):
            st.write(e)

if __name__ == "__main__":
    main()
