from qdrant_client import QdrantClient  # import klienta Qdrant - baza wektorowa do przechowywania embeddingów
import os  # dostęp do zmiennych środowiskowych i operacji na ścieżkach
from openai import OpenAI  # klient OpenAI do generowania embeddingów
from dotenv import load_dotenv  # wczytanie zmiennych z pliku .env

# Załaduj zmienne środowiskowe z pliku .env (jeśli istnieje)
load_dotenv()

# ===== KONFIGURACJA QDRANT =====
# Pobierz adres URL Qdrant ze zmiennych środowiskowych (dla usługi Qdrant Cloud)
QDRANT_URL = os.getenv("QDRANT_URL", None)  # np. https://xxx.qdrant.cloud

# Pobierz klucz API Qdrant ze zmiennych środowiskowych (dla usługi Qdrant Cloud)
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)  # opcjonalny klucz API

# Nazwa kolekcji (tabela w bazie Qdrant gdzie przechowujemy embeddingi)
NAZWA_KOLEKCJI = "opisy_zdjec"

# ===== FUNKCJE POMOCNICZE =====

def utworz_klienta_qdrant():
    """
    Utwórz połączenie z bazą Qdrant
    - Jeśli QDRANT_URL jest ustawiony: użyj Qdrant Cloud
    - Jeśli nie: użyj lokalnego Qdrant (localhost:6333)
    """
    # Jeśli nie ma URL Qdrant - połącz się z lokalnym Qdrant
    if not QDRANT_URL:
        # localhost = Twoja maszyna, 6333 = domyślny port Qdrant
        return QdrantClient(host="localhost", port=6333)
    
    # Jeśli URL istnieje i jest klucz API - przekaż go
    if QDRANT_API_KEY:
        return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    else:
        # Połącz bez klucza
        return QdrantClient(url=QDRANT_URL)

# Inicjalizuj klienta Qdrant (global - używany przez wszystkie funkcje)
klient_qdrant = utworz_klienta_qdrant()

def pobierz_klienta_openai():
    """
    Pobierz klienta OpenAI z kluczem API
    Klucz API musi być w zmiennej środowiskowej OPENAI_API_KEY
    """
    # Pobierz klucz OpenAI ze zmiennych środowiskowych
    klucz_api = os.getenv("OPENAI_API_KEY")
    
    # Jeśli klucz nie istnieje - wyrzuć błąd
    if not klucz_api:
        raise ValueError("Brak klucza OpenAI w zmiennych środowiskowych (OPENAI_API_KEY).")
    
    # Utwórz i zwróć klienta OpenAI z kluczem
    return OpenAI(api_key=klucz_api)

def inicjalizuj_kolekcje():
    """
    Inicjalizuj kolekcję w bazie Qdrant
    - Jeśli kolekcja już istnieje: nic nie rób
    - Jeśli nie istnieje: utwórz ją
    """
    try:
        # Spróbuj pobrać info o kolekcji (aby sprawdzić czy istnieje)
        klient_qdrant.get_collection(NAZWA_KOLEKCJI)
    except Exception as e:
        # Wyłapano wyjątek - sprawdź rodzaj błędu
        msg = str(e)  # zamień wyjątek na string aby sprawdzić kod błędu
        
        # Jeśli błąd to 403 Forbidden - problem z dostępem do Qdrant Cloud
        if "403" in msg or "forbidden" in msg.lower():
            raise ValueError("Brak dostępu do Qdrant (403 Forbidden). Sprawdź QDRANT_URL i QDRANT_API_KEY w .env.")
        
        # Jeśli błąd to 404 Not Found lub "doesn't exist" - kolekcja nie istnieje, trzeba ją utworzyć
        if "404" in msg or "not found" in msg.lower() or "doesn't exist" in msg.lower():
            # Spróbuj utworzyć nową kolekcję
            try:
                klient_qdrant.create_collection(
                    collection_name=NAZWA_KOLEKCJI,  # nazwa kolekcji
                    vectors_config={"size": 1536, "distance": "Cosine"}  # rozmiar wektora=1536 (text-embedding-3-small), miara=cosinus
                )
                print(f"[baza_danych] Utworzono kolekcję '{NAZWA_KOLEKCJI}'")
            except Exception as e2:
                # Jeśli nie udało się utworzyć - wyrzuć błąd
                raise RuntimeError(f"Nie udało się utworzyć kolekcji: {e2}")
        else:
            # Inny nieoczekiwany błąd
            raise RuntimeError(f"Nieoczekiwany błąd przy sprawdzaniu kolekcji: {e}")

