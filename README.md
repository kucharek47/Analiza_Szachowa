# Chess.com Analiza

Projekt to zaawansowane narzędzie napisane w Pythonie, służące do analizy partii szachowych na platformie Chess.com w czasie rzeczywistym.

Głównym celem aplikacji jest **dostarczenie informacji o najlepszym możliwym ruchu podczas rozgrywki lub oglądania**, wykorzystując lokalny silnik Stockfish. Pozwala to na uzyskanie analizy na poziomie arcymistrzowskim bez konieczności korzystania z wbudowanych, płatnych narzędzi analitycznych serwisu.

## 🚀 Funkcjonalności

* **Żywa analiza:** Automatyczne wykrywanie i pobieranie ruchów z interfejsu Chess.com przy użyciu Selenium.
* **Lokalna Analiza Stockfish:** Wykorzystuje binarkę silnika Stockfish do obliczania najlepszych posunięć w czasie rzeczywistym.
* **Translacja Ruchów:** Tłumaczenie notacji szachowej (SAN) na język polski (np. "skoczek z g1 na f3").
* **Obsługa Sesji:** Możliwość załadowania ciasteczek (`cookies.json`) w celu utrzymania sesji zalogowanego użytkownika.
* **Tryb "Tajna Wersja":** Specjalny tryb wyświetlania, który ukrywa najlepszy ruch w ciągu losowych znaków alfanumerycznych, utrudniając osobom postronnym zorientowanie się, że korzystasz z asystenta.

## 🛠️ Wymagania i Instalacja

### 1. Biblioteki Python
Zainstaluj wymagane zależności:

```bash
pip install selenium chess
```
### 2. Chrome
Zainstaluj wymagane zależności:

https://googlechromelabs.github.io/chrome-for-testing/