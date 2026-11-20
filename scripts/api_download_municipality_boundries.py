import json
from pathlib import Path
from shutil import copyfileobj
from tempfile import TemporaryDirectory
from urllib.request import urlopen
from zipfile import ZipFile

import geopandas as gpd
import shapely


STAC_ITEM_URL = (
    "https://data.geo.admin.ch/api/stac/v1/collections/"
    "ch.swisstopo.swissboundaries3d/items/swissboundaries3d_2026-01"
)
ZIP_NAME = "swissboundaries3d_2026-01_2056_5728.gpkg.zip"
TOLERANCE_METRES = 50
GEOJSON_NAME = f"municipalities_api_{TOLERANCE_METRES}m.geojson"


def main():
    project_root = Path(__file__).resolve().parents[1]
    output_dir = project_root / "data" / "raw_data" / "app_data"
    output_dir.mkdir(parents=True, exist_ok=True)

    zip_path = output_dir / ZIP_NAME
    geojson_path = output_dir / GEOJSON_NAME

    print("Frage die STAC-API nach dem Datenstand Januar 2026 ab.")
    with urlopen(STAC_ITEM_URL, timeout=30) as response:
        item = json.load(response)
    download_url = item["assets"][ZIP_NAME]["href"]

    with TemporaryDirectory(dir=output_dir) as temp_dir:
        temp_dir = Path(temp_dir)

        if not zip_path.is_file():
            print(f"Lade {ZIP_NAME} herunter.")
            temp_zip = temp_dir / ZIP_NAME
            with urlopen(download_url, timeout=60) as response:
                with temp_zip.open("wb") as file:
                    copyfileobj(response, file)
            temp_zip.replace(zip_path)
        else:
            print(f"Verwende das vorhandene ZIP-Archiv {ZIP_NAME}.")

        gpkg_path = temp_dir / "boundaries.gpkg"
        with ZipFile(zip_path) as archive:
            (gpkg_member,) = [
                name for name in archive.namelist() if name.lower().endswith(".gpkg")
            ]
            with archive.open(gpkg_member) as source:
                with gpkg_path.open("wb") as target:
                    copyfileobj(source, target)

        municipalities = gpd.read_file(
            gpkg_path,
            layer="tlm_hoheitsgebiet",
            engine="pyogrio",
        )
        municipalities = municipalities.loc[
            municipalities["objektart"].eq("Gemeindegebiet")
            & municipalities["kantonsnummer"].notna()
            & municipalities["bfs_nummer"].notna(),
            ["bfs_nummer", "kantonsnummer", "name", "geometry"],
        ].copy()

        if municipalities.empty:
            raise ValueError("Im GeoPackage wurden keine Schweizer Gemeinden gefunden.")

        municipalities = municipalities.to_crs("EPSG:2056")
        geometry = shapely.force_2d(municipalities.geometry.array)

        if shapely.coverage_is_valid(geometry):
            simplified = shapely.coverage_simplify(geometry, tolerance=TOLERANCE_METRES)
        else:
            print(
                "Einige Grenzkanten stimmen im Eingangslayer nicht überein. "
                "Die Flächen werden einzeln vereinfacht. "
                "Dabei können kleine Lücken oder Überlappungen entstehen."
            )
            simplified = shapely.simplify(
                geometry, tolerance=TOLERANCE_METRES, preserve_topology=True
            )

        municipalities = municipalities.set_geometry(
            gpd.GeoSeries(simplified, index=municipalities.index, crs="EPSG:2056")
        )
        municipalities = municipalities.to_crs("EPSG:4326")

        temp_geojson = temp_dir / GEOJSON_NAME
        municipalities.to_file(
            temp_geojson,
            driver="GeoJSON",
            engine="pyogrio",
            index=False,
            coordinate_precision=6,
        )
        temp_geojson.replace(geojson_path)

    print(f"GeoJSON gespeichert: {geojson_path}")
    print(f"Gemeinden: {municipalities['bfs_nummer'].nunique()}")


if __name__ == "__main__":
    main()
