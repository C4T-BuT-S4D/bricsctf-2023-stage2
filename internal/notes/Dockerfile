FROM ubuntu:22.04

RUN apt update && apt install -y python3-pip

WORKDIR /build

COPY userlib .
RUN python3 setup.py build && mv build/lib*/userlib* userlib.so