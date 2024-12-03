FROM ubuntu:24.04

RUN apt update && \
    apt install -y python3 \
                   python3-pip \
                   python3-numpy \
                   python3-tqdm \
                   python3-pandas \
                   g++ \
                   libpcap-dev \
                   && apt clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app/scripts/clients-analysis