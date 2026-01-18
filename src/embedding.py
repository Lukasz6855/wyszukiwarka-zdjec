# embedding.py

import openai  # Importujemy bibliotekę OpenAI do generowania embeddingów
import numpy as np  # Importujemy NumPy do operacji na tablicach

def generuj_embedding(opis: str, model: str) -> np.ndarray:
    """
    Funkcja generuje embedding dla podanego opisu przy użyciu wybranego modelu OpenAI.
    
    :param opis: Opis, dla którego chcemy wygenerować embedding.
    :param model: Model OpenAI, który ma być użyty do generacji embeddingu.
    :return: Tablica NumPy reprezentująca embedding.
    """
    # Wywołanie API OpenAI w celu uzyskania embeddingu
    odpowiedz = openai.Embedding.create(
        input=opis,
        model=model
    )
    
    # Ekstrakcja embeddingu z odpowiedzi
    embedding = odpowiedz['data'][0]['embedding']
    
    # Konwersja embeddingu na tablicę NumPy
    return np.array(embedding)

def przygotuj_dane_do_bazy(embedding: np.ndarray, id_zdjecia: str) -> dict:
    """
    Funkcja przygotowuje dane do zapisania w bazie danych QDrant.
    
    :param embedding: Tablica NumPy reprezentująca embedding.
    :param id_zdjecia: Unikalny identyfikator zdjęcia.
    :return: Słownik z danymi do zapisania w bazie.
    """
    # Przygotowanie słownika z danymi
    dane = {
        "id": id_zdjecia,
        "embedding": embedding.tolist()  # Konwersja tablicy NumPy na listę
    }
    return dane