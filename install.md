sudo apt update && sudo apt upgrade -y
sudo apt install apache2 libapache2-mod-proxy-uwsgi python3 python3-pip python3.10-venv -y


sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod headers
sudo systemctl restart apache2

cd ~
git clone https://github.com/louis-heraut/OSO-API.git
mv ./OSO-API/Makefile ./
make OSO-API_prod

sudo mv /var/www/OSO-API/env.dist /var/www/OSO-API/.env
sudo nano /var/www/OSO-API/.env

cd ~
make OSO-API_prod

sudo python3 -m venv /var/www/OSO-API/venv
sudo chown -R vmadmin:vmadmin /var/www/OSO-API/venv
source /var/www/OSO-API/venv/bin/activate
pip install --upgrade pip
pip install -r /var/www/OSO-API/requirements.txt


data on https://geodes-portal.cnes.fr/
scp ./data/* user@server-ip:~/
sudo mkdir /var/www/OSO-API/data/
sudo mv ~/data* /var/www/OSO-API/data/
sudo mkdir /var/www/OSO-API/output/

sudo nano /etc/apache2/sites-available/OSO-API.conf
<VirtualHost *:80>
    ServerName 147.100.222.13

    # Proxy all requests to Gunicorn/Uvicorn
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/

    # Serve static files in /output
    Alias /files/ /var/www/OSO-API/output/
    <Directory /var/www/OSO-API/output/>
        Require all granted
        Options Indexes FollowSymLinks
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/OSO-API_error.log
    CustomLog ${APACHE_LOG_DIR}/OSO-API_access.log combined
</VirtualHost>

sudo a2ensite OSO-API
sudo systemctl reload apache2



sudo nano /etc/systemd/system/OSO-API.service
[Unit]
Description=Gunicorn instance to serve OSO API
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/OSO-API
EnvironmentFile=/var/www/OSO-API/.env
ExecStart=/var/www/OSO-API/venv/bin/gunicorn -c /var/www/OSO-API/gunicorn_conf.py main:app

[Install]
WantedBy=multi-user.target

sudo systemctl daemon-reload
sudo systemctl start OSO-API
sudo systemctl enable OSO-API
sudo systemctl status OSO-API




# gen key
make OSO-API_keygen NAME=alice



