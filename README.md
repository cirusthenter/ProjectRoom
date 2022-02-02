# room

## How to deploy on Ubuntu

### Update Package Managers

## Initial setup

```
sudo yum update
```

### Install Python 3.9.4

```
sudo dnf install wget yum-utils make gcc openssl-devel bzip2-devel libffi-devel zlib-devel
wget https://www.python.org/ftp/python/3.9.4/Python-3.9.4.tgz 
tar xzf Python-3.9.4.tgz 
cd cd Python-3.9.4
sudo ./configure --with-system-ffi --with-computed-gotos --enable-loadable-sqlite-extensions 
sudo make -j ${nproc}
sudo make altinstall
cd ../
sudo rm Python-3.9.4.tgz
```

```
sudo yum install python3-pip
sudo yum install python3-devel
sudo yum install postgresql-libs
sudo yum install postgresql
sudo yum install postgresql-contrib
sudo yum install nginx
sudo yum install curl
sudo yum install ufw
```

## PostgreSQL

```
sudo dnf install postgresql-server
sudo postgresql-setup --initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo -i -u postgres
```

You can now access a Postgres prompt immediately by typing:

```
[postgres@room ~]$ psql
psql (10.15)
Type "help" for help.

postgres=# CREATE DATABASE room;
CREATE DATABASE
postgres=# CREATE USER admin WITH PASSWORD 'password';
CREATE ROLE
postgres=# ALTER ROLE admin SET client_encoding TO 'utf8';
postgres=# ALTER ROLE admin SET default_transaction_isolation TO 'read committed';
postgres=# ALTER ROLE admin SET timezone TO 'Asia/Tokyo';
postgres=# GRANT ALL PRIVILEGES ON DATABASE room TO admin;
postgres=# \q;
```

## Git

```
sudo yum install git
git clone 
```

## Virtual env

```
sudo -H pip3 install --upgrade pip
sudo -H pip3 install virtualenv
```

```
cd room
virtualenv roomenv
source roomenv/bin/activate
```

```
(roomenv) [room-hc-st-admin@room room]$ pip install django
(roomenv) [room-hc-st-admin@room room]$ pip install gunicorn
(roomenv) [room-hc-st-admin@room room]$ pip install psycopg2-binary
```

## Setttings for Djnago project

```
vim ~/room/room_project/settings.py
```

```python
ALLOWED_HOSTS = ['localhost']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'room',
        'USER': 'admin',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '',
    }
}

STATICFILES_DIRS = (
    str(BASE_DIR.joinpath('static')),
)
STATIC_ROOT = str(BASE_DIR.joinpath('staticfiles'))
```

```
pip install pipenv
pipenv install
```

```
sudo vim /var/lib/pgsql/data/pg_hba.conf
```

```conf
 77 # TYPE  DATABASE        USER            ADDRESS                 METHOD
 78
 79 # "local" is for Unix domain socket connections only
 80 local   all             all                                     peer
 81 # IPv4 local connections:
 82 host    all             all             127.0.0.1/32            ident
 83 # IPv6 local connections:
 84 host    all             all             ::1/128                 ident
 85 # Allow replication connections from localhost, by a user with the
 86 # replication privilege.
 87 local   replication     all                                     peer
 88 host    replication     all             127.0.0.1/32            ident
 89 host    replication     all             ::1/128                 ident
```

to

```conf
 77 # TYPE  DATABASE        USER            ADDRESS                 METHOD
 78
 79 # "local" is for Unix domain socket connections only
 80 local   all             all                                     peer
 81 # IPv4 local connections:
 82 host    all             all             127.0.0.1/32            md5 # New!
 83 # IPv6 local connections:
 84 host    all             all             ::1/128                 md5 # New!
 85 # Allow replication connections from localhost, by a user with the
 86 # replication privilege.
 87 local   replication     all                                     peer
 88 host    replication     all             127.0.0.1/32            ident
 89 host    replication     all             ::1/128                 ident
```

```
service postgresql restart
```

```
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
```

## gunicorn

```
sudo vim /etc/systemd/system/gunicorn.socket
```

```socket
[Unit]
Description=gunicorn socket
[Socket]
ListenStream=/run/gunicorn.sock
[Install]
WantedBy=sockets.target
```


```
sudo vim /etc/systemd/system/gunicorn.service
```

```
[Unit]
Description=gunicorn daemon
After=network.target
[Service]
User=room-hc-st-admin
Group=nginx
WorkingDirectory=/home/room-hc-st-admin/room
ExecStart=/home/room-hc-st-admin/room/roomenv/bin/gunicorn \
           --workers 3 \
           --bind unix:/home/room-hc-st-admin/room/room.sock \
           room_project.wsgi:application
[Install]
WantedBy=multi-user.target
```

```
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
```

## Nginx

```
     server {
         listen       80 default_server;
         listen       [::]:80 default_server;
         server_name  false_server.com;
         # root         /usr/share/nginx/html;

         # Load configuration files for the default server block.
         include /etc/nginx/default.d/*.conf;

         location = /favicon.ico { access_log off; log_not_found off; }
         location /static/ {
             root /home/room-hc-st-admin/room/staticfiles/;
         }

         location / {
             proxy_set_header Host $http_host;
             proxy_set_header X-Real-IP $remote_addr;
             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
             proxy_set_header X-Forwarded-Proto $scheme;
             proxy_pass http://unix:/home/room-hc-st-admin/room/room.sock;
         }
```

```
sudo usermod -a -G room-hc-st-admin nginx
chmod 710 /home/room-hc-st-admin
```

```
sudo systemctl start nginx
sudo systemctl enable nginx
```

## Should update?
```
sudo ln -s /etc/nginx/sites-available/room /etc/nginx/sites-enabled
```

```
sudo vim /etc/ufw/applications.d/nginx.ini
```

```
[Nginx HTTP]
title=Web Server 
description=Enable NGINX HTTP traffic
ports=80/tcp

[Nginx HTTPS] \
title=Web Server (HTTPS) \
description=Enable NGINX HTTPS traffic
ports=443/tcp

[Nginx Full]
title=Web Server (HTTP,HTTPS)
description=Enable NGINX HTTP and HTTPS traffic
ports=80,443/tcp
```

## .env 

```
SECRET_KEY=deafbeef
DEBUG=False
DB_USER=user
DB_PASSWORD=password
SITE_ID=0
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SECURE_HSTS_SECONDS=31536000
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=True
DJANGO_SECURE_HSTS_PRELOAD=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANG0_SECURE_BROWSER_XSS_FILTER=True
```