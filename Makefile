OSO-API_prod:
	# Clone fresh repo into a temp directory
	git clone https://github.com/louis-heraut/OSO-API.git tmp_OSO-API

	# Synchronize to /var/www/OSO-API while preserving important local data
	sudo rsync -av --delete \
		--exclude='.env' \
		--exclude='venv' \
		--exclude='data' \
		--exclude='output' \
		tmp_OSO-API/ /var/www/OSO-API/

	# Cleanup the temp directory
	rm -rf tmp_OSO-API

	# Set secure permissions
	# ALL dir
	sudo chown -R root:root /var/www/OSO-API
	sudo chmod -R 755 /var/www/OSO-API
	# output dir
	sudo chown root:www-data /var/www/OSO-API/output
	sudo chmod 770 /var/www/OSO-API/output
	# main.py
	sudo chown root:www-data /var/www/OSO-API/main.py
	sudo chmod 750 /var/www/OSO-API/main.py
	# gunicorn_conf.py
	sudo chown root:www-data /var/www/OSO-API/gunicorn_conf.py
	sudo chmod 750 /var/www/OSO-API/gunicorn_conf.py
	# add_api_key.py
	sudo chown root:root /var/www/OSO-API/add_api_key.py
	sudo chmod 700 /var/www/OSO-API/add_api_key.py
	# .env
	sudo chown root:www-data /var/www/OSO-API/.env
	sudo chmod 440 /var/www/OSO-API/.env

	# Restart Apache to apply changes
	sudo systemctl restart apache2

OSO-API_test:
	source /var/www/OSO-API/venv/bin/activate
	sudo -u www-data /var/www/OSO-API/venv/bin/gunicorn -c /var/www/OSO-API/gunicorn_conf.py main:app


OSO-API_keygen:
	sudo /var/www/OSO-API/venv/bin/python /var/www/OSO-API/add_api_key.py $(NAME)
