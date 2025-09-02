OSO-API_prod:
	# Clone fresh repo into a temp directory
	git clone https://github.com/louis-heraut/OSO-API.git tmp_OSO-API

	# Synchronize to /var/www/OSO-API while preserving important local data
	sudo rsync -av --delete \
		--exclude='.env' \
		tmp_OSO-API/ /var/www/OSO-API/

	# Cleanup the temp directory
	rm -rf tmp_OSO-API

	# Set secure permissions
	sudo chown -R root:root /var/www/OSO-API
	sudo chmod -R 755 /var/www/OSO-API
	# sudo chown root:www-data /var/www/OSO-API/app.py
	# sudo chmod 750 /var/www/OSO-API/app.py
	# sudo chown root:www-data /var/www/OSO-API/app.wsgi
	# sudo chmod 750 /var/www/OSO-API/app.wsgi
	sudo chown root:www-data /var/www/OSO-API/.env
	sudo chmod 440 /var/www/OSO-API/.env

	# Restart Apache to apply changes
	sudo systemctl restart apache2
