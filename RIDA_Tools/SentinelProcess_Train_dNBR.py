# SentinelProcess_Train_rNDI.py

import os
import shutil
import time
from threading import Timer
from time import gmtime, strftime
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from skimage import measure
import rasterio
from rasterio.transform import from_origin
from rasterio.enums import Resampling
import geopandas as gpd
from rasterio.features import shapes
from shapely.geometry import shape
from xml.etree import ElementTree as ET
import math
from rasterio.warp import transform
from osgeo import gdal
import warnings
import csv
import json
warnings.filterwarnings(action='ignore')

# Load the configuration values
with open("D:\\RIDA\\RIDA_Tools\\config_dnbr.json", "r") as f:
    config = json.load(f)

# Extracting configuration values
burn_con_lv1_threshold_dnbr = config["burn_con_lv1_threshold_dnbr"]
burn_con_lv3_threshold_dnbr = config["burn_con_lv3_threshold_dnbr"]
burn_con_lv4_threshold_dnbr = config["burn_con_lv4_threshold_dnbr"]

systemCooldown = 2
Error_Limit = 1
mode = True

# Define paths with double backslashes
Drive = "D:\\RIDA\\Sentinel_Process"
Image = os.path.join(Drive, "Image")
Image_Pre = os.path.join(Drive, "Image_Pre")
Image_Finish = os.path.join(Drive, "Image_Finish")
Image_Missing = os.path.join(Drive, "Image_Missing")
Output = os.path.join(Drive, "Output")
Rtbcon = os.path.join(Drive, "Raster_BurnCon")
Rtbreg = os.path.join(Drive, "Raster_BurnReg")
RtbShape = os.path.join(Drive, "Raster_BurnShape")
RtbLevel = os.path.join(Drive, "Raster_BurnLevel")

Track_arr = [
    "Area1\\", "Area2\\", "Area3\\", "Area4\\", "Area5\\", "Area6\\", "Area7\\", "Area8\\", "Area9\\", "Area10\\", "Area11\\", "Area12\\",
    "Area00\\", "Area01\\", "Area02\\", "Area03\\", "Area04\\", "Area05\\", "Area06\\", "Area07\\", "Area08\\", "Area09\\",
    "Area10\\", "Area11\\", "Area12\\", "Area13\\", "Area14\\", "Area15\\", "Area16\\", "Area17\\", "Area18\\", "Area19\\",
    "Area20\\", "Area21\\", "Area22\\", "Area23\\", "Area24\\", "Area25\\", "Area26\\", "Area27\\", "Area28\\", "Area29\\",
    "Area30\\", "Area31\\", "Area32\\", "Area33\\", "Area34\\", "Area35\\", "Area36\\", "Area37\\", "Area38\\", "Area39\\",
    "Area40\\", "Area41\\", "Area42\\", "Area43\\", "Area44\\", "Area45\\", "Area46\\", "Area47\\", "Area48\\", "Area49\\",
    "Area50\\", "Area51\\", "Area52\\", "Area53\\", "Area54\\", "Area55\\", "Area56\\", "Area57\\", "Area58\\", "Area59\\",
    "Area60\\", "Area61\\", "Area62\\", "Area63\\", "Area64\\", "Area65\\", "Area66\\", "Area67\\", "Area68\\", "Area69\\",
    "Area70\\", "Area71\\", "Area72\\", "Area73\\", "Area74\\", "Area75\\", "Area76\\", "Area77\\", "Area78\\", "Area79\\",
    "Area80\\", "Area81\\", "Area82\\", "Area83\\", "Area84\\", "Area85\\"
]

def loadCooldown():
    global mode

def print_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def save_as_geotiff(data, output_path, resolution=10):
    height, width = data.shape
    transform = from_origin(0, height * resolution, resolution, -resolution)
    profile = {
        'driver': 'GTiff',
        'count': 1,
        'dtype': 'uint8',
        'width': width,
        'height': height,
        'crs': 'EPSG:4326',
        'transform': transform,
        'compress': 'packbits',
        'tiled': True,
        'interleave': 'band',
    }

    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(data.astype('uint8'), 1)

