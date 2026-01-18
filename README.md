# 🖼️ Znajdywacz zdjęć na podstawie opisu

Inteligentna aplikacja do zarządzania i wyszukiwania zdjęć przy użyciu AI, która automatycznie generuje opisy obrazów i umożliwia semantyczne wyszukiwanie w naturalnym języku.

## 📋 Opis projektu

Aplikacja wykorzystuje modele OpenAI Vision do automatycznego generowania szczegółowych opisów przesłanych zdjęć, a następnie konwertuje te opisy na embeddingi wektorowe przechowywane w bazie Qdrant. Dzięki temu możesz wyszukiwać zdjęcia używając naturalnego języka, np. "zdjęcie kota na kanapie" lub "zachód słońca nad morzem".

## ✨ Funkcjonalności

### Przetwarzanie zdjęć
- 📤 **Przesyłanie wielu zdjęć** jednocześnie (JPG, JPEG, PNG)
- 🤖 **Automatyczne generowanie opisów** przy użyciu OpenAI Vision API
- 🔄 **Wykrywanie duplikatów** - aplikacja ostrzega przed dodaniem zdjęcia o tej samej nazwie
- 💾 **Automatyczny zapis** przetworzonych zdjęć lokalnie
- 🎉 **Animowany komunikat** po zakończeniu przetwarzania

### Wyszukiwanie
- 🔍 **Semantyczne wyszukiwanie** - znajdź zdjęcia opisując czego szukasz
- 🎯 **Ranking wyników** - każdy wynik ma procent dopasowania
- 🖼️ **Podgląd miniaturek** z pełnymi opisami wygenerowanymi przez AI

### Zarządzanie zdjęciami
- 📂 **Lista wszystkich zdjęć** z miniaturkami obok nazw plików
- ✅ **Zaznaczanie i usuwanie** wybranych zdjęć
- 🗑️ **Usuwanie wszystkich** zdjęć i embeddingów jednym kliknięciem
- 🔄 **Synchronizacja** z bazą Qdrant

### Konfiguracja
- 🔑 **Bezpieczne wprowadzanie** klucza API OpenAI
- 🎛️ **Wybór modelu AI**:
  - Model prosty: `gpt-4o-mini` (tańszy, szybszy)
  - Model średni: `gpt-4o` (balans jakości i ceny)
  - Model zaawansowany: `gpt-4-turbo` (najlepsza jakość)
- 💰 **Oszacowanie kosztów** przed przetworzeniem

## 🏗️ Struktura projektu

```
znajdywacz_zdjec_v4/
├── src/
│   ├── main.py                 # Główna aplikacja Streamlit z UI
│   ├── config.py               # Konfiguracja modeli i kluczy API
│   ├── api_openai.py           # Komunikacja z OpenAI API
│   ├── baza_danych.py          # Obsługa bazy Qdrant (embeddingi)
│   ├── przetwarzanie_zdjec.py  # Przetwarzanie i zapis zdjęć
│   ├── embedding.py            # Generowanie embeddingów
│   └── utils.py                # Funkcje pomocnicze (koszty)
├── zdjecia_przetworzone/       # Zapisane zdjęcia (tworzone automatycznie)
├── uploaded_images/            # Zdjęcia z uploadu (opcjonalne)
├── requirements.txt            # Zależności Python
├── .env.example                # Szablon konfiguracji
├── .gitignore                  # Wykluczenia dla Git
└── README.md                   # Ten plik
```

## 🚀 Instalacja i uruchomienie

