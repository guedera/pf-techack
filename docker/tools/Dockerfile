FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl nmap python3 \
    && rm -rf /var/lib/apt/lists/*

USER 65534:65534
WORKDIR /tmp
CMD ["python3", "--version"]
