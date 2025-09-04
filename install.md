Instalation Guide

sudo apt update && sudo apt upgrade -y
sudo apt install apache2 libapache2-mod-proxy-uwsgi python3 python3-pip python3.10-venv -y

sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod headers
sudo systemctl restart apache2

cd ~
git clone https://github.com/louis-heraut/API-OSO.git
mv ./API-OSO/Makefile ./
make API-OSO_prod

sudo mv /var/www/API-OSO/env.dist /var/www/API-OSO/.env
sudo nano /var/www/API-OSO/.env
sudo mkdir /var/www/API-OSO/data/
sudo mkdir /var/www/API-OSO/output/

sudo python3 -m venv /var/www/API-OSO/venv
sudo chown -R vmadmin:vmadmin /var/www/API-OSO/venv
source /var/www/API-OSO/venv/bin/activate
pip install --upgrade pip
pip install -r /var/www/API-OSO/requirements.txt

data on https://geodes-portal.cnes.fr/
scp ./data/*.tif user@server-ip:~/
sudo mv ~/*.tif /var/www/API-OSO/data/


sudo nano /etc/apache2/sites-available/api-oso.conf
<VirtualHost *:80>
    ServerName 147.100.222.13

    # Proxy all requests to Gunicorn/Uvicorn
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/

    # Serve static files in /output
    Alias /files/ /var/www/API-OSO/output/
    <Directory /var/www/API-OSO/output/>
        Require all granted
        Options Indexes FollowSymLinks
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/api-oso_error.log
    CustomLog ${APACHE_LOG_DIR}/api-oso_access.log combined
</VirtualHost>

sudo a2ensite api-oso
sudo systemctl reload apache2



sudo nano /etc/systemd/system/api-oso.service
[Unit]
Description=Gunicorn instance to serve OSO API
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/API-OSO
EnvironmentFile=/var/www/API-OSO/.env
ExecStart=/var/www/API-OSO/venv/bin/gunicorn -c /var/www/API-OSO/gunicorn_conf.py main:app

[Install]
WantedBy=multi-user.target

sudo systemctl daemon-reload
sudo systemctl start api-oso
sudo systemctl enable api-oso
sudo systemctl status api-oso



cd ~
make API-OSO_prod


# gen key
make API-OSO_keygen NAME=alice



