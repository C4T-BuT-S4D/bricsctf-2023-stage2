FROM ubuntu:22.04

RUN apt update && apt install -y socat python3-pip

WORKDIR /app

COPY src/app.py src/entry.sh src/userlib.so .

CMD ["socat", "TCP-LISTEN:4985,reuseaddr,fork", "EXEC:/app/entry.sh"]