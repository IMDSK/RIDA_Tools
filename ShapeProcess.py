import os
import pandas as pd
from shapely.geometry import Polygon, mapping
import fiona
from pyproj import Proj, Transformer
from fiona.crs import from_epsg

def execute_script(csv_filename, base_path):
    df = pd.read_csv(csv_filename)
    transformer = Transformer.from_crs("epsg:4326", "epsg:32647", always_xy=True)

    schema = {
        'geometry': 'Polygon',
        'properties': {'id': 'int', 'area': 'str'}
    }

    shp_directory = os.path.join(base_path, 'SHP')
    os.makedirs(shp_directory, exist_ok=True)

    for index, row in df.iterrows():
        try:
            top_left_x, top_left_y = transformer.transform(row['top_left_lon'], row['top_left_lat'])
            bottom_right_x, bottom_right_y = transformer.transform(row['bottom_right_lon'], row['bottom_right_lat'])
            geometry = Polygon([
                (top_left_x, top_left_y),
                (bottom_right_x, top_left_y),
                (bottom_right_x, bottom_right_y),
                (top_left_x, bottom_right_y)
            ])
            area = row['area']
            area_directory = os.path.join(shp_directory, area)
            os.makedirs(area_directory, exist_ok=True)
            shapefile_name = os.path.join(area_directory, f'my_shapefile_{index}.shp')
            with fiona.open(shapefile_name, 'w', driver='ESRI Shapefile', crs=from_epsg(32647), schema=schema) as out_file:
                out_file.write({
                    'geometry': mapping(geometry),
                    'properties': {'id': index, 'area': area}
                })
            print(f"Shapefile {shapefile_name} created successfully in the '{area}' folder within 'SHP'.")
        except Exception as e:
            print(f"Failed to create shapefile for {area}: {e}")