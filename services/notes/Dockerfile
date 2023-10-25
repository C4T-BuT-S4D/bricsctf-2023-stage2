FROM ubuntu:22.04 as builder

RUN apt update && apt install -y python3-pip

WORKDIR /build

COPY src/userlib .
RUN python3 setup.py build && mv build/lib*/userlib* userlib.so


FROM ubuntu:22.04

RUN apt update && apt install -y socat python3-pip

WORKDIR /app

COPY src/app.py src/entry.sh .
COPY --from=builder /build/userlib.so .

CMD ["socat", "TCP-LISTEN:4985,reuseaddr,fork", "EXEC:/app/entry.sh"]