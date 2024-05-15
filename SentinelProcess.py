import os
import shutil
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from skimage import measure
import rasterio
from rasterio.transform import from_origin
from rasterio.enums import Resampling
from rasterio.warp import transform
import geopandas as gpd
from threading import Timer
import time
import warnings
warnings.filterwarnings(action='ignore')

# Global variables:
systemCooldown = 2
Error_Limit = 1
mode = True

Drive = "/Users/imdsk/RIDA_Tools/Sentinel_Process/"
Image = os.path.join(Drive, "Image")
Image_Pre = os.path.join(Drive, "Image_Pre/")
Image_Finish = os.path.join(Drive, "Image_Finish/")
Image_Missing = os.path.join(Drive, "Image_Missing/")
Output = os.path.join(Drive, "Output/")
Rtbcon = os.path.join(Drive, "Raster_BurnCon/")
Rtbreg = os.path.join(Drive, "Raster_BurnReg/")
RtbShape = os.path.join(Drive, "Raster_BurnShape/")
RtbLevel = os.path.join(Drive, "Raster_BurnLevel/")


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

def write_to_csv(data, file_name_csv):
    try:
        if isinstance(data, np.ndarray):
            data_list = data.tolist()
        else:
            data_list = data

        with open(file_name_csv, 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            for row in data_list:
                csv_writer.writerow(row)
        print(f"Data successfully written to {file_name_csv}")
    except Exception as e:
        print(f"Error writing to CSV file: {e}")

def save_results_to_csv(data_arrays, csv_filenames, window_size, track):
    output_dir = f"output_data/{track}"
    os.makedirs(output_dir, exist_ok=True)
    for data, filename in zip(data_arrays, csv_filenames):
        full_path = os.path.join(output_dir, filename)
        np.savetxt(full_path, data, delimiter=',')

def print_with_tag(data, tag):
    print("------")
    print(tag)
    print(data)
    print("------")

def resample_raster(input_raster, output_raster, new_resolution):
    with rasterio.open(input_raster) as src:
        transform = src.transform
        data = src.read(
            out_shape=(
                src.count,
                int(src.height * src.transform.a / new_resolution),
                int(src.width * src.transform.a / new_resolution)
            ),
            resampling=Resampling.nearest
        )
        profile = src.profile
        profile.update(transform=transform, width=data.shape[2], height=data.shape[1])
        with rasterio.open(output_raster, 'w', **profile) as dst:
            dst.write(data)

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

def Raster_Process(Track):
    global mode, Image, Image_Pre, Image_Finish, Image_Missing, Output, Error_Limit

    Loop_Limit = 0
    image_track = os.path.join(Image, Track)
    output_track = os.path.join(Output, Track)
    rasters = [r for r in os.listdir(image_track) if r.endswith('B12.jp2')]

    for raster in rasters:
        if Loop_Limit > 0:
            mode = True
            return

        Full_name = os.path.splitext(raster)[0]
        Mid_name = Full_name[:23]
        Short_name = Full_name[:6]

        BFB02 = os.path.join(Image_Pre, Track, f"{Short_name}_B02.jp2")
        BFB03 = os.path.join(Image_Pre, Track, f"{Short_name}_B03.jp2")
        BFB04 = os.path.join(Image_Pre, Track, f"{Short_name}_B08.jp2")
        BFB08 = os.path.join(Image_Pre, Track, f"{Short_name}_B08.jp2")
        BFB12 = os.path.join(Image_Pre, Track, f"{Short_name}_B12.jp2")
        BFB1210 = os.path.join(Image_Pre, Track, f"{Short_name}_B1210.jp2")
        BFNBR = os.path.join(Image_Pre, Track, f"{Short_name}_NBR.tif")

        AFB02 = os.path.join(Image, Track, f"{Mid_name}B02.jp2")
        AFB03 = os.path.join(Image, Track, f"{Mid_name}B03.jp2")
        AFB04 = os.path.join(Image, Track, f"{Mid_name}B04.jp2")
        AFB05 = os.path.join(Image, Track, f"{Mid_name}B05.jp2")
        AFB0510 = os.path.join(Image, Track, f"{Mid_name}B0510.jp2")
        AFB06 = os.path.join(Image, Track, f"{Mid_name}B06.jp2")
        AFB0610 = os.path.join(Image, Track, f"{Mid_name}B0610.jp2")
        AFB07 = os.path.join(Image, Track, f"{Mid_name}B07.jp2")
        AFB0710 = os.path.join(Image, Track, f"{Mid_name}B0710.jp2")
        AFB08 = os.path.join(Image, Track, f"{Mid_name}B08.jp2")
        AFB0810 = os.path.join(Image, Track, f"{Mid_name}B0810.jp2")
        AFB8A = os.path.join(Image, Track, f"{Mid_name}B8A.jp2")
        AFB8A10 = os.path.join(Image, Track, f"{Mid_name}B8A10.jp2")
        AFB09 = os.path.join(Image, Track, f"{Mid_name}B09.jp2")
        AFB0910 = os.path.join(Image, Track, f"{Mid_name}B0910.jp2")
        AFB12 = os.path.join(Image, Track, f"{Mid_name}B12.jp2")
        AFB1210 = os.path.join(Image, Track, f"{Mid_name}B1210.jp2")

        print(BFB12)

        if all(
            [ 
                os.path.exists(BFB02),os.path.exists(BFB03),os.path.exists(BFB04),os.path.exists(BFB08), os.path.exists(BFB12),
                os.path.exists(AFB02),os.path.exists(AFB03), os.path.exists(AFB04),os.path.exists(AFB05),os.path.exists(AFB06),os.path.exists(AFB07),os.path.exists(AFB8A),os.path.exists(AFB08), os.path.exists(AFB09), os.path.exists(AFB12)
            ]
        ):
            print(print_time() + "Raster_Process :: Start GIS Process Please Wait....")
            Loop_Limit += 1
            print(print_time() + "Raster_Process :: Delete Old File")
            files = os.listdir(output_track)
            for f in files:
                try:
                    os.remove(os.path.join(output_track, f))
                except Exception as e:
                    print(print_time() + f"Raster_Process :: Cannot Delete {f}")
                    print(print_time() + str(e))
                    break

            print(print_time() + "Raster_Process :: Delete Old File Complete")
            t = Timer(3, loadCooldown)
            t.start()
            t.join()

            def resample_raster(input_raster, output_raster, new_resolution):
                with rasterio.open(input_raster) as src:
                    transform = src.transform
                    data = src.read(
                        out_shape=(
                            src.count,
                            int(src.height * src.transform.a / new_resolution),
                            int(src.width * src.transform.a / new_resolution)
                        ),
                        resampling=Resampling.nearest
                    )
                    profile = src.profile
                    profile.update(transform=transform, width=data.shape[2], height=data.shape[1])
                    with rasterio.open(output_raster, 'w', **profile) as dst:
                        dst.write(data)

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

            if not os.path.exists(BFB1210):
                print(print_time() + "Raster_Process :: Resample " + Short_name)
                resample_raster(BFB12, BFB1210, 10)
            
            if not os.path.exists(AFB0510):
                print(print_time() + "Raster_Process :: Resample " + Short_name + "B05")
                resample_raster(AFB05, AFB0510, 10)

            if not os.path.exists(AFB0610):
                print(print_time() + "Raster_Process :: Resample " + Short_name + "B06")
                resample_raster(AFB06, AFB0610, 10)
            
            if not os.path.exists(AFB0710):
                print(print_time() + "Raster_Process :: Resample " + Short_name + "B07")
                resample_raster(AFB07, AFB0710, 10)

            if not os.path.exists(AFB0810):
                print(print_time() + "Raster_Process :: Resample " + Short_name + "B08")
                resample_raster(AFB08, AFB0810, 10)
            
            if not os.path.exists(AFB8A10):
                print(print_time() + "Raster_Process :: Resample " + Short_name + "B8A")
                resample_raster(AFB8A, AFB8A10, 10)

            if not os.path.exists(AFB0910):
                print(print_time() + "Raster_Process :: Resample " + Short_name + "B09")
                resample_raster(AFB09, AFB0910, 10)

            if not os.path.exists(AFB1210):
                print(print_time() + "Raster_Process :: Resample " + Mid_name)
                resample_raster(AFB12, AFB1210, 10)

            try:
                print(print_time() + "Raster_Process :: Raster Process " + Full_name[:22])
                with rasterio.open(BFB02) as src_BFB02, rasterio.open(AFB02) as src_AFB02:
                    data_BFB02 = src_BFB02.read(1)
                    data_AFB02 = src_AFB02.read(1)
                with rasterio.open(BFB03) as src_BFB03, rasterio.open(AFB03) as src_AFB03:
                    data_BFB03 = src_BFB03.read(1)
                    data_AFB03 = src_AFB03.read(1)
                with rasterio.open(BFB04) as src_BFB04, rasterio.open(AFB04) as src_AFB04:
                    data_BFB04 = src_BFB04.read(1)
                    data_AFB04 = src_AFB04.read(1)
                with rasterio.open(AFB0510) as src_AFB0510:
                    data_AFB0510 = src_AFB0510.read(1)
                with rasterio.open(AFB0610) as src_AFB0610:
                    data_AFB0610 = src_AFB0610.read(1)
                with rasterio.open(AFB0710) as src_AFB0710:
                    data_AFB0710 = src_AFB0710.read(1)
                with rasterio.open(BFB08) as src_BFB08, rasterio.open(AFB08) as src_AFB08, rasterio.open(AFB8A10) as src_AFB8A10:
                    data_BFB08 = src_BFB08.read(1)
                    data_AFB08 = src_AFB08.read(1)
                    data_AFB8A10 = src_AFB8A10.read(1)
                with rasterio.open(AFB0910) as src_AFB0910:
                    data_AFB0910 = src_AFB0910.read(1)
                with rasterio.open(BFB1210) as src_BFB1210, rasterio.open(AFB1210) as src_AFB1210:
                    data_BFB1210 = src_BFB1210.read(1)
                    data_AFB1210 = src_AFB1210.read(1)

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

                PreNBR_data = (data_BFB08 - data_BFB1210) / (data_BFB08 + data_BFB1210)
                PostNBR_data = (data_AFB08 - data_AFB1210) / (data_AFB08 + data_AFB1210)
                rNDI = (data_BFB08 - data_AFB08) / (data_BFB08 + data_AFB08)
                dNBR = PreNBR_data - PostNBR_data
                dNDWI = (data_AFB03 - data_AFB08) / (data_AFB03 + data_AFB08)
                dNDVI = (data_AFB08 - data_AFB04) / (data_AFB08 + data_AFB04)

                def burn_con_lv1(rNDI, output_path):
                    burn_con_lv1 = np.where((rNDI > 0.3), 1, 0)
                    burn_con_lv1 = np.where(
                        np.any(
                            (
                                (data_AFB08 < 100),
                            ),
                            axis=0,
                        ),
                        0,
                        burn_con_lv1,
                    )
                    save_as_geotiff(burn_con_lv1, output_path)

                output_path = RtbLevel + Track + Full_name + "_Lv1.tif"
                burn_con_lv1(rNDI, output_path)

                BCONLV1 = os.path.join(RtbLevel, Track, f"{Full_name}_Lv1.tif")
                with rasterio.open(BCONLV1) as src_BCONLV1:
                    data_BCONLV1 = src_BCONLV1.read(1)

                def burn_regionlv1(data_BCONLV1, track, full_name):
                    burnRegionGrp = measure.label(data_BCONLV1, connectivity=2)
                    burnRegionGrpThresholded = np.where(burnRegionGrp > 0, 1, 0)
                    burnRegionLv1 = np.where(burnRegionGrpThresholded == 1, 1, 0)
                    output_path = Rtbreg + track + Short_name + "_B12" + "_Lv1" + ".tif"
                    save_as_geotiff(burnRegionLv1, output_path)
                    return burnRegionLv1

                burn_regionlv1(data_BCONLV1, Track, Full_name)

                def burn_con_lv2(rNDI, data_AFB03, data_AFB08, output_path):
                    burn_con_lv1 = np.where((rNDI > 0.3), 1, 0)
                    burn_con_lv2 = np.where(((burn_con_lv1 == 1) & (data_AFB08 > data_AFB03)), 1, 0)
                    burn_con_lv2 = np.where(
                        np.any(
                            (
                                (data_AFB08 < 100),
                            ),
                            axis=0,
                        ),
                        0,
                        burn_con_lv2,
                    )
                    save_as_geotiff(burn_con_lv2, output_path)

                output_path = RtbLevel + Track + Full_name + "_Lv2.tif"
                burn_con_lv2(rNDI, data_AFB03, data_AFB08, output_path)

                BCONLV2 = os.path.join(RtbLevel, Track, f"{Full_name}_Lv2.tif")
                with rasterio.open(BCONLV2) as src_BCONLV2:
                    data_BCONLV2 = src_BCONLV2.read(1)

                def burn_regionlv2(data_BCONLV2, track, full_name):
                    burnRegionGrp = measure.label(data_BCONLV2, connectivity=2)
                    burnRegionGrpThresholded = np.where(burnRegionGrp > 0, 1, 0)
                    burnRegionLv2 = np.where(burnRegionGrpThresholded == 1, 1, 0)
                    output_path = Rtbreg + track + Short_name + "_B12" + "_Lv2" + ".tif"
                    save_as_geotiff(burnRegionLv2, output_path)
                    return burnRegionLv2

                burn_regionlv2(data_BCONLV2, Track, Full_name)

                def burn_con_lv3(dNDVI, rNDI, data_AFB08, data_AFB03, output_path):
                    burn_con_lv1 = np.where((rNDI > 0.3), 1, 0)
                    burn_con_lv2 = np.where((data_AFB08 > data_AFB03), 1, 0)
                    burn_con_lv3 = np.where(((burn_con_lv1 == 1) & (burn_con_lv2 == 1) & (dNDVI < 0.14)), 1, 0)
                    burn_con_lv3 = np.where(
                        np.any(
                            (
                                (data_AFB08 < 100),
                            ),
                            axis=0,
                        ),
                        0,
                        burn_con_lv3,
                    )
                    save_as_geotiff(burn_con_lv3, output_path)

                output_path = RtbLevel + Track + Full_name + "_Lv3.tif"
                burn_con_lv3(dNDVI, rNDI, data_AFB08, data_AFB03, output_path)

                BCONLV3 = os.path.join(RtbLevel, Track, f"{Full_name}_Lv3.tif")
                with rasterio.open(BCONLV3) as src_BCONLV3:
                    data_BCONLV3 = src_BCONLV3.read(1)

                def burn_regionlv3(data_BCONLV3, track, full_name):
                    burnRegionGrp = measure.label(data_BCONLV3, connectivity=2)
                    burnRegionGrpThresholded = np.where(burnRegionGrp > 0, 1, 0)
                    burnRegionLv3 = np.where(burnRegionGrpThresholded == 1, 1, 0)
                    output_path = Rtbreg + track + Short_name + "_B12" + "_Lv3" + ".tif"
                    save_as_geotiff(burnRegionLv3, output_path)
                    return burnRegionLv3

                burn_regionlv3(data_BCONLV3, Track, Full_name)

                def burn_con_lv4(data_AFB08, rNDI, data_AFB03, dNDVI, output_path):
                    burn_con_lv1 = np.where((rNDI > 0.3), 1, 0)
                    burn_con_lv2 = np.where((data_AFB08 > data_AFB03), 1, 0)
                    burn_con_lv3 = np.where((dNDVI < 0.14), 1, 0)
                    burn_con_lv4 = np.where(((burn_con_lv1 == 1) & (burn_con_lv2 == 1) & (burn_con_lv3 == 1) & (data_AFB08 < 2000)), 1, 0)
                    burn_con_lv4 = np.where(
                        np.any(
                            (
                                (data_AFB08 < 100),
                            ),
                            axis=0,
                        ),
                        0,
                        burn_con_lv4,
                    )
                    save_as_geotiff(burn_con_lv4, output_path)

                output_path = RtbLevel + Track + Full_name + "_Lv4.tif"
                burn_con_lv4(data_AFB08, rNDI, data_AFB03, dNDVI, output_path)

                BCONLV4 = os.path.join(RtbLevel, Track, f"{Full_name}_Lv4.tif")
                with rasterio.open(BCONLV4) as src_BCONLV4:
                    data_BCONLV4 = src_BCONLV4.read(1)

                def burn_regionlv4(data_BCONLV4, track, full_name):
                    burnRegionGrp = measure.label(data_BCONLV4, connectivity=2)
                    burnRegionGrpThresholded = np.where(burnRegionGrp > 0, 1, 0)
                    burnRegionLv4 = np.where(burnRegionGrpThresholded == 1, 1, 0)
                    output_path = Rtbreg + track + Short_name + "_B12" + "_Lv4" + ".tif"
                    save_as_geotiff(burnRegionLv4, output_path)
                    return burnRegionLv4

                burn_regionlv4(data_BCONLV4, Track, Full_name)

                def burn_con(rNDI, dNDVI, data_AFB03, data_AFB08, output_path):
                    burn_con_lv1 = np.where((rNDI > 0.3), 1, 0)
                    burn_con_lv2 = np.where((data_AFB08 > data_AFB03), 1, 0)
                    burn_con_lv3 = np.where((dNDVI < 0.14), 1, 0)
                    burn_con_lv4 = np.where((data_AFB08 < 2000), 1, 0)
                    burnCon_Final = np.where(((burn_con_lv1 == 1) & (burn_con_lv2 == 1) & (burn_con_lv3 == 1) & (burn_con_lv4 == 1)), 1, 0)
                    burnCon_Final = np.where(
                        np.any(
                            (
                                (data_AFB08 < 100),
                            ),
                            axis=0,
                        ),
                        0,
                        burnCon_Final,
                    )
                    save_as_geotiff(burnCon_Final, output_path)

                output_path = Rtbcon + Track + Full_name + ".tif"
                burn_con(rNDI, dNDVI, data_AFB03, data_AFB08, output_path)

                BCON = os.path.join(Rtbcon, Track, f"{Full_name}.tif")
                with rasterio.open(BCON) as src_BCON:
                    data_BCON = src_BCON.read(1)

                def burn_region(data_BCON, track, full_name):
                    burnRegionGrp = measure.label(data_BCON, connectivity=1)
                    burnRegionGrpThresholded = np.where(burnRegionGrp > 0, 1, 0)
                    burnRegion = np.where(burnRegionGrpThresholded == 1, 1, 0)
                    output_path = Rtbreg + track + Short_name + "_B12" + ".tif"
                    save_as_geotiff(burnRegion, output_path)
                    return burnRegion

                burn_region(data_BCON, Track, Full_name)

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

                    rNDI_data = rNDI.ravel()
                    dNBR_data = dNBR.ravel()
                    band_3_data = data_AFB03.ravel()
                    band_4_data = data_AFB04.ravel()
                    band_5_data = data_AFB0510.ravel()
                    band_6_data = data_AFB0610.ravel()
                    band_7_data = data_AFB0710.ravel()
                    band_8_data = data_AFB08.ravel()
                    band_8A_data = data_AFB8A10.ravel()
                    band_9_data = data_AFB0910.ravel()
                    band_12_data = data_AFB1210.ravel()
                    PostNBR_data = PostNBR_data.ravel()
                    ndvi_data = dNDVI.ravel()
                    ndwi_data = dNDWI.ravel()
                    level_1_data = burn_regionlv1(data_BCONLV1, Track, Full_name).ravel()
                    level_2_data = burn_regionlv2(data_BCONLV2, Track, Full_name).ravel()
                    level_3_data = burn_regionlv3(data_BCONLV3, Track, Full_name).ravel()
                    level_4_data = burn_regionlv4(data_BCONLV4, Track, Full_name).ravel()
                    label_data = burn_region(data_BCON, Track, Full_name).ravel()

                    df = pd.DataFrame({
                        'Latitude_WGS84': lon_wgs84,
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
                        'PostNBR': PostNBR_data,
                        'NDVI': ndvi_data,
                        'NDWI': ndwi_data,
                        'dNBR': dNBR_data,
                        'rNDI': rNDI_data,
                        'Level_1': level_1_data,
                        'Level_2': level_2_data,
                        'Level_3': level_3_data,
                        'Level_4': level_4_data,
                        'Label': label_data
                    })

                    df.fillna(0, inplace=True)
                    output_filename = f"{Full_name}_burn_data.csv"
                    output_path = os.path.join(Rtbcon + Track, output_filename)
                    df.to_csv(output_path, index=False)

                print(print_time() + "Raster_Process :: Burn Raster Process Complete")

                def reclassify_raster(input_raster, output_raster, remap_dict):
                    with rasterio.open(input_raster) as src:
                        data = src.read(1)
                        profile = src.profile
                        for old_value, new_value in remap_dict.items():
                            data = np.where(data == old_value, new_value, data)
                        with rasterio.open(output_raster, 'w', **profile) as dst:
                            dst.write(data, 1)

                burnRegion = os.path.join(Rtbreg, Track, f"{Short_name}_B12.tif")
                burnReclass = os.path.join(Rtbreg, Track, f"{Short_name}_BurnReclass.tif")
                remap_dict = {1: 1}
                reclassify_raster(burnRegion, burnReclass, remap_dict)

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
                        dissolved_gdf.to_file(output_shapefile)

                burnReclass = os.path.join(Rtbreg, Track, f"{Short_name}_BurnReclass.tif")
                output_shapefile = RtbShape + Track + Short_name + "_B12" + ".shp"
                simplify_value = 0.1
                raster_to_polygon(burnReclass, output_shapefile, simplify=simplify_value)

                print(print_time() + "Raster_Process :: Start Move File ")
                Move_File(Mid_name + "B03.jp2", Image + Track, Image_Finish + Track)
                Move_File(Mid_name + "B04.jp2", Image + Track, Image_Finish + Track)
                Move_File(Mid_name + "B08.jp2", Image + Track, Image_Finish + Track)
                Move_File(Mid_name + "B12.jp2", Image + Track, Image_Finish + Track)
                Move_File(Mid_name + "B1210.jp2", Image + Track, Image_Finish + Track)
                Move_File(Mid_name + "B1210.jp2.aux.xml", Image + Track, Image_Finish + Track)
                Move_File(Mid_name + "B1210.jp2.ovr", Image + Track, Image_Finish + Track)
                Move_File(Mid_name + "B1210.jp2.xml", Image + Track, Image_Finish + Track)
                Error_Limit = 2
                print(print_time() + "Raster_Process :: Raster_Process ALL Complete >>>>>>>>>>>>>>>>>>>> \n \n")

                shapefile_path = os.path.join(RtbShape, Track, f"{Short_name}_B12.shp")
                image_path = os.path.join(Image, Track, f"{Full_name}10.jp2")
                gdf = gpd.read_file(shapefile_path)
                image = plt.imread(image_path)
                fig, ax = plt.subplots(figsize=(16, 16))
                ax.imshow(image, cmap='gray')
                gdf.plot(ax=ax, color='red', edgecolor='red', alpha=.5)
                ax.set_title('Shapefile on Top of Image')
                plt.show()

            except Exception as e:
                print(print_time() + "Raster_Process :: !!!!!!!!!! RASTER ERROR !!!!!!!!!!")
                print(print_time() + str(e))
                Error_Limit -= 1
                if Error_Limit < 1:
                    print(print_time() + "Raster_Process :: !!!!!!!!!! RASTER ERROR 2 Times MoveFile to Image_Missing")
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
            print(BFB03, "_", os.path.exists(BFB03))
            print(BFB04, "_", os.path.exists(BFB04))
            print(BFB08, "_", os.path.exists(BFB08))
            print(BFB12, "_", os.path.exists(BFB12))
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