# ===== FUNKCJE DO OBSŁUGI EMBEDDINGÓW =====

def generuj_embedding(tekst):
    """
    Wygeneruj embedding dla tekstu (zamień tekst na wektor)
    Embedding to reprezentacja matematyczna tekstu - liczby które odzwierciedlają znaczenie tekstu
    """
    try:
        # Pobierz klienta OpenAI
        print(f"[baza_danych] Pobieram klienta OpenAI...")
        klient_openai = pobierz_klienta_openai()
        print(f"[baza_danych] Klient OpenAI gotowy")
        
        # Wyślij tekst do OpenAI i otrzymaj embedding
        print(f"[baza_danych] Wysyłam zapytanie do OpenAI API (model: text-embedding-3-small)...")
        odpowiedz = klient_openai.embeddings.create(
            model="text-embedding-3-small",  # model do generowania embeddingów
            input=tekst  # tekst do przetworzenia
        )
        print(f"[baza_danych] Otrzymano odpowiedź z OpenAI")
        
        # Wyciągnij wektor z odpowiedzi (zwróć jako listę liczb)
        embedding = odpowiedz.data[0].embedding
        print(f"[baza_danych] Embedding wygenerowany pomyślnie (długość: {len(embedding)})")
        return embedding
    except Exception as e:
        print(f"[baza_danych] BŁĄD w generuj_embedding: {e}")
        import traceback
        print(f"[baza_danych] Traceback: {traceback.format_exc()}")
        raise

def pobierz_nazwe_zdjecia(sciezka):
    """
    Ekstraktuj nazwę pliku ze ścieżki
    Np. ze "C:/Users/Łukasz/foto.jpg" -> "foto.jpg"
    """
    # Jeśli ścieżka istnieje
    if sciezka:
        # os.path.basename() zwraca ostatni element ścieżki (nazwę pliku)
        return os.path.basename(sciezka)
    
    # Jeśli ścieżka jest None - zwróć None
    return None

def sprawdz_czy_zdjecie_istnieje(nazwa_zdjecia):
    """
    Sprawdź czy zdjęcie o danej nazwie już istnieje w bazie
    Zwraca: True jeśli istnieje, False jeśli nie
    """
    # Inicjalizuj kolekcję (upewnij się że istnieje)
    inicjalizuj_kolekcje()
    
    try:
        # Pobierz wszystkie punkty (embeddingi) z kolekcji
        # scroll() zwraca tupla (lista_punktów, następny_offset)
        wszystkie_punkty, _ = klient_qdrant.scroll(
            collection_name=NAZWA_KOLEKCJI,  # z której kolekcji
            limit=10000  # maksymalnie 10000 wyników
        )
        
        # Pętla po każdym punkcie (embedding)
        for punkt in wszystkie_punkty:
            # Sprawdź czy nazwa_zdjecia w metadata pasuje do szukanej nazwy
            if punkt.payload.get("nazwa_zdjecia") == nazwa_zdjecia:
                # Znaleźliśmy! Zwróć True
                return True
        
        # Przeglądnęliśmy wszystkie i nie znaleźliśmy - zwróć False
        return False
    except Exception as e:
        # Jeśli coś poszło nie tak - wypisz błąd i zwróć False
        print(f"[baza_danych] Błąd przy sprawdzaniu duplikatu: {e}")
        return False

