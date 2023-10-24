FROM ubuntu@sha256:c9cf959fd83770dfdefd8fb42cfef0761432af36a764c077aed54bbc5bb25368

RUN apt update && apt install -y socat python3-pip

WORKDIR /app

COPY src/ .

RUN cd /app/userlib && python3 setup.py build && mv build/lib*/userlib* userlib.so && rm -rf build && cp userlib.so ../

CMD ["socat", "TCP-LISTEN:4985,reuseaddr,fork", "EXEC:/app/entry.sh"]
