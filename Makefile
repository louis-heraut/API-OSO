OSO-API_prod:
	# Clone fresh repo into a temp directory
	git clone https://github.com/louis-heraut/OSO-API.git tmp_OSO-API

	# Synchronize to /var/www/OSO-API while preserving important local data
	sudo rsync -av --delete \
		--exclude='.env' \
		--exclude='venv' \
		tmp_OSO-API/ /var/www/OSO-API/

	# Cleanup the temp directory
	rm -rf tmp_OSO-API

	# Set secure permissions
	sudo chown -R root:root /var/www/OSO-API
	sudo chmod -R 755 /var/www/OSO-API

	sudo chown root:www-data /var/www/OSO-API/main.py
	sudo chmod 750 /var/www/OSO-API/main.py
	sudo chown root:www-data /var/www/OSO-API/.env
	sudo chmod 440 /var/www/OSO-API/.env

	sudo chown root:root /var/www/OSO-API/add_api_key.py
	sudo chmod 700 /var/www/OSO-API/add_api_key.py

	# Restart Apache to apply changes
	sudo systemctl restart apache2

OSO-API_keygen:
	sudo /var/www/OSO-API/venv/bin/python /var/www/OSO-API/add_api_key.py $(NAME)
