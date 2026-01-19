# Zawartość pliku: /znajdywacz-zdjec/znajdywacz-zdjec/src/przetwarzanie_zdjec.py

import os  # moduł do pracy ze ścieżkami i operacjami na plikach
import base64  # do kodowania zdjęć na base64 (format który API rozumie)
from openai import OpenAI  # klient OpenAI do analizy zdjęć
from dotenv import load_dotenv  # załadowanie zmiennych .env

# Załaduj zmienne środowiskowe z pliku .env
load_dotenv()

# Ścieżka do folderu gdzie będą zapisywane przetworzone zdjęcia
FOLDER_ZDJEC = "zdjecia_przetworzone"

# Utwórz folder jeśli nie istnieje
if not os.path.exists(FOLDER_ZDJEC):
    os.makedirs(FOLDER_ZDJEC)  # makedirs = utwórz folder (i wszystkie nadrzędne jeśli potrzeba)
    print(f"[przetwarzanie_zdjec] Utworzono folder '{FOLDER_ZDJEC}'")

def przetworz_zdjecia(lista_plikow, model, klucz_api, mapowanie_nazw=None):
    """
    Przetwórz zdjęcia - wygeneruj opisy za pomocą Vision API OpenAI
    
    Parametry:
    - lista_plikow: lista plików przesłanych przez użytkownika (z Streamlit)
    - model: nazwa modelu OpenAI do użycia (np. "gpt-4o-mini", "gpt-4o")
    - klucz_api: klucz API OpenAI
    - mapowanie_nazw: słownik mapujący indeksy na nowe nazwy (dla duplikatów)
    
    Zwraca: lista słowników z kluczami "opis" i "sciezka"
    """
    
    # Jeśli mapowanie_nazw nie zostało przekazane - utwórz pusty słownik
    if mapowanie_nazw is None:
        mapowanie_nazw = {}
    
    # Jeśli klucz nie istnieje - wyrzuć błąd (aplikacja się zatrzyma)
    if not klucz_api:
        raise ValueError("Brak klucza OpenAI.")
    
    # Utwórz klienta OpenAI - zaraz będziemy go używać do wysyłania zdjęć
    klient = OpenAI(api_key=klucz_api)
    
    # Lista na wyniki (opis + ścieżka dla każdego zdjęcia)
    wyniki = []
    
    # Pętla po każdym przesłanym pliku
    for idx, plik in enumerate(lista_plikow):
        print(f"[przetwarzanie_zdjec] Przetwarzanie zdjęcia {idx + 1}/{len(lista_plikow)}: {plik.name}")
        
        try:
            # Pobierz oryginalną nazwę pliku (bez żadnych zmian!)
            oryginalna_nazwa = plik.name
            
            # Sprawdź czy istnieje mapowanie dla tego indeksu (dla duplikatów)
            # Jeśli istnieje - użyj nową nazwę, jeśli nie - użyj oryginalną
            nazwa_do_zapisu = mapowanie_nazw.get(idx, oryginalna_nazwa)
            
            # Odczytaj zawartość pliku (cały plik jako bajty)
            zawartosc_pliku = plik.read()
            
            # Zamień zdjęcie (bajty) na kod base64 (tekst który API rozumie)
            # base64 to standard kodowania - zamieniamy dane binarne na tekst
            zdjecie_base64 = base64.b64encode(zawartosc_pliku).decode('utf-8')
            
            # Pobierz rozszerzenie pliku (np. ".jpg" z "foto.jpg")
            # os.path.splitext() dzieli nazwę na (nazwa, rozszerzenie)
            _, rozszerzenie = os.path.splitext(oryginalna_nazwa)
            
            # Mapa zamieniająca rozszerzenia na MIME types
            # MIME type mówi API jaki format ma plik
            mime_type_map = {
                ".jpg": "image/jpeg",  # JPEG to format zdjęcia
                ".jpeg": "image/jpeg",  # JPEG to format zdjęcia
                ".png": "image/png",  # PNG to format zdjęcia
                ".gif": "image/gif",  # GIF to format animacji
                ".webp": "image/webp"  # WebP to nowoczesny format
            }
            
            # Pobierz MIME type dla tego rozszerzenia (domyślnie jpeg)
            mime_type = mime_type_map.get(rozszerzenie.lower(), "image/jpeg")
            
            # Wyślij zdjęcie do OpenAI Vision API z prośbą o opis
            # WAŻNE: Używamy client.chat.completions.create() z modelami vision
            odpowiedz = klient.chat.completions.create(
                model=model,  # którego modelu użyć (gpt-4o-mini, gpt-4o, itp.)
                messages=[
                    {
                        "role": "user",  # to jest wiadomość od użytkownika
                        "content": [
                            # Instrukcja tekstowa dla modelu
                            {
                                "type": "text",  # typ: tekst
                                "text": "Opisz to zdjęcie szczegółowo. Opisz co widzisz, kolory, obiekty, osoby, tło, nastrój. Odpowiedź powinna być konkretna i informacyjna."  # co ma zrobić
                            },
                            # Zdjęcie w formacie base64
                            {
                                "type": "image_url",  # typ: URL do zdjęcia
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{zdjecie_base64}"  # zdjęcie zakodowane w base64
                                }
                            }
                        ]
                    }
                ]
            )
            
            # Pobierz wygenerowany opis z odpowiedzi
            # choices[0] = pierwsza odpowiedź
            # message.content = tekst odpowiedzi
            opis = odpowiedz.choices[0].message.content
            
            # Utwórz ścieżkę do zapisania zdjęcia
            # Użyj nazwę ze zmapowanego słownika (która może zawierać _1 dla duplikatów)
            sciezka_docelowa = os.path.join(FOLDER_ZDJEC, nazwa_do_zapisu)
            
            # Jeśli plik już istnieje na dysku - dodaj numer aby uniknąć nadpisania
            licznik = 2  # licznik do numeru (zaczynamy od 2, bo _1 mogło być już dodane)
            nazwa_bazowa, rozszerzenie_plik = os.path.splitext(nazwa_do_zapisu)  # podziel nazwę
            
            # Pętla: dopóki plik istnieje - dodawaj numer
            while os.path.exists(sciezka_docelowa):
                # Utwórz nową ścieżkę z numerem (np. "foto_2.jpg", "foto_3.jpg")
                sciezka_docelowa = os.path.join(FOLDER_ZDJEC, f"{nazwa_bazowa}_{licznik}{rozszerzenie_plik}")
                licznik += 1  # zwiększ licznik
            
            # Zapisz zdjęcie do pliku na dysku
            with open(sciezka_docelowa, 'wb') as f:
                # 'wb' = write binary (otworz plik do zapisu w trybie binarnym)
                f.write(zawartosc_pliku)  # zapisz zawartość do pliku
            
            # Wypisz komunikat że zdjęcie zostało zapisane
            print(f"[przetwarzanie_zdjec] ✅ Zdjęcie zapisane: {sciezka_docelowa}")
            
            # Dodaj wynik do listy (opis AI + ścieżka do pliku)
            wyniki.append({
                "opis": opis,  # wygenerowany opis AI
                "sciezka": sciezka_docelowa  # ścieżka do zapisanego zdjęcia
            })
            
        except Exception as e:
            # Jeśli coś poszło nie tak przy przetwarzaniu tego zdjęcia
            print(f"[przetwarzanie_zdjec] ❌ Błąd przy przetwarzaniu {plik.name}: {e}")
            continue  # przejdź do następnego zdjęcia (pomiń ten błąd)
    
    # Zwróć listę wyników (wszystkie opisy + ścieżki)
    return wyniki