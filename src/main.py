# Zawartość pliku: /znajdywacz-zdjec/znajdywacz-zdjec/src/main.py

import streamlit as st
import os
from config import wczytaj_klucz_openai, wczytaj_modele, pobierz_rzeczywista_nazwe_modelu
from przetwarzanie_zdjec import przetworz_zdjecia
from baza_danych import (
    zapisz_embedding, wyszukaj_zdjecia, pobierz_wszystkie_zdjecia,
    usun_embedding, usun_wszystkie_embeddingi, sprawdz_czy_zdjecie_istnieje
)
from utils import oszacuj_koszt

# ===== FUNKCJE POMOCNICZE =====
def sprawdz_dostepnosc_klucza_openai():
    """
    Sprawdź czy klucz OpenAI jest dostępny w zmiennych środowiskowych.
    
    UWAGA: Celowo NIE sprawdzamy st.secrets dla klucza OpenAI!
    Każdy użytkownik aplikacji na Streamlit Cloud musi podać swój własny klucz.
    
    Secrets są używane tylko dla infrastruktury (Qdrant), nie dla kluczy użytkowników.
    
    Zwraca: True jeśli klucz jest dostępny w os.environ, False jeśli nie
    """
    # Sprawdź tylko zmienne środowiskowe (dla lokalnego użycia z .env)
    if os.getenv("OPENAI_API_KEY"):
        return True
    
    return False

# ===== KONFIGURACJA STRONY =====
st.set_page_config(page_title="Znajdywacz zdjęć", layout="wide")

# ===== INICJALIZACJA SESJI =====
if "reset_uploader" not in st.session_state:
    st.session_state.reset_uploader = False

if "selected_images" not in st.session_state:
    st.session_state.selected_images = set()

if "opis_wyszukiwania" not in st.session_state:
    st.session_state.opis_wyszukiwania = ""

if "potwierdz_usuniec_wszystko" not in st.session_state:
    st.session_state.potwierdz_usuniec_wszystko = False

# Stany dla przetwarzania duplikatów
if "w_trakcie_sprawdzania" not in st.session_state:
    st.session_state.w_trakcie_sprawdzania = False

if "znalezione_duplikaty" not in st.session_state:
    st.session_state.znalezione_duplikaty = []

if "decyzje_uzytkownika" not in st.session_state:
    st.session_state.decyzje_uzytkownika = {}

if "cached_files" not in st.session_state:
    st.session_state.cached_files = None

if "model_do_przetworzenia" not in st.session_state:
    st.session_state.model_do_przetworzenia = None

if "model_id_do_przetworzenia" not in st.session_state:
    st.session_state.model_id_do_przetworzenia = None

