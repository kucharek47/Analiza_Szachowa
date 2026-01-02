import random
import string
from terminal_najlepszy_ruch import analizer

class TajnaWersja(analizer):
    def pokaz_wynik(self, naj, score):
        losowy_tekst1 = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        losowy_tekst2 = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        sekretna_wiadomosc = f"{losowy_tekst1}{random.choice(string.digits)}{naj['san']}{losowy_tekst2}"

        print(sekretna_wiadomosc)

if __name__ == "__main__":
    app = TajnaWersja()
    app.main()