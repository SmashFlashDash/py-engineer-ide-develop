-------СДЕЛАТЬ ДАМП ИЗ ОБЫЧНО НА ВИРТУАЛКЕ АСТРЫ (МОЖНО ПРОПУСТИТЬ)-----------
поставить постгре
подключиться к БД
psql -U postgres --------можно поменять в pg_hba.conf все на trust чтобы не писать пароль
создать пользователей и базу
CREATE ROLE gusers WITH LOGIN;
CREATE ROLE rokot WITH PASSWORD '@sS00n@s' LOGIN CREATEDB CREATEROLE;
GRANT postgres TO rokot;
CREATE DATABASE rokot_ng OWNER postgres;
восстановить базу
psql -v ON_ERROR_STOP=1 -f /home/administrator/shit.backup -h 127.0.0.1 -p 5432 rokot_ng -U postgres
создать дамп
pg_dump --format plain --file "/home/administrator/db.db" rokot_ng -U postgre --disable-macs --no-security-labels



---------------ДАМП ДЛЯ КОНТЕЙНЕРА-------------------
в initSQL положить файл дампа базы без MAC labels
shit-noMAC.sql
чтобы сделать такой дамп на компе с базой
pg_dump --format plain --file "/home/administrator/db.db" rokot_ng -U postgre --disable-macs --no-security-labels

-------------ЗАПУСТИТЬ КОНТЙНЕРЫ------------------
в power shell из текущей папки:
docker compose up

--------------ЖДАТЬ ДАМП ЗАПИШЕТСЯ-----------------------------
создадутся контйнеры и запустятся
!!!!!!!!!!!!!!!!!!!!!!!!!!
в контйенере postgre будет видно выполняемые в дампе команды
если база большая сидеть и ждать пока postgre не перезапустится
ждать даже если пишет ошибки в pgadmin или в postgre:
postgres_db  | ERROR:  canceling autovacuum task
postgres_db  | CONTEXT:  automatic analyze of table "postgres.dbo.tm"

в итоге размер volume контейнера postgre будет больше файла с дампом
Когда дамп заплился напишет
postgres_db  | PostgreSQL init process complete; ready for start up.
postgres_db  |
postgres_db  | LOG:  database system was shut down at 2022-08-04 11:00:26 UTC
postgres_db  | LOG:  MultiXact member wraparound protections are now enabled
postgres_db  | LOG:  autovacuum launcher started
postgres_db  | LOG:  database system is ready to accept connections

-----------------------PGADMIN------------------------------
зайти в браузере localhost:5050
открыть сервер с базой пароль postgres

----------------IVK----------------------------
поменять настройки конфига подключение к базам