# ===== PASEK BOCZNY =====
with st.sidebar:
    st.header("⚙️ Konfiguracja")
    
    # SEKCJA 1: KLUCZ OPENAI
    # Sprawdź czy klucz jest już w zmiennych środowiskowych (z pliku .env - tylko lokalnie)
    klucz_z_env = sprawdz_dostepnosc_klucza_openai()
    
    if klucz_z_env:
        # Klucz załadowany z .env (użycie lokalne)
        st.success("✅ Klucz OpenAI załadowany z pliku .env")
        st.info("💡 Używasz klucza z lokalnego pliku .env")
        klucz_openai_aktywny = True
    else:
        # Wymaga ręcznego wprowadzenia (Streamlit Cloud lub brak .env)
        klucz_openai = st.text_input(
            "Wprowadź swój klucz OpenAI:",
            type="password",
            help="Twój klucz nie jest nigdzie zapisywany. Jest używany tylko w tej sesji."
        )
        
        if klucz_openai:
            wczytaj_klucz_openai(klucz_openai)
            klucz_openai_aktywny = True
        else:
            klucz_openai_aktywny = False
            st.warning("⚠️ Wprowadź klucz OpenAI, aby korzystać z aplikacji")
    
    # SEKCJA 2: WYBÓR MODELU (dostępny zawsze, ale funkcjonalny tylko gdy klucz jest aktywny)
    modele, model_domyslny = wczytaj_modele()
        
    try:
        indeks_domyslny = modele.index(model_domyslny)
    except Exception:
        indeks_domyslny = 0
    
    mapy_modeli = {
        "model_prosty": "Model prosty: gpt-4o-mini",
        "model_sredni": "Model średni: gpt-4o",
        "model_zaawansowany": "Model zaawansowany: gpt-4-turbo"
    }
    
    opcje_wyswietlane = [mapy_modeli.get(m, m) for m in modele]
    
    model_wybrany_display = st.selectbox(
        "Wybierz model OpenAI:",
        opcje_wyswietlane,
        index=indeks_domyslny
    )
    
    model_wybrany_id = modele[opcje_wyswietlane.index(model_wybrany_display)]
    model_wybrany = pobierz_rzeczywista_nazwe_modelu(model_wybrany_id)
    
    # SEKCJA 3: WCZYTYWANIE ZDJĘĆ
    st.subheader("📸 Wczytaj zdjęcia")
    
    uploaded_files = st.file_uploader(
        "Prześlij zdjęcia",
        accept_multiple_files=True,
        type=["jpg", "jpeg", "png"],
        key=f"uploader_{st.session_state.reset_uploader}"
    )
    
    # PRZYCISK: Przetwórz zdjęcia
    if st.button("Przetwórz zdjęcia", key="btn_process", disabled=not klucz_openai_aktywny):
        if uploaded_files:
            st.session_state.cached_files = uploaded_files
            st.session_state.model_do_przetworzenia = model_wybrany
            st.session_state.model_id_do_przetworzenia = model_wybrany_id
            st.session_state.w_trakcie_sprawdzania = True
            st.session_state.znalezione_duplikaty = []
            st.session_state.decyzje_uzytkownika = {}
            st.rerun()
        else:
            st.warning("Proszę wybrać co najmniej jedno zdjęcie.")
        
        # ===== OBSŁUGA DUPLIKATÓW W PASKU BOCZNYM =====
        if st.session_state.w_trakcie_sprawdzania and st.session_state.cached_files:
            st.divider()
            
            # KROK 1: Sprawdzenie duplikatów (tylko raz)
            if not st.session_state.znalezione_duplikaty and len(st.session_state.decyzje_uzytkownika) == 0:
                st.write("🔍 Sprawdzanie duplikatów w bazie Qdrant...")
                
                for idx, plik in enumerate(st.session_state.cached_files):
                    czy_istnieje = sprawdz_czy_zdjecie_istnieje(plik.name)
                    
                    if czy_istnieje:
                        st.session_state.znalezione_duplikaty.append((idx, plik.name))
                        st.write(f"  ⚠️ Duplikat: {plik.name}")
                    else:
                        st.write(f"  ✅ Nowe: {plik.name}")
            
            # KROK 2: Pytanie o duplikaty
            if st.session_state.znalezione_duplikaty:
                st.warning("⚠️ Znaleziono duplikaty!")
                st.write("Co chcesz zrobić z każdym duplikatem?")
                
                # Dla każdego duplikatu pokaż opcje
                for idx, nazwa_pliku in st.session_state.znalezione_duplikaty:
                    st.write(f"📄 **{nazwa_pliku}**")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("⏭️ Pomiń", key=f"pominac_{idx}"):
                            st.session_state.decyzje_uzytkownika[idx] = "pomiń"
                            st.rerun()
                    
                    with col2:
                        if st.button("✅ Przetwórz jako nowy", key=f"przetwarzac_{idx}"):
                            st.session_state.decyzje_uzytkownika[idx] = "przetwórz"
                            st.rerun()
                
                # Sprawdź czy są wszystkie decyzje
                czy_wszystkie = len(st.session_state.decyzje_uzytkownika) == len(st.session_state.znalezione_duplikaty)
                
                if czy_wszystkie:
                    st.success(f"✅ Decyzje dla {len(st.session_state.decyzje_uzytkownika)} duplikatów podane")
                else:
                    st.info(f"⏳ Czekam: {len(st.session_state.decyzje_uzytkownika)}/{len(st.session_state.znalezione_duplikaty)}")
            
            # KROK 3: Przetwarzanie (gdy są decyzje lub brak duplikatów)
            czy_gotowe_do_przetworzenia = (
                (not st.session_state.znalezione_duplikaty) or 
                (len(st.session_state.decyzje_uzytkownika) == len(st.session_state.znalezione_duplikaty))
            )
            
            if czy_gotowe_do_przetworzenia and st.session_state.cached_files and st.session_state.w_trakcie_sprawdzania:
                
                with st.spinner("⏳ Przetwarzanie zdjęć..."):
                    # Przygotuj mapowanie nazw
                    mapowanie_nazw = {}
                    
                    for idx, plik in enumerate(st.session_state.cached_files):
                        decyzja = st.session_state.decyzje_uzytkownika.get(idx, None)
                        
                        # Pomiń?
                        if decyzja == "pomiń":
                            continue
                        
                        # Przetwórz jako duplikat?
                        if decyzja == "przetwórz":
                            nazwa_bez_rozszerzenia, rozszerzenie = plik.name.rsplit('.', 1)
                            nowa_nazwa = f"{nazwa_bez_rozszerzenia}_1.{rozszerzenie}"
                            mapowanie_nazw[idx] = nowa_nazwa
                        else:
                            # Nie duplikat - użyj oryginalnej nazwy
                            mapowanie_nazw[idx] = plik.name
                    
                    # Przygotuj listę do przetworzenia
                    pliki_do_przetworzenia = []
                    nowe_mapowanie = {}
                    
                    for idx, plik in enumerate(st.session_state.cached_files):
                        if idx in mapowanie_nazw:
                            pliki_do_przetworzenia.append(plik)
                            nowe_mapowanie[len(pliki_do_przetworzenia) - 1] = mapowanie_nazw[idx]
                    
                    if pliki_do_przetworzenia:
                        # Przetwórz
                        opisy = przetworz_zdjecia(
                            pliki_do_przetworzenia,
                            st.session_state.model_do_przetworzenia,
                            nowe_mapowanie
                        )
                        
                        # Wylicz koszt
                        wynik = oszacuj_koszt(len(pliki_do_przetworzenia), st.session_state.model_id_do_przetworzenia)
                        
                        # Pokaż wyniki
                        st.divider()
                        st.info(wynik["uwaga"])
                        st.write(f"💰 Koszt: {wynik['koszt_calkowity_pln']} PLN")
                        st.write(f"  • Tekst: {wynik['szczegoly']['koszt_generacji_tokeny_pln']} PLN")
                        st.write(f"  • Embeddingi: {wynik['szczegoly']['koszt_embedding_pln']} PLN")
                        
                        # Zapisz embeddingi
                        for item in opisy:
                            zapisz_embedding(item["opis"], item["sciezka"])
                        
                        st.success("✅ Zdjęcia przetworzone i zapisane!")
                        
                        # Ustaw flagę dla animowanego komunikatu
                        st.session_state.przetwarzanie_zakonczone = True
                    else:
                        st.warning("Wszystkie zdjęcia pominięte.")
                    
                    # Resetuj stany
                    st.session_state.w_trakcie_sprawdzania = False
                    st.session_state.cached_files = None
                    st.session_state.znalezione_duplikaty = []
                    st.session_state.decyzje_uzytkownika = {}
                    st.session_state.reset_uploader = not st.session_state.reset_uploader

