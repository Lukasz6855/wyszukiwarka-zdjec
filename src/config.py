# Zawartość pliku src/config.py

# Importujemy potrzebne biblioteki
import os
from dotenv import load_dotenv

# Ładujemy zmienne środowiskowe z pliku .env
load_dotenv()

# ===== KONFIGURACJA MODELI =====
# Słownik z mapowaniem internal identyfikatorów na rzeczywiste nazwy modeli OpenAI
MODELE = {
    "model_prosty": "gpt-4o-mini",  # internal: model_prosty -> rzeczywista nazwa: gpt-4o-mini
    "model_sredni": "gpt-4o",  # internal: model_sredni -> rzeczywista nazwa: gpt-4o
    "model_zaawansowany": "gpt-4-turbo"  # internal: model_zaawansowany -> rzeczywista nazwa: gpt-4-turbo
}

# Model domyślnie wybrany przy uruchomieniu aplikacji
MODEL_DOMYSLNY = "model_prosty"  # domyślnie wybieramy "model_prosty" (gpt-4o-mini)

# ===== FUNKCJE KONFIGURACYJNE =====

def wczytaj_klucz_openai(klucz):
    """
    Wczytaj klucz OpenAI do zmiennych środowiskowych
    
    Parametr:
    - klucz: string zawierający klucz API OpenAI
    
    Ta funkcja zapisuje klucz w zmiennych środowiskowych aplikacji
    aby była dostępna dla wszystkich modułów
    """
    # Zapisz klucz w zmiennych środowiskowych
    os.environ["OPENAI_API_KEY"] = klucz
    print(f"[config] ✅ Klucz OpenAI załadowany")

def wczytaj_modele():
    """
    Pobierz listę dostępnych modeli i model domyślny
    
    Zwraca: tupla (lista_identyfikatorów, model_domyslny)
    np. (["model_prosty", "model_sredni", "model_zaawansowany"], "model_prosty")
    
    Te identyfikatory będą zamieniane na rzeczywiste nazwy modeli
    przed wysłaniem do OpenAI
    """
    # Lista internal identyfikatorów modeli (klucze ze słownika MODELE)
    lista_modeli = list(MODELE.keys())
    
    # Zwróć listę identyfikatorów i model domyślny
    return lista_modeli, MODEL_DOMYSLNY

def pobierz_rzeczywista_nazwe_modelu(identyfikator):
    """
    Zamień internal identyfikator modelu na rzeczywistą nazwę OpenAI
    
    Parametr:
    - identyfikator: internal nazwa (np. "model_prosty")
    
    Zwraca: rzeczywista nazwa modelu (np. "gpt-4o-mini")
    """
    # Pobierz z słownika MODELE rzeczywistą nazwę
    # Jeśli identyfikator nie istnieje - zwróć "gpt-4o-mini" (default)
    return MODELE.get(identyfikator, "gpt-4o-mini")

def oszacuj_koszt(liczba_zdjec, identyfikator_modelu):
    """
    Oszacuj koszt przetwarzania zdjęć
    
    Parametry:
    - liczba_zdjec: ile zdjęć będzie przetwarzanych
    - identyfikator_modelu: internal identyfikator modelu (np. "model_prosty")
    
    Zwraca: słownik z informacjami o kosztach
    """
    
    # Mapowanie modeli na cenę za 1M tokenów (ceny z OpenAI)
    ceny = {
        "model_prosty": {  # gpt-4o-mini
            "input": 0.15,  # cena za 1M tokenów wejścia (USD)
            "output": 0.60  # cena za 1M tokenów wyjścia (USD)
        },
        "model_sredni": {  # gpt-4o
            "input": 5.00,  # cena za 1M tokenów wejścia (USD)
            "output": 15.00  # cena za 1M tokenów wyjścia (USD)
        },
        "model_zaawansowany": {  # gpt-4-turbo
            "input": 10.00,  # cena za 1M tokenów wejścia (USD)
            "output": 30.00  # cena za 1M tokenów wyjścia (USD)
        }
    }
    
    # Pobierz cenę dla wybranego modelu
    cena_modelu = ceny.get(identyfikator_modelu, ceny["model_prosty"])
    
    # Oszacowanie: każde zdjęcie ~200 tokenów wejścia + 300 tokenów wyjścia
    tokeny_wejscia = liczba_zdjec * 200  # liczba zdjęć * średnia tokenów na zdjęcie
    tokeny_wyjscia = liczba_zdjec * 300  # liczba zdjęć * średnia tokenów opisu
    
    # Oblicz koszt wejścia (tokeny * cena za 1M)
    koszt_wejscia = (tokeny_wejscia / 1_000_000) * cena_modelu["input"]
    
    # Oblicz koszt wyjścia (tokeny * cena za 1M)
    koszt_wyjscia = (tokeny_wyjscia / 1_000_000) * cena_modelu["output"]
    
    # Całkowity koszt w USD
    koszt_usd = koszt_wejscia + koszt_wyjscia
    
    # Zamień USD na PLN (kurs: 1 USD = 4.0 PLN - przybliżenie)
    kurs_usd_pln = 4.0
    koszt_pln = koszt_usd * kurs_usd_pln
    
    # Zwróć słownik z informacjami
    return {
        "uwaga": f"ℹ️ Przetwarzanie {liczba_zdjec} zdjęć(a) będzie kosztować około {koszt_pln:.2f} PLN",
        "koszt_calkowity_pln": f"{koszt_pln:.2f}",
        "szczegoly": {
            "koszt_generacji_tokeny_pln": f"{koszt_wejscia * kurs_usd_pln:.2f}",
            "koszt_embedding_pln": f"{koszt_wyjscia * kurs_usd_pln:.2f}"
        }
    }