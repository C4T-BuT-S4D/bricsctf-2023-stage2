#!/bin/bash
set -e

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

	CREATE USER notify WITH PASSWORD 'notify-password';
	CREATE USER stalwart WITH PASSWORD 'stalwart-password';

	GRANT SELECT, INSERT, DELETE ON TABLE account TO notify;
	GRANT INSERT ON TABLE group_member TO notify;
	GRANT SELECT ON TABLE account, group_member TO stalwart;
	GRANT SELECT, INSERT, DELETE ON TABLE notification TO notify;
	GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE notification_queue TO notify;
EOSQL