# ===== GŁÓWNY WIDOK APLIKACJI =====
st.title("🖼️ Znajdywacz zdjęć na podstawie opisu")

st.markdown("""
### O aplikacji
Aplikacja umożliwia wczytanie zdjęć i automatyczne generowanie ich opisów za pomocą AI. 
Następnie możesz szukać zdjęcia na podstawie słów kluczowych i opisu.

### Jak to działa?
1. **Wczytaj zdjęcia** - Prześlij zdjęcia za pomocą paska bocznego
2. **Przetwórz** - Aplikacja wygeneruje opisy i embeddingi dla każdego zdjęcia
3. **Szukaj** - Wpisz opis szukanych zdjęć w zakładce "Wyszukiwanie"
""")

# Animowany komunikat po przetworzeniu
if st.session_state.get("przetwarzanie_zakonczone", False):
    st.markdown(
        """
        <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .success-message {
            animation: fadeIn 0.5s ease-in;
            padding: 1rem;
            background: linear-gradient(90deg, #00c853 0%, #64dd17 100%);
            color: white;
            border-radius: 8px;
            text-align: center;
            font-weight: bold;
            font-size: 1.2rem;
            margin: 1rem 0;
            box-shadow: 0 4px 6px rgba(0, 200, 83, 0.3);
        }
        </style>
        <div class="success-message">
            🎉 Twoje zdjęcie/a zostały przetworzone! 🎉
        </div>
        """,
        unsafe_allow_html=True
    )
    # Resetuj flagę po wyświetleniu
    st.session_state.przetwarzanie_zakonczone = False

st.divider()

# --- ZAKŁADKI ---
tab1, tab2 = st.tabs(["Wyszukiwanie", "Zarządzanie zdjęciami"])

