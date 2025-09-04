# API-OSO Installation Guide
This guide walks you through installing and configuring **API-OSO** on a Linux server with Apache, Python, and Gunicorn.


## Update & Install Required Packages
First, update your system and install the necessary dependencies:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install apache2 libapache2-mod-proxy-uwsgi python3 python3-pip python3.10-venv -y
```


## Enable Apache Modules
Enable the required Apache modules for proxying requests and handling headers:
```bash
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod headers
sudo systemctl restart apache2
```


## Clone the Repository & Build
Clone the **API-OSO** repository and build the production setup:
```bash
cd ~
git clone https://github.com/louis-heraut/API-OSO.git
mv ./API-OSO/Makefile ./
make API-OSO_prod
```


## Configure Environment & Directories
Prepare environment variables and create necessary folders:
```bash
sudo mv /var/www/API-OSO/env.dist /var/www/API-OSO/.env
sudo nano /var/www/API-OSO/.env
sudo mkdir /var/www/API-OSO/data/
sudo mkdir /var/www/API-OSO/output/
```
Edit the `.env` file as needed (e.g., database credentials, API keys).


## Set Up Python Virtual Environment
Create and activate a virtual environment, then install dependencies:
```bash
sudo python3 -m venv /var/www/API-OSO/venv
sudo chown -R vmadmin:vmadmin /var/www/API-OSO/venv
source /var/www/API-OSO/venv/bin/activate
pip install --upgrade pip
pip install -r /var/www/API-OSO/requirements.txt
```


## Download & Move Data
Fetch data from [Geodes Portal](https://geodes-portal.cnes.fr/) and move it to the correct directory:
```bash
scp ./data/*.tif user@server-ip:~/
sudo mv ~/*.tif /var/www/API-OSO/data/
```


## Configure Apache Virtual Host
Create a new Apache site configuration:
```bash
sudo nano /etc/apache2/sites-available/api-oso.conf
```
Paste the following configuration:
```apache
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
```
Enable the site and reload Apache:
```bash
sudo a2ensite api-oso
sudo systemctl reload apache2
```


## Create a Systemd Service for Gunicorn
Create and edit the service file:
```bash
sudo nano /etc/systemd/system/api-oso.service
```
Paste this configuration:
```ini
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
```
Reload `systemd`, then start and enable the service:
```bash
sudo systemctl daemon-reload
sudo systemctl start api-oso
sudo systemctl enable api-oso
sudo systemctl status api-oso
```


## Rebuild Production (Optional)
If you need to rebuild the project later:
```bash
cd ~
make API-OSO_prod
```


## Generate a Key
Generate a key for a user (example: `alice`):
```bash
make API-OSO_keygen NAME=alice
```

