
# API de Découpe OSO – Documentation

## Sommaire
1. [Contexte du projet (SPCD)](#1-contexte-du-projet-spcd)
2. [Fonctionnement de l'API](#2-fonctionnement-de-lapi)
3. [Installation sur un nouveau serveur](#3-installation-sur-un-nouveau-serveur)
    - [Outils utiles pour le déploiement](#outils-utiles-pour-le-déploiement)
    - [Architecture et technologies](#architecture-et-technologies)
    - [Structure des dossiers](#structure-des-dossiers)
    - [Fichier des dépendances (`requirements.txt`)](#fichier-des-dépendances-requirementstxt)
    - [Étapes d'installation](#étapes-dinstallation)

## 1. Contexte du projet (SPCD)

L'objectif de cette API est de fournir un service de découpage à la volée des cartes OSO (Occupation du Sol). Actuellement, pour exploiter une petite zone de ces cartes, un utilisateur doit télécharger le fichier GeoTIFF complet pour la France (plusieurs Go).

Ce processus est long et gourmand en bande passante et en espace de stockage.

Avec cette API, l'utilisateur envoie simplement les coordonnées d'un polygone et reçoit une URL pour télécharger directement le petit fichier découpé. Elle est conçue pour être intégrée dans des applications externes, comme le module SPCD, afin d'automatiser et d'accélérer le traitement des données géographiques.

## 2. Fonctionnement de l'API

L'API expose un unique point de terminaison qui accepte une requête `POST` pour effectuer le découpage.

- **Endpoint :** `POST /clip/`
- **Authentification :** Requise. Une clé API valide doit être fournie dans l'en-tête HTTP `X-API-Key`.

### Paramètres de la requête

Le corps de la requête doit être un JSON contenant les champs suivants :

- `points` (obligatoire) : Une liste de points `[longitude, latitude]` (format WGS84, EPSG:4326) définissant le polygone de découpe.
- `year` (obligatoire) : L'année du millésime OSO à utiliser.
- `filename` (optionnel) : Un nom de base pour le fichier de sortie. Si non fourni, un nom sera généré.

### Règles et conditions

- **Clé API :** Une requête sans clé API valide sera rejetée avec une erreur `403 Forbidden`.
- **Année :** Seules les années `2018`, `2019`, `2020`, `2021`, `2022`, `2023` et `2024` sont acceptées. Toute autre valeur provoquera une erreur `422 Unprocessable Entity`.
- **Zone géographique :** Le polygone fourni doit être entièrement contenu dans les limites de la France métropolitaine. Sinon, une erreur `400 Bad Request` est retournée.

### Réponse de l'API

Si la requête est valide, l'API répond avec un statut `200 OK` et un corps JSON contenant l'URL du fichier généré.

```json
{
  "url": "http://VOTRE_DOMAINE_OU_IP/files/clip_resultat_20231027T140000Z_a1b2c3d4.tif"
}
```
**Important :** Le fichier généré n'est disponible que pendant **1 heure**. Passé ce délai, il est automatiquement supprimé du serveur.

### Exemple de requête avec `curl`

```bash
# Remplacez VOTRE_DOMAINE_OU_IP et VOTRE_CLE_API par vos valeurs.
curl -X POST "http://VOTRE_DOMAINE_OU_IP/clip/" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: VOTRE_CLE_API" \
     -d '{
           "points": [
             [2.34, 48.85],
             [2.35, 48.85],
             [2.35, 48.86],
             [2.34, 48.86],
             [2.34, 48.85]
           ],
           "year": 2022,
           "filename": "decoupe_paris"
         }'
```
Vous pouvez également utiliser la documentation interactive Swagger disponible à l'adresse `http://VOTRE_DOMAINE_OU_IP/docs` pour tester l'API depuis votre navigateur.

## 3. Installation sur un nouveau serveur

### Outils utiles pour le déploiement

Pour interagir avec votre serveur Linux depuis une machine Windows, ces deux outils sont indispensables :
- **PuTTY (ou tout client SSH) :** Pour vous connecter en ligne de commande au serveur, y exécuter les commandes d'installation et gérer les services.
- **WinSCP (ou tout client SFTP) :** Pour transférer des fichiers de manière graphique entre votre ordinateur et le serveur (par exemple, pour déposer les GeoTIFFs sources dans le dossier `/data`).

### Architecture et technologies
Ce guide décrit l'installation complète de l'API en production avec une pile technologique robuste :
- **Gunicorn :** Un serveur d'application Python éprouvé pour gérer les processus de l'API en production.
- **Nginx :** Un serveur web haute performance qui agira comme *reverse proxy*. Il reçoit les requêtes des utilisateurs et les transmet à Gunicorn, en plus de servir directement les fichiers générés.
- **Systemd :** Le gestionnaire de services standard de Linux, utilisé pour que notre API tourne en continu comme un service, même après un redémarrage du serveur.

### Structure des dossiers

Une fois l'installation terminée, votre dossier `/home/VOTRE_UTILISATEUR/OSO_API` ressemblera à ceci :
```
OSO_API/
├── data/               # Contient les GeoTIFFs sources (format requis: OSO_2021.tif, OSO_2022.tif, etc.) A télécharger sur GEODES (voir avec pascal si besoin)
├── output/             # Les fichiers découpés y sont générés et stockés temporairement
├── venv/               # L'environnement virtuel Python avec les dépendances isolées
├── .env                # Fichier SECRET contenant les clés API (NE PAS PARTAGER)
├── .gitignore          # Indique à Git d'ignorer les fichiers sensibles et les dossiers générés
├── main.py             # Le code source de l'application FastAPI
├── requirements.txt    # La liste des dépendances Python du projet
└── gunicorn_conf.py    # Le fichier de configuration pour Gunicorn
```

### Fichier des dépendances (`requirements.txt`)

Pour simplifier l'installation des librairies Python, nous utilisons un fichier `requirements.txt`. Ce fichier liste toutes les dépendances nécessaires au projet, ce qui rend l'installation plus rapide et reproductible. Le contenu de ce fichier est généré à partir des `import` de votre code.

```txt
# Contenu du fichier requirements.txt
fastapi
uvicorn[standard]
gunicorn
rasterio
shapely
pydantic
python-dotenv
```

### Étapes d'installation

Suivez ces étapes sur votre serveur Debian ou Ubuntu.

#### Étape 1 : Prérequis système
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3.10-venv nginx -y
```

#### Étape 2 : Création de la structure du projet
Remplacez `VOTRE_UTILISATEUR` par votre nom d'utilisateur.
```bash
mkdir /home/VOTRE_UTILISATEUR/OSO_API
cd /home/VOTRE_UTILISATEUR/OSO_API
mkdir data output
```
*Utilisez WinSCP pour déposer vos fichiers GeoTIFF sources dans le dossier `data/`.*

#### Étape 3 : Environnement virtuel et installation des dépendances
```bash
# Créer et activer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Créer le fichier des dépendances
nano requirements.txt
```
Copiez-collez le contenu de la section `Fichier des dépendances` ci-dessus dans ce fichier, puis sauvegardez.

```bash
# Installer toutes les dépendances d'un coup
pip install -r requirements.txt
```

#### Étape 4 : Ajout du code et des fichiers de configuration

1.  **Code de l'application (`main.py`) :**
    Créez le fichier avec `nano main.py`, puis copiez-y le code de votre application.
    ```bash
    nano main.py
    ```

2.  **Fichier des clés API (`.env`) :**
    Ce fichier est sensible et ne doit pas être partagé.
    ```bash
    nano .env
    ```
    Ajoutez votre ou vos clés API, séparées par une virgule si vous en avez plusieurs.
    ```ini
    VALID_API_KEYS=clesecuriseinraespcd,une_autre_cle_si_besoin
    ```

3.  **Fichier `.gitignore` :**
    ```bash
    nano .gitignore
    ```
    Contenu :
    ```
    venv/
    __pycache__/
    *.pyc
    .env
    output/
    ```

#### Étape 5 : Configuration de Gunicorn
Créez un fichier `nano gunicorn_conf.py` avec le contenu suivant :
```python
# Adresse et port sur lesquels Gunicorn écoutera
bind = "127.0.0.1:8000"

# Nombre de processus workers.
workers = 4
```

#### Étape 6 : Configuration de Nginx
Créez un fichier de configuration pour Nginx.
```bash
sudo nano /etc/nginx/sites-available/oso_api
```
Collez cette configuration en remplaçant `VOTRE_DOMAINE_OU_IP` et `VOTRE_UTILISATEUR` :
```nginx
server {
    listen 80;
    server_name VOTRE_DOMAINE_OU_IP;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Permet de servir les fichiers générés dans /output/
    location /files/ {
        alias /home/VOTRE_UTILISATEUR/OSO_API/output/;
        autoindex off;
    }
}
```
Activez le site et redémarrez Nginx :
```bash
sudo ln -s /etc/nginx/sites-available/oso_api /etc/nginx/sites-enabled/
# Si le fichier 'default' existe, il peut entrer en conflit. Supprimez le lien symbolique.
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

#### Étape 7 : Création du service `systemd`
Créez un fichier de service avec `sudo nano /etc/systemd/system/oso_api.service` en remplaçant `VOTRE_UTILISATEUR` :
```ini
[Unit]
Description=Gunicorn instance to serve OSO API
After=network.target

[Service]
User=VOTRE_UTILISATEUR
Group=www-data
WorkingDirectory=/home/VOTRE_UTILISATEUR/OSO_API
# Charge les clés API depuis le fichier .env
EnvironmentFile=/home/VOTRE_UTILISATEUR/OSO_API/.env
# Commande pour lancer Gunicorn avec son fichier de config
ExecStart=/home/VOTRE_UTILISATEUR/OSO_API/venv/bin/gunicorn -c /home/VOTRE_UTILISATEUR/OSO_API/gunicorn_conf.py main:app

[Install]
WantedBy=multi-user.target
```
Activez et démarrez le service :
```bash
sudo systemctl daemon-reload
sudo systemctl start oso_api
sudo systemctl enable oso_api
# Vérifiez que tout fonctionne :
sudo systemctl status oso_api
```

#### Étape 8 : Sécurisation avec HTTPS
Si vous utilisez un nom de domaine, il est fortement recommandé d'activer HTTPS.

Votre API est maintenant déployée, sécurisée et prête à l'emploi.
