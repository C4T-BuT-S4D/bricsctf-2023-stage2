#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	CREATE TABLE account (
		username TEXT,
		password_hash TEXT NOT NULL,
		created_at TIMESTAMP NOT NULL DEFAULT now(),
		CONSTRAINT account_pk PRIMARY KEY (username)
	);
	
	CREATE TABLE group_member (
		username TEXT NOT NULL,
		group_name TEXT NOT NULL,
		CONSTRAINT group_member_pk PRIMARY KEY (username, group_name),
		CONSTRAINT group_member_username_fk FOREIGN KEY (username) REFERENCES account (username)
	);

	CREATE USER notify WITH PASSWORD 'notify-password';
	CREATE USER stalwart WITH PASSWORD 'stalwart-password';

	GRANT SELECT, INSERT, DELETE ON TABLE account TO notify;
	GRANT INSERT ON TABLE group_member TO notify;
	GRANT SELECT ON TABLE account, group_member TO stalwart;
EOSQL
