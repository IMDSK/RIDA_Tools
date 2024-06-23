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
from rasterio.warp import transform
import warnings
import csv
import dask.dataframe as dd  # Using Dask for handling large dataframes
from concurrent.futures import ThreadPoolExecutor  # For parallel processing

warnings.filterwarnings(action='ignore')

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

# Adjusted file paths in Track_arr list
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

        if all(
            [
                os.path.exists(AFB02), os.path.exists(AFB03), os.path.exists(AFB04), 
                os.path.exists(AFB0510), os.path.exists(AFB0610), os.path.exists(AFB0710), 
                os.path.exists(AFB8A10), os.path.exists(AFB08), os.path.exists(AFB0910), 
                os.path.exists(AFB1210)
            ]
        ):
            print(print_time() + "Raster_Process :: Start Raster Process Please Wait....")
            Loop_Limit += 1
            t = Timer(3, loadCooldown)
            t.start()
            t.join()

            try:
                print(print_time()+"Raster_Process :: Raster Process " + Full_name[:22])

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
                
                with rasterio.open(AFB08) as src_AFB08, rasterio.open(AFB8A10) as src_AFB8A10:
                    data_AFB08 = src_AFB08.read(1)
                    data_AFB8A10 = src_AFB8A10.read(1)
                    print("Shape of data_AFB08:", data_AFB08.shape)  
                    print("Shape of data_AFB8A:", data_AFB8A10.shape)  

                with rasterio.open(AFB0910) as src_AFB0910:
                    data_AFB0910 = src_AFB0910.read(1) 
                
                with rasterio.open(AFB1210) as src_AFB1210:
                    data_AFB1210 = src_AFB1210.read(1)

                    print("Shape of data_AFB12:", data_AFB1210.shape)

                afb08_shape = data_AFB08.shape
                data_AFB02 = np.resize(data_AFB02, afb08_shape)
                data_AFB03 = np.resize(data_AFB03, afb08_shape)
                data_AFB04 = np.resize(data_AFB04, afb08_shape)
                data_AFB0510 = np.resize(data_AFB0510, afb08_shape)
                data_AFB0610 = np.resize(data_AFB0610, afb08_shape)
                data_AFB0710 = np.resize(data_AFB0710, afb08_shape)
                data_AFB8A10 = np.resize(data_AFB8A10, afb08_shape)
                data_AFB0910 = np.resize(data_AFB0910, afb08_shape)
                data_AFB1210 = np.resize(data_AFB1210, afb08_shape)

                print("Shape of data_AFB02 (Reshape):", data_AFB02.shape) 
                print("Shape of data_AFB03 (Reshape):", data_AFB03.shape)  
                print("Shape of data_AFB04 (Reshape):", data_AFB04.shape)
                print("Shape of data_AFB05 (Reshape):", data_AFB0510.shape)  
                print("Shape of data_AFB06 (Reshape):", data_AFB0610.shape) 
                print("Shape of data_AFB07 (Reshape):", data_AFB0710.shape)  
                print("Shape of data_AFB08 (Reshape):", data_AFB08.shape)  
                print("Shape of data_AFB8A (Reshape):", data_AFB8A10.shape)  
                print("Shape of data_AFB09 (Reshape):", data_AFB0910.shape)  
                print("Shape of data_AFB12 (Reshape):", data_AFB1210.shape) 


                print(print_time()+"  GeoTIFF Process ")
                # File paths for the JP2 band images
                band_paths = [
                    src_AFB02,
                    src_AFB03,
                    src_AFB04,
                    src_AFB0510,
                    src_AFB0610,
                    src_AFB0710,
                    src_AFB08,
                    src_AFB8A10,
                    src_AFB0910,
                    src_AFB1210
                ]

                # List to hold the bands data and metadata
                bands_data = []
                metadata = None

                # Reading the bands without resampling
                for path in band_paths:
                    with rasterio.open(path) as src:
                        data = src.read(1)
                        transform = src.transform
                        
                        # Convert to binary (1-bit) based on a threshold
                        threshold = data.mean()  # This is an example, you can choose a different threshold
                        binary_data = (data > threshold).astype(np.uint8)
                        bands_data.append(binary_data)
                        
                        if metadata is None:
                            # Initialize metadata from the first band
                            metadata = src.meta.copy()
                            metadata.update(
                                count=len(band_paths),
                                dtype='uint8',
                                driver='GTiff',
                                transform=transform,
                                compress='lzw'
                            )

                output_filename = f"{Full_name[:-6]}.tif" 
                output_dir = os.path.join(Rtbcon, Track)
                os.makedirs(output_dir, exist_ok=True)  # Create the subdirectory if it doesn't exist
                output_tif_path = os.path.join(output_dir, output_filename)  # Path to the output TIFF file


                # Writing the combined bands into a single TIFF file with compression
                with rasterio.open(output_tif_path, 'w', **metadata) as dst:
                    for i, band in enumerate(bands_data, start=1):
                        dst.write(band, i)

                # Optionally, print the combined metadata
                print("Combined Metadata with Compression and 1-bit:")
                print(metadata)

                print(print_time()+"  DataFrame Process ")

                # with rasterio.open(AFB08) as src:
                #     bounds = src.bounds
                #     width, height = src.width, src.height
                #     crs = src.crs

                #     lats = np.linspace(bounds.top, bounds.bottom, height)
                #     longs = np.linspace(bounds.left, bounds.right, width)
                #     lon_grid, lat_grid = np.meshgrid(longs, lats)
                #     lat_list = lat_grid.ravel()
                #     lon_list = lon_grid.ravel()

                #     lat_wgs84, lon_wgs84 = transform(crs, 'EPSG:4326', lon_list, lat_list)
                    
                #     band_3_data = data_AFB03.ravel()
                #     band_4_data = data_AFB04.ravel()
                #     band_5_data = data_AFB0510.ravel()
                #     band_6_data = data_AFB0610.ravel()
                #     band_7_data = data_AFB0710.ravel()
                #     band_8_data = data_AFB08.ravel()
                #     band_8A_data = data_AFB8A10.ravel()
                #     band_9_data = data_AFB0910.ravel()
                #     band_12_data = data_AFB1210.ravel()

                #     df = pd.DataFrame({
                #             'Tile': tile,
                #             'Date': date,
                #             'Latitude_WGS84': lon_wgs84, # Lat and lng wgs84 is flip verticle map so i need to swap value 
                #             'Longitude_WGS84': lat_wgs84,
                #             'Band_3_Post': band_3_data,
                #             'Band_4_Post': band_4_data,
                #             'Band_5_Post': band_5_data,
                #             'Band_6_Post': band_6_data,
                #             'Band_7_Post': band_7_data,
                #             'Band_8_Post': band_8_data,
                #             'Band_8A_Post': band_8A_data,
                #             'Band_9_Post': band_9_data,
                #             'Band_12_Post': band_12_data,
                #         })

                #     df.fillna(0, inplace=True)

                #     output_filename = f"{Full_name[:-6]}.csv" 
                #     output_dir = os.path.join(Rtbcon, Track)
                #     os.makedirs(output_dir, exist_ok=True)  # Create the subdirectory if it doesn't exist
                #     output_path = os.path.join(output_dir, output_filename)
                #     df.to_csv(output_path, index=False)

 
                # print(print_time()+"Raster_Process :: Burn Raster Process Complate")


                # # Read true color bands
                # with rasterio.open(AFB02) as src:
                #     band2 = src.read(1)
                #     profile = src.profile

                # with rasterio.open(AFB03) as src:
                #     band3 = src.read(1)

                # with rasterio.open(AFB04) as src:
                #     band4 = src.read(1)

                # true_color_image = np.dstack((band4, band3, band2))

                # true_color_normalized = true_color_image / true_color_image.max()

                # true_color_uint16 = (true_color_normalized * 65535).astype(np.uint16)

                # # Define the output path for the new image
                # output_path = os.path.join(Rtbcon, Track, f"{Mid_name[:-1]}.tif")

                # profile.update(count=3, dtype=rasterio.uint16)

                # with rasterio.open(output_path, 'w', **profile) as dst:
                #     dst.write(true_color_uint16[:, :, 0], 1)  # Red channel
                #     dst.write(true_color_uint16[:, :, 1], 2)  # Green channel
                #     dst.write(true_color_uint16[:, :, 2], 3)  # Blue channel

                # print(f"True color image saved to {output_path}")

                # # Create side by side plots
                # fig, axes = plt.subplots(1, 2, figsize=(8, 5))

                # # Plot true color image
                # axes[0].imshow(true_color_normalized)
                # axes[0].set_title('True Color Image')
                # axes[0].axis('off')

                # plt.tight_layout()
                # plt.show()

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
            print(print_time() + f"Raster_Process :: {Full_name[:22]} Image not Found !!!!")
            print(AFB03, "_", os.path.exists(AFB03))
            print(AFB04, "_", os.path.exists(AFB04))
            print(AFB08, "_", os.path.exists(AFB08))
            Move_File(f"{Mid_name}B03.jp2", os.path.join(Image, Track), os.path.join(Image_Missing, Track))
            Move_File(f"{Mid_name}B04.jp2", os.path.join(Image, Track), os.path.join(Image_Missing, Track))
            Move_File(f"{Mid_name}B08.jp2", os.path.join(Image, Track), os.path.join(Image_Missing, Track))
            Move_File(f"{Mid_name}B12.jp2", os.path.join(Image, Track), os.path.join(Image_Missing, Track))
            Move_File(f"{Mid_name}B1210.jp2", os.path.join(Image, Track), os.path.join(Image_Missing, Track))
            Move_File(f"{Mid_name}B1210.jp2.aux.xml", os.path.join(Image, Track), os.path.join(Image_Missing, Track))
            Move_File(f"{Mid_name}B1210.jp2.ovr", os.path.join(Image, Track), os.path.join(Image_Missing, Track))
            Move_File(f"{Mid_name}B1210.jp2.xml", os.path.join(Image, Track), os.path.join(Image_Missing, Track))
        
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