def zapisz_embedding(opis, sciezka_zdjecia=None):
    """
    Zapisz embedding (reprezentacja wektorowa tekstu) w bazie
    
    Parametry:
    - opis: tekst opisu zdjęcia (będzie zamieniony na wektor)
    - sciezka_zdjecia: ścieżka do pliku zdjęcia (opcjonalna)
    """
    # Inicjalizuj kolekcję
    inicjalizuj_kolekcje()
    
    # Wygeneruj embedding dla opisu (zamień tekst na wektor liczb)
    embedding = generuj_embedding(opis)
    
    # Pobierz nazwę zdjęcia ze ścieżki (np. "foto.jpg" z "C:/Users/.../foto.jpg")
    nazwa_zdjecia = pobierz_nazwe_zdjecia(sciezka_zdjecia)
    
    # Utwórz słownik metadanych (dodatkowe info powiązane z embeddingiem)
    metadata = {
        "opis": opis,  # oryginalny tekst opisu
        "sciezka": sciezka_zdjecia,  # ścieżka do pliku
        "nazwa_zdjecia": nazwa_zdjecia  # nazwa pliku (bez ścieżki)
    }
    
    # Wygeneruj unikalny ID dla tego embeddingu
    # hash() = funkcja zamieniająca tekst na liczbę, % (10**10) = mod 10 bilionów (aby ID nie był gigantyczny)
    id_punktu = hash(opis) % (10 ** 10)
    
    try:
        # Wstaw (lub zaktualizuj jeśli istnieje) punkt do Qdrant
        klient_qdrant.upsert(
            collection_name=NAZWA_KOLEKCJI,  # w którą kolekcję
            points=[  # lista punktów do wstawienia
                {
                    "id": id_punktu,  # unikalny identyfikator
                    "vector": embedding,  # wektor (embedding) tekstu
                    "payload": metadata  # metadane (info dodatkowe)
                }
            ]
        )
        print(f"[baza_danych] Embedding zapisany (ID: {id_punktu})")
    except Exception as e:
        # Jeśli coś poszło nie tak - wypisz błąd
        print(f"[baza_danych] Błąd przy zapisie embeddingu: {e}")

def wyszukaj_zdjecia(opis_wyszukiwania, liczba_wynikow=5):
    """
    Wyszukaj zdjęcia pasujące do opisu
    
    Parametry:
    - opis_wyszukiwania: tekst co szukamy (np. "psy")
    - liczba_wynikow: ile wyników zwrócić (domyślnie 5)
    
    Zwraca: lista słowników z metadanymi znalezionych zdjęć (zawiera także similarity)
    """
    print(f"[baza_danych] Rozpoczynam wyszukiwanie dla: '{opis_wyszukiwania}'")
    
    # Inicjalizuj kolekcję
    inicjalizuj_kolekcje()
    print(f"[baza_danych] Kolekcja '{NAZWA_KOLEKCJI}' zainicjalizowana")
    
    try:
        # Wygeneruj embedding dla zapytania (słowo/fraza co szukamy)
        print(f"[baza_danych] Generuję embedding dla zapytania...")
        embedding_zapytania = generuj_embedding(opis_wyszukiwania)
        print(f"[baza_danych] Embedding wygenerowany (długość: {len(embedding_zapytania)})")
    except Exception as e:
        print(f"[baza_danych] BŁĄD przy generowaniu embeddingu: {e}")
        return []
    
    try:
        # Wyszukaj w Qdrant embeddingi podobne do naszego zapytania
        print(f"[baza_danych] Wyszukuję w Qdrant...")
        wyniki = klient_qdrant.search(
            collection_name=NAZWA_KOLEKCJI,  # gdzie szukać
            query_vector=embedding_zapytania,  # nasz wektor zapytania
            limit=liczba_wynikow  # ile wyników zwrócić
        )
        print(f"[baza_danych] Znaleziono {len(wyniki)} wyników")
        
        # Utwórz listę na wyniki
        lista_wynikow = []
        
        # Pętla po każdym znalezionym wyniku
        for wynik in wyniki:
            # Wyciągnij metadane (info) z wyniku
            metadata = wynik.payload
            
            # Dodaj współczynnik dopasowania (similarity) do metadanych
            # wynik.score = współczynnik Cosine Similarity (0-1)
            metadata["similarity"] = wynik.score
            
            # Dodaj metadane do listy wyników
            lista_wynikow.append(metadata)
            print(f"[baza_danych]   - {metadata.get('nazwa_zdjecia')} (similarity: {wynik.score:.4f})")
        
        # Zwróć listę wyników z similarity
        return lista_wynikow
    except Exception as e:
        # Jeśli coś poszło nie tak - wypisz błąd i zwróć pustą listę
        print(f"[baza_danych] BŁĄD przy wyszukiwaniu w Qdrant: {e}")
        import traceback
        print(f"[baza_danych] Traceback: {traceback.format_exc()}")
        return []

# ===== FUNKCJE DO ZARZĄDZANIA ZDJĘCIAMI =====