def Move_File(FileName, CurrDir, DestDir):
    try:
        if os.path.exists(os.path.join(CurrDir, FileName)):
            if os.path.exists(os.path.join(DestDir, FileName)):
                os.remove(os.path.join(DestDir, FileName))
            shutil.copy(os.path.join(CurrDir, FileName), DestDir)
            t = Timer(1, loadCooldown)
            t.start()
            t.join()
            os.remove(os.path.join(CurrDir, FileName))
            print(print_time() + f"Raster_Process :: Move File {FileName} Complete")
    except Exception as e:
        print(print_time() + f"Raster_Process :: Can not Move File {FileName}")
        print(print_time() + str(e))

def Raster_Process(Track):
    global mode, Image, Image_Pre, Image_Finish, Image_Missing, Output, Error_Limit
    Loop_Limit = 0
    image_track = os.path.join(Image, Track)
    rasters = [r for r in os.listdir(image_track) if r.endswith('B1210.jp2')]

    for raster in rasters:
        if Loop_Limit > 0:
            mode = True
            return
        Full_name = os.path.splitext(raster)[0]
        Mid_name = Full_name[:23]
        Short_name = Full_name[:6]

        BFB02 = os.path.join(Image_Pre, Track, f"{Short_name}_B02.jp2")
        BFB03 = os.path.join(Image_Pre, Track, f"{Short_name}_B03.jp2")
        BFB04 = os.path.join(Image_Pre, Track, f"{Short_name}_B04.jp2")
        BFB08 = os.path.join(Image_Pre, Track, f"{Short_name}_B08.jp2")
        BFB1210 = os.path.join(Image_Pre, Track, f"{Short_name}_B1210.jp2")

        AFB02 = os.path.join(Image, Track, f"{Mid_name}B02.jp2")
        AFB03 = os.path.join(Image, Track, f"{Mid_name}B03.jp2")
        AFB04 = os.path.join(Image, Track, f"{Mid_name}B04.jp2")
        AFB0510 = os.path.join(Image, Track, f"{Mid_name}B0510.jp2")
        AFB0610 = os.path.join(Image, Track, f"{Mid_name}B0610.jp2")
        AFB0710 = os.path.join(Image, Track, f"{Mid_name}B0710.jp2")
        AFB08 = os.path.join(Image, Track, f"{Mid_name}B08.jp2")
        AFB8A10 = os.path.join(Image, Track, f"{Mid_name}B8A10.jp2")
        AFB0910 = os.path.join(Image, Track, f"{Mid_name}B0910.jp2")
        AFB1210 = os.path.join(Image, Track, f"{Mid_name}B1210.jp2")

        tile = Short_name
        date = Full_name[7:15] 
        
        print(print_time() + f"Checking files for {Full_name}")
        file_check = {
            "BFB08": os.path.exists(BFB08),
            "BFB1210": os.path.exists(BFB1210),
            "AFB02": os.path.exists(AFB02),
            "AFB03": os.path.exists(AFB03),
            "AFB04": os.path.exists(AFB04),
            "AFB0510": os.path.exists(AFB0510),
            "AFB0610": os.path.exists(AFB0610),
            "AFB0710": os.path.exists(AFB0710),
            "AFB08": os.path.exists(AFB08),
            "AFB8A10": os.path.exists(AFB8A10),
            "AFB0910": os.path.exists(AFB0910),
            "AFB1210": os.path.exists(AFB1210),
        }
        for key, value in file_check.items():
            print(f"{key}: {value}")

        if all(file_check.values()):
            print(print_time() + "Raster_Process :: Start Raster Process Please Wait....")
            Loop_Limit += 1
            t = Timer(3, loadCooldown)
            t.start()
            t.join()

            try:
                print(print_time()+"Raster_Process :: Raster Process " + Full_name[:22])

                threshold_value = 0

                with rasterio.open(AFB02) as src_AFB02:
                    data_AFB02 = src_AFB02.read(1)
                    print("Shape of data_AFB02:", data_AFB02.shape) 
                    
                with rasterio.open(AFB03) as src_AFB03:
                    data_AFB03 = src_AFB03.read(1)
                    print("Shape of data_AFB03:", data_AFB03.shape) 

                with rasterio.open(AFB04) as src_AFB04:
                    data_AFB04 = src_AFB04.read(1)
                    print("Shape of data_AFB04:", data_AFB04.shape)

                with rasterio.open(AFB0510) as src_AFB0510:
                    data_AFB0510 = src_AFB0510.read(1)
                    print("Shape of data_AFB05:", data_AFB0510.shape)  
                
                with rasterio.open(AFB0610) as src_AFB0610:
                    data_AFB0610 = src_AFB0610.read(1)
                    print("Shape of data_AFB06:", data_AFB0610.shape) 
                
                with rasterio.open(AFB0710) as src_AFB0710:
                    data_AFB0710 = src_AFB0710.read(1)
                    print("Shape of data_AFB07:", data_AFB0710.shape)  
                
                with rasterio.open(BFB08) as src_BFB08, rasterio.open(AFB08) as src_AFB08, rasterio.open(AFB8A10) as src_AFB8A10:
                    data_BFB08 = src_BFB08.read(1)
                    data_AFB08 = src_AFB08.read(1)
                    data_AFB8A10 = src_AFB8A10.read(1)
                    print("Shape of data_AFB08:", data_AFB08.shape)  
                    print("Shape of data_AFB8A:", data_AFB8A10.shape)  

                with rasterio.open(AFB0910) as src_AFB0910:
                    data_AFB0910 = src_AFB0910.read(1) 
                
                with rasterio.open(BFB1210) as src_BFB1210,rasterio.open(AFB1210) as src_AFB1210:
                    data_BFB1210 = src_BFB1210.read(1)
                    data_AFB1210 = src_AFB1210.read(1)
                    print("Shape of data_BFB12:", data_BFB1210.shape) 
                    print("Shape of data_AFB12:", data_AFB1210.shape)

                bfb08_shape = data_BFB08.shape
                data_BFB08 = np.resize(data_BFB08, bfb08_shape)
                data_BFB1210 = np.resize(data_BFB1210, bfb08_shape)
                data_AFB02 = np.resize(data_AFB02, bfb08_shape)
                data_AFB03 = np.resize(data_AFB03, bfb08_shape)
                data_AFB04 = np.resize(data_AFB04, bfb08_shape)
                data_AFB0510 = np.resize(data_AFB0510, bfb08_shape)
                data_AFB0610 = np.resize(data_AFB0610, bfb08_shape)
                data_AFB0710 = np.resize(data_AFB0710, bfb08_shape)
                data_AFB8A10 = np.resize(data_AFB8A10, bfb08_shape)
                data_AFB0910 = np.resize(data_AFB0910, bfb08_shape)
                data_AFB1210 = np.resize(data_AFB1210, bfb08_shape)

                print("Shape of data_AFB02 (Reshape):", data_AFB02.shape) 
                print("Shape of data_AFB03 (Reshape):", data_AFB03.shape)  
                print("Shape of data_AFB04 (Reshape):", data_AFB04.shape)
                print("Shape of data_AFB05 (Reshape):", data_AFB0510.shape)  
                print("Shape of data_AFB06 (Reshape):", data_AFB0610.shape) 
                print("Shape of data_AFB07 (Reshape):", data_AFB0710.shape)  
                print("Shape of data_AFB08 (Reshape):", data_AFB08.shape)  
                print("Shape of data_AFB8A (Reshape):", data_AFB8A10.shape)  
                print("Shape of data_AFB09 (Reshape):", data_AFB0910.shape)  
                print("Shape of data_BFB12 (Reshape):", data_BFB1210.shape) 
                print("Shape of data_AFB12 (Reshape):", data_AFB1210.shape) 

                PreNBR_data = (data_BFB08 - data_BFB1210) / (data_BFB08 + data_BFB1210)
                PostNBR_data = (data_AFB08 - data_AFB1210) / (data_AFB08 + data_AFB1210)

                print(print_time()+"Raster_Process :: Burn Raster Condition")

                rNDI = (data_BFB08 - data_AFB08) /(data_BFB08 + data_AFB08)    
                dNBR = PreNBR_data-PostNBR_data
                dNDWI = (data_AFB03 - data_AFB08) /(data_AFB03 + data_AFB08)
                dNDVI = (data_AFB08-data_AFB04) / (data_AFB08+data_AFB04)

                def burn_con(dNBR, dNDVI, data_AFB03, data_AFB08, output_path):
                    burn_con_lv1 = np.where((dNBR > burn_con_lv1_threshold_dnbr), 1, 0)
                    burn_con_lv2 = np.where((data_AFB08 > data_AFB03), 1, 0)
                    burn_con_lv3 = np.where((dNDVI < burn_con_lv3_threshold_dnbr), 1, 0)
                    burn_con_lv4 = np.where((data_AFB08 < burn_con_lv4_threshold_dnbr), 1, 0)
                    burnCon_Final = np.where(((burn_con_lv1 == 1) &(burn_con_lv2 == 1) &(burn_con_lv3 == 1) &(burn_con_lv4== 1)), 1, 0)
                    burnCon_Final = np.where(
                        np.any(
                            (
                                (data_AFB08 < 100),(data_AFB8A10 < 100),(data_AFB03 < 100),
                                (data_AFB02 < 100),(data_AFB04 < 100),(data_AFB0510 < 100),
                                (data_AFB0610 < 100),(data_AFB0710 < 100),(data_AFB0910 < 100),
                                (data_AFB1210 < 100),
                            ),
                            axis=0,
                        ),
                        0,
                        burnCon_Final,
                    )
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    save_as_geotiff(burnCon_Final, output_path)

                output_path = os.path.join(Rtbcon, Track, f"{Full_name}.tif")
                burn_con(dNBR, dNDVI, data_AFB03, data_AFB08, output_path)

                print(print_time()+"Raster_Process :: RegionGroup")

                BCON = os.path.join(Rtbcon, Track, f"{Full_name}.tif")

                with rasterio.open(BCON) as src_BCON:
                    data_BCON = src_BCON.read(1)

                def burn_region(data_BCON, track, full_name):
                    burnRegionGrp = measure.label(data_BCON, connectivity=1)
                    print(print_time() + f"Raster_Process :: Region > {threshold_value}")

                    burnRegionGrpThresholded = np.where(burnRegionGrp > threshold_value, 1, 0)

                    burnRegion = np.where(burnRegionGrpThresholded == 1, 1, 0)

                    print(print_time() + "Raster_Process :: Save Raster")

                    output_path = os.path.join(Rtbreg, Track, f"{Short_name}_B12.tif")
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    save_as_geotiff(burnRegion, output_path)
                    
                    return burnRegion
                
                burn_region(data_BCON, Track, Full_name)
                burnRegion = burn_region(data_BCON, Track, Full_name)

                print(print_time()+"  DataFrame Process ")

                with rasterio.open(BFB08) as src:
                    bounds = src.bounds
                    width, height = src.width, src.height
                    crs = src.crs

                    lats = np.linspace(bounds.top, bounds.bottom, height)
                    longs = np.linspace(bounds.left, bounds.right, width)
                    lon_grid, lat_grid = np.meshgrid(longs, lats)
                    lat_list = lat_grid.ravel()
                    lon_list = lon_grid.ravel()

                    lat_wgs84, lon_wgs84 = transform(crs, 'EPSG:4326', lon_list, lat_list)
                    
                    band_3_data = data_AFB03.ravel()
                    band_4_data = data_AFB04.ravel()
                    band_5_data = data_AFB0510.ravel()
                    band_6_data = data_AFB0610.ravel()
                    band_7_data = data_AFB0710.ravel()
                    band_8_data = data_AFB08.ravel()
                    band_8A_data = data_AFB8A10.ravel()
                    band_9_data = data_AFB0910.ravel()
                    band_12_data = data_AFB1210.ravel()
                    label_data = burnRegion.ravel()

                    df = pd.DataFrame({
                            'Tile': tile,
                            'Date': date,
                            'Latitude_WGS84': lon_wgs84, # Lat and lng wgs84 is flip verticle map so i need to swap value 
                            'Longitude_WGS84': lat_wgs84,
                            'Band_3_Post': band_3_data,
                            'Band_4_Post': band_4_data,
                            'Band_5_Post': band_5_data,
                            'Band_6_Post': band_6_data,
                            'Band_7_Post': band_7_data,
                            'Band_8_Post': band_8_data,
                            'Band_8A_Post': band_8A_data,
                            'Band_9_Post': band_9_data,
                            'Band_12_Post': band_12_data,
                            'Label': label_data
                        })

                    df.fillna(0, inplace=True)

                    output_filename = f"{Full_name[:-6]}.csv" 
                    output_dir = os.path.join(Rtbcon, Track)
                    os.makedirs(output_dir, exist_ok=True)  # Create the subdirectory if it doesn't exist
                    output_path = os.path.join(output_dir, output_filename)
                    df.to_csv(output_path, index=False)

                    # # Copy AFB02, AFB03, and AFB04 images to the output directory
                    # shutil.copy(AFB02, output_dir)
                    # shutil.copy(AFB03, output_dir)
                    # shutil.copy(AFB04, output_dir)

                print(print_time()+"Raster_Process :: Burn Raster Process Complate")

                def reclassify_raster(input_raster, output_raster, remap_dict):
                    with rasterio.open(input_raster) as src:
                        data = src.read(1)
                        profile = src.profile

                        for old_value, new_value in remap_dict.items():
                            data = np.where(data == old_value, new_value, data)

                        output_dir = os.path.dirname(output_raster)
                        os.makedirs(output_dir, exist_ok=True)  # Ensure the directory exists

                        with rasterio.open(output_raster, 'w', **profile) as dst:
                            dst.write(data, 1)

                burnRegion = os.path.join(Rtbreg, Track, f"{Short_name}_B12.tif")
                burnReclass = os.path.join(Rtbreg, Track, f"{Short_name}_BurnReclass.tif")
                remap_dict = {1: 1}

                reclassify_raster(burnRegion, burnReclass, remap_dict)

                print("After burn reclasss")

                def raster_to_polygon(input_raster, output_shapefile, simplify=0, value_field="VALUE"):
                    with rasterio.open(input_raster) as src:
                        image = src.read(1)
                        shapes = rasterio.features.shapes(image, transform=src.transform)

                        geometries = []
                        values = []

                        for geom, value in shapes:
                            if simplify > 0:
                                geom = shape(geom).simplify(simplify)

                            geometries.append(geom)
                            values.append(value)

                        gdf = gpd.GeoDataFrame({value_field: values, 'geometry': geometries})

                        if simplify > 0:
                            gdf['geometry'] = gdf['geometry'].apply(lambda x: x.simplify(simplify))

                        dissolved_gdf = gdf.dissolve(by=value_field)
                        os.makedirs(os.path.dirname(output_shapefile), exist_ok=True)  # Ensure directory exists
                        dissolved_gdf.to_file(output_shapefile)

                burnReclass = os.path.join(Rtbreg, Track, f"{Short_name}_BurnReclass.tif")
                output_shapefile = os.path.join(RtbShape, Track, f"{Short_name}_B12.shp")
                simplify_value = 0.1

                raster_to_polygon(burnReclass, output_shapefile, simplify=simplify_value)
                
                Error_Limit = 2
                print(print_time()+"Plot Image and Label \n \n")


                # Read true color bands
                with rasterio.open(BFB02) as src:
                    band2 = src.read(1)
                    profile = src.profile

                with rasterio.open(BFB03) as src:
                    band3 = src.read(1)

                with rasterio.open(BFB04) as src:
                    band4 = src.read(1)

                true_color_image = np.dstack((band4, band3, band2))

                true_color_normalized = true_color_image / true_color_image.max()

                true_color_uint16 = (true_color_normalized * 65535).astype(np.uint16)

                # Define the output path for the new image
                output_path = os.path.join(Rtbcon, Track, f"{Mid_name[:-1]}.tif")

                profile.update(count=3, dtype=rasterio.uint16)

                with rasterio.open(output_path, 'w', **profile) as dst:
                    dst.write(true_color_uint16[:, :, 0], 1)  # Red channel
                    dst.write(true_color_uint16[:, :, 1], 2)  # Green channel
                    dst.write(true_color_uint16[:, :, 2], 3)  # Blue channel

                print(f"True color image saved to {output_path}")

                # Paths to the shapefile
                shapefile_path = os.path.join(RtbShape, Track, f"{Short_name}_B12.shp")

                # Read the shapefile
                gdf = gpd.read_file(shapefile_path)

                # Create side by side plots
                fig, axes = plt.subplots(1, 2, figsize=(8, 5))

                # Plot true color image
                axes[0].imshow(true_color_normalized)
                axes[0].set_title('True Color Image')
                axes[0].axis('off')

                # Plot shapefile only
                gdf.plot(ax=axes[1], color='red', edgecolor='red', alpha=0.5)
                axes[1].set_title('Shapefile Only')
                axes[1].axis('off')

                plt.tight_layout()
                plt.show()

                print(print_time()+"Raster_Process :: Raster_Process ALL Complate  \n \n")
                

            except Exception as e:
                print(print_time()+"Raster_Process :: !!!!!!!!!! RASTER ERROR !!!!!!!!!!")
                print(print_time() + str(e))
                Error_Limit = Error_Limit - 1
                if Error_Limit < 1 :
                    print(print_time()+"Raster_Process :: !!!!!!!!!! RASTER ERROR 2 Time MoveFile to Image_Missin")
                    Move_File(Mid_name + "B03.jp2", Image + Track, Image_Missing + Track)
                    Move_File(Mid_name + "B04.jp2", Image + Track, Image_Missing + Track)
                    Move_File(Mid_name + "B08.jp2", Image + Track, Image_Missing + Track)
                    Move_File(Mid_name + "B12.jp2", Image + Track, Image_Missing + Track)
                    Move_File(Mid_name + "B1210.jp2", Image + Track, Image_Missing + Track)
                    Move_File(Mid_name + "B1210.jp2.aux.xml", Image + Track, Image_Missing + Track)
                    Move_File(Mid_name + "B1210.jp2.ovr", Image + Track, Image_Missing + Track)
                    Move_File(Mid_name + "B1210.jp2.xml", Image + Track, Image_Missing + Track)
                    Error_Limit = 2

        else:
            print(print_time() + f"Raster_Process :: {Full_name} Image not Found !!!!")
            for key, value in file_check.items():
                print(f"{key}: {value}")
        
    print(print_time() + "Wait New Raster ::")
    mode = True

def main():
    current_dir = os.getcwd()
    print("Current Working Directory:", current_dir)
    global mode, Image_Post
    print(print_time() + "Application Start ::")

    # Get the list of directories inside the 'Image' directory
    image_directories = [d for d in os.listdir(Image) if os.path.isdir(os.path.join(Image, d))]

    for area_dir in image_directories:
        area_path = os.path.join(Image, area_dir)
        rasters = [r for r in os.listdir(area_path) if r.endswith('B1210.jp2')]
        if rasters:
            mode = False
            print(print_time() + f"Found NEW Raster in Area: {area_dir}")
            try:
                Raster_Process(area_dir)
            except Exception as e:
                print(print_time() + "!!!!!!!!!SYSTEM ERROR !!!!!!!!!!!")
                print(print_time() + str(e))
                print(print_time() + "Wait New Raster ::")
        else:
            print(f"No rasters found in directory: {area_path}")

    print(print_time() + f"{len(image_directories)} Area(s) processed.")

main()