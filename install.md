sudo apt update && sudo apt upgrade -y
sudo apt install apache2 libapache2-mod-proxy-uwsgi python3 python3-pip python3.10-venv -y


sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod headers
sudo systemctl restart apache2

cd ~
git clone https://github.com/louis-heraut/OSO-API.git
mv ./OSO-API/Makefile .
make OSO-API_prod

sudo mv /var/www/OSO-API/env.dist /var/www/OSO-API/.env
sudo nano /var/www/OSO-API/.env

cd ~
make OSO-API_prod


make OSO-API_keygen NAME=alice