### Wymagania
- Python 3.8+
- Klucz API OpenAI ([uzyskaj tutaj](https://platform.openai.com/api-keys))
- Konto Qdrant Cloud ([zarejestruj się](https://cloud.qdrant.io/))

### Krok 1: Klonowanie repozytorium
```bash
git clone <url-repozytorium>
cd znajdywacz_zdjec_v4
```

### Krok 2: Instalacja zależności
```bash
pip install -r requirements.txt
```

### Krok 3: Konfiguracja zmiennych środowiskowych
1. Skopiuj plik `.env.example` jako `.env`:
```bash
cp .env.example .env
```

2. Edytuj plik `.env` i uzupełnij swoje klucze:
```env
OPENAI_API_KEY=sk-twoj-klucz-openai
QDRANT_URL=https://twoja-instancja.qdrant.cloud
QDRANT_API_KEY=twoj-klucz-qdrant
```

### Krok 4: Uruchomienie aplikacji
```bash
streamlit run src/main.py
```

Aplikacja uruchomi się w przeglądarce pod adresem `http://localhost:8501`

## 📖 Instrukcja użycia

### 1. Pierwsza konfiguracja
1. Wprowadź swój **klucz OpenAI** w pasku bocznym
2. Wybierz **model AI** (zalecany: gpt-4o-mini dla testów)

### 2. Dodawanie zdjęć
1. Kliknij "**Browse files**" w sekcji "📸 Wczytaj zdjęcia"
2. Wybierz jedno lub więcej zdjęć (JPG, JPEG, PNG)
3. Kliknij "**Przetwórz zdjęcia**"
4. Jeśli aplikacja wykryje duplikaty, zdecyduj czy pominąć czy przetwórz jako nowe
5. Poczekaj na animowany komunikat o zakończeniu 🎉

### 3. Wyszukiwanie zdjęć
1. Przejdź do zakładki "**Wyszukiwanie**"
2. Wpisz opis w naturalnym języku, np.:
   - "kot na kanapie"
   - "zachód słońca"
   - "osoba w czerwonej kurtce"
3. Zobacz wyniki z procentem dopasowania

### 4. Zarządzanie zdjęciami
1. Przejdź do zakładki "**Zarządzanie zdjęciami**"
2. Zobacz listę wszystkich zdjęć z miniaturkami
3. Zaznacz zdjęcia do usunięcia lub użyj "🗑️ Usuń wszystkie"

## 💰 Szacowanie kosztów

Aplikacja automatycznie oszacuje koszt przed przetworzeniem zdjęć:
- **Model prosty (gpt-4o-mini)**: ~0.001 PLN/zdjęcie
- **Model średni (gpt-4o)**: ~0.05 PLN/zdjęcie  
- **Model zaawansowany (gpt-4-turbo)**: ~0.10 PLN/zdjęcie

Koszty obejmują:
- Generowanie opisów (Vision API)
- Tworzenie embeddingów (text-embedding-3-small)

## 🔒 Bezpieczeństwo

### ⚠️ WAŻNE - Przed pushowaniem na Git:

1. **Nigdy nie commituj pliku `.env`** - zawiera wrażliwe klucze API
2. Plik `.gitignore` automatycznie wyklucza:
   - `.env` (klucze API)
   - `zdjecia_przetworzone/` (dane użytkowników)
   - `uploaded_images/` (tymczasowe pliki)
   - `__pycache__/` (cache Python)

3. Jeśli **przypadkowo** dodałeś `.env` do repozytorium:
```bash
# Usuń plik z historii Git
git rm --cached .env
git commit -m "Remove .env from tracking"

# NATYCHMIAST wygeneruj nowe klucze API!
```

## 🛠️ Technologie

- **Frontend**: Streamlit 1.39.0
- **AI/ML**: OpenAI API (Vision + Embeddings)
- **Baza wektorowa**: Qdrant Cloud
- **Język**: Python 3.8+

## 🐛 Rozwiązywanie problemów

### Błąd: "Brak klucza OpenAI"
✅ Sprawdź czy plik `.env` istnieje i zawiera prawidłowy klucz

### Błąd: "403 Forbidden" (Qdrant)
✅ Sprawdź poprawność `QDRANT_URL` i `QDRANT_API_KEY` w `.env`

### Aplikacja nie wyświetla zdjęć
✅ Upewnij się, że folder `zdjecia_przetworzone/` istnieje (tworzy się automatycznie)

### Wysokie koszty
✅ Użyj modelu `gpt-4o-mini` zamiast droższych wariantów

## 📝 Changelog

### v4 (aktualna)
- ✨ Dodano animowany komunikat po przetworzeniu zdjęć
- 🖼️ Dodano miniaturki w zakładce zarządzania
- 🔒 Utworzono `.gitignore` i `.env.example`

### v3
- 🔄 Aktualizacja kluczy Qdrant w `.env`

### v2
- 📊 Przeniesienie kontrolek do paska bocznego
- 🔍 Wykrywanie duplikatów zdjęć
- 🗑️ Zarządzanie zapisanymi zdjęciami

### v1
- 🎉 Pierwsza wersja aplikacji

## 📄 Licencja

Projekt dostępny na licencji MIT.

## 👤 Autor

Kurs "Od zera do AI" - Moduł 8

---

**Uwaga**: Pamiętaj o regularnej regeneracji kluczy API i nigdy nie udostępniaj ich publicznie!
