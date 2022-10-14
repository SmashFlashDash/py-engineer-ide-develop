Windows:
1) Установить python 3.8+, установить redis из redis-win, установить локально Postgresql для логгировнаия
2) Из папки redis_win, разархивировать архив в любую папку и запустить 64bit/redis-server.exe
3) Зайти в консоли в каталог с программой и выполнить "pip install -r requirements.txt" (нужен интернет)
4) Зайти в консоли в каталог с программой и выполнить "pyhton launcher.py"


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


Подключение strech репозиториев и добавление общей папки с виндой для VirtualBox:
! https://wiki.astralinux.ru/pages/viewpage.action?pageId=3276859
sudo apt install dirmngr
sudo nano /etc/apt/souces.list
   deb http://ftp.ru.debian.org/debian/ stretch main contrib non-free
sudo apt update
    берем последний открытый ключ из ошибки
sudo apt-key adv --recv-keys --keyserver keys.gnupg.net EF0F382A1A7B6500
sudo apt update
! https://gist.github.com/estorgio/1d679f962e8209f8a9232f7593683265
Размонтируем все из дисковода и монтируем диск дополнений гостевой ОС через меню VirtualBox
Копируем все файлы с диска в какую-нибудь папку в ~
sudo apt-get install build-essential linux-headers-`uname -r`
./VBoxLinuxAdditions.run
выключаем вируталку
создаем в VirtualBox общую папку, галки не ставим
включаем вируталку
mkdir ~/SVN
sudo mount -t vboxsf SVN ~/SVN
еще можно в bashrc добавить "sudo mount -t vboxsf SVN ~/SVN", чтоб при старте системы само mount делало 

Настройка GIT
https://docs.gitlab.com/ee/gitlab-basics/start-using-git.html


