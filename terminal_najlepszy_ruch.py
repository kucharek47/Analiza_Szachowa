import json
import time
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chess
import chess.engine
import re
import os

CHROMEDRIVER_PATH = "chromedriver-win64/chromedriver-win64/chromedriver.exe"
CHROMIUM_PATH = "chrome-win64/chrome-win64/chrome.exe"

nazwa_uzytkownika = input("Nazwa uzytkownika: ")

STOCKFISH_PATH = "stockfish/stockfish-windows-x86-64-avx2.exe"


class analizer:
    def __init__(self):
        self.silnik2 = None
        self.silnik = threading.Lock()
        self.id_gry = None
        self.analiza = False

    def setup_chrome(self):
        options = Options()
        options.binary_location = CHROMIUM_PATH
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        service = Service(CHROMEDRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver

    def load_cookies(self, driver):
        try:
            with open("cookies.json", "r", encoding="utf-8") as f:
                cookies = json.load(f)

            for c in cookies:
                cookie_data = {
                    "name": c["name"],
                    "value": c["value"]
                }
                if "domain" in c:
                    cookie_data["domain"] = c["domain"]
                if "path" in c:
                    cookie_data["path"] = c["path"]
                if "secure" in c:
                    cookie_data["secure"] = c["secure"]
                try:
                    driver.add_cookie(cookie_data)
                except Exception as e:
                    continue

            driver.refresh()
            return True
        except Exception as e:
            print(f"Błąd ładowania cookies: {e}")
            return False

    def pobieranie_id(self, driver):
        try:
            akt_url = driver.current_url
            if "/live/" in akt_url:
                return akt_url.split("/live/")[-1].split("/")[0]
            elif "/game/" in akt_url:
                return akt_url.split("/game/")[-1].split("/")[0]
            elif "/analysis/" in akt_url:
                return akt_url.split("/analysis/")[-1].split("/")[0]

            try:
                element = driver.find_element(By.CSS_SELECTOR, "[data-game-id]")
                return element.get_attribute("data-game-id")
            except:
                pass

            return akt_url
        except:
            return None

    def pobioeranie_ruchow(self, driver):
        try:
            wait = WebDriverWait(driver, 2)
            lista_ruchow = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "wc-simple-move-list"))
            )
            lista_ruchow2 = []

            for element in lista_ruchow.find_elements(By.CSS_SELECTOR, ".node"):
                try:
                    span = element.find_element(By.CSS_SELECTOR, ".node-highlight-content")
                    tekst_ruchu = span.get_attribute("textContent").strip()
                    tekst_ruchu = re.sub(r'\s+', ' ', tekst_ruchu).strip()

                    figury = span.find_elements(By.CSS_SELECTOR, "[data-figurine]")

                    if figury:
                        for figura in figury:
                            data = figura.get_attribute("data-figurine")
                            figurine_text = figura.get_attribute("textContent").strip()

                            if figurine_text in tekst_ruchu:
                                tekst_ruchu = tekst_ruchu.replace(figurine_text, data, 1)

                    if tekst_ruchu and not re.match(r'^\d+\.$', tekst_ruchu):
                        lista_ruchow2.append(tekst_ruchu)

                except Exception as e:
                    continue

            return lista_ruchow2

        except Exception as e:
            return []

    def stop_analizy(self):
        with self.silnik:
            if self.silnik2 and self.analiza:
                try:
                    self.silnik2.quit()
                    self.silnik2 = None
                    self.analiza = False
                    print("🛑 Zatrzymano analizę silnika")
                except:
                    pass

    def stockfish_ruch(self, board, time_limit=2.5):
        try:
            if not os.path.exists(STOCKFISH_PATH):
                return None, None

            with self.silnik:
                self.analiza = True
                try:
                    if not self.silnik2:
                        self.silnik2 = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
                    wynik = self.silnik2.analyse(
                        board,
                        chess.engine.Limit(time=time_limit),
                        info=chess.engine.INFO_PV
                    )

                    naj = wynik["pv"][0] if wynik.get("pv") else None
                    score = wynik.get("score", chess.engine.PovScore(chess.engine.Cp(0), board.turn))

                    if naj:
                        san_move = board.san(naj)
                        polish_move = self.tlumacz(naj, board)

                        return {
                            'uci': naj.uci(),
                            'san': san_move,
                            'polish': polish_move,
                            'score': score
                        }, score
                finally:
                    self.analiza = False

        except Exception as e:
            print(f"Błąd silnika: {e}")
            with self.silnik:
                self.analiza = False
                if self.silnik2:
                    try:
                        self.silnik2.quit()
                    except:
                        pass
                    self.silnik2 = None
            return None, None

    def tlumacz(self, ruch, szachownica):
        piece_names = {
            chess.KING: "król",
            chess.QUEEN: "hetman",
            chess.ROOK: "wieża",
            chess.BISHOP: "goniec",
            chess.KNIGHT: "koń",
            chess.PAWN: "pion"
        }

        z = chess.square_name(ruch.from_square)
        na = chess.square_name(ruch.to_square)
        nazwa_szachowa = szachownica.piece_at(ruch.from_square)

        if not nazwa_szachowa:
            return f"ruch z {z} na {na}"

        piece_name = piece_names.get(nazwa_szachowa.piece_type, "figura")

        if ruch == chess.Move.from_uci("e1g1") or ruch == chess.Move.from_uci("e8g8"):
            return "roszada krótka"
        elif ruch == chess.Move.from_uci("e1c1") or ruch == chess.Move.from_uci("e8c8"):
            return "roszada długa"
        elif ruch.promotion:
            return f"{piece_name} z {z} na {na} z promocją na {piece_names.get(ruch.promotion, "hetman")}"
        elif szachownica.is_capture(ruch):
            capture = szachownica.piece_at(ruch.to_square)
            return f"{piece_name} z {z} bije {piece_names.get(capture.piece_type if capture else chess.PAWN, "figura")} na {na}"
        else:
            return f"{piece_name} z {z} na {na}"

    def naprawa(self, ruchy):
        szachownica = chess.Board()
        lista = []

        for m, ruch in enumerate(ruchy):
            try:
                ruch = ruch.strip()
                if not ruch:
                    continue

                if ruch == "O-O":
                    ruch = chess.Move.from_uci("e1g1" if szachownica.turn else "e8g8")
                elif ruch == "O-O-O":
                    ruch = chess.Move.from_uci("e1c1" if szachownica.turn else "e8c8")
                else:
                    try:
                        if "=" in ruch:
                            ruch = re.sub(r'=([QRBN])', r'=\1', ruch)
                            ruch = re.sub(r'=H', '=N', ruch)

                        ruch = szachownica.parse_san(ruch)
                    except ValueError as e:
                        lista_alt = [
                            ruch.replace("=H", "=N"),
                            ruch.replace("H", "N"),
                            ruch.replace("+", ""),
                            ruch.replace("#", ""),
                        ]

                        dopasowanie = False
                        for alt in lista_alt:
                            try:
                                ruch = szachownica.parse_san(alt)
                                dopasowanie = True
                                break
                            except:
                                continue

                        if not dopasowanie:
                            print(f"Nie można sparsować ruchu: '{ruch}' (błąd: {e})")
                            continue

                if ruch in szachownica.legal_moves:
                    szachownica.push(ruch)
                    lista.append({
                        'move_number': (m // 2) + 1,
                        'color': 'białe' if m % 2 == 0 else 'czarne',
                        'san': ruch,
                        'uci': ruch.uci(),
                        'polish': self.tlumacz(ruch, chess.Board().copy())
                    })
                else:
                    print(f"Nielegalny ruch: {ruch}")
                    break

            except Exception as e:
                print(f"Błąd przetwarzania ruchu '{ruch}': {e}")
                continue

        return lista, szachownica

    def main(self):
        print("=== ANALIZATOR RUCHÓW CHESS.COM ===")

        if not os.path.exists(STOCKFISH_PATH):
            print(f"⚠️ UWAGA: Nie znaleziono silnika Stockfish: {STOCKFISH_PATH}")
            return

        driver = self.setup_chrome()

        try:
            print("Łączenie z Chess.com...")
            driver.get(f"https://www.chess.com/member/{nazwa_uzytkownika}")

            if not self.load_cookies(driver):
                print("Kontynuacja bez cookies...")

            liczba_ruchow = 0
            lista = []

            print("\n🔍 Monitorowanie ruchów... (Ctrl+C aby zatrzymać)")
            print("Przejdź do gry na Chess.com")

            while True:
                try:
                    if driver.current_url == f"https://www.chess.com/member/{nazwa_uzytkownika}":
                        link = driver.find_elements(By.LINK_TEXT, "Oglądaj")
                        if link:
                            driver.get(link[0].get_attribute("href"))
                        else:
                            time.sleep(1)
                            driver.refresh()
                            continue

                    if driver.find_elements(By.CSS_SELECTOR, "div.game-over-modal-content"):
                        driver.get(f"https://www.chess.com/member/{nazwa_uzytkownika}")
                        continue
                    id = self.pobieranie_id(driver)
                    if id != self.id_gry:
                        if id:
                            print(f"\n🎯 Wykryto nową grę: {id}")
                            self.id_gry = id
                            liczba_ruchow = 0
                            lista = []
                            self.stop_analizy()

                    lista_ruchow = self.pobioeranie_ruchow(driver)

                    if lista_ruchow != lista or len(lista_ruchow) > liczba_ruchow:
                        if len(lista_ruchow) > liczba_ruchow:
                            self.stop_analizy()

                        print(f"\nAktualizacja! Ruchów: {len(lista_ruchow)}")
                        liczba_ruchow = len(lista_ruchow)
                        lista = lista_ruchow.copy()

                        if lista_ruchow:
                            lista2, szachownica = self.naprawa(lista_ruchow)
                            if lista2:
                                print("\nOstatnie ruchy:")
                                for move in lista2[-3:]:
                                    print(f"  {move['move_number']}. {move['color']}: {move['polish']}")
                                if not szachownica.is_game_over():
                                    print(
                                        f"\nAnalizuję pozycję dla: {'białych' if szachownica.turn else 'czarnych'}")
                                    def analyze_position():
                                        naj, score = self.stockfish_ruch(szachownica,
                                                                                    time_limit=1.0)
                                        if naj:
                                            self.pokaz_wynik(naj, score)
                                    analiza_zadanie = threading.Thread(target=analyze_position)
                                    analiza_zadanie.daemon = True
                                    analiza_zadanie.start()

                                else:
                                    if szachownica.is_checkmate():
                                        print(f"Koniec gry: Mat! Wygrywają {"Czarne" if szachownica.turn else "Białe"}")
                                    elif szachownica.is_stalemate():
                                        print("Koniec gry: Remis przez pat!")
                                    elif szachownica.is_insufficient_material():
                                        print("Koniec gry: Remis przez brak materiału!")

                        print("\n" + "=" * 50)

                    time.sleep(0.2)

                except Exception as e:
                    print(f"\nBłąd w głównej pętli: {e}")
                    time.sleep(1)

        except KeyboardInterrupt:
            print("\n\nZatrzymywanie...")
        except Exception as e:
            print(f"\nBłąd krytyczny: {e}")
        finally:
            if self.silnik2:
                try:
                    self.silnik2.quit()
                except:
                    pass
            driver.quit()
            print("Przeglądarka zamknięta.")
    def pokaz_wynik(self, naj, score):
        print("\n" + "💡" * 30)
        print(f"   NAJLEPSZY RUCH: {naj['polish']}")
        print(f"   Notacja: {naj['san']}")
        if hasattr(score, 'relative'):
            score_value = score.relative.score(mate_score=1000)
            if score_value:
                print(f"   Ocena: {score_value / 100:.1f}")
        print("💡" * 30)


if __name__ == "__main__":
    start = analizer()
    start.main()