# Projekt VaR WIG20

## Wymagania
Docker Desktop

## Uruchomienie
1. Uruchom kontener:
docker run -it -v /sciezka/do/folderu:/home/fluxuser/projekt fluxrm/flux-sched:latest

2. Zainstaluj biblioteki:
pip install yfinance pandas numpy mpi4py --break-system-packages

3. Pobierz dane:
python3 pobierz_dane.py

4. Uruchom FLUX:
flux start --test-size=4

5. Uruchom eksperymenty:
python3 porownanie.py