import streamlit as st 
import pandas as pd

# Ustawienie konfiguracji strony
st.set_page_config(page_title="Prosty Magazyn", layout="centered")

def main():
    st.title("📦 Prosty Magazyn (Streamlit)")

    # 1. Inicjalizacja stanu (Session State)
    # To pozwala pamiętać listę towarów między kliknięciami, mimo braku bazy danych
    if 'magazyn' not in st.session_state:
        st.session_state.magazyn = []

    # --- SEKCJA DODAWANIA TOWARU (SIDEBAR) ---
    with st.sidebar:
        st.header("Dodaj towar")
        nazwa_towaru = st.text_input("Nazwa produktu")
        ilosc_towaru = st.number_input("Ilość", min_value=1, value=1, step=1)
        jednostka = st.selectbox("Jednostka", ["szt.", "kg", "litr", "opak."])

        if st.button("Dodaj do magazynu"):
            if nazwa_towaru:
                nowy_towar = {
                    "Nazwa": nazwa_towaru,
                    "Ilość": ilosc_towaru,
                    "Jednostka": jednostka
                }
                st.session_state.magazyn.append(nowy_towar)
                st.success(f"Dodano: {nazwa_towaru}")
            else:
                st.warning("Podaj nazwę produktu!")

    # --- SEKCJA WYŚWIETLANIA I USUWANIA ---
    st.subheader("Aktualny stan magazynowy")

    if len(st.session_state.magazyn) > 0:
        # Wyświetlamy każdy towar w osobnym wierszu z przyciskiem usuwania
        for index, towar in enumerate(st.session_state.magazyn):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.write(f"**{towar['Nazwa']}**")
            with col2:
                st.write(f"{towar['Ilość']}")
            with col3:
                st.write(f"{towar['Jednostka']}")
            with col4:
                # Unikalny klucz dla każdego przycisku jest wymagany
                if st.button("Usuń", key=f"del_{index}"):
                    usun_towar(index)
        
        st.divider()
        st.info(f"Łącznie pozycji w magazynie: {len(st.session_state.magazyn)}")
    else:
        st.info("Magazyn jest pusty. Dodaj towary używając panelu po lewej stronie.")

def usun_towar(index):
    """Funkcja pomocnicza do usuwania towaru z listy"""
    del st.session_state.magazyn[index]
    st.rerun()

if __name__ == "__main__":
    main()
