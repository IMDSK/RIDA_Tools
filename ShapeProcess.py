import os
import pandas as pd
from shapely.geometry import Polygon, mapping
import fiona
from pyproj import Transformer
from fiona.crs import from_epsg

def execute_script(csv_filename, base_path):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(csv_filename)
    # Create a transformer to convert coordinates from EPSG:4326 to EPSG:32647
    transformer = Transformer.from_crs("epsg:4326", "epsg:32647", always_xy=True)

    # Define the schema for the shapefile
    schema = {
        'geometry': 'Polygon',
        'properties': {'id': 'int', 'area': 'str'}
    }

    # Create the SHP directory if it doesn't exist
    shp_directory = os.path.join(base_path, 'SHP')
    os.makedirs(shp_directory, exist_ok=True)

    # Iterate through each row in the DataFrame
    for index, row in df.iterrows():
        try:
            # Transform the coordinates from EPSG:4326 to EPSG:32647
            top_left_x, top_left_y = transformer.transform(row['top_left_lon'], row['top_left_lat'])
            bottom_right_x, bottom_right_y = transformer.transform(row['bottom_right_lon'], row['bottom_right_lat'])
            
            # Create a polygon geometry from the transformed coordinates
            geometry = Polygon([
                (top_left_x, top_left_y),
                (bottom_right_x, top_left_y),
                (bottom_right_x, bottom_right_y),
                (top_left_x, bottom_right_y)
            ])
            
            # Get the area name from the current row
            area = row['area']
            # Create a directory for the area if it doesn't exist
            area_directory = os.path.join(shp_directory, area)
            os.makedirs(area_directory, exist_ok=True)
            
            # Define the shapefile name based on the area name
            shapefile_name = os.path.join(area_directory, f'{area}.shp')
            
            # Write the shapefile with the geometry and properties
            with fiona.open(shapefile_name, 'w', driver='ESRI Shapefile', crs=from_epsg(32647), schema=schema) as out_file:
                out_file.write({
                    'geometry': mapping(geometry),
                    'properties': {'id': index, 'area': area}
                })
            print(f"Shapefile {shapefile_name} created successfully in the '{area}' folder within 'SHP'.")
        
        except Exception as e:
            print(f"Failed to create shapefile for {area}: {e}")

