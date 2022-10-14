-- ivk_log
CREATE DATABASE ivk_log WITH OWNER postgres ENCODING 'UTF8';
grant all privileges on database ivk_log to postgres;

--rokot_db
CREATE ROLE gusers WITH LOGIN;
CREATE ROLE rokot WITH PASSWORD '@sS00n@s' LOGIN CREATEDB CREATEROLE;
GRANT postgres TO rokot;
CREATE DATABASE rokot_ng OWNER postgres;