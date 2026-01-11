import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Magazyn Cloud", layout="centered")

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
    # Pamiętaj: tabela nazywa się 'produkty' (małą literą, bo tak naprawiliśmy w SQL)
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

# --- 4. APLIKACJA ---

def main():
    st.title("📦 System Magazynowy (Supabase)")

    # --- PANEL BOCZNY (DODAWANIE) ---
    with st.sidebar:
        st.header("Dodaj nowy towar")
        
        # 1. Nazwa
        nazwa_input = st.text_input("Nazwa produktu")
        
        # 2. Ilość
        liczba_input = st.number_input("Liczba (sztuk)", min_value=1, value=1)
        
        # 3. NOWOŚĆ: Cena
        # format="%.2f" sprawia, że wyświetla się np. 10.00 zamiast 10
        cena_input = st.number_input("Cena (PLN)", min_value=0.00, value=0.00, step=0.01, format="%.2f")

        if st.button("Zapisz w bazie"):
            if nazwa_input:
                # Tutaj pakujemy dane do wysyłki
                # Klucze (po lewej) muszą pasować do nazw kolumn w Supabase!
                nowy_towar = {
                    "nazwa": nazwa_input,   
                    "Liczba": liczba_input, 
                    "Cena": cena_input      # Dodaliśmy cenę do paczki
                }
                
                try:
                    # Wysyłamy do tabeli produkty
                    supabase.table('produkty').insert(nowy_towar).execute()
                    
                    # Logujemy w historii (bez ceny, bo historia rejestruje tylko ruch towaru)
                    dodaj_log(nazwa_input, "PRZYJĘCIE", liczba_input)
                    
                    st.success(f"Dodano: {nazwa_input} (Cena: {cena_input} PLN)")
                    st.rerun()
                except Exception as e:
                    st.error(f"Błąd zapisu: {e}")
            else:
                st.warning("Podaj nazwę produktu!")

    # --- WIDOK GŁÓWNY ---
    tab1, tab2 = st.tabs(["📊 Stan Magazynu", "📜 Historia Ruchów"])

    with tab1:
        st.subheader("Aktualne stany")
        try:
            df = pobierz_magazyn()

            if not df.empty:
                # Wybieramy kolumny do wyświetlenia, w tym Cenę
                # Upewniamy się, że nazwy kolumn pasują do tych z bazy
                kolumny_chciane = ["id", "nazwa", "Liczba", "Cena"]
                
                # Filtrujemy, żeby wyświetlić tylko te kolumny, które faktycznie istnieją
                dostepne = [k for k in kolumny_chciane if k in df.columns]
                
                # Wyświetlamy tabelę
                st.dataframe(df[dostepne], use_container_width=True, hide_index=True)
                
                # Opcjonalnie: Podsumowanie wartości magazynu
                if "Cena" in df.columns and "Liczba" in df.columns:
                    wartosc_calkowita = (df["Cena"] * df["Liczba"]).sum()
                    st.info(f"💰 Całkowita wartość magazynu: {wartosc_calkowita:.2f} PLN")

                st.divider()
                st.write("🔴 **Usuwanie towaru**")
                
                if 'id' in df.columns:
                    opcje = df.apply(lambda x: f"{x['id']}: {x['nazwa']}", axis=1)
                    do_usuniecia = st.selectbox("Wybierz towar do usunięcia", opcje)
                    
                    if st.button("Usuń trwale"):
                        id_usun = int(do_usuniecia.split(":")[0])
                        nazwa_usun = do_usuniecia.split(":")[1].strip()

                        supabase.table('produkty').delete().eq('id', id_usun).execute()
                        dodaj_log(nazwa_usun, "USUNIĘCIE", 0)
                        
                        st.success("Usunięto!")
                        st.rerun()
            else:
                st.info("Magazyn jest pusty. Dodaj coś w panelu bocznym.")
        except Exception as e:
             st.error(f"Błąd pobierania danych: {e}")

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
             st.write("Brak historii lub tabela nie istnieje.")

if __name__ == "__main__":
    main()
