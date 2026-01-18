import requests  # import do wykonywania żądań HTTP (pobranie kursu walut)
import os  # import do dostępu do zmiennych środowiskowych

# SŁOWNIK CEN: uzupełnij te wartości zgodnie z aktualną dokumentacją OpenAI (wartości w USD)
ceny_modeli = {  # słownik z przykładowymi cenami (zmień na prawdziwe)
    "model_prosty": {  # przykład prostego, taniego modelu
        "cena_za_1k_tokenow_usd": 0.00075,  # cena za 1000 tokenów generacji tekstu (USD) — gpt-4o-mini
        "cena_embedding_za_1k_tokenow_usd": 0.00013  # cena za 1000 tokenów embedding (USD)
    },
    "model_sredni": {  # przykład modelu średniej klasy
        "cena_za_1k_tokenow_usd": 0.0125,  # cena za 1000 tokenów generacji (USD) — gpt-4o
        "cena_embedding_za_1k_tokenow_usd": 0.00013  # cena za 1000 tokenów embedding (USD)
    },
    "model_zaawansowany": {  # przykład modelu zaawansowanego
        "cena_za_1k_tokenow_usd": 0.03,  # cena za 1000 tokenów generacji (USD) — gpt-4-turbo
        "cena_embedding_za_1k_tokenow_usd": 0.00013  # cena za 1000 tokenów embedding (USD)
    }
}

# Mapa aliasów do rzeczywistych ID modeli OpenAI (WAŻNE: tylko modele z vision support!)
mapa_modeli = {  # mapa alias -> id modelu/opis
    "model_prosty": {  # alias używany w aplikacji
        "id_modelu": "gpt-4o-mini",  # model z obsługą vision (tańszy, szybszy)
        "opis": "tani model z vision"  # krótki opis
    },
    "model_sredni": {  # alias średni
        "id_modelu": "gpt-4o",  # model GPT-4o z pełną obsługą vision
        "opis": "model średniej klasy, vision"  # opis
    },
    "model_zaawansowany": {  # alias zaawansowany
        "id_modelu": "gpt-4-turbo",  # model zaawansowany (wolniejszy, droższy)
        "opis": "zaawansowany model, vision, wyższa jakość"  # opis
    }
}

def pobierz_kurs_usd_na_pln():  # funkcja pobierająca kurs USD->PLN
    try:  # spróbuj pobrać kurs z publicznego API
        resp = requests.get("https://api.exchangerate.host/latest", params={"base": "USD", "symbols": "PLN"}, timeout=5)  # żądanie do API
        resp.raise_for_status()  # rzuć wyjątek przy błędnym statusie HTTP
        dane = resp.json()  # parsuj odpowiedź jako JSON
        kurs = dane.get("rates", {}).get("PLN")  # pobierz kurs dla PLN
        if kurs and kurs > 0:  # sprawdź poprawność kursu
            return float(kurs)  # zwróć kurs jako float
    except Exception:  # w przypadku błędu przejdź dalej do fallbacku
        pass  # brak działań, użyj fallbacku poniżej
    fallback = os.getenv("FALLBACK_USD_PLN", "4.0")  # pobierz fallback z .env lub użyj 4.0
    try:  # spróbuj zwrócić fallback jako float
        return float(fallback)  # zwróć fallback
    except Exception:  # w razie problemu zwróć ostateczny fallback
        return 4.0  # ostateczny fallback kursu

def oszacuj_koszt(liczba_zdjec, model, srednia_liczba_tokenow_na_zdjecie=150, srednia_liczba_tokenow_na_embedding=50):  # główna funkcja szacująca koszt
    if model not in ceny_modeli:  # walidacja czy model jest zdefiniowany
        raise ValueError("Nieznany model. Uzupełnij cennik w utils.py (ceny_modeli).")  # rzuć błąd jeśli brak modelu
    
    cennik = ceny_modeli[model]  # pobierz cennik dla wybranego modelu
    cena_za_1k_tokenow_usd = float(cennik.get("cena_za_1k_tokenow_usd", 0.0))  # cena za 1000 tokenów generacji (USD)
    cena_embedding_za_1k_tokenow_usd = float(cennik.get("cena_embedding_za_1k_tokenow_usd", 0.0))  # cena za 1000 tokenów embedding (USD)

    # oblicz koszt w USD za generację opisów
    koszt_generacji_tokeny_usd = (srednia_liczba_tokenow_na_zdjecie / 1000.0) * liczba_zdjec * cena_za_1k_tokenow_usd  # koszt generacji tekstu w USD
    
    # oblicz koszt w USD za embeddingi
    koszt_embedding_usd = (srednia_liczba_tokenow_na_embedding / 1000.0) * liczba_zdjec * cena_embedding_za_1k_tokenow_usd  # koszt embeddingów w USD

    # suma kosztów w USD (bez ceny za przetworzenie obrazu)
    laczny_koszt_usd = koszt_generacji_tokeny_usd + koszt_embedding_usd  # suma

    # przelicz na PLN
    kurs = pobierz_kurs_usd_na_pln()  # pobierz kurs USD->PLN
    koszt_generacji_tokeny_pln = round(koszt_generacji_tokeny_usd * kurs, 2)  # koszt generacji w PLN
    koszt_embedding_pln = round(koszt_embedding_usd * kurs, 2)  # koszt embeddingów w PLN
    laczny_koszt_pln = round(laczny_koszt_usd * kurs, 2)  # łączny koszt w PLN

    return {  # zwróć wynik jako słownik z rozbiciem
        "koszt_calkowity_pln": laczny_koszt_pln,  # całkowity koszt w PLN
        "szczegoly": {  # szczegółowe rozbicie kosztów
            "koszt_generacji_tokeny_pln": koszt_generacji_tokeny_pln,  # koszt generacji tekstu
            "koszt_embedding_pln": koszt_embedding_pln,  # koszt embeddingów
            "kurs_usd_pln": kurs  # użyty kurs USD->PLN
        },
        "uwaga": "⚠️ Wyliczenie nie uwzględnia kosztu przetworzenia obrazu przez OpenAI. Rzeczywisty koszt może być wyższy — cena przetworzenia obrazu zależy od liczby pikseli i nie ma jednoznacznego cennika."  # ostrzeżenie dla użytkownika
    }

def waliduj_klucz_api(klucz):  # prosta walidacja długości klucza (można rozszerzyć)
    if not klucz or len(klucz) < 30:  # sprawdź minimalną długość klucza
        raise ValueError("Nieprawidłowy klucz API. Sprawdź wpisany klucz.")  # rzuć błąd jeśli niepoprawny
    return True  # zwróć True jeśli OK

def zapisz_zdjecie(plik, sciezka):  # funkcja zapisująca przesłane pliki na dysk
    with open(sciezka, "wb") as f:  # otwórz plik do zapisu w trybie binarnym
        f.write(plik.getbuffer())  # zapisz zawartość przesłanego pliku
    return sciezka  # zwróć ścieżkę do zapisanego pliku

def generuj_nazwe_zdjecia(numer):  # funkcja generująca prostą nazwę pliku
    return f"zdjecie_{numer}.jpg"  # zwróć nazwę pliku w formacie jpg