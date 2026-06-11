import json
import time
import csv
from var_simulation import wczytaj_dane, oblicz_zwroty, symuluj_portfel, oblicz_var
import numpy as np

PORTFELE = {
    "Zdywersyfikowany": {"PKO.WA": 0.15, "PKN.WA": 0.15, "KGH.WA": 0.10,
                         "PZU.WA": 0.10, "ALE.WA": 0.10, "CDR.WA": 0.10,
                         "DNP.WA": 0.10, "LPP.WA": 0.10, "PEO.WA": 0.05, "MBK.WA": 0.05},
    "Bankowy":          {"PKO.WA": 0.30, "PEO.WA": 0.25, "MBK.WA": 0.20,
                         "SPL.WA": 0.15, "ING.WA": 0.10},
    "Surowcowy":        {"KGH.WA": 0.40, "PKN.WA": 0.35, "JSW.WA": 0.25},
    "Technologiczny":   {"CDR.WA": 0.35, "ALE.WA": 0.35, "XTB.WA": 0.30},
}

WARTOSC_PORTFELA = 100_000
N_SYMULACJI = 40_000


def main():
    print("Value at Risk – obliczenia sekwencyjne (bez rownoleglosci)")
    print(f"Wartosc portfela: {WARTOSC_PORTFELA:,} zl, symulacji: {N_SYMULACJI:,}")
    print("=" * 60)

    ceny = wczytaj_dane()
    zwroty = oblicz_zwroty(ceny)

    wszystkie_wyniki = []

    for nazwa, wagi in PORTFELE.items():
        sklad = ", ".join(f"{t}({int(w*100)}%)" for t, w in wagi.items())
        print(f"\nPortfel: {nazwa}")
        print(f"Sklad:   {sklad}")

        start = time.time()
        wyniki = symuluj_portfel(zwroty, wagi, n_symulacji=N_SYMULACJI, seed=42)
        var = oblicz_var(wyniki, WARTOSC_PORTFELA)
        czas = round(time.time() - start, 2)

        sredni_zwrot = round(float(np.mean(wyniki)) * WARTOSC_PORTFELA, 2)
        odch_std = round(float(np.std(wyniki)) * WARTOSC_PORTFELA, 2)

        print(f"Symulacji lacznie: {N_SYMULACJI:,}")
        print(f"Czas obliczen:     {czas:.2f} s")
        print(f"Sredni zwrot:      {sredni_zwrot:.2f} zl")
        print(f"Odch. std:         {odch_std:.2f} zl")
        print(f"VaR 90%:           {var['VaR_90']:.2f} zl")
        print(f"VaR 95%:           {var['VaR_95']:.2f} zl")
        print(f"VaR 99%:           {var['VaR_99']:.2f} zl")

        wszystkie_wyniki.append({
            "portfel": nazwa,
            "sklad": ", ".join(wagi.keys()),
            "n_symulacji": N_SYMULACJI,
            "czas_s": czas,
            "sredni_zwrot": sredni_zwrot,
            "odch_std": odch_std,
            "VaR_90": var["VaR_90"],
            "VaR_95": var["VaR_95"],
            "VaR_99": var["VaR_99"],
        })

    print("\n" + "=" * 60)
    print("Podsumowanie")
    print(f"{'Portfel':<20} {'Czas [s]':>10} {'VaR 90%':>12} {'VaR 95%':>12} {'VaR 99%':>12}")
    print("-" * 70)
    for w in wszystkie_wyniki:
        print(f"{w['portfel']:<20} {w['czas_s']:>10.2f} {w['VaR_90']:>12.0f} "
              f"{w['VaR_95']:>12.0f} {w['VaR_99']:>12.0f}")

    with open("wyniki_sequential.csv", "w", newline="", encoding="utf-8") as f:
        pola = ["portfel", "sklad", "n_symulacji", "czas_s",
                "sredni_zwrot", "odch_std", "VaR_90", "VaR_95", "VaR_99"]
        writer = csv.DictWriter(f, fieldnames=pola)
        writer.writeheader()
        writer.writerows(wszystkie_wyniki)

    print("\nWyniki zapisane do wyniki_sequential.csv")


if __name__ == "__main__":
    main()