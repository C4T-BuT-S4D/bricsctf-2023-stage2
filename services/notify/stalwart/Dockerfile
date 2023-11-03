FROM stalwartlabs/mail-server:v0.4.2

RUN mkdir \
  /opt/stalwart-mail/data \
  /opt/stalwart-mail/data/blobs \
  /opt/stalwart-mail/queue \
  /opt/stalwart-mail/reports

RUN chown -R stalwart-mail:stalwart-mail /opt/stalwart-mail
