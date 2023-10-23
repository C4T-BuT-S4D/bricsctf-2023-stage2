#!/bin/bash
set -e

NOTIFIER_PASSWORD=$(openssl rand -hex 32)
NOTIFIER_PASSWORD_HASH_SALT=$(openssl rand -hex 16)
NOTIFIER_PASSWORD_HASH_PBKDF2=$(openssl kdf -keylen 32 -kdfopt digest:SHA512 -kdfopt "pass:${NOTIFIER_PASSWORD}" -kdfopt "salt:${NOTIFIER_PASSWORD_HASH_SALT}" -kdfopt iter:10000 -binary PBKDF2 | base64 | sed 's/=//g')
NOTIFIER_PASSWORD_HASH_PHC="\$pbkdf2-sha512\$i=10000\$$(echo -n $NOTIFIER_PASSWORD_HASH_SALT | base64 | sed 's/=//g')\$${NOTIFIER_PASSWORD_HASH_PBKDF2}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	CREATE TABLE account (
		username text NOT NULL,
		password_hash text NOT NULL,
		created_at timestamptz NOT NULL DEFAULT now(),
		CONSTRAINT account_pk PRIMARY KEY (username)
	);
	
	CREATE TABLE group_member (
		username text NOT NULL,
		group_name text NOT NULL,
		CONSTRAINT group_member_pk PRIMARY KEY (username, group_name),
		CONSTRAINT group_member_username_fk FOREIGN KEY (username) REFERENCES account (username)
	);

	CREATE TABLE notification (
		id uuid NOT NULL DEFAULT gen_random_uuid(),
		username text NOT NULL,
		title text NOT NULL,
		content text NOT NULL,
		CONSTRAINT notification_pk PRIMARY KEY (id),
		CONSTRAINT notification_username_fk FOREIGN KEY (username) REFERENCES account (username)
	);

	CREATE TYPE notification_state AS ENUM ('planned', 'inprogress', 'sent', 'failed');

	CREATE TABLE notification_queue (
		notification_id uuid NOT NULL,
		planned_at timestamptz NOT NULL,
		state notification_state NOT NULL DEFAULT 'planned',
		sent_at timestamptz NULL,
		CONSTRAINT notification_queue_pk PRIMARY KEY (notification_id, planned_at),
		CONSTRAINT notification_queue_notification_id_fk FOREIGN KEY (notification_id) REFERENCES notification (id)
	);

	INSERT INTO account (username, password_hash)
	VALUES ('notifier', '$NOTIFIER_PASSWORD_HASH_PHC');

	INSERT INTO group_member (username, group_name)
	VALUES ('notifier', 'superusers');

	CREATE USER notify WITH PASSWORD 'notify-password';
	CREATE USER stalwart WITH PASSWORD 'stalwart-password';

	GRANT SELECT, INSERT, DELETE ON TABLE account, notification TO notify;
	GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE notification_queue TO notify;
	GRANT SELECT ON TABLE account, group_member TO stalwart;
EOSQL

echo -n "$NOTIFIER_PASSWORD" > /var/lib/notifier-secret/value
