import subprocess
import json
import time
import csv

# Portfele do porównania
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

WARTOSC_PORTFELA = 100_000   # 100 000 zł
N_SYMULACJI     = 10_000     # symulacji na węzeł
N_WEZLOW        = 4          # węzły FLUX


def uruchom_flux(nazwa, wagi):
    """Uruchamia symulację MPI przez FLUX"""
    portfel_json = json.dumps(wagi)

    p = subprocess.run(
        ["flux", "run", "-n", str(N_WEZLOW),
         "python3", "var_simulation_mpi.py",
         portfel_json,
         str(N_SYMULACJI),
         str(WARTOSC_PORTFELA)],
        capture_output=True, text=True
    )

    linie = []
    if p.stdout.strip():
        linie.append(p.stdout.strip())
    return linie

def polacz_wyniki(linie):
    """Łączy wyniki ze wszystkich węzłów"""
    var90_lista, var95_lista, var99_lista = [], [], []
    zwroty, odch = [], []

    for linia in linie:
        linia = linia.strip()
        if not linia:
            continue
        try:
            # Spróbuj sparsować bezpośrednio
            dane = json.loads(linia)
        except Exception:
            # Jeśli nie wyszło - usuń prefix "0: " od FLUXa
            try:
                linia = linia.split(": ", 1)[1]
                dane = json.loads(linia)
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
    print("║         VALUE AT RISK – SYMULACJA MPI                        ║")

    wszystkie_wyniki = []

    for nazwa, wagi in PORTFELE.items():
        print(f"  Symuluje portfel: {nazwa}...")
        print(f"  Skład: {', '.join(f'{t}({int(w*100)}%)' for t,w in wagi.items())}")

        start = time.time()
        linie = uruchom_flux(nazwa, wagi)
        czas = round(time.time() - start, 2)

        wynik = polacz_wyniki(linie)

        if wynik is None:
            print(f"  BŁĄD – brak wyników!\n")
            continue

        print(f"""
  ┌─────────────────────────────────────────┐
  │  Symulacji łącznie: {wynik['n_symulacji']:>10,}           │
  │  Czas obliczeń:     {czas:>10.2f} s         │
  │  Średni zwrot:      {wynik['sredni_zwrot']:>10.2f} zł        │
  │  Odch. std:         {wynik['odch_std']:>10.2f} zł        │
  ├─────────────────────────────────────────┤
  │  VaR 90%:           {wynik['VaR_90']:>10.2f} zł        │
  │  VaR 95%:           {wynik['VaR_95']:>10.2f} zł        │
  │  VaR 99%:           {wynik['VaR_99']:>10.2f} zł        │
  └─────────────────────────────────────────┘
""")

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

    # Podsumowanie
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    PODSUMOWANIE KOŃCOWE                      ║
╚══════════════════════════════════════════════════════════════╝""")
    print(f"\n  {'Portfel':<20} {'VaR 90%':>12} {'VaR 95%':>12} {'VaR 99%':>12} {'Śr. zwrot':>12}")
    print("  " + "─" * 70)
    for w in wszystkie_wyniki:
        print(f"  {w['portfel']:<20} {w['VaR_90']:>11.0f}zł {w['VaR_95']:>11.0f}zł "
              f"{w['VaR_99']:>11.0f}zł {w['sredni_zwrot']:>11.0f}zł")

    # Zapis CSV
    with open("wyniki_var.csv", "w", newline="", encoding="utf-8") as f:
        pola = ["portfel", "sklad", "n_symulacji", "czas_s",
                "sredni_zwrot", "odch_std", "VaR_90", "VaR_95", "VaR_99"]
        writer = csv.DictWriter(f, fieldnames=pola)
        writer.writeheader()
        writer.writerows(wszystkie_wyniki)

    print("\n  Wyniki zapisane do: wyniki_var.csv")


if __name__ == "__main__":
    main()