# ZAKŁADKA 1: WYSZUKIWANIE
with tab1:
    st.subheader("🔍 Wyszukaj zdjęcia")
    
    opis_wyszukiwania = st.text_input(
        "Wprowadź opis szukanych zdjęć:",
        key="search_input"
    )
    
    # Sprawdź czy klucz OpenAI jest aktywny (z inputu lub zmiennych środowiskowych)
    if sprawdz_dostepnosc_klucza_openai():
        if opis_wyszukiwania:
            st.subheader("📋 Wyniki wyszukiwania")
            
            wyniki = wyszukaj_zdjecia(opis_wyszukiwania)
            
            if wyniki:
                st.write(f"**Znalezione {len(wyniki)} zdjęcie(a):**")
                
                for idx, wynik in enumerate(wyniki):
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        sciezka = wynik.get("sciezka")
                        if sciezka:
                            st.image(sciezka, use_column_width=True)
                    
                    with col2:
                        opis = wynik.get("opis")
                        dopasowanie = wynik.get("similarity", 0)
                        procent_dopasowania = int(dopasowanie * 100)
                        
                        st.metric(label="Dopasowanie", value=f"{procent_dopasowania}%")
                        st.write(f"**Opis:**")
                        st.write(opis)
                    
                    st.divider()
            else:
                st.info("Nie znaleziono zdjęć pasujących do opisu.")
        else:
            st.info("💡 Wpisz opis szukanych zdjęć, aby zobaczyć wyniki.")
    else:
        st.warning("⚠️ Proszę wprowadzić klucz OpenAI na pasku bocznym.")

# ZAKŁADKA 2: ZARZĄDZANIE ZDJĘCIAMI
with tab2:
    st.subheader("📂 Lista wszystkich zdjęć")
    
    # Sprawdź czy klucz OpenAI jest aktywny
    if sprawdz_dostepnosc_klucza_openai():
        wszystkie_zdjecia = pobierz_wszystkie_zdjecia()
        
        if wszystkie_zdjecia:
            st.write(f"**Liczba zapisanych zdjęć: {len(wszystkie_zdjecia)}**")
            
            col_delete_all = st.columns([1, 3, 1])[0]
            if col_delete_all.button("🗑️ Usuń wszystkie", key="delete_all"):
                st.session_state.potwierdz_usuniec_wszystko = True
            
            if st.session_state.get("potwierdz_usuniec_wszystko", False):
                st.warning("⚠️ Czy na pewno chcesz usunąć wszystkie zdjęcia i embeddingi?")
                
                col_confirm_yes, col_confirm_no = st.columns(2)
                
                with col_confirm_yes:
                    if st.button("✅ Tak, usuń wszystko"):
                        usun_wszystkie_embeddingi()
                        st.success("Wszystkie zdjęcia usunięte.")
                        st.session_state.potwierdz_usuniec_wszystko = False
                        st.rerun()
                
                with col_confirm_no:
                    if st.button("❌ Anuluj"):
                        st.session_state.potwierdz_usuniec_wszystko = False
                        st.rerun()
            
            st.write("---")
            st.write("**Wybierz zdjęcia do usunięcia:**")
            
            for zdj in wszystkie_zdjecia:
                nazwa = zdj.get("nazwa", "Nieznana nazwa")
                sciezka = zdj.get("sciezka", "")
                
                col_thumb, col_check = st.columns([0.5, 3])
                
                with col_thumb:
                    # Wyświetl miniaturkę zdjęcia
                    if sciezka:
                        try:
                            st.image(sciezka, width=50)
                        except:
                            st.write("📷")
                    else:
                        st.write("📷")
                
                with col_check:
                    is_selected = st.checkbox(nazwa, key=f"select_{nazwa}")
                    
                    if is_selected:
                        st.session_state.selected_images.add(nazwa)
                    else:
                        st.session_state.selected_images.discard(nazwa)
            
            if st.session_state.selected_images:
                if st.button(f"🗑️ Usuń zaznaczone ({len(st.session_state.selected_images)})"):
                    for nazwa in st.session_state.selected_images:
                        usun_embedding(nazwa)
                    
                    st.success(f"Usunięto {len(st.session_state.selected_images)} zdjęcie(a).")
                    st.session_state.selected_images = set()
                    st.rerun()
        else:
            st.info("Brak zapisanych zdjęć.")
    else:
        st.warning("⚠️ Proszę wprowadzić klucz OpenAI na pasku bocznym.")