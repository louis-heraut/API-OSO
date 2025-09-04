import os
import datetime
import uuid
import asyncio
import secrets
import json
from enum import Enum
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from shapely.geometry import Polygon, box, mapping
import rasterio
from rasterio.mask import mask
from rasterio.warp import transform_geom

# ─── Configuration ──────────────────────────────────────────────────────────
load_dotenv()
API_KEYS_PATH = os.getenv("API_KEYS_PATH")

DATA_DIR = "data"
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Périmètre géographique autorisé (France métropolitaine, un peu élargi)
# Format: min_lon, min_lat, max_lon, max_lat
FRANCE_METRO_BBOX = box(-5.5, 41.0, 9.8, 51.5)

# Années pour lesquelles des données sont disponibles
class AvailableYears(int, Enum):
    y2016 = 2016
    y2017 = 2017
    y2018 = 2018
    y2019 = 2019
    y2020 = 2020
    y2021 = 2021
    y2022 = 2022
    y2023 = 2023

# ─── Application FastAPI ────────────────────────────────────────────────────
app = FastAPI(
    title="API Découpe GeoTIFF",
    description="Un service pour découper des rasters OSO selon un polygone. L'authentification par clé API est requise.",
    version="1.1.0",
    contact={
        "name": "Louis Héraut (INRAE, UR RiverLy, Villeurbanne, France)",
        "email": "louis.heraut@inrae.fr",
        "url": "https://github.com/louis-heraut/API-OSO"
    }
)

app.mount("/files", StaticFiles(directory=OUTPUT_DIR), name="files")

# ─── Sécurité ───────────────────────────────────────────────────────────────
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# async def get_api_key(api_key_header: str = Security(api_key_header)):
#     """Valide la clé API fournie dans l'en-tête de la requête."""
#     valid_keys_str = os.getenv("VALID_API_KEYS")
#     if not valid_keys_str:
#         raise HTTPException(status_code=500, detail="Configuration des clés API manquante sur le serveur.")

#     valid_keys = [key.strip() for key in valid_keys_str.split(",")]

#     if not api_key_header or not any(secrets.compare_digest(api_key_header, key) for key in valid_keys):
#         raise HTTPException(status_code=403, detail="Clé API invalide ou manquante.")
#     return api_key_header

def load_keys_from_file():
    """Load API keys from JSON file safely."""
    if not API_KEYS_PATH or not os.path.exists(API_KEYS_PATH):
        return {}
    with open(API_KEYS_PATH, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

async def get_api_key(api_key_header: str = Security(api_key_header)):
    """Valide la clé API fournie dans l'en-tête de la requête."""
    keys = load_keys_from_file()
    if not keys:
        raise HTTPException(status_code=500, detail="Aucune clé API n'est configurée sur le serveur.")

    valid_keys = list(keys.values())  # get just the key strings

    if not api_key_header or not any(secrets.compare_digest(api_key_header, key) for key in valid_keys):
        raise HTTPException(status_code=403, detail="Clé API invalide ou manquante.")
    return api_key_header

# ─── Modèles de données (Pydantic) ──────────────────────────────────────────
class ClipRequest(BaseModel):
    points: List[List[float]] = Field(
        ...,
        description="Liste de points [longitude, latitude] en WGS84.",
        example=[[5.72, 45.18], [5.73, 45.18], [5.73, 45.19], [5.72, 45.19], [5.72, 45.18]]
    )
    year: AvailableYears = Field(..., description="Année du raster OSO à utiliser.")
    filename: Optional[str] = Field(None, description="Nom de base pour le fichier de sortie (sans extension).")

class ClipResponse(BaseModel):
    url: str = Field(..., description="URL de téléchargement du fichier découpé (valide 1 heure).")

# ─── Tâches en arrière-plan ─────────────────────────────────────────────────
async def _remove_file_after_delay(path: str, delay_seconds: int = 3600):
    """Supprime un fichier après un certain délai."""
    await asyncio.sleep(delay_seconds)
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass # Ignorer les erreurs (ex: fichier déjà supprimé)

# ─── Point de terminaison (Endpoint) ────────────────────────────────────────
@app.post(
    "/clip/",
    response_model=ClipResponse,
    summary="Découpe un raster OSO",
    dependencies=[Depends(get_api_key)]
)
async def clip_polygon(req: ClipRequest, request: Request):
    """
    Découpe un raster OSO pour une année donnée à partir d'un polygone.
    - Le polygone doit être en France métropolitaine.
    - Le fichier généré est supprimé après 1 heure.
    """
    # 1. Validation du polygone (géométrie et localisation)
    try:
        poly = Polygon(req.points)
        if not poly.is_valid or poly.is_empty:
            raise ValueError("Géométrie du polygone invalide ou vide.")
        if not FRANCE_METRO_BBOX.contains(poly):
            raise ValueError("Le polygone est en dehors de la zone supportée (France métropolitaine).")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 2. Vérification du fichier source
    src_path = os.path.join(DATA_DIR, f"OCS_{req.year.value}.tif")
    if not os.path.exists(src_path):
        raise HTTPException(status_code=404, detail=f"Le fichier de données pour l'année {req.year.value} est introuvable.")

    # # 3. Découpage du raster
    # try:
    #     with rasterio.open(src_path) as src:
    #         geom_in_crs = transform_geom("EPSG:4326", src.crs, mapping(poly))
    #         out_image, out_transform = mask(src, [geom_in_crs], crop=True, nodata=src.nodata)
    #         out_meta = src.meta.copy()
    #         out_meta.update({
    #             "driver": "GTiff",
    #             "height": out_image.shape[1],
    #             "width": out_image.shape[2],
    #             "transform": out_transform,
    #         })
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"Erreur lors du traitement du raster : {e}")

    # # 4. Génération du fichier de sortie
    # base_name = os.path.splitext(req.filename.strip())[0] if req.filename else "clip"
    # timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    # unique_suffix = uuid.uuid4().hex[:8]
    # unique_name = f"{base_name}_{timestamp}_{unique_suffix}.tif"
    # out_path = os.path.join(OUTPUT_DIR, unique_name)

    # with rasterio.open(out_path, "w", **out_meta) as dst:
    #     dst.write(out_image)

    # 3. Découpage du raster
    try:
        with rasterio.open(src_path) as src:
            geom_in_crs = transform_geom("EPSG:4326", src.crs, mapping(poly))
            out_image, out_transform = mask(src, [geom_in_crs], crop=True, nodata=src.nodata)
            out_meta = src.meta.copy()
            out_meta.update({
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
            })

            # Récupérer le colormap tant que src est ouvert
            cmap = None
            if out_meta.get("count", 1) == 1:  # seulement pour les rasters 1 bande
                try:
                    cmap = src.colormap(1)
                except ValueError:
                    cmap = None

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement du raster : {e}")

    # 4. Génération du fichier de sortie
    base_name = os.path.splitext(req.filename.strip())[0] if req.filename else "clip"
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    unique_suffix = uuid.uuid4().hex[:8]
    unique_name = f"{base_name}_{timestamp}_{unique_suffix}.tif"
    out_path = os.path.join(OUTPUT_DIR, unique_name)

    with rasterio.open(out_path, "w", **out_meta) as dst:
        dst.write(out_image)
        # Réécrire le colormap si présent
        if cmap:
            dst.write_colormap(1, cmap)


    # 5. Planification de la suppression et construction de la réponse
    asyncio.create_task(_remove_file_after_delay(out_path))
    file_url = f"{str(request.base_url).rstrip('/')}/files/{unique_name}"

    return ClipResponse(url=file_url)
