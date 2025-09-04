
# API de Découpe OSO

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