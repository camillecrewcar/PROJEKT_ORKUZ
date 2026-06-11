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
    print("Porownanie FLUX vs MPI – Value at Risk, portfele WIG20")
    print(f"Wartosc portfela: {WARTOSC_PORTFELA:,} zl, symulacji na wezel: {N_SYMULACJI:,}")
    print("=" * 70)

    wszystkie = []

    for nazwa, wagi in PORTFELE.items():
        sklad = ", ".join(f"{t}({int(w*100)}%)" for t, w in wagi.items())
        print(f"\nPortfel: {nazwa}")
        print(f"Sklad:   {sklad}")
        print("-" * 70)

        start = time.time()
        linie_flux = uruchom_flux(wagi)
        czas_flux = round(time.time() - start, 2)
        wynik_flux = parsuj_flux(linie_flux)

        start = time.time()
        linie_mpi = uruchom_mpi(wagi)
        czas_mpi = round(time.time() - start, 2)
        wynik_mpi = parsuj_mpi(linie_mpi)

        if wynik_flux and wynik_mpi:
            print(f"{'Miara':<22} {'FLUX':>12} {'MPI':>12} {'Roznica':>12}")
            print("-" * 60)
            print(f"{'Symulacji lacznie':<22} {wynik_flux['n_symulacji']:>12,} {wynik_mpi['n_symulacji']:>12,}")
            print(f"{'Czas obliczen [s]':<22} {czas_flux:>12.2f} {czas_mpi:>12.2f} {czas_flux-czas_mpi:>+12.2f}")
            print(f"{'Sredni zwrot [zl]':<22} {wynik_flux['sredni_zwrot']:>12.0f} {wynik_mpi['sredni_zwrot']:>12.0f}")
            print(f"{'Odch. std [zl]':<22} {wynik_flux['odch_std']:>12.0f} {wynik_mpi['odch_std']:>12.0f}")
            print("-" * 60)
            print(f"{'VaR 90% [zl]':<22} {wynik_flux['VaR_90']:>12.0f} {wynik_mpi['VaR_90']:>12.0f} {wynik_flux['VaR_90']-wynik_mpi['VaR_90']:>+12.0f}")
            print(f"{'VaR 95% [zl]':<22} {wynik_flux['VaR_95']:>12.0f} {wynik_mpi['VaR_95']:>12.0f} {wynik_flux['VaR_95']-wynik_mpi['VaR_95']:>+12.0f}")
            print(f"{'VaR 99% [zl]':<22} {wynik_flux['VaR_99']:>12.0f} {wynik_mpi['VaR_99']:>12.0f} {wynik_flux['VaR_99']-wynik_mpi['VaR_99']:>+12.0f}")
            szybszy = "FLUX" if czas_flux < czas_mpi else "MPI"
            print(f"\nSzybsza implementacja: {szybszy} (roznica {abs(round(czas_flux-czas_mpi,2))}s)")

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

    print("\n" + "=" * 70)
    print("Podsumowanie")
    print("=" * 70)
    print(f"{'Portfel':<20} {'FLUX [s]':>10} {'MPI [s]':>10} {'FLUX VaR95':>12} {'MPI VaR95':>12}")
    print("-" * 70)
    for w in wszystkie:
        print(f"{w['portfel']:<20} {w['flux_czas']:>10.2f} {w['mpi_czas']:>10.2f} "
              f"{w['flux_var95']:>12.0f} {w['mpi_var95']:>12.0f}")

    with open("porownanie_flux_mpi.csv", "w", newline="", encoding="utf-8") as f:
        pola = list(wszystkie[0].keys()) if wszystkie else []
        writer = csv.DictWriter(f, fieldnames=pola)
        writer.writeheader()
        writer.writerows(wszystkie)

    print("\nWyniki zapisane do porownanie_flux_mpi.csv")


if __name__ == "__main__":
    main()