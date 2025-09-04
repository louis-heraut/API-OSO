API-OSO_prod:
	# Clone fresh repo into a temp directory
	git clone https://github.com/louis-heraut/API-OSO.git tmp_API-OSO

	# Synchronize to /var/www/API-OSO while preserving important local data
	sudo rsync -av --delete \
		--exclude='.env' \
		--exclude='venv' \
		--exclude='data' \
		--exclude='output' \
		tmp_API-OSO/ /var/www/API-OSO/

	# Cleanup the temp directory
	rm -rf tmp_API-OSO

	# Set secure permissions
	# ALL dir
	sudo chown -R root:root /var/www/API-OSO
	sudo chmod -R 755 /var/www/API-OSO
	# output dir
	sudo chown root:www-data /var/www/API-OSO/output
	sudo chmod 770 /var/www/API-OSO/output
	# main.py
	sudo chown root:www-data /var/www/API-OSO/main.py
	sudo chmod 750 /var/www/API-OSO/main.py
	# gunicorn_conf.py
	sudo chown root:www-data /var/www/API-OSO/gunicorn_conf.py
	sudo chmod 750 /var/www/API-OSO/gunicorn_conf.py
	# add_api_key.py
	sudo chown root:root /var/www/API-OSO/add_api_key.py
	sudo chmod 700 /var/www/API-OSO/add_api_key.py
	# .env
	sudo chown root:www-data /var/www/API-OSO/.env
	sudo chmod 440 /var/www/API-OSO/.env

	# Restart Apache to apply changes
	sudo systemctl restart apache2
	sudo systemctl restart api-oso

API-OSO_test:
	source /var/www/API-OSO/venv/bin/activate
	sudo -u www-data /var/www/API-OSO/venv/bin/gunicorn -c /var/www/API-OSO/gunicorn_conf.py main:app

API-OSO_keygen:
	sudo /var/www/API-OSO/venv/bin/python /var/www/API-OSO/add_api_key.py $(NAME)
