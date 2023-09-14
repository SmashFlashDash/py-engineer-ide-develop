#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	CREATE DATABASE ivk_log WITH OWNER postgres ENCODING 'UTF8';
	grant all privileges on database ivk_log to postgres;
	CREATE ROLE gusers WITH LOGIN;
    CREATE ROLE rokot WITH PASSWORD '@sS00n@s' LOGIN CREATEDB CREATEROLE;
    GRANT postgres TO rokot;
    CREATE DATABASE rokot_ng ENCODING 'UTF8' OWNER postgres;
EOSQL

psql -c "CREATE TABLE IF NOT EXISTS log (dt timestamp NOT NULL, 
        username varchar(250), 
        thread_id int8 NOT NULL, 
        source_name varchar(250) NOT NULL, 
        source_path text, 
        log text NOT NULL, 
        error bool NOT NULL, 
        additional text);" -v ON_ERROR_STOP=1 -U postgres -d ivk_log

# psql -v ON_ERROR_STOP=1 -f /docker-entrypoint-initdb.d/shit-noMAC.sql -h 127.0.0.1 -p 5432 rokot_ng -U postgres
psql -v ON_ERROR_STOP=1 -f /docker-entrypoint-initdb.d/rokot_ng.backup --dbname rokot_ng -U postgres

psql -c "ALTER DATABASE rokot_ng set search_path = dbo;" -U postgres -d postgres
psql -c "ALTER DATABASE ivk_log set search_path = public;" -U postgres -d postgres

echo "-------------------------Konets blyat ----------------------------\n"
