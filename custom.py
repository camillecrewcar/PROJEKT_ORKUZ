import subprocess
import json

DOSTEPNE_AKCJE = [
    "PKN.WA", "PKO.WA", "KGH.WA", "PZU.WA", "ALE.WA",
    "CDR.WA", "DNP.WA", "LPP.WA", "PEO.WA", "MBK.WA",
    "CPS.WA", "JSW.WA", "KTY.WA", "OPL.WA", "SPL.WA",
    "TPE.WA", "BDX.WA", "XTB.WA", "ENA.WA", "ING.WA"
]

NAZWY = {
    "PKN.WA": "PKN Orlen",     "PKO.WA": "PKO Bank",
    "KGH.WA": "KGHM",          "PZU.WA": "PZU",
    "ALE.WA": "Allegro",       "CDR.WA": "CD Projekt",
    "DNP.WA": "Dino",          "LPP.WA": "LPP",
    "PEO.WA": "Pekao",         "MBK.WA": "mBank",
    "CPS.WA": "Cyfrowy Polsat","JSW.WA": "JSW",
    "KTY.WA": "Kety",          "OPL.WA": "Orange",
    "SPL.WA": "Santander",     "TPE.WA": "Tauron",
    "BDX.WA": "Budimex",       "XTB.WA": "XTB",
    "ENA.WA": "Enea",          "ING.WA": "ING Bank"
}

WARTOSC_PORTFELA = 100_000
N_SYMULACJI = 10_000
N_WEZLOW = 4


def pokaz_dostepne_akcje():
    print("\nDostepne akcje WIG20:")
    for i, ticker in enumerate(DOSTEPNE_AKCJE):
        print(f"  {ticker:<12} {NAZWY[ticker]:<20}", end="")
        if (i + 1) % 2 == 0:
            print()
    print()


def wczytaj_portfel():
    wagi = {}

    print("Kalkulator VaR – portfel niestandardowy")
    print(f"Wartosc portfela: {WARTOSC_PORTFELA:,} zl")
    print("-" * 40)
    pokaz_dostepne_akcje()
    print("Wpisuj kolejne akcje i ich udzial procentowy.")
    print("Wpisz 'koniec' aby zakonczyc wprowadzanie.\n")

    while True:
        suma = sum(wagi.values()) * 100
        pozostalo = 100 - suma

        if pozostalo <= 0:
            break

        ticker = input(f"Ticker (pozostalo {pozostalo:.0f}%): ").strip().upper()

        if ticker.lower() == "koniec":
            if not wagi:
                print("Nie dodano zadnej akcji.")
                continue
            break

        if not ticker.endswith(".WA"):
            ticker = ticker + ".WA"

        if ticker not in DOSTEPNE_AKCJE:
            print(f"Nieznana akcja: {ticker}")
            continue

        if ticker in wagi:
            print(f"{ticker} jest juz w portfelu.")
            continue

        try:
            waga = float(input(f"Udzial {ticker} w %: ").strip())
        except ValueError:
            print("Podaj liczbe.")
            continue

        if waga <= 0 or waga > pozostalo:
            print(f"Udzial musi byc z przedzialu (0, {pozostalo:.0f}].")
            continue

        wagi[ticker] = waga / 100
        print(f"Dodano {ticker} ({NAZWY[ticker]}): {waga:.0f}%\n")

    # normalizacja wag do 100%
    suma = sum(wagi.values())
    wagi = {k: round(v / suma, 4) for k, v in wagi.items()}
    return wagi


def uruchom_symulacje(wagi):
    portfel_json = json.dumps(wagi)
    wyniki = []
    print(f"\nUruchamianie {N_WEZLOW} wezlow FLUX...")
    for i in range(N_WEZLOW):
        p = subprocess.run(
            ["flux", "run", "python3", "var_simulation.py",
             portfel_json, str(i * 99991),
             str(N_SYMULACJI), str(WARTOSC_PORTFELA)],
            capture_output=True, text=True
        )
        if p.stdout.strip():
            wyniki.append(p.stdout.strip())
    return wyniki


def polacz_wyniki(linie):
    var90, var95, var99, zwroty, odch = [], [], [], [], []
    for linia in linie:
        try:
            dane = json.loads(linia)
            var90.append(dane["var"]["VaR_90"])
            var95.append(dane["var"]["VaR_95"])
            var99.append(dane["var"]["VaR_99"])
            zwroty.append(dane["sredni_zwrot"])
            odch.append(dane["odch_std"])
        except Exception:
            continue
    if not var90:
        return None
    return {
        "VaR_90": round(sum(var90) / len(var90), 2),
        "VaR_95": round(sum(var95) / len(var95), 2),
        "VaR_99": round(sum(var99) / len(var99), 2),
        "sredni_zwrot": round(sum(zwroty) / len(zwroty), 2),
        "odch_std": round(sum(odch) / len(odch), 2),
        "n_symulacji": len(var90) * N_SYMULACJI
    }


def main():
    wagi = wczytaj_portfel()

    print("\nSkad portfela:")
    for ticker, waga in wagi.items():
        print(f"  {ticker:<12} {NAZWY[ticker]:<20} {waga * 100:.1f}%")
    print(f"Wartosc portfela: {WARTOSC_PORTFELA:,} zl")

    linie = uruchom_symulacje(wagi)
    wynik = polacz_wyniki(linie)

    if wynik is None:
        print("Blad: nie udalo sie obliczyc VaR.")
        return

    print("\nWyniki symulacji Monte Carlo")
    print("-" * 40)
    print(f"Liczba symulacji:  {wynik['n_symulacji']:>10,}")
    print(f"Sredni zwrot:      {wynik['sredni_zwrot']:>10.2f} zl")
    print(f"Odch. std:         {wynik['odch_std']:>10.2f} zl")
    print("-" * 40)
    print(f"VaR 90%:           {wynik['VaR_90']:>10.2f} zl")
    print(f"VaR 95%:           {wynik['VaR_95']:>10.2f} zl")
    print(f"VaR 99%:           {wynik['VaR_99']:>10.2f} zl")
    print("-" * 40)
    print(f"Interpretacja VaR 95%: z prawdopodobienstwem 95% portfel")
    print(f"nie straci wiecej niz {wynik['VaR_95']:,.2f} zl w ciagu 30 dni.")

    again = input("\nObliczyc dla innego portfela? (t/n): ").strip().lower()
    if again == "t":
        main()


if __name__ == "__main__":
    main()