import yfinance as yf
import pandas as pd

# Akcje z WIG20
TICKERY = [
    "PKN.WA",  # PKN Orlen
    "PKO.WA",  # PKO Bank
    "KGH.WA",  # KGHM
    "PZU.WA",  # PZU
    "ALE.WA",  # Allegro
    "CDR.WA",  # CD Projekt
    "DNP.WA",  # Dino
    "LPP.WA",  # LPP
    "PEO.WA",  # Pekao
    "MBK.WA",  # mBank
    "CPS.WA",  # Cyfrowy Polsat
    "JSW.WA",  # JSW
    "KTY.WA",  # Kęty
    "OPL.WA",  # Orange Polska
    "SPL.WA",  # Santander Bank Polska
    "TPE.WA",  # Tauron
    "BDX.WA",  # Budimex
    "XTB.WA",  # XTB
    "ENA.WA",  # Enea
    "ING.WA",  # ING Bank Śląski
]


def pobierz_dane(tickery, start="2023-01-01", end="2024-12-31"):
    print(f"Pobieram dane dla {len(tickery)} spółek...")

    ceny = {}
    for ticker in tickery:
        print(f"  Pobieram {ticker}...", end=" ")
        dane = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
        if len(dane) > 0:
            ceny[ticker] = dane["Close"].squeeze()
            print(f"OK ({len(dane)} sesji)")
        else:
            print("BRAK DANYCH")

    df = pd.DataFrame(ceny)
    df.dropna(how="all", inplace=True)

    return df


if __name__ == "__main__":
    df = pobierz_dane(TICKERY)

    print(f"\nPobrano dane: {df.shape[0]} sesji, {df.shape[1]} spółek")
    print(f"Okres: {df.index[0].date()} – {df.index[-1].date()}")
    print("\nPierwsze wiersze:")
    print(df.head())

    # Zapisz do pliku
    df.to_csv("dane/ceny_wig20.csv")
    print("\nZapisano do: dane/ceny_wig20.csv")