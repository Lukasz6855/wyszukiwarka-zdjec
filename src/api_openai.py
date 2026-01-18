# Zawartość pliku /znajdywacz-zdjec/znajdywacz-zdjec/src/api_openai.py

import os  # dostęp do zmiennych środowiskowych
import base64  # kodowanie pliku obrazu do base64
import mimetypes  # wykrywanie typu MIME po rozszerzeniu pliku
from openai import OpenAI  # nowy klient OpenAI (openai>=1.0.0)
from utils import mapa_modeli  # mapa aliasów -> id rzeczywiste

def pobierz_klienta_openai():  # funkcja tworząca klienta OpenAI z aktualnym kluczem
    klucz = os.getenv("OPENAI_API_KEY")  # pobierz klucz z ENV
    if not klucz:  # jeśli brak klucza
        raise ValueError("Brak klucza OPENAI_API_KEY w zmiennych środowiskowych")  # zgłoś błąd
    return OpenAI(api_key=klucz)  # zwróć klienta z ustawionym kluczem

def generuj_opis(sciezka_zdjecia, model_alias):  # funkcja generująca opis dla obrazu
    klient = pobierz_klienta_openai()  # utwórz klienta OpenAI
    # ustal rzeczywisty ID modelu: zmapuj alias na ID
    id_modelu = mapa_modeli.get(model_alias, {}).get("id_modelu", model_alias)  # mapowanie alias -> id
    
    print(f"[api_openai] Używam modelu: {id_modelu} (alias: {model_alias})")  # log dla debugowania

    # wczytaj plik obrazu i zakoduj do base64
    with open(sciezka_zdjecia, "rb") as f:  # otwórz plik binarnie
        dane = f.read()  # przeczytaj wszystkie bajty
    zakodowany = base64.b64encode(dane).decode("utf-8")  # zakoduj do base64 i zamień na string

    # wykryj typ MIME na podstawie rozszerzenia pliku
    typ_mime = mimetypes.guess_type(sciezka_zdjecia)[0] or "image/jpeg"  # domyślnie image/jpeg

    # Przygotuj wiadomość z tekstem i obrazem
    wiadomosc = [
        {
            "role": "user",  # rola użytkownika
            "content": [  # lista fragmentów contentu
                {"type": "text", "text": "Opisz to zdjęcie szczegółowo w 2-3 zdaniach."},  # instrukcja
                {"type": "image_url", "image_url": {"url": f"data:{typ_mime};base64,{zakodowany}"}}  # obraz
            ],
        }
    ]

    try:  # wywołanie API w bloku try
        odpowiedz = klient.chat.completions.create(
            model=id_modelu,  # użyj zmapowanego modelu (np. gpt-4o-mini)
            messages=wiadomosc,  # przekaż wiadomości z tekstem i obrazem
            max_tokens=200  # ogranicz liczbę tokenów w odpowiedzi
        )

        # wyciągnij tekst z odpowiedzi
        tekst = ""
        try:
            choices = getattr(odpowiedz, "choices", None) or odpowiedz.get("choices", None)
            if choices and len(choices) > 0:
                choice0 = choices[0]
                message = choice0.get("message") if isinstance(choice0, dict) else getattr(choice0, "message", None)
                if message:
                    content = message.get("content") if isinstance(message, dict) else getattr(message, "content", None)
                    if isinstance(content, str):  # jeśli content to string
                        tekst = content
                    elif isinstance(content, list):  # jeśli content jest listą
                        for frag in content:
                            if isinstance(frag, dict) and frag.get("type") == "text":
                                tekst += frag.get("text", "")
        except Exception as e:
            print(f"[api_openai] Błąd parsowania odpowiedzi: {e}")
            tekst = ""

        return tekst.strip()

    except Exception as e:
        raise RuntimeError(f"Błąd przy generowaniu opisu (model: {id_modelu}): {e}")