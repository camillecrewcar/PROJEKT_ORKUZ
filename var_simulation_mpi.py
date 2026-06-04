from mpi4py import MPI
import numpy as np
import pandas as pd
import json
import sys

def wczytaj_dane(plik="dane/ceny_wig20.csv"):
    return pd.read_csv(plik, index_col="Date", parse_dates=True)

def oblicz_zwroty(ceny):
    return np.log(ceny / ceny.shift(1)).dropna()

def symuluj_portfel(zwroty, wagi, n_dni=30, n_symulacji=10000, seed=None):
    if seed is not None:
        np.random.seed(seed)

    tickery = list(wagi.keys())
    w = np.array([wagi[t] for t in tickery])
    Z = zwroty[tickery].dropna()

    srednie = Z.mean().values
    kowariancja = Z.cov().values

    wyniki = []
    for _ in range(n_symulacji):
        dzienne_zwroty = np.random.multivariate_normal(
            mean=srednie,
            cov=kowariancja,
            size=n_dni
        )
        zwrot_portfela = np.sum(dzienne_zwroty, axis=0)
        zwrot_wazona = np.dot(zwrot_portfela, w)
        wyniki.append(zwrot_wazona)

    return np.array(wyniki)

def oblicz_var(wyniki, wartosc_portfela, poziomy=[0.90, 0.95, 0.99]):
    var = {}
    for p in poziomy:
        prog = np.percentile(wyniki, (1 - p) * 100)
        var[f"VaR_{int(p*100)}"] = round(-prog * wartosc_portfela, 2)
    return var

def main():
    # Inicjalizacja MPI
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()   # numer tego procesu
    size = comm.Get_size()   # łączna liczba procesów

    # Parametry
    portfel_json = sys.argv[1] if len(sys.argv) > 1 else None
    n_symulacji = int(sys.argv[2]) if len(sys.argv) > 2 else 10000
    wartosc_portfela = float(sys.argv[3]) if len(sys.argv) > 3 else 100000

    if portfel_json is None:
        wagi = {"PKO.WA": 0.3, "PKN.WA": 0.3, "KGH.WA": 0.2, "PZU.WA": 0.2}
    else:
        wagi = json.loads(portfel_json)

    # Każdy proces ma inne ziarno
    np.random.seed(rank * 99991)

    # Wczytaj dane i symuluj
    ceny = wczytaj_dane()
    zwroty = oblicz_zwroty(ceny)
    wyniki_lokalne = symuluj_portfel(zwroty, wagi, n_symulacji=n_symulacji)

    # Zbierz wszystkie wyniki do procesu 0 przez MPI
    wszystkie_wyniki = comm.gather(wyniki_lokalne, root=0)

    # Tylko proces 0 liczy VaR i wypisuje wynik
    if rank == 0:
        wyniki_laczone = np.concatenate(wszystkie_wyniki)
        var = oblicz_var(wyniki_laczone, wartosc_portfela)

        print(json.dumps({
            "portfel": list(wagi.keys()),
            "n_symulacji": len(wyniki_laczone),
            "var": var,
            "sredni_zwrot": round(float(np.mean(wyniki_laczone)) * wartosc_portfela, 2),
            "odch_std": round(float(np.std(wyniki_laczone)) * wartosc_portfela, 2)
        }))

if __name__ == "__main__":
    main()