def pobierz_wszystkie_zdjecia():
    """
    Pobierz listę wszystkich zdjęć zapisanych w bazie
    Zwraca: lista słowników z info o zdjęciach (nazwa, opis, ścieżka, ID)
    """
    # Inicjalizuj kolekcję
    inicjalizuj_kolekcje()
    
    try:
        # Pobierz wszystkie punkty z kolekcji
        # scroll() zwraca tupla (lista_punktów, następny_offset)
        wszystkie_punkty, _ = klient_qdrant.scroll(
            collection_name=NAZWA_KOLEKCJI,  # z której kolekcji
            limit=10000  # maksymalnie 10000
        )
        
        # Utwórz listę na wyniki
        lista_zdjec = []
        
        # Zbiór przechowujący już widziane nazwy (aby uniknąć duplikatów)
        widziane_nazwy = set()
        
        # Pętla po każdym punkcie (embedding)
        for punkt in wszystkie_punkty:
            # Pobierz nazwę zdjęcia z metadanych
            nazwa_zdjecia = punkt.payload.get("nazwa_zdjecia")
            
            # Jeśli nazwa istnieje i nie widzieliśmy jej wcześniej
            if nazwa_zdjecia and nazwa_zdjecia not in widziane_nazwy:
                # Dodaj do listy słownik z info o zdjęciu
                lista_zdjec.append({
                    "nazwa": nazwa_zdjecia,  # nazwa pliku
                    "opis": punkt.payload.get("opis"),  # opis AI
                    "sciezka": punkt.payload.get("sciezka"),  # ścieżka do pliku
                    "id": punkt.id  # ID embeddingu
                })
                
                # Dodaj nazwę do zbioru już widzanych
                widziane_nazwy.add(nazwa_zdjecia)
        
        # Zwróć listę zdjęć
        return lista_zdjec
    except Exception as e:
        # Jeśli coś poszło nie tak - wypisz błąd i zwróć pustą listę
        print(f"[baza_danych] Błąd przy pobieraniu zdjęć: {e}")
        return []

def usun_embedding(nazwa_zdjecia):
    """
    Usuń embedding (i wszystkie jego kopie) na podstawie nazwy zdjęcia
    
    Parametr:
    - nazwa_zdjecia: nazwa pliku do usunięcia (np. "foto.jpg")
    """
    # Inicjalizuj kolekcję
    inicjalizuj_kolekcje()
    
    try:
        # Pobierz wszystkie punkty z kolekcji
        wszystkie_punkty, _ = klient_qdrant.scroll(
            collection_name=NAZWA_KOLEKCJI,  # z której kolekcji
            limit=10000  # maksymalnie 10000
        )
        
        # Utwórz listę na ID embeddingów do usunięcia
        ids_do_usuniecia = []
        
        # Pętla po każdym punkcie
        for punkt in wszystkie_punkty:
            # Jeśli nazwa w metadata pasuje do szukanej nazwy
            if punkt.payload.get("nazwa_zdjecia") == nazwa_zdjecia:
                # Dodaj ID do listy do usunięcia
                ids_do_usuniecia.append(punkt.id)
        
        # Jeśli znaleźliśmy embeddingi do usunięcia
        if ids_do_usuniecia:
            # Usuń każdy embedding
            for id_punktu in ids_do_usuniecia:
                klient_qdrant.delete(
                    collection_name=NAZWA_KOLEKCJI,  # z której kolekcji
                    points_selector=[id_punktu]  # które ID usunąć
                )
            
            # Wypisz komunikat o liczbie usuniętych
            print(f"[baza_danych] Usunięto {len(ids_do_usuniecia)} embedding(i) dla zdjęcia: {nazwa_zdjecia}")
        else:
            # Jeśli nic nie znaleziono - wypisz info
            print(f"[baza_danych] Nie znaleziono embeddingu dla zdjęcia: {nazwa_zdjecia}")
    except Exception as e:
        # Jeśli coś poszło nie tak - wypisz błąd
        print(f"[baza_danych] Błąd przy usuwaniu embeddingu: {e}")

def usun_wszystkie_embeddingi():
    """
    Usuń całą kolekcję - wszystkie embeddingi naraz
    Uwaga: Ta operacja nie może być cofnięta!
    """
    try:
        # Usuń całą kolekcję
        klient_qdrant.delete_collection(NAZWA_KOLEKCJI)
        
        # Wypisz komunikat
        print(f"[baza_danych] Kolekcja '{NAZWA_KOLEKCJI}' została całkowicie usunięta")
    except Exception as e:
        # Jeśli coś poszło nie tak - wypisz błąd
        print(f"[baza_danych] Błąd przy usuwaniu kolekcji: {e}")

def usun_kolekcje():
    """
    Alias (inny név) do funkcji usun_wszystkie_embeddingi
    Dla wstecznej kompatybilności ze starszym kodem
    """
    usun_wszystkie_embeddingi()