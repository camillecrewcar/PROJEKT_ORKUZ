import subprocess
import json
import time
import csv

PI = 3.141592653589793

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


def uruchom_flux(wagi):
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


def uruchom_mpi(wagi):
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


def parsuj_flux(linie):
    var90, var95, var99, zwroty, odch = [], [], [], [], []
    for linia in linie:
        try:
            dane = json.loads(linia)
        except Exception:
            try:
                dane = json.loads(linia.split(": ", 1)[1])
            except Exception:
                continue
        var90.append(dane["var"]["VaR_90"])
        var95.append(dane["var"]["VaR_95"])
        var99.append(dane["var"]["VaR_99"])
        zwroty.append(dane["sredni_zwrot"])
        odch.append(dane["odch_std"])

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


def parsuj_mpi(linie):
    if not linie:
        return None
    try:
        dane = json.loads(linie[0])
        return {
            "VaR_90": dane["var"]["VaR_90"],
            "VaR_95": dane["var"]["VaR_95"],
            "VaR_99": dane["var"]["VaR_99"],
            "sredni_zwrot": dane["sredni_zwrot"],
            "odch_std": dane["odch_std"],
            "n_symulacji": dane["n_symulacji"]
        }
    except Exception:
        return None


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║         PORÓWNANIE: FLUX vs MPI                              ║
║         Value at Risk – Portfele WIG20                       ║
║         Wartość portfela: 100 000 zł                         ║
╚══════════════════════════════════════════════════════════════╝""")

    wszystkie = []

    for nazwa, wagi in PORTFELE.items():
        print(f"\n  ┌─ Portfel: {nazwa} {'─'*(47-len(nazwa))}┐")
        print(f"  │  Skład: {', '.join(f'{t}({int(w*100)}%)' for t,w in wagi.items())}")
        print(f"  │")

        # FLUX
        print(f"  │  Uruchamiam FLUX...", end="\r")
        start = time.time()
        linie_flux = uruchom_flux(wagi)
        czas_flux = round(time.time() - start, 2)
        wynik_flux = parsuj_flux(linie_flux)

        # MPI
        print(f"  │  Uruchamiam MPI... ", end="\r")
        start = time.time()
        linie_mpi = uruchom_mpi(wagi)
        czas_mpi = round(time.time() - start, 2)
        wynik_mpi = parsuj_mpi(linie_mpi)

        if wynik_flux and wynik_mpi:
            print(f"""  │
  │  {'Miara':<20} {'FLUX':>12} {'MPI':>12} {'Różnica':>12}
  │  {'─'*58}
  │  {'Symulacji łącznie':<20} {wynik_flux['n_symulacji']:>12,} {wynik_mpi['n_symulacji']:>12,}
  │  {'Czas obliczeń':<20} {czas_flux:>11.2f}s {czas_mpi:>11.2f}s {round(czas_flux-czas_mpi,2):>+11.2f}s
  │  {'Średni zwrot':<20} {wynik_flux['sredni_zwrot']:>11.0f}zł {wynik_mpi['sredni_zwrot']:>11.0f}zł
  │  {'Odch. std':<20} {wynik_flux['odch_std']:>11.0f}zł {wynik_mpi['odch_std']:>11.0f}zł
  │  {'─'*58}
  │  {'VaR 90%':<20} {wynik_flux['VaR_90']:>11.0f}zł {wynik_mpi['VaR_90']:>11.0f}zł {round(wynik_flux['VaR_90']-wynik_mpi['VaR_90'],0):>+10.0f}zł
  │  {'VaR 95%':<20} {wynik_flux['VaR_95']:>11.0f}zł {wynik_mpi['VaR_95']:>11.0f}zł {round(wynik_flux['VaR_95']-wynik_mpi['VaR_95'],0):>+10.0f}zł
  │  {'VaR 99%':<20} {wynik_flux['VaR_99']:>11.0f}zł {wynik_mpi['VaR_99']:>11.0f}zł {round(wynik_flux['VaR_99']-wynik_mpi['VaR_99'],0):>+10.0f}zł""")

            szybszy = "FLUX" if czas_flux < czas_mpi else "MPI "
            print(f"  │")
            print(f"  │  ⚡ Szybszy: {szybszy} | Różnica czasu: {abs(round(czas_flux-czas_mpi,2))}s")
            print(f"  └{'─'*60}┘")

            wszystkie.append({
                "portfel": nazwa,
                "flux_czas": czas_flux,
                "mpi_czas": czas_mpi,
                "flux_var90": wynik_flux["VaR_90"],
                "flux_var95": wynik_flux["VaR_95"],
                "flux_var99": wynik_flux["VaR_99"],
                "mpi_var90": wynik_mpi["VaR_90"],
                "mpi_var95": wynik_mpi["VaR_95"],
                "mpi_var99": wynik_mpi["VaR_99"],
                "flux_zwrot": wynik_flux["sredni_zwrot"],
                "mpi_zwrot": wynik_mpi["sredni_zwrot"],
            })

    # Podsumowanie
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    PODSUMOWANIE KOŃCOWE                      ║
╚══════════════════════════════════════════════════════════════╝
  {'Portfel':<20} {'FLUX t':>8} {'MPI t':>8} {'FLUX VaR95':>12} {'MPI VaR95':>12}
  {'─'*64}""")
    for w in wszystkie:
        szybszy = "✅" if w["flux_czas"] < w["mpi_czas"] else "  "
        print(f"  {w['portfel']:<20} {w['flux_czas']:>7.2f}s {szybszy} {w['mpi_czas']:>7.2f}s "
              f"{w['flux_var95']:>11.0f}zł {w['mpi_var95']:>11.0f}zł")

    # Zapis CSV
    with open("porownanie_flux_mpi.csv", "w", newline="", encoding="utf-8") as f:
        pola = list(wszystkie[0].keys()) if wszystkie else []
        writer = csv.DictWriter(f, fieldnames=pola)
        writer.writeheader()
        writer.writerows(wszystkie)

    print(f"\n  Wyniki zapisane do: porownanie_flux_mpi.csv")


if __name__ == "__main__":
    main()