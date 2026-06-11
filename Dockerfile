FROM fluxrm/flux-sched:latest

RUN sudo apt-get update && \
    sudo apt-get install -y python3-pip && \
    pip install yfinance pandas numpy mpi4py --break-system-packages

WORKDIR /home/fluxuser/projekt