## Description
IDE для python, в которой можно разрабатывать и запускать скрипты как один файл или состоящие из модулей.  
IDE взаимодействует с аппаратурой тестировочного шкафа, куда подключается оборудование, которым управляет скрипт.    
В ./cpi фреймворке конфигурируется взаимодействие ide с тестировочным шкафом и сторонним оборудованием.   

В ide можно запускать скрипты написанные на python для тестирования аппаратуры в реальном временим, получать информацию.
от аппаратуры и отображать эту информацию.

В модуле engineers_src написаны функции которые по умолчанию импортированы в запускаемые скрипты.  
Вызовов этих функций упрощает взаимодействие инженера с python для отправки сообщений, обработки информации, служит интерфейсом для написания скриптов тестирования.

IDE написана на pyqt5. Использует redis и postgre **(можно развернуть с помощью docker compose в ./dockercomposedb/)**  
Интерфейс:
![img1.jpg](.documentation%2Fimg1.jpg)

---
## BUILD
Windows:
1) Установить python 3.8+, установить redis из redis-win, установить локально Postgresql для логгировнаия
2) Из папки redis_win, разархивировать архив в любую папку и запустить 64bit/redis-server.exe
3) Зайти в консоли в каталог с программой и выполнить "pip install -r requirements.txt" (нужен интернет)
4) Зайти в консоли в каталог с программой и выполнить "pyhton launcher.py"

---
astra-linux 1.6:
sudo apt install python3-pyqt5 python3-pyqt5.qsci postgresql #Установятся верссии python3-pyqt5 5.10.1, python3-pyqt5.qsci 2.9.3
sudo apt install python3-psycopg2 python3-psutil redis-server python3-redis (с диска разработчика)

Для доп пакетов на астре 1.6 -> вставляем диск разработчика
sudo apt-cdrom add
sudo apt update

Для iso файла:
sudo mkdir /aptoncd-mountpoint
sudo mount /run/user/....../file.iso /aptoncd-mountpoint -oloop
sudo apt-cdrom -d=/aptoncd-mountpoint add
а при установке монтируем на media/cdrom

Redis astra:
sudo systemctl start|stop|restart|status redis
sudo nano /etc/redis/redis.conf
redis-cli
FLUSHALL (полный вайп)

Postgres astra:
sudo -u postgres psql
\password postgres -> Z84h9!d
CREATE DATABASE ivk_log WITH OWNER postgres ENCODING 'UTF8';
grant all privileges on database ivk_log to postgres;
Для коннектра к базе \c ivk_log
