import numpy as np
import pandas as pd
import sys
import json
import os


def wczytaj_dane(plik="dane/ceny_wig20.csv"):
    df = pd.read_csv(plik, index_col="Date", parse_dates=True)
    return df


def oblicz_zwroty(ceny):
    """Dzienne zwroty logarytmiczne"""
    return np.log(ceny / ceny.shift(1)).dropna()


def symuluj_portfel(zwroty, wagi, n_dni=30, n_symulacji=1000, seed=None):
    """
    Symuluje końcową wartość portfela metodą błądzenia losowego.

    zwroty   - DataFrame z dziennymi zwrotami akcji
    wagi     - słownik {ticker: waga}, np. {"PKO.WA": 0.4, "PKN.WA": 0.6}
    n_dni    - ile dni do przodu symulujemy
    n_symulacji - ile razy powtarzamy symulację
    """
    if seed is not None:
        np.random.seed(seed)

    # Wybierz tylko akcje z portfela
    tickery = list(wagi.keys())
    w = np.array([wagi[t] for t in tickery])
    Z = zwroty[tickery].dropna()

    # Parametry rozkładu
    srednie = Z.mean().values
    kowariancja = Z.cov().values

    wyniki = []

    for _ in range(n_symulacji):
        # Losuj dzienne zwroty z rozkładu wielowymiarowego normalnego
        dzienne_zwroty = np.random.multivariate_normal(
            mean=srednie,
            cov=kowariancja,
            size=n_dni
        )
        # Łączny zwrot portfela po n_dni dniach
        zwrot_portfela = np.sum(dzienne_zwroty, axis=0)
        zwrot_wazona = np.dot(zwrot_portfela, w)
        wyniki.append(zwrot_wazona)

    return np.array(wyniki)


def oblicz_var(wyniki, wartosc_portfela, poziomy=[0.90, 0.95, 0.99]):
    """Oblicza VaR dla podanych poziomów ufności"""
    var = {}
    for p in poziomy:
        prog = np.percentile(wyniki, (1 - p) * 100)
        var[f"VaR_{int(p * 100)}"] = round(-prog * wartosc_portfela, 2)
    return var


def main():
    # Wczytaj parametry z argumentów (dla FLUXa)
    portfel_json = sys.argv[1] if len(sys.argv) > 1 else None
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else os.getpid()
    n_symulacji = int(sys.argv[3]) if len(sys.argv) > 3 else 10000
    wartosc_portfela = float(sys.argv[4]) if len(sys.argv) > 4 else 100000

    # Domyślny portfel jeśli nie podano
    if portfel_json is None:
        wagi = {
            "PKO.WA": 0.3,
            "PKN.WA": 0.3,
            "KGH.WA": 0.2,
            "PZU.WA": 0.2
        }
    else:
        wagi = json.loads(portfel_json)

    # Wczytaj dane i oblicz zwroty
    ceny = wczytaj_dane()
    zwroty = oblicz_zwroty(ceny)

    # Symuluj
    wyniki = symuluj_portfel(zwroty, wagi, n_symulacji=n_symulacji, seed=seed)

    # Oblicz VaR
    var = oblicz_var(wyniki, wartosc_portfela)

    # Wypisz wyniki (zbierze je var_flux.py)
    print(json.dumps({
        "portfel": list(wagi.keys()),
        "n_symulacji": n_symulacji,
        "var": var,
        "sredni_zwrot": round(float(np.mean(wyniki)) * wartosc_portfela, 2),
        "odch_std": round(float(np.std(wyniki)) * wartosc_portfela, 2)
    }))


if __name__ == "__main__":
    main()