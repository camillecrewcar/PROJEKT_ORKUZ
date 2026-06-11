import subprocess
import json
import time
import csv

PORTFELE = {
    "Zdywersyfikowany": {
        "PKO.WA": 0.15,
        "PKN.WA": 0.15,
        "KGH.WA": 0.10,
        "PZU.WA": 0.10,
        "ALE.WA": 0.10,
        "CDR.WA": 0.10,
        "DNP.WA": 0.10,
        "LPP.WA": 0.10,
        "PEO.WA": 0.05,
        "MBK.WA": 0.05,
    },
    "Bankowy": {
        "PKO.WA": 0.30,
        "PEO.WA": 0.25,
        "MBK.WA": 0.20,
        "SPL.WA": 0.15,
        "ING.WA": 0.10,
    },
    "Surowcowy": {
        "KGH.WA": 0.40,
        "PKN.WA": 0.35,
        "JSW.WA": 0.25,
    },
    "Technologiczny": {
        "CDR.WA": 0.35,
        "ALE.WA": 0.35,
        "XTB.WA": 0.30,
    },
}

WARTOSC_PORTFELA = 100_000
N_SYMULACJI = 10_000
N_WEZLOW = 4


def uruchom_flux(nazwa, wagi):
    portfel_json = json.dumps(wagi)
    wyniki_linie = []
    for i in range(N_WEZLOW):
        p = subprocess.run(
            ["flux", "run", "python3", "var_simulation.py",
             portfel_json,
             str(i * 99991),
             str(N_SYMULACJI),
             str(WARTOSC_PORTFELA)],
            capture_output=True, text=True
        )
        if p.stdout.strip():
            wyniki_linie.append(p.stdout.strip())
    return wyniki_linie


def polacz_wyniki(linie):
    var90_lista, var95_lista, var99_lista = [], [], []
    zwroty, odch = [], []

    for linia in linie:
        linia = linia.strip()
        if not linia:
            continue
        try:
            dane = json.loads(linia)
        except Exception:
            try:
                dane = json.loads(linia.split(": ", 1)[1])
            except Exception:
                continue

        var90_lista.append(dane["var"]["VaR_90"])
        var95_lista.append(dane["var"]["VaR_95"])
        var99_lista.append(dane["var"]["VaR_99"])
        zwroty.append(dane["sredni_zwrot"])
        odch.append(dane["odch_std"])

    if not var90_lista:
        return None

    return {
        "VaR_90": round(sum(var90_lista) / len(var90_lista), 2),
        "VaR_95": round(sum(var95_lista) / len(var95_lista), 2),
        "VaR_99": round(sum(var99_lista) / len(var99_lista), 2),
        "sredni_zwrot": round(sum(zwroty) / len(zwroty), 2),
        "odch_std": round(sum(odch) / len(odch), 2),
        "n_symulacji": len(var90_lista) * N_SYMULACJI
    }


def main():
    print("Value at Risk – symulacja Monte Carlo, portfele WIG20")
    print(f"Wartosc portfela: {WARTOSC_PORTFELA:,} zl, wezly FLUX: {N_WEZLOW}, symulacji na wezel: {N_SYMULACJI:,}")
    print("=" * 60)

    wszystkie_wyniki = []

    for nazwa, wagi in PORTFELE.items():
        sklad = ", ".join(f"{t}({int(w*100)}%)" for t, w in wagi.items())
        print(f"\nPortfel: {nazwa}")
        print(f"Sklad:   {sklad}")

        start = time.time()
        linie = uruchom_flux(nazwa, wagi)
        czas = round(time.time() - start, 2)

        wynik = polacz_wyniki(linie)

        if wynik is None:
            print("Blad: brak wynikow.")
            continue

        print(f"Symulacji lacznie: {wynik['n_symulacji']:,}")
        print(f"Czas obliczen:     {czas:.2f} s")
        print(f"Sredni zwrot:      {wynik['sredni_zwrot']:.2f} zl")
        print(f"Odch. std:         {wynik['odch_std']:.2f} zl")
        print(f"VaR 90%:           {wynik['VaR_90']:.2f} zl")
        print(f"VaR 95%:           {wynik['VaR_95']:.2f} zl")
        print(f"VaR 99%:           {wynik['VaR_99']:.2f} zl")

        wszystkie_wyniki.append({
            "portfel": nazwa,
            "sklad": ", ".join(wagi.keys()),
            "n_symulacji": wynik["n_symulacji"],
            "czas_s": czas,
            "sredni_zwrot": wynik["sredni_zwrot"],
            "odch_std": wynik["odch_std"],
            "VaR_90": wynik["VaR_90"],
            "VaR_95": wynik["VaR_95"],
            "VaR_99": wynik["VaR_99"],
        })

    print("\n" + "=" * 60)
    print("Podsumowanie")
    print(f"{'Portfel':<20} {'VaR 90%':>12} {'VaR 95%':>12} {'VaR 99%':>12} {'Sr. zwrot':>12}")
    print("-" * 60)
    for w in wszystkie_wyniki:
        print(f"{w['portfel']:<20} {w['VaR_90']:>12.0f} {w['VaR_95']:>12.0f} "
              f"{w['VaR_99']:>12.0f} {w['sredni_zwrot']:>12.0f}")

    with open("wyniki_var.csv", "w", newline="", encoding="utf-8") as f:
        pola = ["portfel", "sklad", "n_symulacji", "czas_s",
                "sredni_zwrot", "odch_std", "VaR_90", "VaR_95", "VaR_99"]
        writer = csv.DictWriter(f, fieldnames=pola)
        writer.writeheader()
        writer.writerows(wszystkie_wyniki)

    print("\nWyniki zapisane do wyniki_var.csv")


if __name__ == "__main__":
    main()