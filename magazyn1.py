import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Magazyn Cloud", layout="centered")

# --- 2. POŁĄCZENIE Z BAZĄ ---
try:
    # Pobieramy hasła z secrets
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)
except Exception as e:
    st.error("⚠️ Błąd połączenia! Upewnij się, że masz wpisane secrets (w pliku lokalnie lub w chmurze).")
    st.stop()

# --- 3. FUNKCJE ---

def pobierz_magazyn():
    """Pobiera dane z Twojej tabeli Produkty"""
    # WAŻNE: Nazwa tabeli "Produkty" (z dużej litery, jak na zdjęciu)
    response = supabase.table('Produkty').select("*").execute()
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
    # Jeśli zapomniałeś stworzyć tabeli historia w SQL, ta funkcja nie zadziała
    try:
        supabase.table('historia').insert(dane).execute()
    except:
        pass # Ignorujemy błąd braku historii, żeby apka nie padła

# --- 4. APLIKACJA ---

def main():
    st.title("📦 System Magazynowy (Supabase)")

    # --- PANEL BOCZNY (DODAWANIE) ---
    with st.sidebar:
        st.header("Dodaj nowy towar")
        
        # Formularz dopasowany do Twoich kolumn
        nazwa_input = st.text_input("Nazwa produktu")
        liczba_input = st.number_input("Liczba (sztuk)", min_value=1, value=1)
        cena_input = st.number_input("Cena (PLN)", min_value=0.0, value=0.0, step=0.1)
        
        # (Opcjonalnie można by tu wybierać kategorię, ale na razie upraszczamy)

        if st.button("Zapisz w bazie"):
            if nazwa_input:
                # Mapowanie: Twoja zmienna -> Kolumna w Supabase
                nowy_towar = {
                    "nazwa": nazwa_input,   # Kolumna: nazwa
                    "Liczba": liczba_input, # Kolumna: Liczba (z dużej!)
                    "Cena": cena_input      # Kolumna: Cena (z dużej!)
                }
                
                # Wysyłamy do tabeli Produkty
                supabase.table('Produkty').insert(nowy_towar).execute()
                
                # Logujemy w historii
                dodaj_log(nazwa_input, "PRZYJĘCIE", liczba_input)
                
                st.success(f"Dodano: {nazwa_input}")
                st.rerun()
            else:
                st.warning("Podaj nazwę produktu!")

    # --- WIDOK GŁÓWNY ---
    tab1, tab2 = st.tabs(["📊 Stan Magazynu", "📜 Historia Ruchów"])

    with tab1:
        st.subheader("Aktualne stany (Tabela: Produkty)")
        df = pobierz_magazyn()

        if not df.empty:
            # Wyświetlamy tabelę
            # Ukrywamy kolumnę Kategoria_id, bo jest mało czytelna dla człowieka
            kolumny_do_wyswietlenia = ["id", "nazwa", "Liczba", "Cena"]
            # Sprawdzamy czy te kolumny są w danych (dla bezpieczeństwa)
            dostepne_kolumny = [k for k in kolumny_do_wyswietlenia if k in df.columns]
            
            st.dataframe(df[dostepne_kolumny], use_container_width=True, hide_index=True)

            st.divider()
            st.write("🔴 **Usuwanie towaru**")
            
            # Usuwanie po ID
            if 'id' in df.columns:
                opcje = df.apply(lambda x: f"{x['id']}: {x['nazwa']}", axis=1)
                do_usuniecia = st.selectbox("Wybierz towar do usunięcia", opcje)
                
                if st.button("Usuń trwale"):
                    id_usun = int(do_usuniecia.split(":")[0])
                    nazwa_usun = do_usuniecia.split(":")[1].strip()

                    # Usuwamy z tabeli Produkty
                    supabase.table('Produkty').delete().eq('id', id_usun).execute()
                    
                    # Logujemy
                    dodaj_log(nazwa_usun, "USUNIĘCIE", 0)
                    
                    st.success("Usunięto!")
                    st.rerun()
        else:
            st.info("Baza jest pusta. Dodaj coś w panelu bocznym.")

    with tab2:
        st.subheader("Logi operacji")
        try:
            res = supabase.table('historia').select("*").order("id", desc=True).execute()
            df_hist = pd.DataFrame(res.data)
            if not df_hist.empty:
                st.dataframe(df_hist, use_container_width=True)
            else:
                st.write("Brak historii.")
        except:
            st.warning("Tabela 'historia' nie istnieje. Uruchom skrypt SQL z instrukcji.")

if __name__ == "__main__":
    main()
